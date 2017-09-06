#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/8/10 16:04
# @Author  : ywendeng
# @Description : 城市级别的数据抽取转换和计算
import pandas as pd
import matplotlib.pyplot as plt


def city_data_etl(path, outpath, prov_list):
    fread = open(path)
    fread.readline()
    line = fread.readline()
    data = {}
    while line:
        fields = line.split(",")
        start_city = fields[1][:2] + "0000"
        # start_city = fields[0]
        if start_city in prov_list:
            user_num = int(fields[1])
            if start_city not in data: data.setdefault(start_city, 0)
            # data[start_city] += user_num
            data[start_city] += 1
        line = fread.readline()
    fread.close()
    with open(outpath, "w+") as f:
        for key, val in data.items():
            f.write(key + "," + str(val) + "\n")


if __name__ == '__main__':
    prov_list = ['510000', '420000', '320000', '440000', '370000','230000','620000','330000','410000','530000','110000']
    city_active_path = "data_set/city_active"
    city_active_oupath = "data_set/city_active_result"
    city_search_user = "data_set/city_search_user.csv"
    city_search_user_output = "data_set/city_search_user_output"
    # city_data_etl(city_active_path, city_active_oupath, prov_list)
    # city_data_etl(city_search_user, city_search_user_output, prov_list)
    city_data_etl("data_set/good_bad_cargo.csv", "data_set/cargo_user_result", prov_list)
