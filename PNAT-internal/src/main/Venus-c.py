'''
@desc:内网穿透客户端入口
@author: Martin Huang
@time: created on 2019/6/21 16:34
@修改记录:
'''
import json
from Utils.IOUtils import IOUtils
from InternalMain import *
#pycharm
# from src.main.Utils.IOUtils import *
# from src.main.InternalMain import *
import multiprocessing

if __name__ == '__main__':
    str = IOUtils.getConfigJson('config-c.json')
    #JSON加载后变成一个字典，对于每一个key(配置文件中定义的应用程序名)，启动一个进程处理
    for eachApp in str.keys():
        appconfig = str.get(eachApp)
        p = multiprocessing.Process(target=InternalMain,args=(appconfig.get('remoteIP'),int(appconfig.get('commonPort')),int(appconfig.get('remotePort')),appconfig.get('localIP'),int(appconfig.get('localPort'))))
        p.start()