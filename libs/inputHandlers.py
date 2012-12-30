# /* encoding: utf-8 */
# Copyright Altaire bot Â© Assassin, 2011 - 2012
# This program published under Apache 2.0 license
# See LICENSE for more details
# My EMail: assassin@sonikelf.ru
# handlers-file for Altaire bot

from __main__ import *

class dialogue:
	def __init__(self, jid, access = 1):
		self.jid = get_jid(jid)
		self.access = access
		self.answers = dict()
	def add_answer(self, answer, func):
		self.answers[answer] = func

def message(connect, SMessage):
	# message handler
	if not SMessage.timestamp:
		text = SMessage.getBody()
		if text:
			text = text.strip().decode('utf8')
			botJid = get_connect_jid(connect)
			type = SMessage.getType()
			fullJid = SMessage.getFrom()
			if type == 'groupchat':
				# message in conference
				try: chat = fullJid.getStripped().decode('utf8')
				except: return
				if chat in blocked_chats: return
				else:
					botNick = get_bot_nick(chat).lower().decode('utf8')
					nick = fullJid.getResource().decode('utf8')
					if text.startswith(botNick):
#						for x in [': ', ', ', '> ', '- ']:
#							text.replace(botNick + x, '')
						text = text[len(botNick) + 2:]
						command = text.lower().split()[0]
					else:
						command = text.lower().split()[0]
						if not search_command(command): return
			elif type == 'chat':
				command = text.lower().split()[0]
				if SMessage.getTag('request'):
					notSetReport = xmpp.Message(fullJid)
					notSetReport.setID(SMessage.getID())
					notSetReport.addChild('received', namespace = xmpp.protocol.NS_RECEIPTS)
					connect.send(notSetReport)
				if fullJid.getStripped() in JIDS \
					[get_connect_jid(connect)].conferences.keys():
					# message in private
					chat = fullJid.getStripped().decode('utf8')
					botNick = get_bot_nick(chat).decode('utf8')
					nick = fullJid.getResource().decode('utf8')
					type = 'private'
				else:
					# message in roster
					chat = None
					botNick = None
					nick = None
			else: return
		else: return
		fullJid = unicode(fullJid).decode('utf8')
		trueJid = get_jid(fullJid).decode('utf8')
		if not trueJid in blocked_jids:
			if flooders.has_key(trueJid):
				timer = time() - flooders[trueJid]['lastMessage']
				if timer < antispam_limit:
					if flooders[trueJid]['police'] > antispam_polices:
						blocked_jids.append(trueJid)
						return
					else: flooders[trueJid]['police'] += 1
				elif timer > 4: flooders[trueJid]['police'] = 0
				flooders[trueJid]['lastMessage'] = time()
			else: flooders[trueJid] = {'police': int(), 'lastMessage': time()}
			info['inMsg'] += 1
			text = text[len(command):].strip()
			if dialogues.has_key(trueJid):
				if access(fullJid) >= dialogues[trueJid].access:
					info['comms'] += 1
					if dialogues[trueJid].answers.has_key(command):
						smartThr.Thread(None, hand, 'command-%d' % info['comms'],
							(dialogues[trueJid].answers[command],
							((connect, type, fullJid, chat, botNick, botJid, nick, trueJid),
							text,), command)).start()
					else: fmsg([connect, type, fullJid], translate['badAnswer'])
				else:
					fmsg([connect, type, fullJid], translate['noAccessDialogue'])
					del dialogues[trueJid]
			else:
				temp = search_command(command)
				if temp:
					if access(fullJid) >= commands[temp].access:
						info['comms'] += 1
						commands[temp].used += 1
						smartThr.Thread(None, hand, 'command-%s-%d' % (temp, info['comms']),
							(commands[temp].function,
							((connect, type, fullJid, chat, botNick, botJid, nick, trueJid),
							text,), temp)).start()
					else: fmsg([connect, type, fullJid], translate['noAccess'])

def presence(connect, SPresence):
	# presence handler
	info['prs'] += 1
	type = SPresence.getType()
	fullJid = SPresence.getFrom()
	conference = fullJid.getStripped().decode('utf8')
	if conference in JIDS[get_connect_jid(connect)].conferences.keys():
		nick = fullJid.getResource().decode('utf8')
		jid = SPresence.getJid()
		botJid = get_connect_jid(connect)
		afl = SPresence.getAffiliation()
		role = SPresence.getRole()
		if type in ('available', None):
			# join to conference
			if jid:
				trueJid = get_jid(jid)
				if JIDS[botJid].conferences[conference].notAdmin:
					JIDS[botJid].conferences[conference].notAdmin.cancel()
					JIDS[botJid].conferences[conference].notAdmin = False
					blocked_chats.remove(conference)
					File('other/blocked_chats.list', blocked_chats)
					setStatus(connect, conference, STATUS)
					msg(connect, 'groupchat', conference, translate['getAdmin'])
					JIDS[botJid].conferences[conference].rejoin(0)
				else:
					JIDS[botJid].conferences[conference].users[nick] = user(jid, role, conference)
			else:
				blocked_chats.append(conference)
				File('other/blocked_chats.list', blocked_chats)
				msg(connect, 'groupchat', conference, translate['notAdmin'])
				setStatus(connect, conference, translate['sleepForAdmin'], 'dnd')
				JIDS[botJid].conferences[conference].notAdmin = \
					smartThr.Timer(40, JIDS[botJid].conferences[conference].leave, ())
				JIDS[botJid].conferences[conference].notAdmin.start()
		elif type == 'unavailable':
			# leave from conference
			reason = SPresence.getReason or SPresence.getStatus()
			if nick == get_bot_nick(conference):
				JIDS[botJid].conferences[conference].leave()
				del JIDS[botJid].conferences[conference]
				if reason == '301': repo(translate['botWasBanned'] % conference)
				elif reason == '307': repo(translate['botWasKicked'] % conference)
			else: JIDS[botJid].conferences[conference].users[nick].online = False
		elif type == 'error':
			errorCode = SPresence.getErrorCode()
			if errorCode == '409': JIDS[botJid].conferences[conference].rejoin(1)
			elif errorCode in ['401', '403', '404', '405', '503']:
				JIDS[botJid].conferences[conference].leave()
				del JIDS[botJid].conferences[conference]
	else:
		if type == 'subscribe':
			connect.send(xmpp.Presence(to=fullJid, typ='subscribed'))
		elif type == 'unsubscribe':
			connect.send(xmpp.Presence(to=fullJid, typ='unsubscribed'))	
				

def iq(connect, SIQ):
	# iq handler
	info['iq'] += 1
	type = SIQ.getType()
	if type == 'get':
		ns = SIQ.getQueryNS()
		if ns in (xmpp.NS_VERSION, xmpp.NS_TIME) or SIQ.getTag('ping'):
			out = SIQ.buildReply('result')
			if ns == xmpp.NS_VERSION:
				IQ_version = out.getTag('query')
				IQ_version.setTagData('os', os.name)
				IQ_version.setTagData('version', version)
				IQ_version.setTagData('name', u'Altaire bot © Assssin')
			elif ns == xmpp.NS_TIME:
				IQ_time = out.getTag('IQ_time')
				if IQ_time:
					IQ_time.setTagData('tz', strftime('%Z'))
					IQ_time.setTagData('display', strftime('%a, %d %b %Y %H:%M:%S'))
					IQ_time.setTagData('utc', strftime('%Y%m%dT%H:%M:%S (GMT)', gmtime()))
			connect.send(out)
