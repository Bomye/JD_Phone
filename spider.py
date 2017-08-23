#!user/bin/env python
#-*- coding:utf-8 -*-

import time
from multiprocessing.dummy import Pool as ThreadPool
import pymongo
import sys
import requests
from lxml import etree
import json
import urllib2
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# 禁用安全请求警告
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def get_response(url):
    html = requests.get(url,headers=headers, verify=False) #发送一次请求
    selector = etree.HTML(html.text)
    product_list = selector.xpath('//*[@id="J_goodsList"]/ul/li')
    for product in product_list:
        try:
            sku_id = product.xpath('@data-sku')[0]
            product_url = 'https://item.jd.com/{}.html'.format(str(sku_id))
            get_data(product_url)
        except Exception,e:
            print e


def get_data(product_url):
    '''
    获取商品详情
    :param url:
    :return:
    '''
    product_dict = {}
    html = requests.get(product_url,headers = headers, verify=False)
    seletor = etree.HTML(html.text)
    product_info = seletor.xpath('//*[@class="parameter2 p-parameter-list"]')
    for product in product_info:
        #这里用正则匹配更好
        product_number = product.xpath('li[2]/@title')[0]
        product_price = get_product_price(product_number)
        product_dict['商品名称'] = product.xpath('li[1]/@title')[0]
        product_dict['商品ID'] = product_number
        product_dict['商品毛重'] = product.xpath('li[3]/@title')[0]
        product_dict['商品产地'] = product.xpath('li[4]/@title')[0]
        product_dict['系统'] = product.xpath('li[5]/@title')[0]
        product_dict['电池容量'] = product.xpath('li[7]/@title')[0]
        product_dict['机身颜色'] = product.xpath('li[8]/@title')[0]
        product_dict['热点'] = product.xpath('li[9]/@title')[0]
        product_dict['运行内存'] = product.xpath('li[10]/@title')[0]
        product_dict['前置摄像头像素'] = product.xpath('li[11]/@title')[0]
        product_dict['后置摄像头像素'] = product.xpath('li[12]/@title')[0]
        product_dict['价格'] = product_price
        #product_dict['机身内存'] = product.xpath('li[13]/@title')[0]
        print product_dict
    save_to_mongo(product_dict)

def get_product_price(sku):
    '''
    获取价格
    :return:
    '''
    price_url = 'https://p.3.cn/prices/mgets?skuIds=J_{}'.format(str(sku))
    response = requests.get(price_url,headers=headers, verify=False).content #返回的事Json
    response_json = json.loads(response)
    for info in response_json:
        return info.get('p')


def save_to_mongo(product_list):
    '''
    保存数据
    :param list:
    :return:
    '''
    client = pymongo.MongoClient('localhost')
    db = client['product_dict'] # 数据库
    content = db['jd'] #表
    content.insert(product_list)




if __name__ == '__main__':
    headers = {
        "User - Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36"
    }
    urls = ['https://search.jd.com/Search?keyword=%E6%89%8B%E6%9C%BA&enc=utf-8&qrst=1&rt=1&stop=1&vt=2&wq=%E6%89%8B%E6%9C%BA&cid2=653&cid3=655&page={}&s=55&click=0'.format(page) for page in range(1,5,2)]
    pool = ThreadPool(2)
    start_time = time.time()
    pool.map(get_response,urls)
    pool.close()
    pool.join()
    end_time = time.time()
    print u'用时{}second'.format(str(end_time-start_time))