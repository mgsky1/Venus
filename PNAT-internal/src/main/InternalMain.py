'''
@desc:内网穿透(映射)客户端 部署在内网
@author: Martin Huang
@time: created on 2019/6/14 20:43
@修改记录:
2019/07/12 => 增加DEBUG选项 默认False 改为True可显示更多信息
2021/01/03 => 使用日志模块优化日志输出
2021/02/28 => 使用TLS实现安全通信
https://blog.csdn.net/robin912/article/details/44497355
https://blog.csdn.net/vip97yigang/article/details/84721027
'''
import select
import ssl
import socket
import time
import logging
from threading import Thread
from Utils.ConversionUtils import ConversionUtils
#pycharm
#from src.main.Utils.IOUtils import *

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

CA_FILE = 'ssl/ca/ca.crt'
CLIENT_CERT_FILE = 'ssl/client/client.crt'
CLIENT_KEY_FILE = 'ssl/client/client.key'

class MappingClient:
    def __init__(self,fromIP,fromPort,type,remoteIp,remotePort):
        #远程VPS的IP地址
        self.remoteIp = remoteIp
        #远程VPS数据监听端口
        self.remotePort = remotePort
        #源/本地ip
        self.fromIP = fromIP
        #源/本地端口
        self.fromPort = fromPort
        #clientA->连接内网App
        self.clientA = None
        #clientB->连接VPS
        self.clientB = None
        #select监听的可读列表、可写列表、错误列表
        self.readableList = []
        #协议类型
        self.type = type
    #连接内网App
    def connectClientA(self):
        if not self.clientA:
            self.clientA = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.clientA.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 0)
            self.clientA.connect((self.fromIP,self.fromPort))
            logger.info("与内网应用程序的连接已建立")
            #将clientA添加进监听可读队列
            self.readableList.append(self.clientA)
    #连接VPS
    def connectClientB(self):
        if not self.clientB:
            noneSSLClientB = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            noneSSLClientB.setsockopt(socket.SOL_SOCKET,socket.SO_KEEPALIVE,0)
            # TLS上下文
            context = ssl.SSLContext(ssl.PROTOCOL_TLS)
            context.check_hostname = False
            context.load_cert_chain(certfile=CLIENT_CERT_FILE, keyfile=CLIENT_KEY_FILE)
            context.load_verify_locations(CA_FILE)
            context.verify_mode = ssl.CERT_REQUIRED
            self.clientB = context.wrap_socket(noneSSLClientB,server_side=False)
            self.clientB.connect((self.remoteIp, self.remotePort))
            logger.info("内外网数据通道已打通")
            # 将client添加进监听可读队列
            self.readableList.append(self.clientB)
    #关闭clientA
    def closeClintA(self):
        #先将clientA从监听队列中移除，再关闭，否则会有异常,clientB同理
        if self.clientA in self.readableList:
            self.readableList.remove(self.clientA)
        # self.clientA.shutdown(socket.SHUT_RDWR)
        self.clientA.close()
        self.clientA = None
        logger.info("与内网应用程序的连接已断开...")
    def closeClintB(self):
        if self.clientB in self.readableList:
            self.readableList.remove(self.clientB)
        # self.clientB.shutdown(socket.SHUT_RDWR)
        self.clientB.close()
        self.clientB = None
        logger.info("内外网数据传输通道已断开...")
    #端口映射
    def TCPMapping(self):
        #连接内网App和外网VPS
        self.connectClientA()
        self.connectClientB()
        while True:
            #使用select监听
            rs, ws, es = select.select(self.readableList, [], [])
            for each in rs:
                #如果当前可读对象为clientA，将读取的数据转发到clientB，若遇到异常/无数据则关闭连接
                if each == self.clientA:
                    try:
                        tdataA = each.recv(1024)
                        self.clientB.send(tdataA)
                    except ConnectionResetError as e:
                        logger.error(e)
                        self.closeClintA()
                        self.closeClintB()
                        return
                    #print(tdataA)
                    if not tdataA:
                        if self.clientA is not None:
                            self.closeClintA()
                            self.closeClintB()
                            return
                 # 如果当前可读对象为clientB，将读取的数据转发到clientA，若遇到异常/无数据则关闭连接
                elif each == self.clientB:
                    try:
                        tdataB = each.recv(1024)
                        self.clientA.send(tdataB)
                    except ConnectionResetError:
                        self.closeClintA()
                        self.closeClintB()
                        return
                    #print(tdataB)
                    #若收到外部用户意外中断信息，关闭全部连接，结束
                    if tdataB == bytes('NODATA',encoding='utf-8'):
                        self.closeClintA()
                        self.closeClintB()
                        return
                    if not tdataB:
                        self.closeClintA()
                        self.closeClintB()
                        return

#主方法
def InternalMain(remoteIP,commonPort,remotePort,localIp,localPort):
    #remoteIP ->远程VPS的IP地址
    #commonPort -> 心跳检测端口
    #remotePort -> 远程VPS数据监听端口
    #localIp -> 本地IP
    #localPort -> 本地端口
    #clientC专门与远程VPS做心跳
    noneSSLClientC = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # TLS上下文
    context = ssl.SSLContext(ssl.PROTOCOL_TLS)
    context.check_hostname = False
    context.load_cert_chain(certfile=CLIENT_CERT_FILE, keyfile=CLIENT_KEY_FILE)
    context.load_verify_locations(CA_FILE)
    context.verify_mode = ssl.CERT_REQUIRED
    clientC = context.wrap_socket(noneSSLClientC,server_side=False)
    clientC.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 0)
    clientC.connect((remoteIP, commonPort))
    rl = [clientC]
    #监听
    while True:
        rs, ws, es = select.select(rl, [], [])
        for each in rs:
            if each == clientC:
                tdataC = each.recv(1024)
                if not tdataC:
                    rl.remove(clientC)
                    clientC.close()
                    clientC.connect((remoteIP, commonPort))
                    rl = [clientC]
                    break
                logger.debug(tdataC)
                #若远程VPS接收到用户访问请求，则激活一个线程用于处理
                if tdataC == bytes('ACTIVATE',encoding='utf-8'):
                    b = bytes('OK', encoding='utf-8')
                    each.send(b)
                    foo = MappingClient(localIp,localPort,'tcp',remoteIP,remotePort)
                    t = Thread(target=foo.TCPMapping)
                    t.setDaemon(True)
                    t.start()
                #心跳检测
                elif tdataC == bytes('IAMALIVE',encoding='utf-8'):
                    b = bytes('OK', encoding='utf-8')
                    each.send(b)