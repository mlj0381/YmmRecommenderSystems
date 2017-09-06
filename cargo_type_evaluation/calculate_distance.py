#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/8/11 10:39
# @Author  : ywendeng
# @Description : 计算两个城市之间的距离
import pandas as pd
import numpy as np
from datetime import datetime


def load_data(distance_path, cargo_path, prov_list, end_time):
    # 距离文件
    dist_read = open(distance_path)
    line = dist_read.readline()
    dist_data = []
    while line:
        fields = line.split("\001")
        id = fields[0]
        distance = fields[3]
        dist_data.append([id, distance])
        line = dist_read.readline()
    dist_read.close()
    # 货源文件
    cargo_read = open(cargo_path)
    cargo_data = []
    cargo_read.readline()
    cargo_line = cargo_read.readline()
    while cargo_line:
        deline_end_time = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
        fields = cargo_line.split(",")
        cargo_id = fields[0]
        start = fields[1]
        start_prov = fields[3]
        end_prov = fields[5]
        show_end_time = fields[-2][:-2]
        fact_end_time = datetime.strptime(show_end_time, "%Y-%m-%d %H:%M:%S")
        # 计算货源是否展现时间结束
        cargo_line=cargo_read.readline()
        if start_prov in prov_list and fact_end_time <= deline_end_time:
            cargo_data.append([cargo_id, str(start + end_prov)])

    cargo_read.close()
    return dist_data, cargo_data


def calculate_distance(dist_set, cargo_set,output_path):
    dist = pd.DataFrame(dist_set, columns=["id", "distance"], dtype=str)
    cargo = pd.DataFrame(cargo_set, columns=['cargoid', "id"], dtype=str)
    distance_result=pd.merge(cargo, dist, on='id')

    print distance_result.head()
    distance_result.to_csv(output_path)


if __name__ == '__main__':
    distance_path = "data_set/all_distance"
    cargo_path = "data_set/good_bad_cargo.csv"
    output="data_set/distance_result_2.csv"
    prov_list = ['510000', '420000', '320000','230000',  '310000'
                 ]
    deline_time = "2017-08-01 00:00:00"
    dist, cargo = load_data(distance_path, cargo_path, prov_list, deline_time)
    print "数据清洗完成"
    calculate_distance(dist,cargo,output)
