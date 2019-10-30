import re
import json
import time
import random
import requests
from retrying import retry
import numpy as np
import os
import shutil
import pandas as pd
import jieba.analyse
from pyecharts import options as opts
from pyecharts.globals import SymbolType
from snapshot_selenium import snapshot
from pyecharts.render import make_snapshot
from pyecharts.charts import Pie, Bar, Map, WordCloud


COOKIES_FILE_PATH = 'taobao_login_cookies.txt'

goodsSearchName = '女装'

dictName = "{}数据分析".format(goodsSearchName)
# 关闭警告
requests.packages.urllib3.disable_warnings()
# 登录与爬取需使用同一个Session对象
req_session = requests.Session()
# 淘宝商品excel文件保存路径
GOODS_EXCEL_PATH = 'taobao_goods_{}.xlsx'.format(goodsSearchName)
# 淘宝商品标准excel文件保存路径
GOODS_STANDARD_EXCEL_PATH = 'taobao_goods_{}_standard.xlsx'.format(goodsSearchName)
# 清洗词
STOP_WORDS_FILE_PATH = 'stop_words.txt'



#获取当前用户桌面目录
topdeskPath = os.path.join(os.path.expanduser("~"), 'Desktop/{}'.format(dictName))

# shutil.rmtree(topdeskPath)
#
# #在桌面下创建文件夹
# os.mkdir(topdeskPath)

try:
    os.mkdir(topdeskPath)
except:
    shutil.rmtree(topdeskPath)
    os.mkdir(topdeskPath)



class TaoBaoLogin:

    def __init__(self, session):
        """
        账号登录对象
        :param username: 用户名
        :param ua: 淘宝的ua参数
        :param TPL_password2: 加密后的密码
        """
        # 检测是否需要验证码的URL
        self.user_check_url = 'https://login.taobao.com/member/request_nick_check.do?_input_charset=utf-8'
        # 验证淘宝用户名密码URL
        self.verify_password_url = "https://login.taobao.com/member/login.jhtml"
        # 访问st码URL
        self.vst_url = 'https://login.taobao.com/member/vst.htm?st={}'
        # 淘宝个人 主页
        self.my_taobao_url = 'http://i.taobao.com/my_taobao.htm'

        # 淘宝用户名
        self.username = 't_1498213087885_0711'
        # 淘宝重要参数，从浏览器或抓包工具中复制，可重复使用
        self.ua = '121#spqlkEDComllVlhLxBhmllXi6USrKujVlGgYezNbDTdJvMg1El55ll9YOc8MKujVlwuYxzB5SDtZxlrJEIiIlQXYOcFNv+JbVmgY+1Y5KM9VKyrnEkDIll9YOc8fDujllwKY+zPIDM9lOQrJEmD5lCoYOcfd7bVCC9MmltpgebCs8ySm/0bvGFQmCbibYQhEU960C6JbnnCVp2D0CZ04Mu/1nsfq6NIaFtclb6i0nn2Yug90k65T8Khhbgi0kNaXF960C6ibnnC9pCibCZ5T8uBmCbibCeIaFtFbbnaln4emsyY0CZeT8upmVdEb/jn1FkFbG6fjJyC9pCDRVl1RWM8RD+jJ/20ClV/j/OP/xfnZMR1IjcyJBnT1J5VFSESaAcU8jDqXC1GSS32JirKa1Vgib+YCA8j6wR2WzJWJe8LsuMDKTkEe3GkMFK+8UeEAWFt9b5J0fWJKAbHvzTboYvaGLlYuT2cZH/3vBXCImaPvVZOTI2r/REtAwD/QK+bUDKikCAmvFc+26jXyzeAEQcOO48m7qlCh3NojwbcMSy8K1s1j0zq09dN1PrvAd9V/oPdSd3lrq6xJwI0OQ0zFypTBUQz5A3edwPgR2MO5u3S+7Y7+Zqs/MSSoYAAtulm5lagQT5v55Ye3c/wxuUCam3hftV/7XIbjijWysy+NQFAk9LC3EJQj2NfSlL+ohbbk/EA0SjZuhE8OA/jI4KGPaC+xsY4uszpVxjBmSNDMWQlx+F774PlJZ2/GjbPG1Kpu1Y1jiE9rWQATUqogtmbDMS/djB7qIcXsAN1adKtARBhDxx1c5S+0ukVfuGlbNHesj4BdlcUtC4xOJi64pZ8WdZRklardEWf/goock6pkfoK1hzETsWwJ+eGnrf5t8bvl1EMBa7zxFGNNvC7gMiVbCX3kc5v5JfzbRmWM1EZJjzMupydZKO3AVvjNU3j6IZZ3kY1Z/JiPeLGF4ze1WrJhZ4uSEevtN7gwj9MpoN+tQcnEmzxVWUYxIhGcPwkOlLGCeCJMzFM0uNmM9VnpdtM1FmHAXzWsETRYwa92BzxTcxgijTgcR1aquejsDYddT4pdZqSqS8zlD+8Oae8/Wk4UIjntQgjAIFcpxvV/uMZrTw=='
        # 加密后的密码，从浏览器或抓包工具中复制，可重复使用
        self.TPL_password2 = '184b90910737f3535e8920325f24ca0730b0f6769a254b77505f96a9645680b1b30d09e1d7799ba4e8e97d9ae182f3b35beade3c963e99981d23f5bcded67af14f6957dce49316115a91e63039b8238f905b84de2c30696783badbeda9ba52f81a0760f420c772441408b518f012fe64660a36d02c2dbf8e670904cf8ac529cc'

        # 请求超时时间
        self.timeout = 3
        # session对象，用于共享cookies
        self.session = session

        if not self.username:
            raise RuntimeError('请填写你的淘宝用户名')

    def _user_check(self):
        """
        检测账号是否需要验证码
        :return:
        """
        data = {
            'username': self.username,
            'ua': self.ua
        }
        try:
            response = self.session.post(self.user_check_url, data=data, timeout=self.timeout)
            response.raise_for_status()
        except Exception as e:
            print('检测是否需要验证码请求失败，原因：')
            raise e
        needcode = response.json()['needcode']
        print('是否需要滑块验证：{}'.format(needcode))
        return needcode

    def _verify_password(self):
        """
        验证用户名密码，并获取st码申请URL
        :return: 验证成功返回st码申请地址
        """
        verify_password_headers = {
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'Origin': 'https://login.taobao.com',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Referer': 'https://login.taobao.com/member/login.jhtml?from=taobaoindex&f=top&style=&sub=true&redirect_url=https%3A%2F%2Fi.taobao.com%2Fmy_taobao.htm',
        }
        # 登录toabao.com提交的数据，如果登录失败，可以从浏览器复制你的form data
        verify_password_data = {
            'TPL_username': self.username,
            'ncoToken': '78401cd0eb1602fc1bbf9b423a57e91953e735a5',
            'slideCodeShow': 'false',
            'useMobile': 'false',
            'lang': 'zh_CN',
            'loginsite': 0,
            'newlogin': 0,
            'TPL_redirect_url': 'https://s.taobao.com/search?q=%E9%80%9F%E5%BA%A6%E9%80%9F%E5%BA%A6&imgfile=&commend=all&ssid=s5-e&search_type=item&sourceId=tb.index&spm=a21bo.2017.201856-taobao-item.1&ie=utf8&initiative_id=tbindexz_20170306',
            'from': 'tb',
            'fc': 'default',
            'style': 'default',
            'keyLogin': 'false',
            'qrLogin': 'true',
            'newMini': 'false',
            'newMini2': 'false',
            'loginType': '3',
            'gvfdcname': '10',
            # 'gvfdcre': '68747470733A2F2F6C6F67696E2E74616F62616F2E636F6D2F6D656D6265722F6C6F676F75742E6A68746D6C3F73706D3D61323330722E312E3735343839343433372E372E33353836363032633279704A767526663D746F70266F75743D7472756526726564697265637455524C3D6874747073253341253246253246732E74616F62616F2E636F6D25324673656172636825334671253344253235453925323538302532353946253235453525323542412532354136253235453925323538302532353946253235453525323542412532354136253236696D6766696C65253344253236636F6D6D656E64253344616C6C2532367373696425334473352D652532367365617263685F747970652533446974656D253236736F75726365496425334474622E696E64657825323673706D253344613231626F2E323031372E3230313835362D74616F62616F2D6974656D2E31253236696525334475746638253236696E69746961746976655F69642533447462696E6465787A5F3230313730333036',
            'TPL_password_2': self.TPL_password2,
            'loginASR': '1',
            'loginASRSuc': '1',
            'oslanguage': 'zh-CN',
            'sr': '1440*900',
            'osVer': 'macos|10.145',
            'naviVer': 'chrome|76.038091',
            'osACN': 'Mozilla',
            'osAV': '5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36',
            'osPF': 'MacIntel',
            'appkey': '00000000',
            'mobileLoginLink': 'https://login.taobao.com/member/login.jhtml?redirectURL=https://s.taobao.com/search?q=%E9%80%9F%E5%BA%A6%E9%80%9F%E5%BA%A6&imgfile=&commend=all&ssid=s5-e&search_type=item&sourceId=tb.index&spm=a21bo.2017.201856-taobao-item.1&ie=utf8&initiative_id=tbindexz_20170306&useMobile=true',
            'showAssistantLink': '',
            'um_token': 'TD0789BC99BFBBF893B3C8C0E1729CCA3CB0469EA11FF6D196BA826C8EB',
            'ua': self.ua
        }
        try:
            response = self.session.post(self.verify_password_url, headers=verify_password_headers, data=verify_password_data,
                              timeout=self.timeout)
            response.raise_for_status()
            # 从返回的页面中提取申请st码地址
        except Exception as e:
            print('验证用户名和密码请求失败，原因：')
            raise e
        # 提取申请st码url
        apply_st_url_match = re.search(r'<script src="(.*?)"></script>', response.text)
        # 存在则返回
        if apply_st_url_match:
            print('验证用户名密码成功，st码申请地址：{}'.format(apply_st_url_match.group(1)))
            return apply_st_url_match.group(1)
        else:
            raise RuntimeError('用户名密码验证失败！response：{}'.format(response.text))

    def _apply_st(self):
        """
        申请st码
        :return: st码
        """
        apply_st_url = self._verify_password()
        try:
            response = self.session.get(apply_st_url)
            response.raise_for_status()
        except Exception as e:
            print('申请st码请求失败，原因：')
            raise e
        st_match = re.search(r'"data":{"st":"(.*?)"}', response.text)
        if st_match:
            print('获取st码成功，st码：{}'.format(st_match.group(1)))
            return st_match.group(1)
        else:
            raise RuntimeError('获取st码失败！response：{}'.format(response.text))

    def login(self):
        """
        使用st码登录
        :return:
        """
        # 加载cookies文件
        if self._load_cookies():
            return True
        # 判断是否需要滑块验证
        self._user_check()
        st = self._apply_st()
        headers = {
            'Host': 'login.taobao.com',
            'Connection': 'Keep-Alive',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
        }
        try:
            response = self.session.get(self.vst_url.format(st), headers=headers)
            response.raise_for_status()
        except Exception as e:
            print('st码登录请求，原因：')
            raise e
        # 登录成功，提取跳转淘宝用户主页url
        my_taobao_match = re.search(r'top.location.href = "(.*?)"', response.text)
        if my_taobao_match:
            print('登录淘宝成功，跳转链接：{}'.format(my_taobao_match.group(1)))
            self._serialization_cookies()
            return True
        else:
            raise RuntimeError('登录失败！response：{}'.format(response.text))

    def _load_cookies(self):
        # 1、判断cookies序列化文件是否存在
        if not os.path.exists(COOKIES_FILE_PATH):
            return False
        # 2、加载cookies
        self.session.cookies = self._deserialization_cookies()
        # 3、判断cookies是否过期
        try:
            self.get_taobao_nick_name()
        except Exception as e:
            os.remove(COOKIES_FILE_PATH)
            print('cookies过期，删除cookies文件！')
            return False
        print('加载淘宝登录cookies成功!!!')
        return True

    def _serialization_cookies(self):
        """
        序列化cookies
        :return:
        """
        cookies_dict = requests.utils.dict_from_cookiejar(self.session.cookies)
        with open(COOKIES_FILE_PATH, 'w+', encoding='utf-8') as file:
            json.dump(cookies_dict, file)
            print('保存cookies文件成功！')

    def _deserialization_cookies(self):
        """
        反序列化cookies
        :return:
        """
        with open(COOKIES_FILE_PATH, 'r+', encoding='utf-8') as file:
            cookies_dict = json.load(file)
            cookies = requests.utils.cookiejar_from_dict(cookies_dict)
            return cookies

    def get_taobao_nick_name(self):
        """
        获取淘宝昵称
        :return: 淘宝昵称
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
        }
        try:
            response = self.session.get(self.my_taobao_url, headers=headers)
            response.raise_for_status()
        except Exception as e:
            print('获取淘宝主页请求失败！原因：')
            raise e
        # 提取淘宝昵称
        nick_name_match = re.search(r'<input id="mtb-nickname" type="hidden" value="(.*?)"/>', response.text)
        if nick_name_match:
            print('登录淘宝成功，你的用户名是：{}'.format(nick_name_match.group(1)))
            return nick_name_match.group(1)
        else:
            raise RuntimeError('获取淘宝昵称失败！response：{}'.format(response.text))

class GoodsSpider:

    def __init__(self, goodsSearchName):
        self.q = goodsSearchName
        # 超时
        self.timeout = 15
        self.goods_list = []
        # 淘宝登录
        tbl = TaoBaoLogin(req_session)
        tbl.login()
        tbl.get_taobao_nick_name()

    @retry(stop_max_attempt_number=3)
    def spider_goods(self, page):
        """

        :param page: 淘宝分页参数
        :return:
        """
        s = page * 44
        # 搜索链接，q参数表示搜索关键字，s=page*44 数据开始索引
        search_url = f'https://s.taobao.com/search?initiative_id=tbindexz_20170306&ie=utf8&spm=a21bo.2017.201856-taobao-item.2&sourceId=tb.index&search_type=item&ssid=s5-e&commend=all&imgfile=&q={self.q}&suggest=history_1&_input_charset=utf-8&wq=biyunt&suggest_query=biyunt&source=suggest&bcoffset=4&p4ppushleft=%2C48&s={s}&data-key=s&data-value={s + 44}'

        # 代理ip，网上搜一个，猪哥使用的是 站大爷：http://ip.zdaye.com/dayProxy.html
        # 尽量使用最新的，可能某些ip不能使用，多试几个。后期可以考虑做一个ip池
        # 爬取淘宝ip要求很高，西刺代理免费ip基本都不能用，如果不能爬取就更换代理ip
        # proxies = {'http': '14.29.232.142:8082',
        #            'http': '222.64.158.143:9000',
        #            'http': '223.75.67.42:63000',
        #            'http': '47.96.133.222:8118',
        #            'http': '49.77.209.42:50144',
        #            'http': '121.226.188.4:50043',
        #            'http': '49.88.118.78:50134'
        #            }
        # 请求头
        headers = {
            'referer': 'https://www.taobao.com/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
        }
        # proxies = proxies,
        response = req_session.get(search_url, headers=headers,
                                   verify=False, timeout=self.timeout)
        # print(response.text)
        goods_match = re.search(r'g_page_config = (.*?)}};', response.text)
        # 没有匹配到数据
        if not goods_match:
            print('提取页面中的数据失败！')
            print(response.text)
            raise RuntimeError
        goods_str = goods_match.group(1) + '}}'
        goods_list = self._get_goods_info(goods_str)
        self._save_excel(goods_list)
        # print(goods_str)

    def _get_goods_info(self, goods_str):
        """
        解析json数据，并提取标题、价格、商家地址、销量、评价地址
        :param goods_str: string格式数据
        :return:
        """
        goods_json = json.loads(goods_str)
        goods_items = goods_json['mods']['itemlist']['data']['auctions']
        goods_list = []
        for goods_item in goods_items:
            goods = {
                    'goodsId': goods_item["nid"],
                    'title': goods_item['raw_title'],
                     'price': goods_item['view_price'],
                     'location': goods_item['item_loc'],
                     'sales': goods_item['view_sales'],
                        "shop_id": goods_item["user_id"],
                        "shop_name": goods_item["nick"],
                        "comment_count": goods_item["comment_count"],
                     'comment_url': goods_item['comment_url']}
            goods_list.append(goods)
        return goods_list

    def _save_excel(self, goods_list):
        """
        将json数据生成excel文件
        :param goods_list: 商品数据
        :param startrow: 数据写入开始行
        :return:
        """
        # pandas没有对excel没有追加模式，只能先读后写
        if os.path.exists(GOODS_EXCEL_PATH):
            df = pd.read_excel(GOODS_EXCEL_PATH)
            df = df.append(goods_list)
        else:
            df = pd.DataFrame(goods_list)

        writer = pd.ExcelWriter(GOODS_EXCEL_PATH)
        # columns参数用于指定生成的excel中列的顺序
        df.to_excel(excel_writer=writer, columns=['goodsId','title', 'price', 'location', 'sales', 'shop_id','shop_name',"comment_count",'comment_url'], index=False,
                    encoding='utf-8', sheet_name='Sheet')
        writer.save()
        writer.close()

    def patch_spider_goods(self):
        """
        批量爬取淘宝商品
        如果爬取20多页不能爬，可以分段爬取
        :return:
        """
        # 写入数据前先清空之前的数据
        # if os.path.exists(GOODS_EXCEL_PATH):
        #     os.remove(GOODS_EXCEL_PATH)
        # 批量爬取，自己尝试时建议先爬取3页试试
        for i in range(0, 100):
            print('第%d页' % (i + 1))
            self.spider_goods(i)
            # 设置一个时间间隔
            time.sleep(random.randint(10, 15))


def standard_data():
    """
    处理淘宝爬取下来的原生数据
    例：
        1.5万人付款 -> 15000
        广州 广州 -> 广州
    :return:
    """
    df = pd.read_excel(GOODS_EXCEL_PATH)
    # 1、将价格转化为整数型
    raw_sales = df['sales'].values
    new_sales = []
    for sales in raw_sales:
        sales = sales[:-3]
        sales = sales.replace('+', '')
        if '万' in sales:
            sales = sales[:-1]
            if '.' in sales:
                sales = sales.replace('.', '') + '000'
            else:
                sales = sales + '0000'
        sales = int(sales)
        new_sales.append(sales)
    df['sales'] = new_sales
    print(df['sales'].values)

    # 2、将地区转化为只包含省
    raw_location = df['location'].values
    new_location = []
    for location in raw_location:
        if ' ' in location:
            location = location[:location.find(' ')]
        new_location.append(location)
    # df.location与df[location]效果类似
    df.location = new_location
    print(df['location'].values)

    # 3、生成新的excel
    writer = pd.ExcelWriter(GOODS_STANDARD_EXCEL_PATH)
    # columns参数用于指定生成的excel中列的顺序
    df.to_excel(excel_writer=writer, columns=['goodsId','title', 'price', 'location', 'sales', 'shop_id','shop_name',"comment_count",'comment_url'], index=False,
                encoding='utf-8', sheet_name='Sheet')
    writer.save()
    writer.close()




def analysis_title():
    """
    词云分析商品标题
    :return:
    """
    # 引入全局数据
    global DF_STANDARD
    # 数据清洗，去掉无效词
    # jieba.analyse.set_stop_words(STOP_WORDS_FILE_PATH)
    # 1、词数统计
    ciyun_file_name = os.getcwd() + "/{}关键词Top50词云图.png".format(goodsSearchName)
    keywords_count_list = jieba.analyse.textrank(' '.join(DF_STANDARD.title), topK=50, withWeight=True)
    print(keywords_count_list)
    # 生成词云
    word_cloud = (
        WordCloud()
            .add("", keywords_count_list, word_size_range=[20, 100], shape=SymbolType.DIAMOND)
            .set_global_opts(title_opts=opts.TitleOpts(title="{}词云TOP50".format(goodsSearchName)))
    )
    make_snapshot(snapshot,  word_cloud.render(),"{}关键词Top50词云图.png".format(goodsSearchName),)
    shutil.move(ciyun_file_name,topdeskPath)



    # 2、商品标题词频分析生成柱状图
    # 2.1统计词数
    # 取前20高频的关键词
    file_name = os.getcwd() + "/{}词频Top20.png".format(goodsSearchName)
    keywords_count_dict = {i[0]: 0 for i in reversed(keywords_count_list[:20])}
    cut_words = jieba.cut(' '.join(DF_STANDARD.title))
    for word in cut_words:
        for keyword in keywords_count_dict.keys():
            if word == keyword:
                keywords_count_dict[keyword] = keywords_count_dict[keyword] + 1
    print(keywords_count_dict)
    # 2.2生成柱状图
    keywords_count_bar = (
        Bar()
            .add_xaxis(list(keywords_count_dict.keys()))
            .add_yaxis("", list(keywords_count_dict.values()))
            .reversal_axis()
            .set_series_opts(label_opts=opts.LabelOpts(position="right"))
            .set_global_opts(
            title_opts=opts.TitleOpts(title="{}热门词TOP20".format(goodsSearchName)),
            yaxis_opts=opts.AxisOpts(name="热门词"),
            xaxis_opts=opts.AxisOpts(name="商品数")
        )
    )
    make_snapshot(snapshot,  keywords_count_bar.render(),"{}词频Top20.png".format(goodsSearchName),)
    shutil.move(file_name,topdeskPath)

    # 3、标题高频关键字与平均销量关系
    keywords_sales_dict = analysis_title_keywords(keywords_count_list, 'sales', 20)
    # 生成柱状图
    keywords_sales_bar = (
        Bar()
            .add_xaxis(list(keywords_sales_dict.keys()))
            .add_yaxis("", list(keywords_sales_dict.values()))
            .reversal_axis()
            .set_series_opts(label_opts=opts.LabelOpts(position="right"))
            .set_global_opts(
            title_opts=opts.TitleOpts(title="{}关键词与平均销量关系TOP20".format(goodsSearchName)),
            yaxis_opts=opts.AxisOpts(name="关键词"),
            xaxis_opts=opts.AxisOpts(name="平均销量")
        )
    )
    file_name = os.getcwd() + "/{}关键词与平均销量关系TOP20.png".format(goodsSearchName)
    make_snapshot(snapshot,  keywords_sales_bar.render(),"{}关键词与平均销量关系TOP20.png".format(goodsSearchName),)
    shutil.move(file_name,topdeskPath)

    # 4、标题高频关键字与平均售价关系
    keywords_price_dict = analysis_title_keywords(keywords_count_list, 'price', 20)
    # 生成柱状图
    keywords_price_bar = (
        Bar()
            .add_xaxis(list(keywords_price_dict.keys()))
            .add_yaxis("", list(keywords_price_dict.values()))
            .reversal_axis()
            .set_series_opts(label_opts=opts.LabelOpts(position="right"))
            .set_global_opts(
            title_opts=opts.TitleOpts(title="{}关键词与平均售价关系TOP20".format(goodsSearchName)),
            yaxis_opts=opts.AxisOpts(name="关键词"),
            xaxis_opts=opts.AxisOpts(name="平均售价")
        )
    )
    file_name = os.getcwd() + "/{}关键词与平均售价关系TOP20.png".format(goodsSearchName)
    make_snapshot(snapshot,  keywords_price_bar.render(),"{}关键词与平均售价关系TOP20.png".format(goodsSearchName),)
    shutil.move(file_name,topdeskPath)


def analysis_title_keywords(keywords_count_list, column, top_num) -> dict:
    """
    分析标题关键字与其他属性的关系
    :param keywords_count_list: 关键字列表
    :param column: 需要分析的属性名
    :param top_num: 截取前多少个
    :return:
    """
    # 1、获取高频词，生成一个dict={'keyword1':[], 'keyword2':[],...}
    keywords_column_dict = {i[0]: [] for i in keywords_count_list}
    for row in DF_STANDARD.iterrows():
        for keyword in keywords_column_dict.keys():
            if keyword in row[1].title:
                # 2、 将标题包含关键字的属性值放在列表中，dict={'keyword1':[属性值1,属性值2,..]}
                keywords_column_dict[keyword].append(row[1][column])
    # 3、 求属性值的平均值，dict={'keyword1':平均值1, 'keyword2',平均值2}
    for keyword in keywords_column_dict.keys():
        keyword_column_list = keywords_column_dict[keyword]
        keywords_column_dict[keyword] = sum(keyword_column_list) / len(keyword_column_list)
    # 4、 根据平均值排序，从小到大
    keywords_price_dict = dict(sorted(keywords_column_dict.items(), key=lambda d: d[1]))
    # 5、截取平均值最高的20个关键字
    keywords_price_dict = {k: keywords_price_dict[k] for k in list(keywords_price_dict.keys())[-top_num:]}
    print(keywords_price_dict)
    return keywords_price_dict





def analysis_price():
    """
    分析商品价格
    :return:
    """
    # 引入全局数据
    global DF_STANDARD
    # 设置切分区域
    price_list_bins = [0, 20, 40, 60, 80, 100, 120, 150, 200, 1000000]
    # 设置切分后对应标签
    price_list_labels = ['0-20', '21-40', '41-60', '61-80', '81-100', '101-120', '121-150', '151-200', '200以上']
    # 分区统计
    price_count = cut_and_sort_data(price_list_bins, price_list_labels, DF_STANDARD.price)
    print(price_count)
    # 生成柱状图
    bar = (
        Bar()
            .add_xaxis(list(price_count.keys()))
            .add_yaxis("", list(price_count.values()))
            .set_global_opts(
            title_opts=opts.TitleOpts(title="{}价格区间分布柱状图".format(goodsSearchName)),
            yaxis_opts=opts.AxisOpts(name="个商品"),
            xaxis_opts=opts.AxisOpts(name="商品售价：元")
        )
    )
    file_name = os.getcwd() + "/{}价格区间分布柱状图.png".format(goodsSearchName)
    make_snapshot(snapshot,  bar.render(),"{}价格区间分布柱状图.png".format(goodsSearchName),)
    shutil.move(file_name,topdeskPath)
    # 生成饼图
    age_count_list = [list(z) for z in zip(price_count.keys(), price_count.values())]
    pie = (
        Pie()
            .add("", age_count_list)
            .set_global_opts(title_opts=opts.TitleOpts(title="{}价格区间饼图".format(goodsSearchName)))
            .set_series_opts(label_opts=opts.LabelOpts(formatter="{b}: {c}"))
    )
    file_name = os.getcwd() + "/{}价格区间饼图.png".format(goodsSearchName)
    make_snapshot(snapshot,  pie.render(),"{}价格区间饼图.png".format(goodsSearchName),)
    shutil.move(file_name,topdeskPath)


def analysis_sales():
    """
    销量情况分布
    :return:
    """
    # 引入全局数据
    global DF_STANDARD
    # 设置切分区域
    listBins = [0, 1000, 5000, 10000, 50000, 100000, 1000000]
    # 设置切分后对应标签
    listLabels = ['一千以内', '一千到五千', '五千到一万', '一万到五万', '五万到十万', '十万以上']
    # 分区统计
    sales_count = cut_and_sort_data(listBins, listLabels, DF_STANDARD.sales)
    print(sales_count)
    # 生成柱状图
    bar = (
        Bar()
            .add_xaxis(list(sales_count.keys()))
            .add_yaxis("", list(sales_count.values()))
            .set_global_opts(
            title_opts=opts.TitleOpts(title="{}商品销量区间饼图".format(goodsSearchName)),
            yaxis_opts=opts.AxisOpts(name="个商品"),
            xaxis_opts=opts.AxisOpts(name="销售件数")
        )
    )
    file_name = os.getcwd() + "/{}销量区间柱状图.png".format(goodsSearchName)
    make_snapshot(snapshot,  bar.render(),"{}销量区间柱状图.png".format(goodsSearchName),)
    shutil.move(file_name,topdeskPath)

    # 生成饼图
    age_count_list = [list(z) for z in zip(sales_count.keys(), sales_count.values())]
    pie = (
        Pie()
            .add("", age_count_list)
            .set_global_opts(title_opts=opts.TitleOpts(title="{}商品销量区间饼图".format(goodsSearchName)))
            .set_series_opts(label_opts=opts.LabelOpts(formatter="{b}: {c}"))
    )
    file_name = os.getcwd() + "/{}销量区间饼图.png".format(goodsSearchName)
    make_snapshot(snapshot,  pie.render(),"{}销量区间饼图.png".format(goodsSearchName),)
    shutil.move(file_name,topdeskPath)

def analysis_price_sales():
    """
    商品价格与销量关系分析
    :return:
    """
    # 引入全局数据
    global DF_STANDARD
    df = DF_STANDARD.copy()
    df['group'] = pd.qcut(df.price, 12)
    df.group.value_counts().reset_index()
    df_group_sales = df[['sales', 'group']].groupby('group').mean().reset_index()
    df_group_str = [str(i) for i in df_group_sales['group']]
    print(df_group_str)
    # 生成柱状图
    bar = (
        Bar()
            .add_xaxis(df_group_str)
            .add_yaxis("", list(df_group_sales['sales']), category_gap="50%")
            .set_global_opts(
            title_opts=opts.TitleOpts(title="{}价格分区与平均销量柱状图".format(goodsSearchName)),
            yaxis_opts=opts.AxisOpts(name="价格区间"),
            xaxis_opts=opts.AxisOpts(name="平均销量", axislabel_opts={"rotate": 30})
        )
    )
    file_name = os.getcwd() + "/{}价格分区与平均销量柱状图.png".format(goodsSearchName)
    make_snapshot(snapshot,  bar.render(),"{}价格分区与平均销量柱状图.png".format(goodsSearchName),)
    shutil.move(file_name,topdeskPath)




def cut_and_sort_data(listBins, listLabels, data_list) -> dict:
    """
    统计list中的元素个数，返回元素和count
    :param listBins: 数据切分区域
    :param listLabels: 切分后对应标签
    :param data_list: 数据列表形式
    :return: key为元素value为count的dict
    """
    data_labels_list = pd.cut(data_list, bins=listBins, labels=listLabels, include_lowest=True)
    # 生成一个以listLabels为顺序的字典，这样就不需要后面重新排序
    data_count = {i: 0 for i in listLabels}
    # 统计结果
    for value in data_labels_list:
        # get(value, num)函数的作用是获取字典中value对应的键值, num=0指示初始值大小。
        data_count[value] = data_count.get(value) + 1
    return data_count

def analysis_province_sales():
    """
    省份与销量的分布
    :return:
    """
    # 引入全局数据
    global DF_STANDARD

    # 1、全国商家数量分布
    province_sales = DF_STANDARD.location.value_counts()
    province_sales_list = [list(item) for item in province_sales.items()]
    print(province_sales_list)
    # 1.1 生成热力图
    province_sales_map = (
        Map()
            .add("{}商家数量全国分布图".format(goodsSearchName), province_sales_list, "china")
            .set_global_opts(
            visualmap_opts=opts.VisualMapOpts(max_=647),
        )
    )
    file_name = os.getcwd() + "/{}商家数量全国分布图.png".format(goodsSearchName)
    make_snapshot(snapshot,  province_sales_map.render(),"{}商家数量全国分布图.png".format(goodsSearchName),)
    shutil.move(file_name,topdeskPath)

    # 1.2 生成柱状图
    province_sales_bar = (
        Bar()
            .add_xaxis(province_sales.index.tolist())
            .add_yaxis("", province_sales.values.tolist(), category_gap="50%")
            .set_global_opts(
            title_opts=opts.TitleOpts(title="{}商家数量地区柱状图".format(goodsSearchName)),
            yaxis_opts=opts.AxisOpts(name="商家数量"),
            xaxis_opts=opts.AxisOpts(name="地区", axislabel_opts={"rotate": 90})
        )
    )
    file_name = os.getcwd() + "/{}商家数量地区柱状图.png".format(goodsSearchName)
    make_snapshot(snapshot,  province_sales_bar.render(),"{}商家数量地区柱状图.png".format(goodsSearchName),)
    shutil.move(file_name,topdeskPath)

    # 3、全国商家省份平均销量分布
    province_sales_mean = DF_STANDARD.pivot_table(index='location', values='sales', aggfunc=np.mean)
    # 根据平均销量排序
    province_sales_mean.sort_values('sales', inplace=True, ascending=False)
    province_sales_mean_list = [list(item) for item in
                                zip(province_sales_mean.index, np.ravel(province_sales_mean.values))]

    print(province_sales_mean_list)
    # 3.1 生成热力图
    province_sales_mean_map = (
        Map()
            .add("{}商家平均销量全国分布图".format(goodsSearchName), province_sales_mean_list, "china")
            .set_global_opts(
            visualmap_opts=opts.VisualMapOpts(max_=1536),
        )
    )
    file_name = os.getcwd() + "/{}商家平均销量全国分布图.png".format(goodsSearchName)
    make_snapshot(snapshot,  province_sales_mean_map.render(),"{}商家平均销量全国分布图.png".format(goodsSearchName),)
    shutil.move(file_name,topdeskPath)
    # 3.2 生成柱状图
    province_sales_mean_bar = (
        Bar()
            .add_xaxis(province_sales_mean.index.tolist())
            .add_yaxis("", list(map(int, np.ravel(province_sales_mean.values))), category_gap="50%")
            .set_global_opts(
            title_opts=opts.TitleOpts(title="{}商家平均销量地区柱状图".format(goodsSearchName)),
            yaxis_opts=opts.AxisOpts(name="平均销量"),
            xaxis_opts=opts.AxisOpts(name="地区", axislabel_opts={"rotate": 90})
        )
    )
    file_name = os.getcwd() + "/{}商家平均销量地区柱状图.png".format(goodsSearchName)
    make_snapshot(snapshot,  province_sales_mean_bar.render(),"{}商家平均销量地区柱状图.png".format(goodsSearchName),)
    shutil.move(file_name,topdeskPath)


if __name__ == '__main__':
    try:
        gs = GoodsSpider(goodsSearchName)
        gs.patch_spider_goods()
        # 数据清洗
        standard_data()
        # 数据分析
        # 读取标准数据
        DF_STANDARD = pd.read_excel(GOODS_STANDARD_EXCEL_PATH)
        analysis_title()
        analysis_price()
        analysis_sales()
        analysis_price_sales()
        analysis_province_sales()

    except:
        print('遭到淘宝的反爬虫测试，无法继续爬取数据，目前爬取的数据已保存，并进行分析')
        # 数据清洗
        standard_data()
        # 数据分析
        # 读取标准数据
        DF_STANDARD = pd.read_excel(GOODS_STANDARD_EXCEL_PATH)
        analysis_title()
        analysis_price()
        analysis_sales()
        analysis_price_sales()
        analysis_province_sales()



