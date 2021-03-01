'''
@desc:内网穿透(映射)服务器端
@author: Martin Huang
@time: created on 2019/6/14 20:48
@修改记录:
2019/07/12 => 增加DEBUG选项 默认False 改为True可显示更多信息
2021/01/03 => 使用日志模块优化日志输出
2021/02/28 => 使用SSL/TLS实现安全通信
'''
import select
import socket
import time
import logging
import ssl
from threading import Thread, Lock
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

SERVER_CERT_FILE = 'ssl/certFile.pem'
SERVER_KEY_FILE = 'ssl/keyFile.pem'

# 内网穿透服务器端子线程类
class MappingSubServer:
    def __init__(self,connA,connB):
        # serverA的连接对象
        self.connA = connA
        # serverB的连接对象
        self.connB = connB
        # 监听可读列表、可写列表、错误列表
        self.readableList = [connA,connB]
        self.writeableList = []
        self.errorList = []
    # 关闭连接
    def closeConnectrion(self):
        b = bytes('NODATA', encoding='utf-8')
        self.connA.send(b)
        self.readableList.remove(self.connB)
        self.readableList.remove(self.connA)
        self.connB.shutdown(2)
        self.connB.close()
        self.connA.shutdown(2)
        self.connA.close()
        logger.info('连接已关闭！')
    # 端口转发
    def TCPForwarding(self):
        while self.readableList:
            rs, ws, es = select.select(self.readableList, self.writeableList, self.errorList)
            logger.info('可读列表长度：' + str(len(rs)) + ', 可写列表长度：' + str(len(ws)) + ', 错误列表长度' + str(len(es)))
            for each in rs:
                # 如果当前是connA，则接收数据转发给connB，传输结束关闭连接返回，遇错返回
                if each == self.connA:
                    try:
                        tdataA = each.recv(1024)
                        if len(tdataA) != 0:
                            logger.info('接收到【内网】消息：' + str(len(tdataA)) + 'Bytes')
                            self.connB.send(tdataA)
                        else:
                            self.closeConnectrion()
                            return
                    except BlockingIOError as e:
                        self.closeConnectrion()
                        logger.error(e)
                        return
                    except ConnectionAbortedError as e:
                        self.closeConnectrion()
                        logger.error(e)
                        return
                # 如果当前是connB，则接收数据转发给connA，传输结束关闭连接返回，遇错返回
                elif each == self.connB:
                    try:
                        tdataB = each.recv(1024)
                        if len(tdataB) != 0:
                            logger.info('接收到【用户】消息：' + str(len(tdataB)) + 'Bytes')
                            self.connA.send(tdataB)
                        else:
                            self.closeConnectrion()
                            return
                    except ConnectionAbortedError as e:
                        self.closeConnectrion()
                        logger.error(e)
                        return
                    except ConnectionResetError as e:
                        self.closeConnectrion()
                        logger.error(e)
                        return
# 内网穿透服务器端
class MappingServer:
    def __init__(self,toPort,commonPort,remotePort):
        # remotePort -> 内网机器连接本台机器的数据监听端口
        self.remotePort = remotePort
        # commonPort -> 心跳检测端口
        self.commonPort = commonPort
        # toPort -> 外部用户访问端口
        self.toPort = toPort
        self.serverA = None
        self.serverB = None
        self.serverC = None
        # connC实例，需要每个对象维护一个，用于心跳检测
        self.connC = None
        # 判断connC是否挂掉
        self.isAlive = False
        self.mutux = Lock()
        self.context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
        self.context.load_cert_chain(certfile=SERVER_CERT_FILE,keyfile=SERVER_KEY_FILE)
    def initServerA(self):
        self.serverA = None
        noneSSLServerA = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serverA = self.context.wrap_socket(noneSSLServerA, server_side=True)
        self.serverA.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEPORT,1)
        self.serverA.bind(('',self.remotePort))
        self.serverA.listen(50000)
        self.serverA.setblocking(1)
    def initServerB(self):
        self.serverB = None
        self.serverB = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serverB.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.serverB.bind(('', self.toPort))
        self.serverB.listen(50000)
        self.serverB.setblocking(1)
    def initServerC(self):
        self.serverC = None
        noneSSLServerC = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serverC = self.context.wrap_socket(noneSSLServerC,server_side=True)
        self.serverC.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.serverC.bind(('', self.commonPort))
        self.serverC.listen(5)
        self.serverC.setblocking(1)

    def TCPForwarding(self):
        while True:
            # 如果connC挂掉，不做任何事情，等待连接恢复
            if not self.isAlive:
                logger.info('心跳服务未连接...')
                time.sleep(1)
                continue
            # serverB与serverA是共享变量，需要加锁
            self.mutux.acquire()
            if self.serverB is None and self.serverA is None:
                self.initServerB()
                self.initServerA()
                logger.info("服务器初始化完毕")
            self.mutux.release()
            # 设置select 3秒后不阻塞
            rs, ws, es = select.select([self.serverB], [], [], 3)
            logger.info('主线程：可读列表长度：' + str(len(rs)) + ', 可写列表长度：' + str(len(ws)) + ', 错误列表长度' + str(len(es)))
            for each in rs:
                if each == self.serverB:
                    try:
                        # 如果有外部请求，激活数据管道，每个请求一个线程
                        connB, addB = self.serverB.accept()
                        logger.info("检测到有用户连接，IP地址为: %s:%d" % addB)
                        b = bytes('ACTIVATE', encoding='utf-8')
                        self.connC.send(b)
                        logger.info("已向内网发送应用激活指令")
                        connA, addA = self.serverA.accept()
                        logger.info("内外网数据通道已打通，内网连接的主机IP地址为: %s:%d" % addA)
                        mss = MappingSubServer(connA,connB)
                        t = Thread(target=mss.TCPForwarding)
                        t.setDaemon(True)
                        t.start()
                    except Exception as e:
                        logger.error(e)
                        continue

    # 心跳检测，若挂掉等待连接恢复，每秒发送一次心跳
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
                logger.debug("心跳包已发送")
                tdataC = self.connC.recv(1024)
                if len(tdataC) == 0:
                    logger.info("心跳服务已断开，等待重新连接")
                    self.isAlive = False
                    self.serverC.shutdown(2)
                    self.connC.close()
                    self.connC = None
                    self.mutux.acquire()
                    if self.serverA is not None:
                        self.serverA.shutdown(2)
                        self.serverA.close()
                        self.serverA = None
                        logger.info('ServerA已关闭')
                    if self.serverB is not None:
                        self.serverB.shutdown(2)
                        self.serverB.close()
                        self.serverB = None
                        logger.info('ServerB已关闭')
                    self.mutux.release()
                logger.debug("接收到内网的心跳回应")

            except:
                logger.info("心跳服务已断开，等待重新连接")
                self.isAlive = False
                self.connC.close()
                self.connC = None
                # serverB与serverA是共享变量，需要加锁
                self.mutux.acquire()
                if self.serverA is not None:
                    self.serverA.shutdown(2)
                    self.serverA.close()
                    self.serverA = None
                    logger.info('ServerA已关闭')
                if self.serverB is not None:
                    self.serverB.shutdown(2)
                    self.serverB.close()
                    self.serverB = None
                    logger.info('ServerB已关闭')
                self.mutux.release()
            time.sleep(1)

# 主方法
def ExternalMain(toPort,commonPort,remotePort):
    f = MappingServer(toPort,commonPort,remotePort)
    t = Thread(target=f.heartbeat)
    t.setDaemon(True)
    t.start()
    f.TCPForwarding()