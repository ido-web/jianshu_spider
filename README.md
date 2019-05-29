# 某书整站爬虫
Scrapy + selenium/webdriver + 随机请求头 + IP proxy + twisted ConnectionPool + mysql 爬取某书整站爬虫 

### 环境安装
```vim
pip install requirements
```
### 数据库配置
在setting.py中进行配置。
连接数据库使用的是 **pymysql**

```python
    # database config
    # 数据库主机IP
    HOST = '127.0.0.1'
    # 数据库用户名
    USER = "root"
    # 数据库密码
    PASSWORD = "password"
    # 数据库名称
    DATABASE_NAME = 'jianshu'
```
### selenium + webdriver添加中间件 爬取网页
因为动态网站，数据通过js动态加载，或者有强大反爬虫技术
所以这里使用selenium + chromedriver（chrome浏览器） 完全模拟浏览器操作来爬取。

**tips : selenium + phantomjs也很好用**
```python
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
```


### 随机请求头设置
 http://www.useragentstring.com
 到这个网址，可以找到全部User-Agent
 
 通过中间键的方式设置User_Agent
 
 ```python
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
 ```
 ### 设置IP代理
 获取代理IP的方式:
    
   - 网络爬取，这里推荐一个IP代理池开源项目：
   https://github.com/qiyeboy/IPProxyPool
   - 花钱购买 例如：快代理、芝麻代理等
 
**在项目中，我们获取到一个代理IP一定要充分利用，这里说对的充分利用就是说，一定要等当前IP过期或被网站禁用，再去获取新的ip,特别注意异步做异步爬虫时，对多个线程或者进程，对于代理IP的管理，避免过度浪费。**

本项目中使用的是芝麻代理获取代理IP,代码如下
 ```python
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
 ```
 
  ```python
     class IPProxyModel():
         '''
         代理ip模型类
         '''
         def __init__(self,data):
             # IP
             self.ip = data['ip']
             # 端口号
             self.port = data['port']
             # 过期时间
             self.expire_time_str = data['expire_time']
             # 是否被加入了黑名单
             self.blacked = False
     
             date_str,time_str = self.expire_time_str.split(" ")
             year,month,day = date_str.split('-')
             hour,minute,second = time_str.split(":")
             # 过期时间
             self.expire_time = datetime(year=int(year),month=int(month),day=int(day),hour=int(hour),minute=int(minute),second=int(second))
     
             self.address = "https://{}:{}".format(self.ip,self.port)
     
         @property
         def is_expire(self):
             '''
             验证代理ip是否过期
             :return:
             '''
             now = datetime.now()
             if self.expire_time - now < timedelta(seconds=10):
                 return True
             else:
                 return False
  ```
  
  ### 保存数据到数据库
  本项目使用 twisted提供的数据库连接池插入数据到数据库
  使用方式：
  
  导入
```pyhton
    
     from twisted.enterprise import adbapi
     from pymysql import cursors
   ```
  配置数据库参数并且获取连接池对象：
  
  ```pyhton
      
        db_params = {
           'host': settings.HOST,
           # 'port':'3306'
           'port': 3306,
           'user': settings.USER,
           'password': settings.PASSWORD,
           'database': settings.DATABASE_NAME,
           'charset': 'utf8',
           'cursorclass': cursors.DictCursor
         }
         
         # 使用twisted提供的 ConnectionPool
         self.dbpool = adbapi.ConnectionPool('pymysql', **db_params)
   ```
   
   插入数据到数据库：
   
 ```pyhton
    defer = self.dbpool.runInteraction(self.insert_item, item)
  ```
  
  ### 启动爬虫
  运行 start.py即可启动
  
   ```pyhton
      from scrapy import cmdline
      
      # 在命令行执行 scrapy crawl jianshu 命令
      cmdline.execute('scrapy crawl jianshu'.split())
   ```