#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File: mysql.py
Desc: mysql操作类
Author:yanjingang(yanjingang@baidu.com)
"""

import os
import sys
import time
import logging
import pymysql
from pymysql import cursors
from util import Util
from mysqlgenerator import MySqlGenerator


class Mysql(object):
    """
        Mysql操作类
    """

    def __init__(self, host, port, user, password, db,
                 charset="utf8", debug=0, autocommit=True):
        """
        初始化配置

        :param host: hostname
        :param port: 端口
        :param user: 用户名
        :param password: 密码
        :param db: 库名
        :param charset: 字符集（默认utf8）
        :param debug: 是否打印sql
        :param autocommit: 是否自动提交（默认True）
        :returns:
        """
        self.host = host
        self.port = int(port)
        self.user = user
        self.password = password
        self.db = db
        self.debug_level = debug
        self.conn = None
        self.charset = charset
        self.autocommit = autocommit
        self.sqlGen = MySqlGenerator()

    def __del__(self):
        """__del__"""
        self.disconnect()

    # def connect(self):
    #     """connect"""
    #     if not self.conn or self.conn.open is False:
    #         self.conn = pymysql.connect(host=self.host, port=self.port, user=self.user,
    #                                     password=self.password, db=self.db, charset=self.charset,
    #                                     cursorclass=cursors.DictCursor, autocommit=self.autocommit)

    def connect(self):
        """connect"""
        if not self.conn or self.conn.open is False:    # 未连接
            self._connect()
        else:   # 已连接，校验链接的可用性
            try:
                self.conn.ping()  
            except:     #如果连接不可用将会产生异常，需要自动重连
                self._connect()
            
    def _connect(self):
        """_connect"""
        self.conn = pymysql.connect(host=self.host, port=self.port, user=self.user,
                                    password=self.password, db=self.db, charset=self.charset,
                                    cursorclass=cursors.DictCursor, autocommit=self.autocommit)

    def begin(self):
        """begin"""
        self.conn.begin()

    def commit(self):
        """commit"""
        self.conn.commit()

    def rollback(self):
        """rollback"""
        self.conn.rollback()

    def disconnect(self):
        """disconnect"""
        if self.conn and self.conn.open is True:
            self.conn.close()

    def insert(self, table, values):
        """
        插入数据

        :param table: 表名
        :param values: dict键值对
        :returns: 数据id
        """
        sql = self.sqlGen.insert(table=table, values=values)
        try:
            self.connect()
            cursor = self.conn.cursor()
            self.debug(sql)
            ret = cursor.execute(sql)
            # print(ret)
            lastrowid = cursor.lastrowid
            # self.conn.commit()
            cursor.close()
            # self.conn.close()
            return lastrowid
        except:
            logging.error("{}\t{}".format(sql, Util.get_trace()))
            return 0

    def update(self, table, where, values):
        """
        更新数据

        :param table: 表名
        :param where: where条件键值对
        :param values: 要更新的键值对
        :returns: ret影响行数
        """
        if not isinstance(where, dict):
            logging.error("where must be dict")
        self.connect()
        cursor = self.conn.cursor()
        sql = self.sqlGen.update(table=table, where=where, values=values)
        self.debug(sql)
        ret = cursor.execute(sql)
        # print(ret)
        # self.conn.commit()
        cursor.close()
        # self.conn.close()
        return ret

    def query(self, table, where=None, select='*', groupby='', orderby='', limit=1000):
        """
        查询数据

        :param table: 表名
        :param where: where条件键值对
        :param select: 查询字段
        :param groupby: 分组
        :param orderby: 排序
        :param limit: 限定返回条数(默认1000)
        :returns: 结果集list
        """
        res = []
        self.connect()
        cursor = self.conn.cursor()
        where = where if where is not None else {}
        sql = self.sqlGen.query(table=table, select=select, where=where, groupby=groupby, orderby=orderby, limit=limit)
        self.debug(sql)
        cursor.execute(sql)
        for data in cursor.fetchall():
            res.append(data)
        cursor.close()
        # self.conn.close()
        return res

    def count(self, table, where=None):
        """
        查询记录条数

        :param table: 表名
        :param where: where条件键值对
        :returns: 记录条数
        """
        res = []
        self.connect()
        cursor = self.conn.cursor()
        where = where if where is not None else {}
        sql = self.sqlGen.query(table=table, select='count(*) as count', where=where)
        self.debug(sql)
        cursor.execute(sql)
        for data in cursor.fetchall():
            res.append(data)
        cursor.close()
        # self.conn.close()
        if len(res) > 0:
            return int(res[0]['count'])
        return 0

    def delete(self, table, where):
        """
        删除数据

        :param table: 表名
        :param where: where条件键值对
        :returns: ret影响行数
        """
        self.connect()
        cursor = self.conn.cursor()
        sql = self.sqlGen.delete(table=table, where=where)
        self.debug(sql)
        ret = cursor.execute(sql)
        # print(ret)
        # self.conn.commit()
        cursor.close()
        # self.conn.close()
        return ret

    def execute(self, sql):
        """
        复杂sql执行（慎用-注意性能）

        :param sql: 特殊sql语句
        :returns: 查询返回结果集；增删改返回影响行数
        """
        sql = sql.strip()
        qtype = sql.split()[0].upper()

        res = []
        self.connect()
        cursor = self.conn.cursor()
        self.debug(sql)
        ret = cursor.execute(sql)
        # print(ret)
        if qtype == 'SELECT':
            for data in cursor.fetchall():
                res.append(data)
        else:
            res = ret
            # self.conn.commit()
        cursor.close()
        # self.conn.close()
        return res

    def debug(self, sql):
        """debug"""
        logging.info('SQL: {};'.format(sql))
        if self.debug_level:
            print('SQL: {};'.format(sql))
