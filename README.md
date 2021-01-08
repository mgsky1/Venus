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
> * 由于这只是个人的实验,如有不妥之处，请多多包含。
> * 由于只是实验，日志输出做的不是特别好，请各位看官多多包含~
> * 不支持有随机端口特性的FTP
> * 如果你的服务器和客户端为Unix系统，可使用`ulimit -n x`命令适当提升允许打开的最大文件数量，以获得更好的性能。其中x表示允许打开的最大文件数

# Screen Shots

服务器端运行截图(Ubuntu Server 16.04 LTS)：<br>
![](https://xxx.ilovefishc.com/album/202101/03/153356bscskubxycnzkkou.jpg)
客户端运行截图(macOS Big Sur 此图向公网映射网页)<br>
![](https://xxx.ilovefishc.com/album/202101/03/153409h66dia5h00fzusda.jpg)

WEB应用映射：<br>
内网环境：
![](https://img-blog.csdnimg.cn/20190623221123120.png?x-oss-process=image/watermark,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L21nc2t5MQ==,size_16,color_FFFFFF,t_70)
外网环境：
![](https://img-blog.csdnimg.cn/20190623221148508.png?x-oss-process=image/watermark,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L21nc2t5MQ==,size_16,color_FFFFFF,t_70)

SSH:<br>
内网环境：
![](https://xxx.ilovefishc.com/album/202101/08/085637mtaq8ujs80jjwlu5.png)

外网环境：
![](https://xxx.ilovefishc.com/album/202101/08/085637d3gq55q0u3fm5ngt.png)

# Attention
请不要向公网投射内网中公司敏感资料

# Contribution
欢迎Star or Fork，或者提交Pull Request，共同完善项目！
