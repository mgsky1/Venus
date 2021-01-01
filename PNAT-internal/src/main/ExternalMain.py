'''
@desc:内网穿透(映射)服务器端
@author: Martin Huang
@time: created on 2019/6/14 20:48
@修改记录:
2019/07/12 => 增加DEBUG选项 默认False 改为True可显示更多信息
'''
import select
import socket
import time
import logging
import asyncio
from threading import Thread
#pycharm
'''
日志配置
'''
LEVEL = logging.INFO
logger = logging.getLogger(__name__)
logger.setLevel(LEVEL)
rq = time.strftime('%Y%m%d%H%M', time.localtime(time.time()))
ch = logging.StreamHandler()
ch.setLevel(LEVEL)
formatter = logging.Formatter("%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)
#内网穿透服务器端子线程类
class MappingSubServer:
    def __init__(self,connA,connB,serverB):
        #serverA的连接对象
        self.connA = connA
        #serverB的连接对象
        self.connB = connB
        #监听可读列表、可写列表、错误列表
        self.readableList = [connA,connB]
        self.writeableList = []
        self.errorList = []
        #serverB实体
        self.serverB = serverB
    #关闭连接
    def closeConnectrion(self):
        b = bytes('NODATA', encoding='utf-8')
        self.connA.send(b)
        self.readableList.remove(self.connB)
        self.readableList.remove(self.connA)
        self.connB.close()
        self.connA.close()
    #端口转发
    def TCPForwarding(self):
        while True:
            rs, ws, es = select.select(self.readableList, self.writeableList, self.errorList)
            for each in rs:
                #如果当前是connA，则接收数据转发给connB，传输结束关闭连接返回，遇错返回
                if each == self.connA:
                    try:
                        tdataA = each.recv(1024)
                        self.connB.send(tdataA)
                        logger.debug(tdataA)
                        if not tdataA:
                            self.closeConnectrion()
                            return
                    except BlockingIOError as e:
                        logger.error(e)
                        return
                    except ConnectionAbortedError as e:
                        logger.error(e)
                        return
                # 如果当前是connB，则接收数据转发给connA，传输结束关闭连接返回，遇错返回
                elif each == self.connB:
                    try:
                        tdataB = each.recv(1024)
                        self.connA.send(tdataB)
                        if not tdataB:
                            self.closeConnectrion()
                            return
                    except ConnectionAbortedError as e:
                        logger.error(e)
                        return
                    except ConnectionResetError as e:
                        logger.error(e)
                        return
#内网穿透服务器端
class MappingServer:
    def __init__(self,toPort,commonPort,remotePort):
        #remotePort -> 内网机器连接本台机器的数据监听端口
        self.remotePort = remotePort
        #commonPort -> 心跳检测端口
        self.commonPort = commonPort
        #toPort -> 外部用户访问端口
        self.toPort = toPort
        self.serverA = None
        self.serverB = None
        self.serverC = None
        #connC实例，需要每个对象维护一个，用于心跳检测
        self.connC = None
        #判断connC是否挂掉
        self.isAlive = False
        self.readableList = []
        self.writeableList = []
        self.errorList = []
    def initServerA(self):
        self.serverA = None
        self.serverA = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serverA.bind(('',self.remotePort))
        self.serverA.listen(50000)
        self.serverA.setblocking(1)
    def initServerB(self):
        self.serverB = None
        self.serverB = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serverB.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.serverB.bind(('', self.toPort))
        self.serverB.listen(50000)
        self.serverB.setblocking(1)
        self.readableList.append(self.serverB)
    def initServerC(self):
        self.serverC = None
        self.serverC = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serverC.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.serverC.bind(('', self.commonPort))
        self.serverC.listen(5)
        self.serverC.setblocking(1)

    def TCPForwarding(self):
        self.initServerA()
        self.initServerB()
        while True:
            rs, ws, es = select.select(self.readableList, self.writeableList, self.errorList)
            for each in rs:
                if each == self.serverB:
                    #如果connC挂掉，不做任何事情，等待连接恢复
                    if not self.isAlive:
                        continue
                    try:
                    #如果有外部请求，激活数据管道，每个请求一个线程
                        connB, addB = self.serverB.accept()
                        logger.info("检测到有用户连接，IP地址为: %s:%d" % addB)
                        b = bytes('ACTIVATE', encoding='utf-8')
                        self.connC.send(b)
                        logger.info("已向内网发送应用激活指令")
                        connA, addA = self.serverA.accept()
                        logger.info("内外网数据通道已打通，内网连接的主机IP地址为: %s:%d" % addA)
                        mss = MappingSubServer(connA,connB,self.serverB)
                        # asyncio.run(mss.TCPForwarding())
                        t = Thread(target=mss.TCPForwarding)
                        t.setDaemon(True)
                        t.start()
                    except BlockingIOError as e:
                        logger.error(e)
                        continue

    #心跳检测，若挂掉等待连接恢复，每秒发送一次心跳
    def heartbeat(self):
        while True:
            if not self.isAlive:
                self.initServerC()
                self.connC, addC = self.serverC.accept()
                logger.info("内外网心跳服务已建立，心跳服务IP地址为：%s:%d"%addC)
                self.isAlive = True
            b = bytes('IAMALIVE', encoding='utf-8')
            try:
                self.connC.send(b)
                logger.info("心跳包已发送")
                tdataC = self.connC.recv(1024)
                logger.info("接收到内网的心跳回应")
                if not tdataC:
                    self.connC.close()
                    self.connC = None
                    self.isAlive = False
            except:
                logger.info("心跳服务已断开，等待重新连接")
                self.isAlive = False
                self.connC.close()
                self.connC = None
            time.sleep(1)

#主方法
def ExternalMain(toPort,commonPort,remotePort):
    f = MappingServer(toPort,commonPort,remotePort)
    t = Thread(target=f.heartbeat)
    t.setDaemon(True)
    t.start()
    f.TCPForwarding()