# -*- coding: utf-8 -*-
# 以下是自动生成的 #
# --- 导入系统配置
import util
from Producer import Producer
from Functions import *
from Event import Event
from connection import *
from const import *

from datetime import datetime
import time
import requests
import websockets
import getpass
import base64,rsa,binascii
import json
import trollius
import threading
import functools
import re
import gc
import os

class SinaLevel2WSProducer(Producer):
	def __init__(self, name = None, username = None, pwd = None, symbols = None, hq = 'hq_pjb', query = ['quotation', 'orders', 'deal', 'info'], **kwargs):
		Producer.__init__(self, name=name, **kwargs )
		self.ip = util.get_client_ip()
		self.hq = hq
		self.query = query
		# 登录模块在V('Sina')中
		self.sina = V('Sina')
		self.is_login = self.login()
		if symbols is None:
			self.symbols = self.sina.get_symbols()
		else:
			self.symbols = symbols
		self.websockets = dict()

	def login(self, verify = False):
		return self.sina.login(verify = verify)

	@trollius.coroutine
	def get_ws_token(self,qlist):
		loop = trollius.get_event_loop()
		async_req = loop.run_in_executor(None, functools.partial( self.sina.session.get,
			URL_WSKT_TOKEN,
			params 	=	PARAM_WSKT_TOKEN(ip=self.ip,qlist=qlist, hq = self.hq),
			headers =	HEADERS_WSKT_TOKEN(),
			timeout =	5
		))
		yield trollius.From(async_req)
		# self.logger.info(req.text)
		response = re.findall(r'(\{.*\})',req.text)[0]
		response = json.loads( response.replace(',',',"').replace('{','{"').replace(':','":') )
		# gc.collect()
		raise trollius.Return(response)

	# 2cn_是3秒一条的Level2 10档行情
	# 2cn_symbol_0,2cn_symbol_1是逐笔数据
	# 2cn_symbol_orders是挂单数据
	# symbol_i是基本信息
	def generate_qlist(self,qlist,symbol):
		if 'quotation' in self.query:
			if qlist!='':
				qlist += ','
			qlist += "2cn_%s" % (symbol)
		if 'orders' in self.query:
			if qlist!='':
				qlist += ','
			qlist += "2cn_%s_orders" % (symbol)
		if 'deal' in self.query:
			if qlist!='':
				qlist += ','
			qlist += "2cn_%s_0,2cn_%s_1" % (symbol, symbol)
		if 'info' in self.query:
			if qlist!='':
				qlist += ','
			qlist += "%s_i" % (symbol)
		return qlist

	@trollius.coroutine
	def create_ws(self, qlist, symbolList ):
		retry = True
		while retry:
			try:
				for response in self.get_ws_token(qlist):
					yield response
				if response["msg_code"] == 1:
					token = response["result"]
					self.logger.info(u"成功获取到token, symbolList = {}".format(symbolList) )
					retry = False
				else:
					self.logger.warning( "{},{}".format(response,qlist) )
					if response["msg_code"] == -11:
						time.sleep(2)
						self.logger.warning( u"尝试重新登录新浪" )
						self.sina = V("Sina")
						self.sina.login( verify = False )

			except Exception as e:
				self.logger.warning(e)

		url_wss = 'wss://ff.sinajs.cn/wskt?token=' + token + '&list=' + qlist

		while True:	# 建立websocket连接
			try:
				for ws in websockets.connect(url_wss):
					yield ws
				self.websockets[ symbolList[0] ] = dict()
				self.websockets[ symbolList[0] ]["ws"] = ws
				self.websockets[ symbolList[0] ]["qlist"] = qlist
				self.websockets[ symbolList[0] ]["token"] = token
				self.websockets[ symbolList[0] ]["renewed"] = datetime.now()
				self.websockets[ symbolList[0] ]["trialTime"] = 0
				self.logger.info(u"成功建立ws连接, {}, symbolList = {}".format(threading.current_thread().name, symbolList))
				break
			except Exception as e:
				self.logger.warning(u"重试 websockets.connect , {}, symbolList = {}".format(threading.current_thread().name, symbolList) )

		while self._active:
			try:
				for message in ws.recv():
					yield message
				event = Event(event_type = 'SinaLevel2WS', data = message)

				for q in self._subscriber:
					q.put(event)
					# print( "Producer:\n{},{}".format( event.data,datetime.now() ) )

			except Exception as e:
				self.logger.error("{},{}".format(e, threading.current_thread().name) )
				ws.close()
				for info in self.create_ws(qlist = qlist, symbolList = symbolList):
					yield info

	@trollius.coroutine
	def renew_token(self, symbol):
		try:
			for response in self.get_ws_token( self.websockets[ symbol ]["qlist"] ):
				yield response
			if response["msg_code"] == 1:
				token = response["result"]
				self.websockets[ symbol ]["token"] = token
				self.websockets[ symbol ]["renewed"] = datetime.now()
				for info in self.websockets[ symbol ]["ws"].send("*"+token):
					yield info
				self.websockets[ symbol ]["trialTime"] = 0
			else:
				self.websockets[ symbol ]["trialTime"] += 1
				self.logger.info(response["result"])
		except Exception as e:
			self.websockets[ symbol ]["trialTime"] += 1
			self.logger.warning(u"token获取失败第{}次，待会儿重试".format( self.websockets[ symbol ]["trialTime"] ))
		# gc.collect()


	def websocket_creator(self):
		loop = trollius.new_event_loop()
		trollius.set_event_loop(loop)
		# 首先从新浪获取股票列表
		symbolList = self.symbols
		# Cut symbolList
		weight = (len(self.query)+1) if ('deal' in self.query) else len(self.query)
		step = int(64/weight)
		symbolListSlice = [symbolList[ i : i + step] for i in range(0, len(symbolList), step)]

		tasks = list()
		for symbolList in symbolListSlice:
			qlist = ''
			for symbol in symbolList:
				qlist = self.generate_qlist(qlist=qlist,symbol=symbol)
			qlist = qlist.lower()
			tasks.append( self.create_ws(qlist,symbolList = symbolList) )

		loop.run_until_complete( trollius.wait(tasks) )
		loop.close()

	# 用于定时发送空字符串
	def token_sender(self):
		while True:
			self.logger.info(u"开启话唠模式每55秒的定时与服务器聊天")
			start = datetime.now()
			tasks = list()
			loop = trollius.new_event_loop()
			trollius.set_event_loop(loop)

			for symbol in self.websockets.keys():
				ws = self.websockets[ symbol ]["ws"]
				if ws.open:
					tasks.append( ws.send("*"+self.websockets[symbol]["token"]) )

			if len(tasks)>0:
				loop.run_until_complete( trollius.wait(tasks) )
				loop.close()
			self.logger.info(u"消息全部发送完毕. 耗时：%s" % (datetime.now()-start).total_seconds() )
			time.sleep(55)

	# 持续检查一次更新token
	def token_renewer(self):
		while True:
			loop = trollius.new_event_loop()
			trollius.set_event_loop(loop)
			tasks = list()
			for symbol in self.websockets.keys():
				ws = self.websockets[ symbol ]["ws"]
				if ws.open:
					if (datetime.now()-self.websockets[ symbol ]["renewed"]).total_seconds()>180:
						tasks.append( self.renew_token( symbol ) )

			if len(tasks)>0:
				loop.run_until_complete( trollius.wait(tasks) )
				loop.close()
			time.sleep(1)
			# gc.collect()


	def handler(self):
		# 开启token manager
		tokenRenewer = threading.Thread( target = self.token_renewer )
		tokenSender = threading.Thread( target = self.token_sender )

		websocketCreator = threading.Thread( target = self.websocket_creator )

		tokenRenewer.start()		# 用于更新token
		tokenSender.start()			# 用于定时发送token
		websocketCreator.start()	# 用于建立websocket并接收消息

		tokenRenewer.join()
		tokenSender.join()
		websocketCreator.join()

if __name__ == "__main__":
	p = SinaLevel2WSProducer({'producer_name': 'PrintSinaL2.SinaLevel2-quotation', 'name': 'SinaLevel2WS'})