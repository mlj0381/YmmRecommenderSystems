#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/11/13 10:31
# @Author  : ywendeng
# @Description : 司机的路径行为分析
import numpy as np
import pandas as pd
from datetime import datetime
import geohash
import time


def load_data(file_name):
    data = pd.read_csv(file_name, delimiter=',',
                       usecols=["user_id", "move_days", "lon", "lat", "lon_lat_create_time", "day"],
                       dtype={"lon": np.str, "lat": np.str, "day": np.str})
    return data


# 对应用户的行为数据进行处理
def get_driver_action(data):
    driver_action = {}
    for i in range(np.shape(data)[0]):
        key = str(data.ix[i, "user_id"]) + str(data.ix[i, "move_days"]) + data.ix[i, "day"]
        if key not in driver_action.keys():
            driver_action.setdefault(key, [])
        position = data.ix[i, "lon"] + "," + data.ix[i, "lat"]
        create_time = data.ix[i, "lon_lat_create_time"]
        driver_action.get(key).append((create_time, position))
    # 对列表中的数据进行排序
    for key in driver_action:
        driver_action.get(key).sort(key=lambda x: x[0])
    return driver_action


# 去除司机不移动的位置数据
def filter_static_position(driver_action):
    for key in driver_action:
        del_index = []
        position = []
        for i in range(len(driver_action[key]) - 1):
            # 根据经纬度地址判断位置是否移动
            lon, lat = driver_action[key][i][1].split(",")
            lon_lat_first = geohash.encode(float(lon), float(lat), 5)
            lon, lat = driver_action[key][i + 1][1].split(",")
            lon_lat_second = geohash.encode(float(lon), float(lat), 5)
            # 如果两个位置相同则将司机位置
            if lon_lat_first == lon_lat_second:
                del_index.append(i)
        # 删除list中冗余的元素位置
        for i in range(len(driver_action[key])):
            if i not in del_index:
                position.append(driver_action[key][i])

        driver_action[key] = position


# 计算司机每天的活跃时间段
def get_active_time_interval(filter_action):
    diff_hours = {}
    format = '%Y-%m-%d %H:%M:%S'
    for key in filter_action:
        t1_str = time.localtime(filter_action.get(key)[0][0] / 1000)
        t2_str = time.localtime(filter_action.get(key)[len(filter_action.get(key)) - 1][0] / 1000)
        t1_format = datetime.strptime(time.strftime(format, t1_str), format)
        t2_format = datetime.strptime(time.strftime(format, t2_str), format)
        diff_hour = (t2_format - t1_format).seconds / 3600
        diff_hours[key] = diff_hour
    return diff_hours


if __name__ == '__main__':
    data = load_data("data_set/road.csv")
    actions = get_driver_action(data)
    # 去除每天中司机的静止位置数据
    filter_static_position(actions)
    # 计算每个司机每天的活跃时间
    diff_hours = get_active_time_interval(actions)
