

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File: utils.py
Desc: 常用通用基础函数
Date: 2019/2/21 23:34
"""
import os
import sys
import time
import json
import argparse
import hashlib
import logging
import logging.config
import traceback
import smtplib
import requests
import tempfile
import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class Util(object):
    """
    通用基础函数
    """

    @staticmethod
    def init_logging(log_file="sys", log_path='/tmp', log_level=logging.DEBUG):
        """初始化默认日志参数"""
        Util.mkdir(log_path + '/log')
        logging.basicConfig(level=log_level,
                            format='[%(levelname)s]\t%(asctime)s:%(relativeCreated)d\t%(filename)s:%(lineno)d\t%(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S',
                            filename=log_path + "/log/" + log_file + "." + time.strftime('%Y%m%d%H', time.localtime()) + ".log",
                            filemode='a')
        logging.info("__init_logging__")


    @staticmethod
    def get_trace():
        """获得异常栈内容"""
        try:
            errmsg = "Traceback (most recent call last):\n "
            exc_type, exc_value, exc_tb = sys.exc_info()
            for filename, linenum, funcname, source in traceback.extract_tb(exc_tb):
                errmsg += "  File \"%-23s\", line %s, in %s() \n\t  %s \n" % (filename, linenum, funcname, source)
            errmsg += str(exc_type.__name__) + ": " + str(exc_value)
            # traceback.print_exc()
        except:
            traceback.print_exc()
            errmsg = ''
        return errmsg


    @staticmethod
    def mkdir(path):
        """检查并创建目录"""
        if not os.path.exists(path):
            os.makedirs(path)


    @staticmethod
    def rmdir(path, skips=None):
        """删除目录"""
        # print(path)
        if not os.path.exists(path):
            return
        if os.path.isfile(path):  # 文件
            if skips is None or path not in skips:
                # os.unlink(path)
                os.remove(path)
        elif os.path.isdir(path):  # 目录
            '''for file in os.listdir(path):
                # print(path +'/'+ file)
                rmdir(path + '/' + file, skips=skips)'''
            if skips is None or path not in skips:
                # os.rmdir(path)
                shutil.rmtree(path)

    @staticmethod
    def rm(filename):
        """删除文件"""
        # print(filename)
        if os.path.exists(filename):
            # os.unlink(filename)
            os.remove(filename)


    @staticmethod
    def cp(source_file, target_file, remove=False):
        """复制文件"""
        # cp file
        if not os.path.exists(source_file):
            return False
        if not os.path.exists(target_file) or (os.path.exists(target_file) and os.path.getsize(target_file) != os.path.getsize(source_file)):
            #open(target_file, "wb").write(open(source_file, "rb").read())
            try:
                shutil.copyfile(source_file, target_file)
            except:
                return False
        # rm source
        if remove is True:
            if os.path.exists(target_file) and os.path.getsize(target_file) == os.path.getsize(source_file):  # 确保目标文件与源文件完全一致才能删源文件
                #ret = os.unlink(source_file)
                os.remove(source_file)
                return True
            else:
                return False
        return True


    @staticmethod
    def mv(source_file, target_file):
        """移动文件"""
        return cp(source_file, target_file, remove=True)


    @staticmethod
    def get_ext(filename):
        """获得文件的扩展名"""
        return os.path.splitext(filename)[1]


    @staticmethod
    def get_today():
        """获得今天日期"""
        return time.strftime("%Y-%m-%d", time.localtime())


    @staticmethod
    def get_date(timestamp, format='%Y-%m-%d %H:%M:%S'):
        """返回时间戳对应的格式化日期格式"""
        x = time.localtime(float(timestamp))
        return time.strftime(format, x)


    @staticmethod
    def get_nday(n=0, day=None, format='%Y-%m-%d'):
        """
        获得指定日期前后第n天是哪天
        :param n: 前后n天（0表示当天，-1表示前一天，1表示后一天）
        :param date: 日期字符串：2019-06-25（默认当前日期）
        :returns: 
        """
        if day is None:
            day = Util.get_today()

        date = Util.get_datetime(day)
        if date is None:
            return ''

        #print(y, m, d)
        return (date + datetime.timedelta(days=n)).strftime(format)


    @staticmethod
    def get_datetime(date_str):
        """
        获得日期字符串对应的datetime对象
        :param date_str: 日期字符串：2019-06-25（默认当前日期）
        :returns: datetime
        """
        y, m, d = 0, 0, 0
        if date_str.count('-') > 0:
            y, m, d = date_str.split('-')
        elif date_str.count('/') > 0:
            y, m, d = date_str.split('/')
        elif date_str.count('_') > 0:
            y, m, d = date_str.split('_')
        elif len(date_str) == 8:
            y = date_str[:4]
            m = date_str[4:6]
            d = date_str[6:]
        elif len(date_str) == 6:
            y = '20' + date_str[:2]
            m = date_str[2:4]
            d = date_str[4:]
        if y == 0:
            return None
        return datetime.datetime(int(y), int(m), int(d))


    @staticmethod
    def get_days(date1, date2=None):
        """
        获得两个日期相差几天
        :param date1: 起始日期
        :param date2: 截止日期（默认当天）
        :returns: n 相差天数
        """
        if date2 is None:
            date2 = Util.get_today()

        t1 = Util.get_datetime(date1)
        t2 = Util.get_datetime(date2)
        return (t1 - t2).days


    @staticmethod
    def md5(string):
        """
        生成md5
        :param string: 字符串
        :returns: 字符串对应的md5值
        """
        if isinstance(string, list):
            string = copy.deepcopy(string)
            for i in range(len(string)):
                string[i] = Util.md5(string[i])
                if string[i] == '':
                    return ''
                    # print string
        elif isinstance(string, (str, float, int)):
            try:
                string = str(string)
                string = hashlib.md5(string.encode(encoding='UTF-8')).hexdigest()
            except:
                logging.error('md5 fail! [' + string + ']\n' + Util.get_trace())
                return ''
        return string


    @staticmethod
    def send_mail(subject, body, attach_list, to, user, sender,
                password, smtp_server, smtp_port):
        """
        发送邮件
        :param subject: 邮件标题
        :param body: 邮件正文
        :param attach_list: 附件
        :param to: 收件人
        :param user: 发件人
        :param sender: 发件人信息
        :param password: 密码
        :param smtp_server: smtp 服务器
        :param smtp_port: smtp 端口号
        :returns: True: 发送成功; False: 发送失败
        """
        txt = MIMEText(body.encode('utf-8'), 'html', 'utf-8')
        msg = MIMEMultipart()
        msg.attach(txt)

        for attach in attach_list:
            try:
                att = MIMEText(open(attach, 'rb').read(), 'base64', 'utf-8')
                filename = os.path.basename(attach)
                att["Content-Type"] = 'application/octet-stream'
                att["Content-Disposition"] = 'attachment; filename="%s"' % filename
                msg.attach(att)
            except Exception:
                logging.error(u'附件 %s 发送失败！' % attach)
                continue

        msg['from'] = sender
        msg['to'] = to
        msg['subject'] = subject

        try:
            session = smtplib.SMTP()
            session.connect(smtp_server, smtp_port)
            session.starttls()
            session.login(user, password)
            session.sendmail(sender, to, msg.as_string())
            session.close()
            return True
        except Exception as e:
            logging.error(e)
            return False

    @staticmethod
    def list_path(path, full_path=False, filter=""):
        """
        获取目录下的目录和文件列表
        """
        dirs, files = [], []
        
        res = os.listdir(path)
        res.sort()
        for name in res:
            if filter != "" and name.count(filter) == 0:
                continue
            full_name = "{}/{}".format(path, name)
            # print(full_name)
            if os.path.isfile(full_name):
                if full_path:
                    files.append(full_name)
                else:
                    files.append(name)
            else:
                if full_path:
                    dirs.append(full_name)
                else:
                    dirs.append(name)
        return dirs, files

    @staticmethod
    def get_file_content(filename):
        """
        读取文件内容并返回
        :param filename: 文件路径
        :returns: 文件内容
        :raises IOError: 读取失败则抛出 IOError
        """
        with open(filename, 'rb') as fp:
            return fp.read()

    @staticmethod
    def write_file_content(filename, data):
        """
        写文件内容
        :param filename: 文件路径
        :data: 文件内容
        :returns: 是否成功
        :raises IOError: 读取失败则抛出 IOError
        """
        with open(filename, 'w') as fp:
            return fp.write(data)


    @staticmethod
    def write_temp_file(data, suffix):
        """ 
        写入临时文件
        :param data: 二进制数据
        :param suffix: 后缀名
        :returns: 文件保存后的路径
        """
        filename = ''
        mode = 'w+b'
        if type(data) is str:
            mode = 'w'
        with tempfile.NamedTemporaryFile(mode=mode, suffix=suffix, delete=False) as f:
            f.write(data)
            filename = f.name
        return filename


    @staticmethod
    def cache_file(filename, cache_key, cache_path):
        """
        缓存文件
        :param filename: 要cache的文件名
        :param cache_path: cache保存目录
        :param cache_key: cache唯一key
        """
        #_, ext = os.path.splitext(filename)
        return Util.cp(filename, os.path.join(cache_path, Util.md5(cache_key)))


    @staticmethod
    def get_cache_file(cache_key, cache_path):
        """
        获得缓存文件
        :param filename: 要cache的文件名
        :param cache_path: cache保存目录
        :param cache_key: cache唯一key
        """
        cache_file = os.path.join(cache_path, Util.md5(cache_key))
        if os.path.exists(cache_file):
            return cache_file
        return None


    @staticmethod
    def full2half(s):
        """字符串全角转半角"""
        res = ""
        for uchar in s:
            inside_code = ord(uchar)
            if inside_code == 12288:  # 全角空格直接转换
                res += chr(32)
            elif (inside_code >= 65281 and inside_code <= 65374):  # 全角字符（除空格）根据关系转化
                res += chr(inside_code - 65248)
            else:
                res += uchar.replace('。', '.').replace('《', '<').replace('》', '>').replace('「', '[').replace('」', ']')
        return res


    @staticmethod
    def clear_punctuation(s, split=''):
        """清理字符串中的标点符号"""
        s = full2half(s)
        return s.translate(str.maketrans('', split, string.punctuation))


    @staticmethod
    def base64_encode(s):
        """加密字符串为base64"""
        s = base64.b64encode(s.encode('utf-8'))
        return str(s, 'utf-8')


    @staticmethod
    def base64_decode(bs):
        """还原base64为原字符串"""
        s = base64.b64decode(bs)
        return str(s, 'utf-8')


    @staticmethod
    def get_args(*args):
        """
        获得命令行传入的参数
        :param args: 参数项声明(例如传入'-n=100,--num,返回数量'，即表示注册-n参数，默认值为"100"[可选]，返回参数名为"num"[可选]，help参数说明文本为"返回数量"[可选]。可传入多个参数声明。)
        :returns: args 获得-n参数值：args.num
        """
        # print(args)
        # 设置参数项
        parser = argparse.ArgumentParser()
        for arg in args:
            arg = arg.split(',')
            arg_default = arg[0].split('=')
            # 参数名
            name = arg_default[0]
            if name.strip() == '':
                continue
            # 未传入时的默认值
            default = arg_default[1] if len(arg_default) > 1 else ''
            # 长参数
            long_name = arg[1] if len(arg) > 1 else '-' + name
            # 参数说明
            help = arg[2] if len(arg) > 2 else ''
            # 注册参数
            parser.add_argument(name, long_name, type=str, default=default, help=help)
        # 返回参数值
        return parser.parse_args()


    @staticmethod
    def get_redirect_url(url):
        """
        获得跳转后的url
        :param url: 源ur
        :returns: url 301/302跳转后的url
        """
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Charset': 'UTF-8',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.146 Safari/537.36',
        }
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            url = res.url
        return url


    @staticmethod
    def download(down_url, save_file):
        """
        下载文件
        :param down_url: 要下载的url
        :param save_file: 保存文件
        :returns: boolean 下载是否成功
        """
        res = requests.get(down_url)
        if res.status_code != 200:
            return False
        # 保存到指定位置
        with open(save_file, "wb") as f:
            f.write(res.content)
        return True


if __name__ == '__main__':
    """函数测试"""

    # log
    Util.init_logging(log_file='test')

    # args  python utils.py -q hello -n 20
    args = Util.get_args('-q', '-t,--type,类型', '-n=100,--num,返回数量')
    print(args)
    print(args.q)
    print(args.num)
    print(args.type)

    # test
    print(Util.md5('B000000115915'))
    print(Util.get_date(1548124450.6668496))
    print(Util.get_nday(-1), Util.get_nday(1), Util.get_nday(30, '2019-2-9'), Util.get_nday(day='20190709'), Util.get_nday(-7, day='191021'))
    print(Util.get_days('2019-08-23', '2019-08-22'), Util.get_days('20190505'), Util.get_days(Util.get_nday(-106)))

    # file
    print(Util.list_path('../log/', filter='apimarsgpt.'))
    filename = '/tmp/test.conf'
    print("cp: {} {}".format(Util.cp(filename, filename + ".bak"), filename + ".bak"))
    print("get_file_content: {}".format(Util.get_file_content(filename)))
    print("write_temp_file: {}".format(Util.write_temp_file('aaa', '.txt')))
    print("cache_file: {}".format(Util.cache_file(filename, 'kkk', '/tmp/')))
    print("get_cache_file: {}".format(Util.get_cache_file('kkk', '/tmp/')))

    # download
    down_url = Util.get_redirect_url('http://music.163.com/song/media/outer/url?id=1359595520.mp3')
    print(down_url)
    save_file = '/tmp/1359595520.mp3'
    print(save_file)
    print(Util.download(down_url, save_file))
