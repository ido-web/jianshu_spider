# -*- coding: utf-8 -*-
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from jianshu_spider.items import ArticleItem


class JianshuSpider(CrawlSpider):
    '''
    简书整站爬虫
    '''
    name = 'jianshu'
    allowed_domains = ['jianshu.com']
    start_urls = ['http://jianshu.com/']

    rules = (
        Rule(LinkExtractor(allow=r'.*/p/[0-9a-z]{12}.*'), callback='parse_detail', follow=True),
    )

    def parse_detail(self, response):
        article_ele = response.xpath("//div[@class='article']")
        title = article_ele.xpath(".//h1[@class='title']/text()").get()
        avatar = article_ele.xpath(".//a[@class='avatar']/img/@src").get()
        author = article_ele.xpath(".//span[@class='name']/a/text()").get()
        pub_time = article_ele.xpath('.//span[@class="publish-time"]/text()').get()
        content = article_ele.xpath(".//div[@class='show-content']").get()
        origin_url = response.url
        url1 = origin_url.split('?')[0]
        article_id = url1.split('/')[-1]
        item = ArticleItem(title=title,
                           avatar=avatar,
                           author=author,
                           pub_time=pub_time,
                           content=content,
                           origin_url=origin_url,
                           article_id=article_id)
        return item
