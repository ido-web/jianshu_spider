from datetime import datetime,timedelta

class IPProxyModel():

    def __init__(self,data):
        self.ip = data['ip']
        self.port = data['port']
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
