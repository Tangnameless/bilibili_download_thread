# -*- coding: utf-8 -*-
"""
Created on Mon Mar  2 15:14:06 2020
@author: TangYi
python 3.6.8编写

"""
import requests
import urllib.request
import imageio
import os
import sys
import re
import time
import datetime
imageio.plugins.ffmpeg.download()
from moviepy.editor import *
import threading


# 本程序为不连接数据库的简易版本,用于下载一个或数个视频
# 需要设置的参数
# 存放视频的根目录
rootDir = 'D:/数据备份/bilibili视频备份'
# 收藏夹名称
fav_name = '单文件测试1'
# B站登录后的cookies,登录B站后复制一下cookie中的SESSDATA字段,有效期1个月
cookie = 'SESSDATA='
# 作用于reporthook的一个时间参数,不用修改
a_time = 0

def clean_txt(title):#清洗标题中不能用于命名文件的字符和正则表达式中的特殊字符
    rstr = r"[\^\$\.\[\]\/\\\:\*\?\"\<\>\|\+\{\}\(\)]"  # '^ $ [ ] / \ : * ? " < > | + { } ( )'
    title = re.sub(rstr, "", title)  # 替换为空
    return title

# 访问API地址，获取下载链接
def get_play_list(aid, cid, quality):
    url_api = 'https://api.bilibili.com/x/player/playurl?cid={}&avid={}&qn={}'.format(cid, aid, quality)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
        'Cookie': cookie, 
        'Host': 'api.bilibili.com'
    }
    html = requests.get(url_api, headers=headers).json()
    print(html)
    video_list = [[],[]]
    for i in html['data']['durl']:
        video_list[0].append(i['url'])
    for i in html['data']['durl']:
        video_list[1].append(i['size'])
    print(video_list)
    return video_list

# 下载视频参数
'''
urllib.urlretrieve 的回调函数：
def callbackfunc(blocknum, blocksize, totalsize):
    @blocknum:  已经下载的数据块
    @blocksize: 数据块的大小
    @totalsize: 远程文件的大小
'''
# 显示下载进度条，下载速度
def Schedule_cmd(blocknum, blocksize, totalsize):
    speed = (blocknum * blocksize) / (time.time() - a_time)
    # speed_str = " Speed: %.2f" % speed
    speed_str = " Speed: %s" % format_size(speed)
    recv_size = blocknum * blocksize

    # 设置下载进度条
    f = sys.stdout
    pervent = recv_size / totalsize
    percent_str = "%.2f%%" % (pervent * 100)
    n = round(pervent * 50)
    s = ('#' * n).ljust(50, '-')
    f.write(percent_str.ljust(8, ' ') + '[' + s + ']' + speed_str)
    f.flush()
    # time.sleep(0.1)
    f.write('\r')

# 字节bytes转化K\M\G
def format_size(bytes):
    try:
        bytes = float(bytes)
        kb = bytes / 1024
    except:
        print("传入的字节格式不对")
        return "Error"
    if kb >= 1024:
        M = kb / 1024
        if M >= 1024:
            G = M / 1024
            return "%.3fG" % (G)
        else:
            return "%.3fM" % (M)
    else:
        return "%.3fK" % (kb)

# 根据正则表达式得到文件名列表
def obtain_certrain_name_list(file_list, pattern):
    result = [re.findall(pattern, file) for file in file_list]
    flattened = sum(result, [])
    post_result = list(set(flattened))
    return post_result

# 递归调用urllib.request.urlretrieve下载，克服网络波动问题
def recu_down(url, filename, reporthook): 
    try:
        urllib.request.urlretrieve(url = url,filename = filename,reporthook = reporthook)
    except urllib.error.ContentTooShortError:
        print ('网络状况不佳，重新下载......')
        time.sleep(2)
        recu_down(url, filename, reporthook)

# 多线程下载
class ThreadDownload(threading.Thread):
    def __init__(self, url, startpos, endpos, filename, start_url):
        super(ThreadDownload,self).__init__()
        self.url = url               # 下载链接
        self.startpos = startpos     # 下载起始字节数
        self.endpos = endpos         # 下载终止字节数   
        self.filename = filename     # 下载文件命名
        self.start_url = start_url   # 起始链接

        
    def download_part(self):
        start_time = time.time()
        global a_time 
        a_time = start_time
        print("start thread:%s at %s" % (self.getName(), start_time))
        opener = urllib.request.build_opener()
        # 请求头
        opener.addheaders = [
            ('Host','upos-hz-mirrorks3.acgvideo.com'),  #注意修改host,不用也行
            ('User-Agent','Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:56.0) Gecko/20100101 Firefox/56.0'),
            ('Accept','*/*'),
            ('Accept-Language','en-US,en;q=0.5'),
            ('Accept-Encoding','gzip, deflate, br'),
            ("Range","bytes=%s-%s" % (self.startpos, self.endpos) ),  #设置下载范围
            ('Referer', self.start_url),  
            ('Origin','https://www.bilibili.com'),
            ('Connection','keep-alive'),
        ]
        urllib.request.install_opener(opener)
        filename = self.filename + '_' + str(self.startpos) + '_' + str(self.endpos) + '.temp'
        recu_down(self.url, filename, Schedule_cmd)
        print("stop thread:%s at %s" % (self.getName(), time.time()))
        
    def run(self):
        self.download_part()

# 为每一个视频的下载创建3个线程
def divede(filename, filesize, url,start_url):
    # 线程数
    threadnum = 3
    # 信号量，同时只允许3个线程运行
    threading.BoundedSemaphore(threadnum)
    # 默认三线程下载，也可以通过传参的方式设置线程数
    step = filesize // threadnum
    td_list = []
    start = 0
    end = -1
    while end < filesize -1:
        start = end +1
        end = start + step -1
        if end > filesize:
            end = filesize
        # print("start:%s, end:%s"%(start,end))
        t = ThreadDownload(url,start,end,filename,start_url)   # 一个下载线程
        t.start()
        td_list.append(t)

    for i in  td_list:
        i.join()

#  下载一个分P视频
''' 
传入参数说明:
video_list:包含了每p视频的所有分段
title1:视频的主标题
title:分p视频的标题
start_url:视频下载api地址
page: 分p视频链接尾缀 
'''   
def down_video(video_list, title1, title, start_url, page):
    num = 1
    print('[正在下载P{}段视频,请稍等...]:'.format(page) + title)
    currentVideoPath = os.path.join(rootDir, fav_name, title1, title)
    #传入的url = i,视频的大小为filesize
    for i in range(0,len(video_list[0])):
        url = video_list[0][i]
        filesize = video_list[1][i]
        # 创建文件夹存放下载的视频
        # 同时防止视频重复下载
        if not os.path.exists(currentVideoPath):
            os.makedirs(currentVideoPath)
            # 开始下载
            if len(video_list[0]) > 1:
                filename = os.path.join(currentVideoPath, r'{}-{}'.format(title,num))
                # 多线程下载
                divede(filename,filesize,url,start_url)
                combine_video_part(currentVideoPath,title,num=num)
            else:
                filename = os.path.join(currentVideoPath, r'{}'.format(title))
                # 多线程下载
                divede(filename,filesize,url, start_url)
                combine_video_part(currentVideoPath,title)
            num += 1

# 合并多线程下载的临时文件
def combine_video_part(filename, title, num = 0): 
    print('[片段下载完成,正在合成临时文件...]:' + title)
    # 定义一个数组
    # 访问 video 文件夹 (假设视频都放在这里面)
    root_dir = filename  # 当前目录作为下载目录
    # 选择待合成的视频
    if num == 0:
        files = obtain_certrain_name_list(os.listdir(root_dir), '%s.*?\.temp' % title)
        outfilename = os.path.join(root_dir, r'{}.flv'.format(title))
    else:
        files = obtain_certrain_name_list(os.listdir(root_dir), '%s-%s.*?\.temp' % (title,num))
        outfilename = os.path.join(root_dir, r'{}-{}.flv'.format(title,num))
    # 将文件排序合并
    # rindex() 返回子字符串 str 在字符串中最后出现的位置
    with open(outfilename,'wb+') as f:
        for file in sorted(files, key=lambda x: int(x[x.rindex("_") + 1:x.rindex(".")])):
            print(file)
            # 如果后缀名为 .mp4/.flv
            if os.path.splitext(file)[1] == '.temp':
                # 拼接成完整路径
                filePath = os.path.join(root_dir, file)
                tempfile = open(filePath,'rb+')
                f.write(tempfile.read())
                tempfile.close()
    print('删除临时文件...')
    # 删除视频片段文件
    for file in files:
        filePath = os.path.join(root_dir, file)
        os.remove(filePath)

# 合并视频
def combine_video(video_list, title1, title):
    currentVideoPath = os.path.join(rootDir, fav_name, title1, title)  # 当前目录作为下载目录
    if len(video_list[0]) >= 2:
        # 视频大于一段才要合并
        print('[下载完成,正在合并视频...]:' + title)
        # 定义一个数组
        L = []
        # 访问 video 文件夹 (假设视频都放在这里面)
        root_dir = currentVideoPath
        # 依序遍历所有文件
        for file in sorted(os.listdir(root_dir), key=lambda x: int(x[x.rindex("-") + 1:x.rindex(".")])):
            # 如果后缀名为 .mp4/.flv
            if os.path.splitext(file)[1] == '.flv':
                # 拼接成完整路径
                filePath = os.path.join(root_dir, file)
                # 载入视频
                video = VideoFileClip(filePath)
                # 添加到数组
                L.append(video)
                # 删除视频片段文件
                if(os.path.exists(filePath)):
                    os.remove(filePath)

        # 拼接视频
        final_clip = concatenate_videoclips(L)
        # 生成目标视频文件
        final_clip.to_videofile(os.path.join(root_dir, r'{}.flv'.format(title)), fps=24, remove_temp=False)
        #remove_temp=True表示生成的音频文件是临时存放的，视频生成后，音频文件会自动处理掉！若为False表示，音频文件会同时生成！
        print('[视频合并完成]' + title)

    else:
        # 视频只有一段则直接打印下载完成
        print('[视频合并完成]:' + title)

# 下载视频的主流程
def DownloadVideo(start, quality, start_time):
    if start.isdigit() == True:
        # 如果输入的是av号
        # 获取cid的api, 传入aid即可
        aid = start
        start_url = 'https://api.bilibili.com/x/web-interface/view?aid=' + aid
    else:
        # 如果输入的是url (eg: https://www.bilibili.com/video/av46958874/)
        aid = re.search(r'/av(\d+)/*', start).group(1)
        start_url = 'https://api.bilibili.com/x/web-interface/view?aid=' + aid
    # 获取视频的cid,分p视频的title
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'
    }
    html = requests.get(start_url, headers=headers).json()
    data = html['data']
    cid_list = []
    if '?p=' in start:
        # 单独下载分P视频中的一集
        p = re.search(r'\?p=(\d+)', start).group(1)
        cid_list.append(data['pages'][int(p) - 1])
    else:
        # 默认下载视频的所有分p
        cid_list = data['pages']
    # print(cid_list)
    for item in cid_list:
        cid = str(item['cid'])
        title = item['part']
        title = clean_txt(title)
        print('[下载视频的cid]:' + cid)
        print('[下载视频的标题]:' + title)
        page = str(item['page'])
        start_url = start_url + "/?p=" + page
        # 访问API地址
        video_list = get_play_list(aid, cid, quality)
        # 下载视频 
        down_video(video_list, aid, title, start_url, page)
        combine_video(video_list, aid, title)

# 下载一个bilibili视频的函数，输入参数为：视频的av号或者视频地址，视频质量参数(默认为1080p)
def downloadAvideo(start, quality = 80):
    start = start                   # 视频的av号或者视频地址
    quality = quality               # 视频的质量参数
    start_time = time.time()        # 每次下载开始的时间
    try:
        DownloadVideo(start, quality, start_time)
    except Exception as error1:
        print('当前下载发生了错误,请重新尝试')
        print(error1)
        time.sleep(2)

# 使用示范
if __name__ == "__main__":
    download_list = ['https://www.bilibili.com/video/av92399955',
                     'https://www.bilibili.com/video/av62399999',
                     'https://www.bilibili.com/video/av58825359']
    for url in download_list:
        downloadAvideo(url, 80)
    # 如果是windows系统，下载完成后打开下载目录
    if (sys.platform.startswith('win')):
        os.startfile(rootDir+'/'+fav_name)






