# /* encoding: utf-8 */
# Copyright Altaire bot © Assassin, 2011 - 2012
# This program published under Apache 2.0 license
# See LICENSE for more details
# My EMail: assassin@sonikelf.ru
# packman package for Altaire XMPP bot

from urllib import urlretrieve as download
from urllib2 import urlopen
from re import compile
# заюзать finderFiles (удалить ..)

finderDirs 			= compile('<li><a href=".*">(.*)/</a></li>')
finderFiles			= compile('<li><a href=".*">(.*)</a></li>')
getDirs 			= lambda url: finderDirs.findall(urlopen(url).read())
getAllPacks 		= lambda: getDirs('http://altaire-packages.googlecode.com/git/packages')
getAllDeps 			= lambda: getDirs('http://altaire-packages.googlecode.com/git/depends')
getDepFiles 		= lambda: os.listdir('depends')
getInstalledPacks 	= lambda: os.listdir('packages')
removeItem = '..'

def getFiles(url):
	found = finderFiles.findall(urlopen(url).read())
	if removeItem in found: found.remove(removeItem)
	return found

def downloadDir(url, dir):
	if not os.path.exists(dir): os.makedirs(dir)
	files = getFiles(url)
	for file in files:
		if file.endswith('/'):
			downloadDir('%s/%s' % (url, file), '%s/%s' % (dir, file))
		else:
			path = ('locales/%s' % file if (file.endswith('.help') or file.endswith('.comms')) else dir + '/%s' % file)
			if os.path.exists(path): os.remove(path)					
			download(url + '/%s' % file, path)



def packman_init(pack, depend = False):
	if (pack in getAllPacks()) or (depend and (pack in getAllDeps())):
		temp = ('depends' if depend else 'packages')
		depPacks, depFiles = [eval(x) for x in urlopen('http://altaire-packages.googlecode.com/git/%s/%s/depends' % (temp, pack)).read().splitlines()]
		packs, files = getAllPacks(), getDepFiles()
		installed = list()
		for file in depFiles:
			if file not in files:
				installed += packman_init(file, True)
		for Pack in depPacks:
			if Pack not in packs:
				installed += packman_init(Pack)
		downloadDir('http://altaire-packages.googlecode.com/git/%s/%s' % (temp, pack), '%s/%s' % (temp, pack))
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
					if result: fmsg(source, translate['comms']['packman']['installedDepends'] % ', '.join(result))
				else:
					# install
					allResults = list()
					for pack in parameters[1:]:
						if os.path.exists('packages/' + pack):
							fmsg(source, translate['comms']['packman']['nowPackInstalled'] % pack)
						else:
							result = packman_init(pack)
							if not (result is False):
								allResults += result
								load_package(parameters[1])
							else:
								fmsg(source, translate['comms']['packman']['packNotFound'] % pack)
								return
					fmsg(source, translate['performed'])
					if allResults: fmsg(source, translate['comms']['packman']['installedDepends'] % ', '.join(allResults))
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
