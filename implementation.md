@[TOC]
# 写在前面
 &#12288;去年写过一篇文章[《利用Python+阿里云实现DDNS(动态域名解析)》](https://blog.csdn.net/mgsky1/article/details/80466840)，针对的是有临时公网IP的宽带用户，而这并不是每一家运营商都能做的到，有的朋友虽说有宽带，但是得到的是一个内网IP，这时，就要轮到传说中的内网穿透大展身手了。在这篇文章中，会通过几次的端口转发，实现内外网的端口映射，进而达到内网穿透的目的。效果很像NAPT，但又不是，毕竟没有涉及到修改IP数据报。
   &#12288;比较有代表性的内网穿透的程序有：付费的有花生壳、NAT123，开源的有frp等等。这里实现的内网穿透虽然没有前面列举的那些工具一样那么强大，但是也实现了基本的功能，目前，可以支持**TCP**协议的内网与外网的映射，支持http、mysql、rdp(Windows远程桌面)、SSH应用(以上是测试过的)。

   &#12288;下面先上效果图，最后会奉上代码，由于只是实验品，可能有BUG，还请各位看官多多包含~~
   &#12288;我把这个项目叫做*Venus*(金星--太阳系离太阳第二近的行星，具体为啥会叫这个名，后文揭晓~)
 &#12288;文章会比较长，我尽量将实现的原理说的明白~
  - 工具运行截图
  服务器端运行截图(Ubuntu Server 16.04 LTS)：<br>
![](https://imgconvert.csdnimg.cn/aHR0cHM6Ly94eHguaWxvdmVmaXNoYy5jb20vYWxidW0vMjAxOTA3LzEyLzIyMTg1NG43N3BnNnBnNzc0dnl2dWkucG5n)
客户端运行截图(macOS Mojave 此图向公网映射MySQL)
![](https://imgconvert.csdnimg.cn/aHR0cHM6Ly94eHguaWxvdmVmaXNoYy5jb20vYWxidW0vMjAxOTA3LzEyLzIyMTcxNnRkdDQ3anE3YzlkOXlxejQucG5n)
  - http网站映射：
  内网环境
  ![](https://img-blog.csdnimg.cn/20190623221123120.png?x-oss-process=image/watermark,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L21nc2t5MQ==,size_16,color_FFFFFF,t_70)
  外网环境：
  ![](https://img-blog.csdnimg.cn/20190623221148508.png?x-oss-process=image/watermark,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L21nc2t5MQ==,size_16,color_FFFFFF,t_70)
  - MySQL数据库
  内网环境
  ![](https://img-blog.csdnimg.cn/20190623232435775.png?x-oss-process=image/watermark,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L21nc2t5MQ==,size_16,color_FFFFFF,t_70)
  外网环境：
  ![](https://img-blog.csdnimg.cn/20190623232450659.png?x-oss-process=image/watermark,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L21nc2t5MQ==,size_16,color_FFFFFF,t_70)
  - SSH(Ubuntu 18.04 LTS)
  内网环境：
  ![](https://img-blog.csdnimg.cn/20190623225450405.png?x-oss-process=image/watermark,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L21nc2t5MQ==,size_16,color_FFFFFF,t_70)
  外网环境：
  ![](https://img-blog.csdnimg.cn/20190623225550893.png?x-oss-process=image/watermark,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L21nc2t5MQ==,size_16,color_FFFFFF,t_70)
  # 你需要什么环境？
  > * 一台云主机(带有一个独立的公网IP)做为服务器
  > * 一台运行如WEB服务的内网主机(带有一个内网IP)作为客户端
  > * 服务器与客户端都需要安装Python3环境
  # 架构与数据流
  ## 软件架构
  架构图：
  ![](https://img-blog.csdnimg.cn/20190624111443114.png?x-oss-process=image/watermark,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L21nc2t5MQ==,size_16,color_FFFFFF,t_70)
   &#12288;从图中可以看出，内网的应用拥有属于自身的端口号，比如WEB为80，SSH为22，RDP为3389，经过内网穿透/内外网端口映射后，WEB端口号变为了9000，SSH变成9001，RDP变成9002，这样，外部用户可以利用这些900x端口号访问内网。显然，要实现多个应用的部署，需要使用**多进程**。
## 单一请求的数据流
  &#12288; 但对于**单一**的一次请求(例如WEB服务)，内外网数据是如何进行传递的呢？请看下面这张图(**暂时先无视ClientC与ServerC**)：
  ![](https://img-blog.csdnimg.cn/2019062411402664.png?x-oss-process=image/watermark,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L21nc2t5MQ==,size_16,color_FFFFFF,t_70)
  > 图例：
  > - <font color='red'>红色</font>实线表示数据**出**内网
  > - <font color='green'>绿色</font>实线表示数据**进入**内网
  > - 内网中的<font color='purple'>紫色</font>虚线框代表**客户端(拥有一个内网IP)**
  > - 外网中的<font color='purple'>紫色</font>虚线框代表**服务器(拥有一个公网IP)**
  > 
  &#12288;初看这张图，这不就是网络编程中最基本的Server/Client模型吗？的确，实现内网穿透确实是基于这个模型，但是仔细一看，发现又有跟以前不太一样的地方。例如，我们以前熟知的是Server和Client直接互传信息，而这里却出现了Client与Client间，Server与Server间互传信息的情况。但是细细想，这也有它的道理：
  &#12288;假设这里的APP为*Apache*。刚开始时，内网要主动与外网的VPS建立连接，因为<font color='red'>内网访问外网的VPS很容易，但是外网的VPS要访问内网就难了，因为你可能不知道本次连接的外部端口号<sup>[1]</sup>。</font>在应用中，ClientB与ServerA就起到了建立内外网桥梁的作用。
  &#12288;内外网连接建立后，外部用户请求一个网站。那么此时，用户相当于一个客户端，需要一个服务器来接收他的请求，在这里，就是ServerB。ServerB接受了用户的请求后，需要将这个请求进行转发，前面说到，在刚开始的时候，ClientB与ServerA建立了内外网的连接，于是，用户的请求就从这个路径传送到内网。此时可以发现，在服务器端应用中，已经出现了两个Server，一个是ServerA，一个是ServerB，它们各司其职，一个Server将获取的数据放在缓冲区中，由另外一个Server取走。
  &#12288;由于*Apache*是一个网站服务器，需要一个客户端来连接。此时，用户的请求已由ClientB传送达到内网，需要由一个客户端发给*Apache*，这就是ClientA的作用。可以发现，在客户端应用中，出现了两个Client，ClientA与ClientB，它们也跟服务端的一样，各司其职，将获取的数据放在缓冲区中，由另外一个取走。
  &#12288;以上，数据就已经到达了内网中的网站服务器，网站服务器经过处理后，将响应原路返回。至此，一次请求操作结束。
  ## 多用户情况下的数据流
  &#12288;最初开始设计的时候，我以为多用户访问一个内网时的情况与上面说的相似，只需要ServerB接受多个用户的请求，然后将请求跟排队似的传给内网服务器就完事了。类似下面这张图，当时还没有想到心跳。
  ![](https://img-blog.csdnimg.cn/20190624151312435.png?x-oss-process=image/watermark,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L21nc2t5MQ==,size_16,color_FFFFFF,t_70)
 &#12288; 但是实践之后发现并不是这样，每一种协议都有其特点，下面举几个例子：
  > * http协议：用户发出请求，服务器响应，数据传输完毕后，服务器断开连接
  > * mysql数据库：TCP连接建立后，数据库服务器先发送一个握手信息，客户端不像http那样主动请求，直到客户端收到这个握手信息后再进行响应，整个通讯过程中，连接是不断开的(这里指使用控制台的情况，如果使用第三方可视化工具，会有不一样)
 
 &#12288;这样就产生一个问题，mysql数据库的话还好，可以保持TCP连接不中断，但是HTTP怎么办呢？一旦断了就要马上重连，一是很浪费资源，二是即使这么做了，会大概率造成请求丢失，也就是说有时候会造成我请求AURL，结果我看到的是BURL。
 &#12288;后来想到的办法是，一次请求一个线程，请求完毕就马上释放资源。而什么时候通知内网进行通讯管道建立呢？这时候想到ServerB可以胜任这项工作，因为ServerB就是用来接收外部用户请求的。
  &#12288;接收到用户请求后，应该还要有一个组件来通知内网，这就是上一节图中ServerC和ClientC的作用了。它们就是来激活内网的数据传输管道的。这样，每一次请求就启动一个线程，请求完毕就释放，就不会出现混乱的情况了。
  ## 心跳
  &#12288;心跳常常是维持网络中某一个节点存活的机制。心跳心跳，顾名思义，我们常常用心跳来判断一个人是否过世，这里也一样，用心跳来判断某一个连接是否断开，这里对ServerC与ClientC应用这一机制。因为它们对于整个软件十分重要，没有了它们，内网就不知道什么时候要建立连接了，必须始终保持在线。
  # 技术实现
  > 这里就到上代码的环节了，只挑几个关键的拿出来说一说。
  ## 连接监听
   &#12288;这里连接的监听使用的是Python中select模块的select方法。这是一个大部分平台都支持的方法，可以用来监听Socket。函数原型是这样的。
  `fd_r_list,fd_w_list,fd_e_list = select.select(rlist, wlist, xlist,[timeout])`
 &#12288;显然，select方法有三个参数，三个返回值
> * 当参数1序列中的fd满足“可读”条件时，则获取发生变化的fd并添加进fd_r_list中
> * 当参数2序列中含有fd时，则将该序列中的所有fd添加到fd_w_list中
> * 当参数3序列中的fd发手错误时，则将该发生错误的fs添加到fd_e_list中
> * 当超时时间为空，则select会一直阻塞，直到监听的句柄发生变化，当超时时间=n(正整数)时，那么如果监听的句柄均无任何变化，则select会阻塞n秒，之后返回三个空列表，如果监听的句柄发生变化，则直接执行。
*注：fd指File Descriptor，即文件描述符，比如Socket对象就是一个文件描述符，调用socketobj.fileno()可查看其值。select方法最多支持1024个fd。*

 &#12288;需要注意的是，select方法会采用操作系统的内核态来检测变化，操作还是十分方便的。由于我们需要循环监听，所以需要一个死循环。每次监听后，根据返回的fd_r_list列表，对于其中的对象采取不同的办法。
 &#12288;以下代码描述了在服务器端，ServerA的连接对象connA与ServerB的连接对象connB是如何进行传输数据的：
```python
    def TCPForwarding(self):
        while True:
            rs, ws, es = select.select(self.readableList, self.writeableList, self.errorList)
            for each in rs:
                #如果当前是connA，则接收数据转发给connB，传输结束关闭连接返回，遇错返回
                if each == self.connA:
                    try:
                        tdataA = each.recv(1024)
                        self.connB.send(tdataA)
                        print(tdataA)
                        if not tdataA:
                            self.closeConnectrion()
                            return
                    except BlockingIOError as e:
                        print(e)
                        return
                    except ConnectionAbortedError as e:
                        print(e)
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
                        print(e)
                        return
                    except ConnectionResetError as e:
                        print(e)
                        return
```
 &#12288;上面列举的这个方法，是在ServerB监听到外部用户访问后，接受来自客户端ServerA的连接，启动的一个线程类中的方法。这个方法的主要功能是：将用户发给内网或内网发给用户的数据进行转发。
 &#12288;这里就使用了select方法进行监听connA与connB，connA与connB都已在类初始化的时候放入了readableList中。如果select监听到此时connB有消息可读，就读取消息，然后由connA发送出去，同样，如果此时connA可读，也读取消息，由connB发送出去。如果遇到异常，则终止。
  &#12288;当然，select方法不止用于这一处。
  ## 心跳实现
   &#12288;上面说了为什么要在这里使用心跳，因为ServerC与ClientC实在是太重要了，必须要保证他们“活着”。具体的实现方法是这样的：
    &#12288;在服务器端的类对象中，有一个isAlive的变量，它用于标识ClientC是否存活，刚开始的时候，其值为否，然后有一个线程，专门用于坚持其状态，如果isAlive=False，则说明内网客户端断开了，就会阻塞整个程序，等待连接，连接上后将isAlive设置为true；否则，每过1秒，就会发送心跳信息，如果客户端没有回应，说明客户端离线，将isAlive设置为False。下面是代码：
    服务器端
  ```python
   #心跳检测，若挂掉等待连接恢复，每秒发送一次心跳
    def heartbeat(self):
        while True:
            if not self.isAlive:
                self.initServerC()
                self.connC, addC = self.serverC.accept()
                print('ServerC IP : %s:%d' % addC)
                self.isAlive = True
            b = bytes('IAMALIVE', encoding='utf-8')
            try:
                self.connC.send(b)
                tdataC = self.connC.recv(1024)
                if not tdataC:
                    self.connC.close()
                    self.connC = None
                    self.isAlive = False
            except:
                print('serverC已断开，等待重新连接...')
                self.isAlive = False
            time.sleep(1)
  ```
   &#12288;在服务器端的代码中，整个方法为一个死循环，每隔1秒判断一次状态，心跳信息就为IAMALIVE的字符串，然后发送给内网的客户端，等待回应，如果有回应，说明存活，否则就是离线。当然，这里的ServerC设置成了阻塞式<sup>[2]</sup>，以防止不必要的异常。
   客户端：
   ```python
   #remoteIP ->远程VPS的IP地址
   #commonPort -> 心跳检测端口
   #remotePort -> 远程VPS数据监听端口
   #localIp -> 本地IP
   #localPort -> 本地端口
   #clientC专门与远程VPS做心跳
    clientC = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clientC.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
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
                #print(tdataC)
                #若远程VPS接收到用户访问请求，则激活一个线程用于处理
                if tdataC == bytes('ACTIVATE',encoding='utf-8'):
                    foo = MappingClient(localIp,localPort,'tcp',remoteIP,remotePort)
                    t = Thread(target=foo.TCPMapping)
                    t.setDaemon(True)
                    t.start()
                #心跳检测
                elif tdataC == bytes('IAMALIVE',encoding='utf-8'):
                    b = bytes('OK', encoding='utf-8')
                    each.send(b)
   ```
   这段代码主要就是初始化ClientC，并监听由外网服务器端发来的针对ClientC的信息，如果是IAMALIVE，，说明是心跳包，就回应一个OK信息，如果是ACTIVATE，则会启动一个线程，进行内外网数据传送。
 ## 多线程与多进程
 这就会稍微简单一些了，在服务器端，一定要有了外部用户的连接请求后，再去接受内网的ServerA的连接，然后我设计了一个线程数据转发类MappingSubServer，专门用于ServerA与ServerB之间的数据转发。需要注意的是，一定要将请求时刻所生成的connA与connB同时传入，否则将会导致连接错乱。
 ```python
 					  #如果有外部请求，激活数据管道，每个请求一个线程
                        connB, addB = self.serverB.accept()
                        print('ServerB IP : %s:%d' % addB)
                        b = bytes('ACTIVATE', encoding='utf-8')
                        self.connC.send(b)
                        connA, addA = self.serverA.accept()
                        print('ServerB IP : %s:%d' % addA)
                        mss = MappingSubServer(connA,connB,self.serverB)
                        t = Thread(target=mss.TCPForwarding)
                        t.setDaemon(True)
                        t.start()
 ```
在这里，接收带服务器请求后会由ServerC生成的connC对象往内网发送激活信息，然后在等待接受ServerA的连接。成功后启动线程。
客户端的多线程在上一节已做了说明。
多进程就更加明了了，软件采用JSON为配置文件格式，以下为服务器端配置示例：
```JSON
{
    "App01": {
        "commonPort": "7000",
        "remotePort": "8000",
        "toPort":"9000"
    }
}
```
JSON经过Python解析后，会变成一个字典，即
```JSON
{"App01":{"commonPort":"7000","remotePort":"8000","toPort":"9000"}}
```
然后获取key的集合，对于每一个key，启动一个进程就ok啦~客户端也是同理

# 为什么叫Venus
主要还是最近迷*三体* ，就想拿太阳系的行星来命名。前一阵子写了一个局域网文件传输工具[Mercury](https://github.com/mgsky1/Mercury)，Mercury也叫水星，接下来就是离太阳第二近的金星(Venus)了。
# 文章注解
[1] :  现在有的网络设备使用NAT网络地址转换技术，NAT技术会在连接外网时，随机选择一个端口号进行访问，如果是对称型NAT，每次请求的端口都会不一样。

[2] :非阻塞式：简单来说，在recv数据时，没有数据也返回
	 阻塞式：简单来说，在recv数据时，如果没有数据则阻塞，有数据读取才返回。
# 代码
[Github仓库地址](https://github.com/mgsky1/Venus)
# 写在最后
本文有些部分参考了[我的python学习笔记之select模块](https://blog.csdn.net/zhuangzi123456/article/details/84400108)。
如果有写的不好，名词理解不对的地方还请指出。程序的Bug不能避免，主要是思路，还请各位多多包含~

