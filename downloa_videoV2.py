import requests
import re
import json
import threading
import os
import time

cookie = open('cookie.txt', 'r').read()
if not cookie:
    exit('请先获取cookie')
headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0',
        'Referer': 'https://www.bilibili.com/',
        'Origin': 'https://www.bilibili.com',
        'Cookie': cookie
}

def verify_url(url_list):
    '''
    验证给定的字符串列表是否是有效的bilibili视频链接
    
    :param url_list: 需要验证的url列表
    :return: 有效的url列表
    '''
    vailed_url_list = []
    compile = re.compile(r'^https?://www.bilibili.com/video/(.*?)$')
    for url in url_list:
    # 检查url 是不是为https://www.bilibili.com/video/(BV号) 的格式
        if compile.match(url) != None:
            vailed_url_list.append(compile.match(url).group(0))
    return vailed_url_list

def get_video_number(url):
    # 编译一个正则表达式，用于匹配视频号码
    compile = re.compile('[ab][v]\w+',re.I)
    # 如果url中包含视频号码
    if compile.search(url) != None:
        # 获取视频号码
        result = compile.search(url).group()
        return result
    else:
        # 如果没有找到视频号码，返回None
        return None

def get_video_info(url):
    # 创建一个会话
    session = requests.session()
    # 发送请求，获取响应
    response = session.get(url, headers=headers)
    # 如果响应成功
    if response.ok == True:
        # 获取响应中的html
        html = response.text
        # 使用正则表达式获取json数据
        json_data = json.loads(re.search('<script>window.__playinfo__=(.*?)</script>',html).groups()[0])
        # 使用正则表达式获取标题
        title = re.search('"title":"(.*?)"',html).groups()[0]
        # 获取视频url
        video_url = json_data['data']['dash']['video'][0]['baseUrl']
        # 获取音频url
        audio_url = json_data['data']['dash']['audio'][0]['baseUrl']
        # 将视频信息存入列表
        video_info = [session,title,video_url,audio_url,url]
        # 返回视频信息
        return video_info
    else:
        # 如果响应失败，打印请求失败
        print('请求失败')
        return None

# 定义下载视频的函数
def download_video(video_url,session,headers,Referer):
    # 添加Referer头
    headers['Referer'] = Referer
    # 尝试3次下载
    for i in range(3):
        # 使用session发起请求
        response = session.get(video_url,stream=True,headers=headers)
        # 如果请求成功
        if response.ok == True:
            # 以二进制写模式打开文件
            with open('video.mp4','wb') as f:
                # 遍历响应的content
                for chunk in response.iter_content(chunk_size=1024):
                    # 如果chunk不为空
                    if chunk:
                        # 将chunk写入文件
                        f.write(chunk)
                # 打印下载完成
                print('视频下载完成')
            # 跳出循环
            break
        # 如果请求失败
        else:
            # 打印下载失败次数
            print(f'视频第{i}茨下载失败')

# 定义下载音频的函数
def download_audio(audio_url,session,headers,Referer):
    # 添加Referer头
    headers['Referer'] = Referer
    # 尝试3次下载
    for i in range(3):
        # 使用session发起请求
        response = session.get(audio_url,stream=True,headers=headers)
        # 如果请求成功
        if response.ok == True:
            # 以二进制写模式打开文件
            with open('audio.mp3','wb') as f:
                # 遍历响应的content
                for chunk in response.iter_content(chunk_size=1024):
                    # 如果chunk不为空
                    if chunk:
                        # 将chunk写入文件
                        f.write(chunk)
                # 打印下载完成
                print('音频下载完成')
            # 跳出循环
            break
        # 如果请求失败
        else:
            # 打印下载失败次数
            print(f'视频第{i}茨下载失败')

def download_data(video_info):
    # 如果video_info不为空
    if video_info != None :
        # 获取视频信息
        session = video_info[0]
        title = video_info[1]
        video_url = video_info[2]
        audio_url = video_info[3]
        page_url = video_info[4]
        # 创建两个线程，分别用于下载视频和音频
        t1 = threading.Thread(target=download_video,args=(video_url,session,headers,page_url))
        t1.start()
        t2 = threading.Thread(target=download_audio,args=(audio_url,session,headers,page_url))
        t2.start()
        # 等待两个线程下载完成
        t1.join()
        t2.join()
        # 关闭会话
        session.close()
        # 如果视频和音频都下载成功，返回标题
        if os.path.exists('video.mp4') and os.path.exists('audio.mp3'):
            return title
        else:
            # 如果下载失败，删除视频和音频文件
            try:
                os.remove('video.mp4')
                os.remove('audio.mp3')
            except:
                pass
            # 返回None
            return None
    else:
        # 如果video_info为空，返回None
        return None

def ffmpeg_merge(number):
    # 如果传入的number不为空
    if number != None:
        # 使用os.system()函数执行ffmpeg命令，合并视频和音频
        os.system('ffmpeg -i video.mp4 -i audio.mp3 -c:v copy -c:a copy output.mp4')
        # 如果video文件夹不存在，则创建video文件夹
        if not os.path.exists('video'):
            os.mkdir('video')
        # 获取当前工作目录
        path = os.getcwd()
        # 将当前工作目录和video文件夹路径拼接
        path = os.path.join(path, 'video')
        # 将合并后的视频文件重命名
        new_file_name = number +'.mp4'
        os.renames('output.mp4',os.path.join(path, new_file_name))
        # 删除视频和音频文件
        os.remove('video.mp4')
        os.remove('audio.mp3')
        # 打印提示信息
        print('视频合并完成')
        # 返回True
        return True
    else:
        # 返回False
        return False

def main():
    # 打开文件，读取视频url
    with open('video_url.txt', 'r', encoding='utf-8') as f:
        url_list = f.read()
    # 将url按行分割
    url_list = url_list.split('\n')
    # 验证url
    vailed_url_list = verify_url(url_list)
    # 统计有效url数量
    vailed_url_num = len(vailed_url_list)
    # 如果有效url数量为0，则提示没有有效的url，并返回
    if vailed_url_num == 0:
        print('没有有效的url')
        return
    # 打印总url数量和有效url数量
    print('总url数量',len(url_list),'\n有效的url数量,',vailed_url_num)
    # 计数器
    counter = 0
    # 存储所有视频信息
    all_video_info = []
    # 遍历有效url列表
    for url in vailed_url_list:
        #获取视频信息
        number = get_video_number(url)
        counter +=1
        # 获取视频信息
        video_info = get_video_info(url)
        # 如果获取视频信息失败，则暂停10秒
        if video_info == None:
            print(f'第{counter}个视频获取视频信息失败,暂停10秒')
            # 赞同10秒
            time.sleep(10)
            continue
        #开始下载数据
        title = download_data(video_info)
        # 如果下载数据失败，则暂停10秒
        if title == None:
            time.sleep(10)
            continue
        # 下载完成 开始合并数据
        if ffmpeg_merge(number) != False:
            print(f'{counter}个视频{title} 下载和合并完成,暂停30秒')
            # 创建视频信息字典
            video_info_dict = {
                'title':title,
                'url':url,
                'number':number
            }
            # 将视频信息添加到所有视频信息列表中
            all_video_info.append(video_info_dict)
            #暂停30秒
            if counter != vailed_url_num:
                time.sleep(30)
        else:
            print(f'{counter}个视频{title} 下载或合并失败')
    # 如果存在video_info.json文件，则将所有视频信息添加到该文件中
    if os.path.exists('./video_info.json'):
        with open('./video_info.json','r+',encoding='utf-8') as f:
            json_data = f.read()
            json_data = json.loads(json_data)
            json_data.extend(all_video_info)
            f.seek(0)
            f.write(json.dumps(json_data,indent=4,ensure_ascii=False))
            f.truncate()
    else:
        # 否则创建video_info.json文件，并将所有视频信息写入该文件中
        with open('./video_info.json','w',encoding='utf-8') as f:
            f.write(json.dumps(all_video_info,indent=4,ensure_ascii=False))
if __name__ == '__main__':
    main()