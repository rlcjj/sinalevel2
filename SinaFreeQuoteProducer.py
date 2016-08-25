# -*- coding: utf-8 -*-
"""
# Created on 2016/04/12
# @author: Emptyset
# @contact: Emptyset110@gmail.com
"""
import util
from Producer import Producer
from Event import Event
from Functions import *

import threading
import time
import trollius
import functools
from datetime import datetime

class SinaFreeQuoteProducer(Producer):
	def __init__(self, name = None, symbols = None ,**kwargs):
		Producer.__init__(self, name=name, **kwargs )
		self.sina = V('Sina')
		if symbols is None:
			self.symbols = self.sina.get_symbols()
		else:
			self.symbols = symbols
		[self.szSymbols, self.shSymbols] = util.split_symbols(self.symbols)
		self.szTime = datetime(1970,1,1)
		self.shTime = datetime(1970,1,1)

	# 定时器触发的函数
	def thread_target(self, loop):
		trollius.set_event_loop(loop)
		retry = True
		update = True
		sz = None
		sh = None
		while retry:
			try:
				[ szTime, shTime ] = self.sina.get_ticktime()
				if (szTime > self.szTime) & (len(self.szSymbols)>0):
					self.szTime = szTime
					szUpdate = True
				else:
					szUpdate = False

				if (shTime > self.shTime) & (len(self.shSymbols)>0):
					self.shTime = shTime
					shUpdate = True
				else:
					shUpdate = False
				if szUpdate and shUpdate:
					[ sz ,sh ] = self.sina.get_realtime_quotes( symbols = self.symbols , dataframe=False, loop = loop, split = True )
				elif szUpdate:
					sz = self.sina.get_realtime_quotes( symbols = self.szSymbols , dataframe=False, loop = loop, split=False)
				elif shUpdate:
					sh = self.sina.get_realtime_quotes( symbols = self.shSymbols , dataframe=False, loop = loop, split=False)
				retry = False
			except Exception as e:
				print(e)
		# print( time.time() - start )
		if sz:
			eventSZ = Event( event_type = 'SinaFreeQuote', data = sz )
			eventSZ.time = szTime
			eventSZ.localtime = time.time()
			eventSZ.exchange = 'SZ'
			for q in self._subscriber:
				q.put(eventSZ)
		if sh:
			eventSH = Event( event_type = 'SinaFreeQuote', data = sh )
			eventSH.time = shTime
			eventSH.localtime = time.time()
			eventSH.exchange = 'SH'
			for q in self._subscriber:
				q.put(eventSH)

	def handler(self):
		while self._active:
			loop = trollius.new_event_loop()
			t = threading.Thread( target = functools.partial( self.thread_target, loop ) )
			t.start()
			time.sleep(1)
