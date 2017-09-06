#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/8/23 17:02
# @Author  : ywendeng
# @Description : 主要用于数据加载和转换
import numpy as np
import pandas as pd
import MySQLdb as db
import logging


class Utils(object):
    def __init__(self):
        self.position_header = ["driver_id", "city_id", "position_time", "order_create_time"]
        self.order_header = ["id", "driver_id", "start_city", "end_city", "order_create_time"]

    def load_data(self, file_name, type):
        header_list = self.position_header
        if type == 'order':
            header_list = self.order_header

        data = pd.read_csv(file_name, delimiter='\t', header=None, names=header_list)
        return data

    '''
    MySQL 数据库的连接
    '''

    def get_mysql_connect(self):
        # 获取MySql数据库连接
        con = db.connect(host='10.24.242.129', port=3306, user='algorithmadmin',
                         passwd='Ad$g32@dkneK3#', db='servicedb', charset='utf8')
        # 获取对应操作游标
        cursor = con.cursor()
        return con, cursor

    def commit_close(self, con):
        # 提交数据数据
        if con:
            con.close()
        else:
            logging.log("当前连接不存在")

    # 将mysql中的距离加载到内存中
    def query_distance(self):
        con, cursor = self.get_mysql_connect()
        sql = "select id,mileage from city_mileage"
        city_distanct = {}
        cursor.execute(sql)
        query_result = cursor.fetchall()
        for id, dist in query_result:
            city_distanct[str(id)] = dist
        self.commit_close(con)
        # 返回城市距离表
        return city_distanct

    # def get_random_distance(self):
    #     return np.random.randint(0, 1000000)


if __name__ == '__main__':
    etl = Utils()
    etl.query_distance()
    # position = etl.load_data("data_set/position/position.csv")
    # order_1 = etl.load_data("data_set/order/1-80w.csv")
    # order_2 = etl.load_data("data_set/order/80w.csv")
    # order = order_1.append(order_2)
    # order.reset_index(drop=True)
    # result = etl.find_position_exits(order, position)
    # result.reset_index(drop=True)
    # result.to_csv("data_set/output/order.csv")
