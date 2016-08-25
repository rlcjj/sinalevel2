# -*- coding: utf-8 -*-
from Action import Action
import util
import re
from datetime import datetime
import threading

class PrintSinaFQAction(Action):
    def __init__(self, **kwargs):
        Action.__init__(self, **kwargs )
        self._producer_list = [
            {
                 "name"             :    "SinaFreeQuote",
                 "producer_name"    :    "PrintSinaFQ.SinaFreeQuote-quotation"
            }]
        self._init()
        self.logger.info(self._name +u"初始化")
        self.count = 0

    # 需要重写的方法
    def handler(self, event):
        dt = datetime.now()
        if isinstance(event.data, list):
            for data in event.data:
                self.count += 1
                print("PrintSinaFQ:{}, \nCount:{},  Length: {}\n{}".format( dt,self.count, len(data),data ) )
        else:
            self.count += 1
            print("PrintSinaFQ:{}, \nCount:{},  Length: {}\n{}".format( dt,self.count, len(event.data),event.data ) )

        # self.logger.info("线程退出")
