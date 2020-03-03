# bilibili_download_thread
***
一个bilibili视频多线程下载程序
项目地址：
https://github.com/Tangnameless/bilibili_download_thread  
主要参考项目：
https://github.com/Henryhaohao/Bilibili_video_download  
***
上传的主要目的也是记录一下自己学习大佬代码的成果和熟悉GitHub的使用

# 项目说明
### 下载视频的思路
1. 根据视频链接或者av号，由API获取视频的cid_list，一个视频的不同分p的cid不同
2. 根据aid，cid 可以得到视频的下载地址video_list
3. 如果一个分p视频过大，则video_list中就有可能有多个视频需要下载
4. 将video_list中的所有视频组装为完整的分p视频，组装完成后删除所有视频片段
### 多线程的使用
但是经过测试发现，单线程下载速度较慢，速度在500KB/S ~ 1M/S
为了提高下载速度，充分利用带宽，借鉴JiJiDown的下载思路
为每一个视频片段分配多个线程进行下载
Python是运行在解释器中的语言，python中有一个全局锁（GIL），在使用多线程(Thread)的情况下，不能发挥多核的优势。
但是对于网络请求这种忙等阻塞线程的操作，多线程的优势便非常显著了
设置了多线程下载后，下载速度获得了显著性的提升，默认设置了三线程，基本能达到原本的三倍下载速度
### 一些尝试与仍然存在的问题
使用requests包重写下载部分，替代urllib，未获得下载速度提升，且出现部分视频下载不完整，下载失败的情况
程序长时间运行后总会报错，但是代码没有问题
正在进行多次压力测试，目前最多的一次下载了120G视频没有太多问题
大批量下载的后期，出现无法获取分P视频的title情况

# 环境
python == 3.6.8
moviepy == 0.2.3.2
requests == 2.21.0

# 具体使用
#####1.登录你的b站账号，获得cookie
![cookie](/picture/cookie位置.png)
#####2.设定下载的目录，填入cookie
![设置](/picture/设置.png)
#####3.下载视频
![使用](/picture/使用示例.png)
使用DownloadAvideo函数下载一个b站视频
传入参数为
start —— 视频av号或者视频链接地址
quality —— 视频清晰度

可选值 | 视频质量质量 |是否需要大会员
-|-|-
116 | 高清1080P60 |需要大会员
112 | 高清1080P+ (hdflv2) |需要大会员
80 |高清1080P (flv)|否
74 |高清720P60 |需要大会员
64 |高清720P (flv720)|否
32 |清晰480P (flv480)|否
16 |流畅360P (flv360)|否

