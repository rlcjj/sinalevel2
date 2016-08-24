# sinalevel2

sinalevel2是原dHydra项目中获取新浪行情数据针对Python2.x适配的版本，原项目见[https://github.com/Emptyset110/dHydra](https://github.com/Emptyset110/dHydra)。

原项目功能更为全面，如果对其他数据源有需求的用户请访问原项目。本项目主要是针对python2.x运行环境做的适配。因为环境有限目前只在python2.7测试正常，其他版本未测试。

本项目主要的改动是使用trollius替换了python3.x的asyncio包，此外还包括原作者升级版本后未修改的bug。

使用此项目需要安装python2.7版本的websockets包，这个也是自己将原来的websockets包针对python2.7做的适配：

[https://github.com/evanzd/websockets](https://github.com/evanzd/websockets)

安装时运行`python setup.py install`即可，也可以单独执行build操作后放在此项目目录下调用。

此外其他的依赖包括：

- ntplib
- rsa
- pandas

使用的时候请先根据购买的新浪level2行情修改config.ini的账号密码部分。

运行主程序为app.py。

另外，不保证未来新浪不会限制这一行情源（必须限制登陆等）。
