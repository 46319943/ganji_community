import os
import requests
from bs4 import BeautifulSoup
import time
from urllib.parse import urlparse
import re
import csv
from pathlib import Path
import traceback
import sys

proxies = {'http': 'http://localhost:1080'}
BS_PARSER = 'html.parser'
headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7,ja;q=0.6',
    'Cache-Control': 'max-age=0',
    'Host': 'bj.ganji.com',
    'Proxy-Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.97 Safari/537.36'
}
community_attr_key_list = ['小区名称', '房价', '区域商圈：', '详细地址：', '建筑类型：', '物业费用：',
                           '产权类别：', '容积率：', '总户数：', '绿化率：', '建筑年代：', '停车位：', '开发商：', '物业公司：',
                           '经度', '纬度']
# 更改当前目录为文件锁在目录
current_path = os.path.abspath(__file__)
current_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(current_dir)


def fetch(url, **kwargs):
    url = str(url)
    if url.startswith('//'):
        url = url.replace('//', 'http://', 1)
    while True:
        try:
            # r = requests.get(url, timeout=10, proxies=proxies, **kwargs)
            r = requests.get(url, timeout=10, **kwargs)
            while r.text.strip() == '':
                print('请求内容为空，重新请求')
                r = requests.get(url, timeout=10, **kwargs)
            while '进行验证码校验' in r.text:
                print(url)
                print('程序暂停，请访问链接进行人机验证！')
                os.system("pause")
                r = requests.get(url, timeout=10, **kwargs)
            return r
        except TimeoutError as e:
            print(url)
            print(e)
            print('访问超时')
        except Exception as e:
            print(url)
            print(e)
            print('获取页面内容时出错了')


def geocode(geo_name, city=''):
    url = (
        f'http://api.map.baidu.com/geocoding/v3/?address={geo_name}'
        f'&city={city}&output=json&ak=edUmWCLHPjvuY0OXdRrNna38b4GX30VV'
    )
    r = requests.get(url)
    r = r.json()
    if r['status'] != 0:
        print(r)
        raise Exception('这里有个异常，看看吧')
    return [r['result']['location']['lng'], r['result']['location']['lat']]


def main(city):
    community_list = []
    city_file_path = Path(city+'.csv')
    is_exist = False
    if city_file_path.exists():
        is_exist = True
        with open(str(city_file_path), 'r') as f:
            reader = csv.reader(f)
            next(reader)
            for row in reader:
                community_list.append(row[0])

    city_file = open(str(city_file_path), 'a+', newline='')
    writer = csv.writer(city_file)
    if not is_exist:
        writer.writerow(community_attr_key_list)

    # 赶集网城市选择首页
    index_r = fetch('http://www.ganji.com/index.htm')

    # html.parser、lxml HTML、lxml XML、html5lib解析器区别
    index_bs = BeautifulSoup(index_r.text, BS_PARSER)
    index_a = index_bs.find('a', text=city)

    # 对应城市的子域名
    index_href = index_a['href']

    # --------
    list_r = requests.get(index_href + 'chuzu/pn1')
    list_bs = BeautifulSoup(list_r.text, BS_PARSER)
    subarea_list = [x['href'] for x in list_bs.select('.thr-list a')]
    # --------

    page = 0
    # TODO:在这里改变链接，来爬取不同区域的房租列表
    list_href = index_href + 'chuzu/pn1'
    while True:
        # 出租页面列表
        page += 1
        # 不能直接访问chuzu，学校IP访问次数限制。浏览器代理访问所以不受影响
        # 翻页的时候停一下
        time.sleep(0.5)

        list_r = fetch(list_href)
        list_bs = BeautifulSoup(list_r.text, BS_PARSER)

        time.sleep(1)

        # ...

        # 链接列表
        list_a_list = list_bs.select('.ershoufang-list dd.dd-item.title a')

        list_list = [[l.select_one('dd.dd-item.title a'),
                      l.select_one('.address-eara:last-child').get_text(strip=True).replace('...', '')]
                     for l in list_bs.select('.ershoufang-list')]
        for [list_a, list_community] in list_list:
            # 暂停进行人机验证，不挂起
            # time.sleep(0.5)
            if list_community in community_list:
                print(f'{list_community}已在列表中，跳过')
                continue
            try:
                # &key=¶ms=ra 这里乱码
                item_href = list_a['href']
                # item_href = re.compile(r'entinfo=(\d+)_0').findall(item_href)[0]
                item_href = re.compile('key=.*&').sub('', item_href)

                # item_r = fetch('https://jxjump.58.com/service?target=FCADV8oV3os7xtAj_6pMK7rUlrztK2I2XgGp_ir8Za1X4Ap_Zpk1zEffDjvZrKof8T9H1Etf3gzeNV-h7xP23s1aDYDtaGQMt0V1-x_7k2_EqtKo7wITX0Rw7HMRl9KE7zsZb7bPyKFQTpiGJTuRsjMqTHZzOMkNr3kS6ZtAUEnEhkw5aqSx4Uvrv63dFoqNyNhGQgafNqWfm3ZKqr6XLq3dz06ApDR5hWRpH8YZE29olTwTVbjAbE8amfg&pubid=0&apptype=10&psid=150065938206327100784721924&entinfo=40209270904961_0&cookie=|||9094ac41d9b2fdad39356072c0cc78a8&fzbref=0&key=¶ms=rankbusitime0099^desc&gjcity=bj')
                # item_r = fetch('https://jxjump.58.com/service?target=FCADV8oV3os7xtAj_6pMK7rUlrztK2I2XgGp_ir8Za1X4Ap_Zpk1zEffDjvZrKof8T9H1Etf3gzeNV-h7xP23s1aDYDtaGQMt0V1-x_7k2_EqtKo7wITX0Rw7HMRl9KE7zsZb7bPyKFQTpiGJTuRsjMqTHZzOMkNr3kS6ZtAUEnEhkw5aqSx4Uvrv63dFoqNyNhGQgafNqWfm3ZKqr6XLq3dz06ApDR5hWRpH8YZE29olTwTVbjAbE8amfg&pubid=0&apptype=10&psid=150065938206327100784721924&entinfo=40209270904961_0&gjcity=bj')
                item_r = fetch(item_href)
                item_bs = BeautifulSoup(item_r.text, BS_PARSER)

                # 小区链接
                item_a = item_bs.select_one(
                    'ul.er-list-two.f-clear li.er-item.f-fl .content a')
                if item_a is None:
                    print(item_href)
                    # 在自己封装的fetch函数中处理验证问题
                    # if '验证' in item_r.text:
                    #     print('程序暂停，请访问链接进行人机验证！')
                    #     os.system("pause")
                    #     # 这个小区也不放过
                    #     item_r = fetch(item_href)
                    #     item_bs = BeautifulSoup(item_r.text, BS_PARSER)
                    #     item_a = item_bs.select_one(
                    #         'ul.er-list-two.f-clear li.er-item.f-fl .content a')
                
                    print('此房的小区无信息')
                    continue
                community_r = fetch(item_a['href'])
                community_bs = BeautifulSoup(community_r.text, BS_PARSER)
                if community_bs.select_one('.card-top .card-title') is None:
                    print('小区页面错误：')
                    print(community_r.text)
                    print(item_a['href'])

                community_title = community_bs.select_one(
                    '.card-top .card-title')['title']

                print(
                    f'页数：{page}，已搜索{len(community_list)}个小区，找到小区：{community_title}')
                if community_title in community_list:
                    continue
                # 字符串也是子节点
                community_price = community_bs.select_one(
                    'span.price').contents[0]
                # 是L不是1
                # 可以使用双层列表生成式
                # community_attr_list = [s for attr in community_bs.select('li.item.f-fl .content') for s in attr.stripped_strings]
                # 属性值
                community_attr_value_list = [re.sub(r'\s+', ' ', attr.get_text(strip=True))
                                             for attr in community_bs.select('li.item.f-fl .content')]
                #  属性键
                # community_attr_key_list = [re.sub(r'\s+', '', attr.get_text(strip=True))
                #                            for attr in community_bs.select('li.item.f-fl :first-child')]
                # print(community_attr_key_list)
                # ['区域商圈：', '详细地址：', '建筑类型：', '物业费用：', '产权类别：', '容积率：', '总户数：', '绿化率：', '建筑年代：', '停车位：', '开发商：', '物业公司：']

                # 根据地址获取经纬度信息
                address = city + community_attr_value_list[1] + community_title

                writer.writerow([community_title, community_price,
                                 *community_attr_value_list, *geocode(address, city)])
                community_list.append(community_title)
            except Exception as e:
                print(e)
                ex_type, ex_val, ex_stack = sys.exc_info()
                print(ex_type)
                print(ex_val)
                for stack in traceback.extract_tb(ex_stack):
                    print(stack)
                continue
                # raise Exception('停停停！')
        # 下一页的链接
        list_href = list_bs.find('a', text='下一页')
        print(list_href)
        if list_href is None:
            break
        list_href = list_href['href']

    city_file.close()


if __name__ == "__main__":
    # city_list = [x.name for x in Path('D:\Document\HousePricing\公司').iterdir()]
    # ['上海', '东莞', '北京', '南京', '厦门', '合肥', '大连', '天津', '广州', '成都', '杭州', '武汉', '沈阳', '济南', '深圳', '烟台', '苏州', '重庆', '长沙', '青岛']
    city_list = ['上海', '东莞', '北京', '南京', '厦门', '合肥', '大连', '天津', '广州', '成都', '杭州', '武汉', '沈阳', '济南', '深圳', '烟台', '苏州', '重庆', '长沙', '青岛']
    print(city_list)
    for city in city_list:
        main(city)
