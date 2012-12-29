#! /usr/bin/python2
# encoding: utf-8
# Copyright Altaire bot © Assassin, 2011 - 2012
# This program published under Apache 2.0 license
# See LICENSE.txt for more details
# My EMail: assassin@sonikelf.ru
# Altaire bot for your XMPP-conference
# kernel

# ToDo:
# [core]	rewrite configs with using ConfigParser (rewtite jid's class) (likely done)		(critical)
# [package]	alive_keeper/jids																(optional)
# [package]	alive_keeper/conferences														(optional)
# [package]	send/send (finish)																(optional)
# [core]	доделать систему обработки обновления файлов (которая нужна для send/send)		(optional)
# [core]	доделать систему двух локализаций

import sys, os, gc
from traceback import format_exc
from time import sleep, time
gc.enable()

version = '0.15.2 Alpha Unpublic'

core = os.path.abspath(__file__)
coreDir = os.path.split(core)[0]
if coreDir: os.chdir(coreDir)
pid = os.getpid()

sys.path.insert(0, 'libs')


# print with colors
red		= '1' # errors
green	= '2' # success
brown	= '3' # no-space messages
blue	= '4' # system's messages

def Print(text, color = None, nospace = False):
	try:
		if color and xmpp.debug.colors_enabled:
			text = '%s[3%sm%s%s[0m' % (chr(27), color, text, chr(27))
		if nospace:
			sys.stdout.write(text)
			sys.stdout.flush()
		else: print(text)
	except: pass


try:
	reload(sys).setdefaultencoding('utf8')
except:
	Print('Error while setting default encoding', red)

get_connect_jid = \
	lambda disp: u'%s@%s' % (disp._owner.User, disp._owner.Server)
get_bot_nick = \
	lambda conf: JIDS[search_conf(conf)].conferences[conf].nick
get_connect = \
	lambda jid: JIDS[jid].connect
popen = \
	lambda text: unicode(os.popen('sh -c "%s" 2>&1' % text).read())

# crashlogger
def crash(com = None): 
	if com:
		repo(translate['errorCom'] % (com, format_exc()))
	else:
		repo(translate['error'] % format_exc())

# get and set the config.ini
def setMainCofig():
	import ConfigParser
	CP = ConfigParser.ConfigParser()
	CP.read('other/config.ini')
	global language
	language = CP.get('LANGUAGES', 'LANGUAGE').upper()
	status = CP.get('INFORMATION', 'STATUS')
	default_nick = CP.get('INFORMATION', 'NICK')
	admins = CP.get('INFORMATION', 'STATUS').split()
	antispam_limit = CP.getfloat('ANTISPAM', 'LIMIT')
	antispam_polices = CP.getint('ANTISPAM', 'POLICES')
	limits = \
		{'memory': CP.getint('LIMITS', 'MEMORY'),
		'chat': CP.getfloat('LIMITS', 'CHAT MESSAGE'),
		'roster': CP.getfloat('LIMITS', 'ROSTER MESSAGE'),
		'private': CP.getfloat('LIMITS', 'PRIVATE MESSAGE')}

# get and set the jids.ini
def setJidsConfig():
	import ConfigParser
	CP = ConfigParser.ConfigParser()
	CP.read('other/jids.ini')
	global jids
	jids = dict()
	for jid in CP.sections():
		jids['%s@%s' % (CP.get(jid, 'USER'), CP.get(jid, 'SERVER'))] = \
			{'port': CP.getint(jid, 'PORT'),
			'host': CP.get(jid, 'HOST'),
			'password': CP.get(jid, 'PASSWORD'),
			'tls': CP.getboolean(jid, 'TLS'),
			'resource': CP.get(jid, 'RESOURCE')}

# operations with files
def File(confFile, text = None, ini = False):
	if text is None:
		if os.path.exists(confFile):
			info['rFile'] += 1
			noSetFile = open(confFile, 'r')
			text = noSetFile.read()
			noSetFile.close()
			return text.decode('utf8')
		else:
			return File(confFile, str())
	else:
		if ini:
			if os.path.exists(confFile):
				return File(confFile)
			else:
				return File(confFile, text)
		else:
			confFile, text = unicode(confFile), unicode(text)
			info['wFile'] += 1
			folder = os.path.dirname(confFile)
			if folder and not os.path.exists(folder):
				os.makedirs(folder)
			noSetFile = open(confFile, 'w')
			noSetFile.write(text)
			noSetFile.close()
			return text

access = \
	{'participant': 1,
	'moderator': 2,
	'admin': 1,
	'owner': 2,
	'none': 0,
	'visitor': 0,
	'member': 0}

info = \
	{'comms': 	int(),
	'inMsg': 	int(),
	'outMsg': 	int(),
	'rFile': 	int(),
	'wFile': 	int(),
	'prs': 		int(),
	'iq': 		int(),
	'handlers': int()}
handlers = \
		{
		'after_load_plugins': {'list': list(), 'executed': False},
		'join': {'list': list(), 'executed': False}, # (self.conference, self.connect, self.nick, self.status, self.statusShow, self.password)
		'leave': {'list': list(), 'executed': False}, # (self.conference)
		'after_joins': {'list': list(), 'executed': False},
		'after_load_jids': {'list': list(), 'executed': False},
		}

def register_handler(func, group, now = False):
	if func not in handlers[group]['list']:
		handlers[group]['list'].append(func)
	if handlers[group]['executed']:
		smartThr.Thread(None, func, 'handler-%s-%s-%d' % (group, func.func_name, info['handlers'])).start()
		info['handlers'] += 1
	elif (group == 'join') and now:
		for jid in JIDS:
			for conf in JIDS[jid]['conferences']:
				smartThr.Thread(None, func, 'handler-%s-%s-%d' % (group, func.func_name, info['handlers']), (conf, JIDS[jid].connect, JIDS[jid]['conferences'][conf].nick, JIDS[jid]['conferences'][conf].status, JIDS[jid]['conferences'][conf].statusShow, JIDS[jid]['conferences'][conf].password)).start()
				info['handlers'] += 1

def execute_handlers(group, parameters = None):
	if group in ('after_load_plugins', 'after_load_jids', 'after_joins'):
		handlers[group]['executed'] = True
	for func in handlers[group]['list']:
		smartThr.Thread(None, func, 'handler-%s-%s-%d' % (group, func.func_name, info['handlers']), parameters).start()
		info['handlers'] += 1

JIDS = dict()
dialogues = dict()
commands = dict()
flooders = dict()
translate = {'comms': dict()}
blocked_chats = eval(File('other/blocked_chats.list', list(), True))
blocked_jids = eval(File('other/blocked_jids.list', list(), True))


# debug
def hand(func, params, com = None):
	try:
		func(*params)
	except (KeyboardInterrupt, SystemExit):
		pass
	except:
		crash(com)

rawMsg = lambda connect, msgtype, jid, text: \
	connect.send(xmpp.Message(jid, text, msgtype))
	

# answer (syntax: fmsg(source, text)) (using msg)
fmsg = lambda source, text: \
	msg(source[0], source[1], source[2], text)

# send messages
def msg(connect, msgtype, jid, text):
	text = text.decode('utf8', 'replace')
	while len(text) > limits[msgtype]:
		connect.send(xmpp.Message(jid, u'%s...' % text[:limits[msgtype]], msgtype)) # text[:512] + u'...', 
		text = text[limits[msgtype]:]
	if msgtype in ('private', 'chat'):
		rawMsg(connect, 'chat', jid, text)
	else:
		chat, nick = jid.split('/')
		rawMsg(connect, 'groupchat', chat, u'%s: %s' % (nick, text))
	info['outMsg'] += 1



# work with groupchats file
def refesh_group_file(chat, delete = False):
	jid = search_conf(chat)
	if delete:
		del notSetConferences[jid][chat]
	else:
		if not notSetConferences.has_key(jid):
			confFile[jid] = dict()
		if not notSetConferences[jid].has_key(chat):
			notSetConferences[jid][chat] = dict()
		notSetConferences[jid][chat]['password'] = JIDS[jid].conferences[chat].password
		notSetConferences[jid][chat]['nick'] = JIDS[jid].conferences[chat].nick
		notSetConferences[jid][chat]['status'] = JIDS[jid].conferences[chat].status
	File('other/groupchats.dict', notSetConferences)

def isNumber(text):
	try: int(text)
	except: return False
	else: return True

replaceHTML = lambda text: HTMLParser().unescape(text)

def enumerateLines(list):
	temp = unicode()
	for number, var in enumerate(list):
		temp += u'%d) %s' % (number + 1, var)
	return temp

# classes

# exceptions (new format (Python > 2.5))
class Error(Exception): pass

class user:
	# users in conferences
	__slots__ = ('conference', 'jid', 'role', 'joinTime', 'online')
	def __init__(self, jid, role, conference):
		self.conference = conference
		self.jid = jid
		seld.role = role
		self.joinTime = time()
		self.online = True
	access = lambda self: access[self.role[0]] + access[self.role[1]]

class command:
	__slots__ = ('loaded', 'comstat', 'func', 'access', 'used',
		'commands', 'help')
	def __init__(self, comstat, func, acc = 1):
		self.loaded = False
		self.comstat = comstat
		self.func = func
		self.access = acc
		self.used = int()
	def load(self):
		if self.loaded: raise Error('alreadly loaded')
		else:
			comfile = File(u'locales/%s.%s.comms' % (self.comstat, language)).splitlines()
			if len(comfile) == 2:
				translate['comms'][self.comstat] = eval(comfile[1])
			self.commands = eval(comfile[0])
			self.help = u'locales/%s.%s.help' % (self.comstat, language)
			self.loaded = True
	def unload(self):
		if self.loaded:
			del self.commands, self.help
			self.loaded = False
		else: raise Error('not loaded')
	def reload(self):
		if self.loaded:
			self.unload()
			self.load()
		else: raise Error('not loaded')

class conference:
	__slots__ = ('conference', 'joined', 'connect', 'password',
		'nick', 'status', 'statusShow', 'users', 'notAdmin')
	__str__ = lambda: self.conference
	def __init__(self, connect, conference):
		self.conference = conference
		self.joined = False
		self.connect = connect
	def join(self, password = None, nick = None, status = None, auto = False):
		bot_jid = get_connect_jid(self.connect)
		if not nick: nick = default_nick
		if not status: status = status
		if self.joined: raise Error('already joined')
		else:
			self.password = password
			self.nick = nick
			self.status = status
			self.statusShow = 'chat'
			self.users = dict()
			self.notAdmin = False
			self.joined = True
			if not auto:
				refesh_group_file(self.conference)
			notSetJoinPresence = xmpp.protocol.Presence(u'%s/%s' % (self.conference, nick))
			notSetJoinPresence.setTag("c", namespace = xmpp.NS_CAPS, attrs = \
				{'node': 'http://code.google.com/p/altaire/xmpp/caps#Altaire',
				'ver': version})
			notSetPresenceJoin = notSetJoinPresence.setTag("x", namespace = xmpp.NS_MUC)
			notSetPresenceJoin.addChild("history", {"maxchars": "0"})
			notSetJoinPresence.setStatus(status)
			notSetJoinPresence.setShow("chat")
			if password:
				notSetPresenceJoin.setTagData("password", password)
			self.connect.send(notSetJoinPresence)
			execute_handlers('join', (self.conference, self.connect, self.nick, self.status, self.statusShow, self.password))
	# leave of conference
	def leave(self, auto = False):
		if self.joined:
			execute_handlers('leave', (self.conference))
			self.connect.send(xmpp.Presence(self.conference, 'unavailable'))
			self.joined = False
			if not auto:
				refesh_group_file(self.conference, True)
		else:
			raise Error('not joined')
	# leave and join to conference
	def rejoin(self, code = None, auto = False):
		if self.joined:
			if code == 1:
				self.nick = u'-%s-' % self.nick
			elif code == 2:
				self.status = status
			if not auto: self.leave(True)
			self.join(self.password, self.nick, self.status, True)
		else:
			raise Error('not joined')
	# set status in conference
	def setStatus(self, message = None, status = None, auto = False):
		if not message:
			message = self.status
		if not status:
			status = self.statusShow
		prs = xmpp.protocol.Presence(u'%s/%s' % (self.conference, self.nick))
		prs.setStatus(message)
		prs.setShow(status)
		prs.setTag('c', namespace = xmpp.NS_CAPS, attrs = \
			{'node': 'http://bottiks.tk/xmpp/bots/caps#Altaire',
			'ver': version})
		self.connect.send(prs)
		if not auto:
			self.status = message
			self.statusShow = status
	# system's command
	def send_iq(self, nameItem, item, afrls, afrl, reason = None):
		iq = xmpp.Iq(to = self.conference, typ = 'set')
		query = xmpp.Node('query')
		query.setNamespace(xmpp.NS_MUC_ADMIN)
		role = query.addChild('item', {nameItem: item, afrls: afrl})
		if rsn: role.setTagData('reason', reason)
		iq.addChild(node = query)
		self.connect.send(iq)
	# jid in parameters
	def ban(self, jid, reason = None):
		self.send_iq('jid', jid, 'affiliation', 'outcast', reason)
	def none(self, jid, reason = None):
		self.send_iq('jid', jid, 'affiliation', 'none', reason)
	def member(self, jid, reason = None):
		self.send_iq('jid', jid, 'affiliation', 'member', reason)
	def admin(self, jid, reason = None):
		self.send_iq('jid', jid, 'affiliation', 'admin', reason)
	def owner(self, jid, reason = None):
		self.send_iq('jid', jid, 'affiliation', 'owner', reason)
	# nick in parameters
	def kick(self, nick, reason = None):
		self.send_iq('nick', nick, 'role', 'none', reason)
	def visitor(self, nick, reason = None):
		self.send_iq('nick', nick, 'role', 'visitor', reason)
	def participant(self, nick, reason = None):
		self.send_iq('nick', nick, 'role', 'participant', reason)
	def moderator(self, nick, reason = None):
		self.send_iq('nick', nick, 'role', 'moderator', reason)
	def set_bot_nick(self, newNick):
		self.users[newNick] = self.users.pop(self.nick)
		self.nick = newNick
		refesh_group_file(self.conference)
		self.rejoin(None, True)
		#############
		#############		#############
		#############		#############
		#############		#############
		#############
##############################################

def load_package(pack):
	for packFile in os.listdir('packages/%s' % pack):
			if os.path.isfile(os.path.join('packages/%s' % pack, packFile)) \
			and packFile.endswith('.py'):
				execfile('packages/%s/%s' % (pack, packFile), globals())

def processes(connect):
	jid = get_connect_jid(connect)
	while JIDS.has_key(jid) and connect.isConnected():
		try:
			connect.Process()
		except xmpp.Conflict:
			bot_off('XMPP conflict', jid)
		except:
			crash()
			continue

def search_command(com):
	for comstat, key in commands.items():
		if key.loaded and (com in key.commands):
			return comstat
	return None

def min_confs():
	confs = dict()
	for jid in JIDS:
		confs[len(JIDS[jid].conferences.keys())] = jid
	return confs[min(confs.keys())]

def search_conf(conference):
	for jid in JIDS:
		if JIDS[jid].conferences.has_key(conference):
			return jid
	return None


def get_jid(jid):
	if jid.count('/'):
		conference, user = jid.split('/')
		temp = search_conf(conference)
		if temp:
			return JIDS[temp].conferences[conference].users[user].jid
		else:
			return conference
	else:
		return jid

def bot_off(reason = None, jid = None, reloadJid = False):
	if jid:
		if reloadJid: JIDS[jid].reconnect()
		else:
			if get_connect(jid).isConnected():
				JIDS[jid].disconnect(reason)
			del JIDS[jid]
			for jid in JIDS:
				if JIDS[jid]['connect'].isConnected():
					return
			bot_off(reason)
	else:
		if reason:
			Print(chr(10) + 'Altaire XMPP bot aborting: ' + reason, blue)
		else:
			Print(chr(10) + 'Altaire XMPP bot aborting', blue)
		for jid in JIDS.keys():
			if get_connect(jid).isConnected():
				JIDS[jid].disconnect()
		if reloadJid:
			os.execl(sys.executable,
			sys.executable, core)
		else:
			os._exit(0)

def access(jid):
	if jid.count('/'):
		conference, nick = jid.split('/')
		temp = search_conf(conference)
		if temp:
			if get_jid(jid) in admins:
				return 9
			else:
				JIDS[temp].conferences[conference].users[nick].access()
		else:
			jid = conference
	return (9 if jid in admins else 1)

def reg_command(comstat, func, acc = 1):
	commands[comstat] = command(comstat, func, acc)
	commands[comstat].load()

def repo(message):
	for jid in JIDS:
		connect = get_connect(jid)
		if connect.isConnected():
			for user in admins:
				msg(connect, 'chat', user, message)
			return
	File('REPO', File('REPO', str(), True) + message + (chr(10) * 2))

def checkRepo():
	readed = File('REPO')
	if readed:
		repo(translate['repo'] + readed)
		File('REPO', str())

# only for linux
def getMemory():
	lines = popen('ps -o rss -p %d' % pid).splitlines()
	if len(lines) >= 2:
		return lines[1].strip()
	else: return int()

def dispatcher():
	while True:
		sleep(240)
		if getMemory() > limits['memory']:
			bot_off(translate['memoryLeak'])
		gc.collect()

class JID:
	def __init__(self, jid, dictionary):
		self.jid = jid
		self.user, self.server = jid.split('@')
		self.port = dictionary['port']
		self.host = dictionary['host']
		self.password = dictionary['password']
		self.tls = dictionary['tls']
		self.resource = dictionary['resource']
		self.connect = xmpp.Client(self.host, self.port, None)
		self.conferences = dict()
	def auth(self):
		Print('Connection to server %s (:%i):  ' % (self.server, self.port), brown, True)
		if self.connect.connect((self.server, self.port), None, (None if self.tls else False), (False if self.tls else True)):
			Print('OK', green)
			Print('Authentication:  ', brown, True)
			if self.connect.auth(self.host, self.password, self.resource):
				Print('OK', green)
				self.connect.sendInitPresence()
				self.connect.getRoster()
				self.connect.RegisterHandler('message', inputHandlers.message)
				self.connect.RegisterHandler('presence', inputHandlers.presence)
				self.connect.RegisterHandler('iq', inputHandlers.iq)
				smartThr.Thread(None, hand, 'processes-%s' % self.jid, (processes,
					(self.connect,),)).start()
				return True
			else: return False
		else: return False
	def disconnect(self, reason = None):
		if self.connect.isConnected():
			notSetPresenceOffline = xmpp.Presence(None, 'unavailable')
			if reason:
				notSetPresenceOffline.setStatus(reason)
			self.connect.send(notSetPresenceOffline)
	def reconnect(self, reason = None):
		self.disconnect(reason)
		self.connect()





if (os.name != 'posix') and ('force' not in sys.argv):
	bot_off('Altaire XMPP bot working only on POSIX systems (if you know what are you doing use parameter "force")')

# getting configs (config.ini, jids.ini)
setMainCofig()
setJidsConfig()

import smartThr, inputHandlers, xmpp
execfile('locales/%s' % language)
for packDir in os.listdir('packages'):
	if os.path.isdir(os.path.join('packages', packDir)) and packDir != '.svn':
		load_package(packDir)

notSetConferences = eval(File('other/groupchats.dict', dict(), True))

execute_handlers('after_load_plugins')

for jid in jids:
	try:
		Print(u'< %s >' % jid, blue)
		JIDS[jid] = JID(jid, jids[jid])
		if JIDS[jid].auth():
			Print('Jabber ID %s is successfully initialized\n' % jid, green)
		else:
			Print('Failed\nInitialize of Jabber ID %s is crashed\n' % jid, red)
			del JIDS[jid]
	except KeyboardInterrupt:
		bot_off('CTRL+C')
	except SystemExit: pass

if JIDS:
	Print('All Jabber IDs are initialized', brown)
	smartThr.Thread(None, checkRepo)
	execute_handlers('after_load_jids')
	for jid in JIDS:
		if jid in notSetConferences:
			for chat in notSetConferences[jid]:
				JIDS[jid].conferences[chat] = conference(get_connect(jid), chat)
				JIDS[jid].conferences[chat].join(notSetConferences[jid][chat]['password'],
				notSetConferences[jid][chat]['nick'], notSetConferences[jid][chat]['status'], True)
	execute_handlers('after_joins')
	try:
		dispatcher()
	except KeyboardInterrupt:
		Print(chr(10) + 'Restarting. Press Ctrl+C to exit', blue)
		try:
			sleep(3)
		except KeyboardInterrupt:
			bot_off('CTRL+C')
		else:
			bot_off('CTRL+C', None, True)
	except SystemExit: pass
else:
	bot_off('All initializations of Jabber IDs are crashed')
