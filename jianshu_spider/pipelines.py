# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import pymysql
from twisted.enterprise import adbapi
from pymysql import cursors
from . import settings

class JianshuSpiderPipeline():
    def __init__(self):
        db_params = {
            'host': settings.HOST,
            # 'port':'3306'
            'port': 3306,
            'user': settings.USER,
            'password': settings.PASSWORD,
            'database': settings.DATABASE_NAME,
            'charset': 'utf8'
        }

        self.conn = pymysql.connect(**db_params)
        self.cursor = self.conn.cursor()
        self._sql = None

    def process_item(self, item, spider):
        self.cursor.execute(self.sql, (item['title'], item['avatar'], item['author'], item['pub_time'],
                                       item['origin_url'], item['article_id'], item['content'],))
        self.conn.commit()
        return item

    def spider_close(self):
        '''
        爬虫关闭执行的操作
        :return:
        '''
        pass

    @property
    def sql(self):
        '''
        创建sql语句
        :return: 插入数据的sql语句
        '''
        if not self._sql:
            self._sql = '''
                insert into article(id,title,avatar,author,pub_time,origin_url,article_id,
                content) values (null,%s,%s,%s,%s,%s,%s,%s)
            '''
        return self._sql

class JianshuTwistedPipeline():
    ''''
    '''
    def __init__(self):
        db_params = {
            'host': '127.0.0.1',
            'port': 3306,
            'user': 'root',
            'password': 'password',
            'database': 'jiashu',
            'charset': 'utf8',
            'cursorclass': cursors.DictCursor
        }

        # 使用twisted提供的 ConnectionPool
        self.dbpool = adbapi.ConnectionPool('pymysql', **db_params)
        self._sql = None
    #
    @property
    def sql(self):
        if not self._sql:
            self._sql = "insert into article(id,title,avatar,author,pub_time,origin_url,article_id,content) values (null,%s,%s,%s,%s,%s,%s,%s)"
        return self._sql

    def process_item(self, item, spider):
        defer = self.dbpool.runInteraction(self.insert_item, item)
        defer.addErrback(self.handle_error,item,spider)


    def insert_item(self, cursors, item):
        cursors.execute(self.sql,(item['title'], item['avatar'], item['author'], item['pub_time'],
                                  item['origin_url'], item['article_id'], item['content']))

    def handle_error(self,error,item,spider):
        '''
        处理错误
        :param error:
        :param item:
        :param spider:
        :return:
        '''
        print("*"*10 + 'error' + '*'*10)
        print(error)
        print("*"*10 + 'error' + '*'*10)


