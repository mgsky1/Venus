# Venus
![](https://img.shields.io/badge/Python-3.x+-brightgreen.svg)
# Summary
一个基于Python的TCP内网穿透工具，可以向外网映射内网TCP应用，如http MySQL SSH RDP

# Requirement
> * 一台带有公网IP的云主机
> * 服务器和客户端均装有Python3环境

# Experience

进入`PNAT-internal/src/main`后运行以下代码：<br>
外网服务器：
```
python Venus-s.py
```
内网客户端：
```
python Venus-c.py
```

# Configuration
> 配置文件位于`PNAT-internal/src/main`中，采用JSON格式
## 服务器端 config-s.json
```
{
    "App01": { ->App01为应用程序名称，可以为SSH，WEB等等
        "commonPort": "7000",  -> 用于心跳检测以及激活内网通信管道的端口号
        "remotePort": "8000", -> 用于内外网应用程序数据交流的端口号
        "toPort":"9000" ->外部用户访问的端口号
    },
    "App02":{
        ...
    }
}
```
## 客户端 config-c.json
```
{
    "App01": { ->App01为应用程序名称，可以为SSH，WEB等等
        "commonPort": "7000", ->  用于心跳检测以及激活内网通信管道的端口号
        "remoteIP": "106.x.x.x", ->云主机IP地址
        "remotePort": "8000",-> 用于内外网应用程序数据交流的端口号
        "localIP": "127.0.0.1", ->本地IP
        "localPort": "80" ->本地应用程序端口号
    },
    "App02":{
        ...
    }
}
```

# Note
> * 基于Python3，不依赖第三方库。
> * 由于这只是个人的实验，如有不妥之处，请多多包含。
> * 由于只是实验，日志输出做的不是特别好，请各位看官多多包含~
> * 不支持有随机端口特性的FTP

# Screen Shots

服务器端运行截图(Ubuntu Server 16.04 LTS)：<br>
![](https://xxx.ilovefishc.com/album/201907/12/221854n77pg6pg774vyvui.png)
客户端运行截图(macOS Mojave 此图向公网映射MySQL)
![](https://xxx.ilovefishc.com/album/201907/12/221716tdt47jq7c9d9yqz4.png)

WEB应用映射：<br>
内网环境：
![](https://xxx.ilovefishc.com/album/202101/08/090602gfio4irzszoq4joq.png)
外网环境：
![](https://xxx.ilovefishc.com/album/202101/08/090602uj44lxb9bx60vioz.png)

SSH:<br>

内网环境：<br>
![](https://xxx.ilovefishc.com/album/202101/08/085637mtaq8ujs80jjwlu5.png)

外网环境：<br>
![](https://xxx.ilovefishc.com/album/202101/08/085637d3gq55q0u3fm5ngt.png)

# Attention
请不要向公网投射内网中公司敏感资料

# Contribution
欢迎Star or Fork，或者提交Pull Request，共同完善项目！
