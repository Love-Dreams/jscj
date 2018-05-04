# coding=utf-8
import requests
import re
import json
from lxml import etree
from pymysql import *
import datetime
import time

class NewsSpider:
    def __init__(self):
        self.start_url = "https://www.jinse.com/depth"
        self.next_url_temp = "https://api.jinse.com/v4/information/list/?catelogue_key=shendu&information_id={}&limit=20&flag=down&version=9.9.9"
        self.headers= {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36"}
        self.session = requests.session()
        self.proxies = proxies = {"http":"http://121.8.98.197:80"}
    def parse_url(self,url):
        response = self.session.get(url,headers=self.headers,proxies = self.proxies)
        return response.content.decode()

    def get_first_page_content_list(self,html_str): #提取第一页的url和最后一个信息的id
        html = etree.HTML(html_str)
        div_list = html.xpath("//div[@class='ja-article-list']/div[1]")
        content_list = []
        for div in div_list:
            item = {}
            item['data_url'] = div.xpath('./ol/a/@href')
            # print(item['data_url'])
            item['data-information-id'] = div.xpath('//ol/@data-information-id')[-1]
            # print( item['data-information-id'])
            content_list.append(item)
            url_list = content_list[0]['data_url']

        # print(url_list)
        return content_list,url_list
        # return item['data-information-id'],item['data_url']

    def get_detail_page(self,html_list):
        # print(html_list)
        item = {}
        content1 = re.sub(r"\\n</ul>\\n</div>\\n|width=\"\d+\" height=\"\d+\"", "",str(re.findall(r'<span>.*?</span>(.*?)<img src="/ts.jpg">', html_list, re.DOTALL)))
        content3 = re.sub(r"<p style.*?>", "<p>", content1)
        # print(type(content1))
        content2 = re.sub(r"< img src=","<img src=",content3)
        # print(content2)
        item['text'] = content2
        html = etree.HTML(html_list)
        # print(html)
        item["title"] = html.xpath(".//div[@class='title']/h2/text()")[0]
        try:
            item["source"] = html.xpath(".//div[@class='source']/a/text()")[0]
        except Exception as e:
            item["source"] = ''
            if item["source"] == '':
                item["source"] = html.xpath(".//div[@class='source']//text()")[0]
                a = re.sub("本文来源：", "", item["source"])
                b = a.split('/')[0]
                item["source"] = b.strip()
        item["writer"] = html.xpath(".//div[@class='article-info']/a/text()")[0]
        # item["writer1"] = re.sub(r"'\\n', '\\n', '\\n'","",item["writer"])
        a = html.xpath(".//div[@class='time']/text()")[0]
        if "分钟前" in a:
            a = re.sub(r"分钟前", "", a)
            a = int(a)
            # print(a)
            pastTime = (datetime.datetime.now() - datetime.timedelta(minutes=a)).strftime(
                '%Y-%m-%d %H:%M:%S')  # 过去n分钟时间
            # print(pastTime)
            # 将其转换为时间数组
            timeArray = time.strptime(pastTime, "%Y-%m-%d %H:%M:%S")
            # 转换为时间戳
            timeStamp = int(time.mktime(timeArray))

            item["time"] = timeStamp
        elif "小时前" in a:
            a = re.sub(r"小时前", "", a)
            a = int(a)
            # print(a)
            pastTime = (datetime.datetime.now() - datetime.timedelta(hours=a)).strftime('%Y-%m-%d %H:%M:%S')  # 过去n小时时间
            # print(pastTime)
            # 将其转换为时间数组
            timeArray = time.strptime(pastTime, "%Y-%m-%d %H:%M:%S")
            # 转换为时间戳
            timeStamp = int(time.mktime(timeArray))

            item["time"] = timeStamp

            # print(pastTime)
            item["time"] = timeStamp
        elif "刚刚" in a:
            nowTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # 现在
            timeArray = time.strptime(nowTime, "%Y-%m-%d %H:%M:%S")
            # 转换为时间戳
            timeStamp = int(time.mktime(timeArray))

            item["time"] = timeStamp

        else:
            # 将其转换为时间数组
            timeArray = time.strptime(a, "%Y/%m/%d %H:%M")

            # 转换为时间戳
            timeStamp = int(time.mktime(timeArray))

            # timeStamp == 1381419600
            # print(timeStamp)
            item["time"] = timeStamp
        print(item["time"])
        try:
            item["keyword"] = html.xpath(".//div[@class='tags']/a/@title")
        except Exception as e:
            item["keyword"] = ''
        # print(item)
        # print(item["time"])
        # print(type(item["time"]))
        # print(item["keyword"])
        # print(type(item["keyword"]))
        try:
            item['thumbnail'] = html.xpath(".//div[@class='js-article']//p[contains(@style,'text-align:')]//img/@src")[0]
            s = item['thumbnail'][0:4]
            print(s)
            if s != 'http':
                u=0

            else:
                u =1
                # url = "https://img.jinse.com/708001_image1.png"
                data_size = '0kb'
                dict1 = {}
                dict1['thumb_img'] = item['thumbnail']
                dict1['thumb_size'] = data_size
                # print(dict1)
                item['thumbnail'] = json.dumps(dict1)
                item['thumbnail'] = '['+ item['thumbnail'] + ']'
            # print(item['thumbnail'])
            # print(type(json_thumbnail))
            # print(item['thumbnail'])
        except Exception as e:
            item['thumbnail'] = ''
            u = 1
        print(item['title'])
        return item,u

    def get_content_list(self,json_str): #获取第二页之后的json中的数据
        dict_ret = json.loads(json_str)
        bottom_id = dict_ret['bottom_id']
        data = dict_ret["list"]
        news_quantity = dict_ret['news']
        item = {}
        url_list = []
        for i in data:
            # item['id'] = i['id']
            item['topic_url'] = i['extra']['topic_url']
            url_list.append(item['topic_url'])
            # item['news_quantity'] = i['news']
        # print(url_list)
        return bottom_id,url_list,news_quantity

    def update(self,data):
        # 建立连接
        item = data
        item['text'] = re.sub(r"\['|'\]","",item['text'])
        # item["title"]
        # item["source"]
        # item["writer"]
        # item["time"]
        item["keyword"] = ",".join(item["keyword"])
        print(item["keyword"])
        column = "202"
        conn = connect(host="115.29.213.87",  # localhose默认本机IP,如连接他人,需输入对方ip
                       user="root",
                       password="Redstone123qwe,.",
                       database="moor",
                       port=3306,
                       charset="utf8")
        # 获取数据库操作对象
        cur = conn.cursor()
        # 编写Mysql语句
        try:
            sql = 'insert into rs_content (title,source,author,keywords,create_time,update_time,thumb,cate_id) values (%s,%s,%s,%s,%s,%s,%s,%s)'
            # 执行Mysql语句， 得到数据库变化值
            ret = cur.execute(sql, [item["title"], item["source"], item["writer"], item["keyword"], item["time"],
                                    item["time"], item['thumbnail'], column])
            id = int(cur.lastrowid)  # 最后插入行的主键ID
            print("受影响的行数为%s" % ret)
            # 判断数据库是否改变
            if ret != 0:
                conn.commit()  # 提交
            else:
                conn.rollback()  # 回滚
            sql2 = 'insert into rs_content_detail(detail) values (%s)'
            ret2 = cur.execute(sql2, [item['text']])
            detail_id = int(cur.lastrowid)  # 最后插入行的主键ID
            print(detail_id)
            print("受影响的行数为%s" % ret2)
            # 判断数据库是否改变
            if ret2 != 0:
                conn.commit()  # 提交
            else:
                conn.rollback()  # 回滚

            sql3 = 'update rs_content set detail_id = %s where id = %s'
            # 执行Mysql语句， 得到数据库变化值
            ret = cur.execute(sql3, [detail_id, id])
            # id = int(cur.lastrowid)  # 最后插入行的主键ID
            print("受影响的行数为%s" % ret)
            # 判断数据库是否改变
            if ret != 0:
                conn.commit()  # 提交
            else:
                conn.rollback()  # 回滚
                # 关闭操作对象
            cur.close()
            # 关闭连接对象
            conn.close()
            x = 0
        except Exception as e:
            cur.close()
            # 关闭连接对象
            conn.close()
            x = 1
            print("【重复数据：数据库以存有此数据，以过滤】")
        return x

    def update1(self):
        # 建立连接
        column = "202"
        conn2 = connect(host="115.29.213.87",  # localhose默认本机IP,如连接他人,需输入对方ip
                       user="root",
                       password="Redstone123qwe,.",
                       database="moor",
                       port=3306,
                       charset="utf8")
        # 连接标记库
        conn = connect(host="115.29.213.87",  # localhose默认本机IP,如连接他人,需输入对方ip
                       user="root",
                       password="Redstone123qwe,.",
                       database="spider_mark",
                       port=3306,
                       charset="utf8")

        # 获取数据库操作对象
        cur = conn.cursor()
        cur2 = conn2.cursor()
        # 编写Mysql语句
        # try:
        sql2 = 'select title,create_time from rs_content order by create_time desc LIMIT 1'
        ret2 = cur2.execute(sql2)
        title, create_time = cur2.fetchone()
        print("受影响的行数为%s" % ret2)
        # 判断数据库是否改变
        # if ret2 != 0:
        #     conn.commit()  # 提交
        # else:
        #     conn.rollback()  # 回滚

        sql1 = 'insert into jscj_sd_bj (title,create_time) values (%s,%s)'
        ret1 = cur.execute(sql1, [title, create_time])
        print("777777777777777777777777777777")
        # 执行Mysql语句， 得到数据库变化值
        print("受影响的行数为%s" % ret1)
        # 判断数据库是否改变
        if ret1 != 0:
            conn.commit()  # 提交
        else:
            conn.rollback()  # 回滚

        # 关闭操作对象

        cur2.close()
        # 关闭连接对象
        conn2.close()

            # 关闭操作对象

        cur.close()
        # 关闭连接对象
        conn.close()
        # except Exception as e:
        #     print("【重复数据：数据库以存有此数据，以过滤】")

    def run(self): #实现主要逻辑
        x = 0
        #1.start_url
        #2.发送请求，获取响应
        html_str = self.parse_url(self.start_url)
        #3.提取数据,提取第一页的url和最后一个信息的id
        content_list,url_list= self.get_first_page_content_list(html_str)
        # print(url_list)
        # print("***********************")
        for url in url_list:
            html_str1 = self.parse_url(url)
            # 提取详情页数据
            data,u = self.get_detail_page(html_str1)
            if u == 0:
                print("数据缩略图错误，已删除")
                x = 1
            else:
                # 4.保存
                x = self.update(data)

        if x !=1:
            # while has_more:
                #5.构造下一页的url地址，
            next_url = self.next_url_temp.format(content_list[0]['data-information-id'])
            # print(next_url)
            #6.发送请求，获取响应
            json_str = self.parse_url(next_url)
            # 提取第二页的json数据
            bottom_id, xq_list, news_quantity = self.get_content_list(json_str)
            for url in xq_list:

                # if url == "http://www.jinse.com/news/bitcoin/178023.html":
                #     continue
                # else:
                    # try:
                html_str2 =self.parse_url(url)
                # 详情页提取数据
                data,u = self.get_detail_page(html_str2)
                if u == 0:
                    print("数据缩略图错误，已删除")
                    x = 1
                else:
                        # 4.保存
                    x = self.update(data)
                # except Exception as e:
                #     continue
            if x !=1:
                while news_quantity != 0:
                        # 构造第三页
                    next_url = self.next_url_temp.format(bottom_id)
                    print(next_url)
                    # 获取响应
                    json_str = self.parse_url(next_url)
                    # 提取第三页的json数据
                    bottom_id, xq_list, news_quantity = self.get_content_list(json_str)
                    for url in xq_list:

                        # if url != "http://www.jinse.com/news/bitcoin/178023.html":
                        #     continue
                        #
                        # else:
                            # try:
                        html_str2 =self.parse_url(url)
                        # 详情页提取数据
                        data,u = self.get_detail_page(html_str2)
                        print(data)
                        if u==0:
                            print("数据缩略图错误，已删除")
                            x = 1
                        else:
                            # 4.保存
                            x = self.update(data)
                        # except Exception as e:
                        #     continue
                    if x ==1:
                        break
        print("已完成")
if __name__ == '__main__':
    news = NewsSpider()
    news.run()