'''
@desc:内网穿透(映射)服务器主入口
@author: Martin Huang
@time: created on 2019/6/21 17:31
@修改记录:
2019/07/12 => 优化输出
'''
import json
from Utils.IOUtils import IOUtils
from ExternalMain import *
#pycharm
# from src.main.Utils.IOUtils import *
# from src.main.ExternalMain import *
import multiprocessing

if __name__ == '__main__':
    str = IOUtils.getConfigJson('config-s.json')
    #原理同客户端，每个应用一个进程
    for eachApp in str.keys():
        print(eachApp+' Starting...')
        appconfig = str.get(eachApp)
        p = multiprocessing.Process(target=ExternalMain,args=(int(appconfig.get('toPort')),int(appconfig.get('commonPort')),int(appconfig.get('remotePort'))))
        p.start()