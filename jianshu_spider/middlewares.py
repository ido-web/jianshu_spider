# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/spider-middleware.html

import random
from selenium import webdriver
from scrapy.http.response.html import HtmlResponse
from twisted.internet.defer import DeferredLock
import requests
import json
from .model import IPProxyModel


class ChromeDriverDownloaderMiddleware(object):
    '''
    使用selenium + chromedriver爬取网页
    '''
    def __init__(self):
        driver_path = r'D:\python\chromedriver\chromedriver.exe'
        self.driver = webdriver.Chrome(executable_path=driver_path)
    #
    def process_request(self,request,spider):
        self.driver.get(request.url)
        source = self.driver.page_source
        response = HtmlResponse(self.driver.current_url,body=source,request=request)
        return response
    def process_response(self,request,response,spider):
        pass

class UserAgentRandomDownloaderMiddleware(object):
    '''
    设置随机请头
    '''
    USER_AGENT = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML like Gecko) Chrome/51.0.2704.79 Safari/537.36 Edge/14.14931',
        'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:64.0) Gecko/20100101 Firefox/64.0',
        'Galaxy/1.0 [en] (Mac OS X 10.5.6; U; en)',
        'Mozilla/5.0 (compatible, MSIE 11, Windows NT 6.3; Trident/7.0; rv:11.0) like Gecko'
    ]

    def process_request(self, request, spider):
        request.headers['User-Agent'] = random.choice(self.USER_AGENT)


class IPProxyDownloaderMiddleware(object):
    '''
    IP代理 ，
    '''
    # 获取代理ip信息地址 例如芝麻代理、快代理等
    IP_URL = r'http://xxxxxx.com/getip?xxxxxxxxxx'

    def __init__(self):
        # super(IPProxyDownloaderMiddleware, self).__init__(self)
        super(IPProxyDownloaderMiddleware, self).__init__()

        self.current_proxy = None
        self.lock = DeferredLock()

    def process_request(self, request, spider):
        if 'proxy' not in request.meta or self.current_proxy.is_expire:
            self.updateProxy()

        request.meta['proxy'] = self.current_proxy.address

    def process_response(self, request, response, spider):
        if response.status != 200:
            # 如果来到这里，这个请求相当于被识别为爬虫了
            # 所以这个请求被废掉了
            # 如果不返回request,那么这个请求就是没有获取到数据
            # 返回了request，那么这个这个请求会被重新添加到调速器
            if not self.current_proxy.blacked:
                self.current_proxy.blacked = True
                print("被拉黑了")
            self.updateProxy()
            return request
        # 正常的情况下，返回response
        return response

    def updateProxy(self):
        '''
        获取新的代理ip
        :return:
        '''
        # 因为是异步请求，为了不同时向芝麻代理发送过多的请求这里在获取代理IP
        # 的时候，需要加锁
        self.lock.acquire()
        if not self.current_proxy or self.current_proxy.is_expire or self.current_proxy.blacked:
            response = requests.get(self.IP_URL)
            text = response.text

            # 返回值 {"code":0,"success":true,"msg":"0","data":[{"ip":"49.70.152.188","port":4207,"expire_time":"2019-05-28 18:53:15"}]}
            jsonString = json.loads(text)

            data = jsonString['data']
            if len(data) > 0:
                proxyModel = IPProxyModel(data=data[0])
                self.current_proxy = proxyModel
        self.lock.release()
