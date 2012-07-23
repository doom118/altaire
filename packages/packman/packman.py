# /* encoding: utf-8 */
# Copyright Altaire bot © Assassin, 2011 - 2012
# This program published under Apache 2.0 license
# See LICENSE for more details
# My EMail: assassin@sonikelf.ru
# My XMPP-conference: bottiks@conference.jabber.ru
# My Site: bottiks.ucoz.ru
# packman package for Altaire XMPP bot

from urllib import urlretrieve as download
from urllib2 import urlopen
from re import compile

finder 				= compile('/">(.*)/</a></li>', 16)
getFiles 			= lambda url: finder.findall(urlopen(url).read())
getAllPacks 		= lambda: getFiles('http://altaire.googlecode.com/svn/packages')
getAllDeps 			= lambda: getFiles('http://altaire.googlecode.com/svn/depends')
getDepFiles 		= lambda: os.listdir('depends')
getInstalledPacks 	= lambda: os.listdir('packages')

def downloadDir(url, dir):
	if not os.path.exists(dir): os.makedirs(dir)
	files = findall('">(.*)</a></li>', urlopen(url).read())
	for file in files:
		if file != '..':
			if file.endswith('/'):
				downloadDir('%s/%s' % (url, file), '%s/%s' % (dir, file))
			else:
				path = ('locales/%s' % file if (file.endswith('.help') or file.endswith('.comms')) else dir + '/%s' % file)
				if os.path.exists(path): os.remove(path)					
				download(url + '/%s' % file, path)
	
	

def packman_init(pack, depend = False):
	if (pack in getAllPacks()) or (depend and (pack in getAllDeps())):
		temp = ('depends' if depend else 'packages')
		depPacks, depFiles = [eval(x) for x in urlopen('http://altaire.googlecode.com/svn/%s/%s/depends' % (pack, temp)).read().splitlines()]
		packs, files = getAllPacks(), getDepFiles()
		installed = [pack]
		for file in depFiles:
			if file not in files:
				installed += packman_init(file, True)
		for Pack in depPacks:
			if Pack not in packs:
				installed += packman_init(Pack)
		downloadDir('http://altaire.googlecode.com/svn/%s/%s' % (pack, temp), '%s/%s' % (pack, temp))
		return installed
	else: return False
		
# доделать работу с ретурном функции packman_init (чтобы бот писал какие пакеты установил в качестве зависимостей)
def command_packman(source, parameters):
	parameters = parameters.split()
	lenp = len(parameters)
	if lenp > 0:
		if parameters[0] in translate['comms']['packman']['all']:
			if lenp == 1:
				allPacks = getAllPacks()
				installedPacks, availablePacks = list(allPacks), list(allPacks)
				for pack in getInstalledPacks():
					if pack in allPacks:
						availablePacks.remove(pack)
				for pack in availablePacks:
					installedPacks.remove(pack)
				replic = translate['comms']['packman']['allPacks'] + ', '.join(allPacks)
				if installedPacks:
					replic += chr(10) + translate['comms']['packman']['installedPacks'] + \
						', '.join(installedPacks)
				if availablePacks:
					replic += chr(10) + translate['comms']['packman']['availablePacks'] + \
						', '.join(availablePacks)
				fmsg(source, replic)
			else: fmsg(source, translate['outOfArguments'])
		elif parameters[0] in translate['comms']['packman']['install']:
			if lenp > 1:
				if parameters[1] in translate['comms']['packman']['all']:
					# install
					availablePacks = getAllPacks()
					for pack in getInstalledPacks():
						if pack in availablePacks:
							availablePacks.remove(pack)
					for pack in availablePacks:
						result = packman_init(pack)
						if result:
							load_package(parameters[1])
					fmsg(source, translate['performed'])
				else:
					# install
					for pack in parameters[1:]:
						if os.path.exists('packages/' + pack):
							fmsg(source, translate['comms']['packman']['nowPackInstalled'] % pack)
						else:
							result = packman_init(pack)
							if result:
								load_package(parameters[1])
							else: fmsg(source, translate['comms']['packman']['packNotFound'] % pack)
					fmsg(source, translate['performed'])
			else: fmsg(source, translate['outOfArguments'])
		elif parameters[0] in translate['comms']['packman']['upgrade']:
			if lenp >= 2:
				# install
				if parameters[1] in translate['comms']['packman']['all']:
					installedPacks = getInstalledPacks()
					installedPacks.remove('packman')
					for pack in installedPacks:
						result = packman_init(pack)
						if result:
							load_package(pack)
					fmsg(source, translate['performed'])
				else:
					# install
					for pack in parameters[1:]:
						if os.path.exists('packages/' + pack):
							result = packman_init(pack)
							if result:
								load_package(parameters[1])
						else:
							fmsg(source, translate['comms']['packman']['packNotFound'] % pack)
					fmsg(source, translate['performed'])
			else: fmsg(source, translate['outOfArguments'])
		else: fmsg(source, translate['badArguments'])
	else: fmsg(source, translate['outOfArguments'])

reg_command('packman', command_packman, 8)
