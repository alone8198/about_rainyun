# about_rainyun
## **1.自动签到**
转载[Rainyun-Qiandao-V2](https://github.com/scfcn/Rainyun-Qiandao)

在文件夹sign-in中

支持Github Actions

1.fork本仓库

2.进入仓库的 `Settings` > `Secrets and variables` > `Actions`

3.添加以下密钥：

`RAINYUN_USER`  雨云用户名(支持多行，每行一个用户名)

`RAINYUN_PASS`  雨云账号密码(支持多行，每行一个密码，需与用户名数量匹配)

4.工作流将每天 UTC 4 点（UTC+8 12点）自动运行，也可以手动触发
## **2.雨云账户登录测试**
自己写的

在文件夹login中
