# -*- coding: utf-8 -*-
from Action import Action
import util
import re
from datetime import datetime
import threading

class PrintSinaL2Action(Action):
    def __init__(self, **kwargs):
        Action.__init__(self, **kwargs )
        self._producer_list = [
            {
                 "name"             :    "SinaLevel2WS",
                 "producer_name"    :    "PrintSinaL2.SinaLevel2-quotation"
            }]
        self._init()
        self.logger.info(self._name +u"初始化")
        self.count = 0

    # 需要重写的方法
    def handler(self, event):
        dt = datetime.now()
        event.data = util.ws_parse( message = event.data, to_dict = self.to_dict )
        if isinstance(event.data, list):
            for data in event.data:
                self.count += 1
                print("PrintSinaL2:{}, \nCount:{},  Length: {}\n{}".format( dt,self.count, len(data),data ) )
        else:
            self.count += 1
            print("PrintSinaL2:{}, \nCount:{},  Length: {}\n{}".format( dt,self.count, len(event.data),event.data ) )

        # self.logger.info("线程退出")
