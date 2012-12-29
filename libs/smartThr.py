#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
#  smartThr.py
#  
#  Copyright 2012 Assassin <assassin@sonikelf.ru>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  Modification of threading module for Python

from threading import *
from threading import __all__, _get_ident

import sys

__all__ += ['ThreadKill', 'KillAllThreads', 'oldThread']
__version__ = '0.1 Beta'

class ThreadKill(Exception): pass

oldThread = Thread
class Thread(oldThread):
	trace_global = lambda self, object, reason, args: \
		(self.trace if reason == 'call' else None)
	def trace(self, object, reason, args):
		if (self.killed) and (reason == 'line'):
			raise ThreadKill('killed')
		else:
			return self.trace
	def kill(self):
		self.killed = True
	killed = False
	oldRun = Thread.run
	def run(self):
		if not self.killed:
			sys.settrace(self.trace_global)
			try: self.oldRun()
			except ThreadKill: pass

def KillAllThreads():
	temp = enumerate()
	for thr in temp:
		if thr._Thread__ident != _get_ident():
			thr.kill()
