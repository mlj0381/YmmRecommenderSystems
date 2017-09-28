#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/9/19 15:58
# @Author  : ywendeng
# @Description : 根据司机的定位地址来进行聚类
import pandas as pd
import numpy as np
import math
from geohash import *
import json
import random


def load_data(file_name):
    data = pd.read_csv(file_name, delimiter='\001', header=None,
                       usecols=[0, 1, 2, 3],
                       names=["user_id", "lon", "lat", "city_id"],
                       dtype={"user_id": str})
    return data


# def load_data(file_name):
#     data = pd.read_csv(file_name, delimiter=',',
#                        usecols=["user_id", "lon", "lat", "city_id"],
#                        dtype={"user_id": str})
#     return data


# 将司机静止时出现的多余的定位地址去除
def filter_repetition_logs(data):
    recorde = []
    for i in range(np.shape(data)[0]):
        user_id = data.ix[i, "user_id"]
        geohash_code = data.ix[i, "geohash_code"]
        key = user_id + geohash_code
        if key not in recorde:
            # 如果司机的位置不存在重复的情况则将其加入到列表中
            recorde.append(key)
        else:
            data.drop(i)
    data = data.reset_index(drop=True)
    return data[["lon", "lat", "geohash_code"]]


# 使用geohash 算法将经纬度编码转换
def transfrom_position(data):
    # 为dataFrame新增加一列
    data["geohash_code"] = [""] * np.shape(data)[0]
    for i in range(np.shape(data)[0]):
        if i % 1000 == 0:
            print "geohash transform lon lat data ：%d" % i
        data.ix[i, "geohash_code"] = encode(data.ix[i, "lon"], data.ix[i, "lat"], 7)


# 计算两点之间的距离
def cal_dist(x1, x2, dis):
    # 表示两个司机在同一个范围内
    if x1[0:dis] == x2[0:dis]:
        return 1
    else:
        return 0


# 计算一个点在£域的点集合
def point_scope_set(point, data_set, dis):
    res = []
    for i in range(np.shape(data_set)[0]):
        if cal_dist(point, data_set.ix[i, "geohash_code"], dis) == 1:
            res.append(i)
    return res


# 使用司机的位置进行密度聚类,其中min_ps表示其周围的最少车辆数,d 表示geohash第几位相等
def positon_dbscan(data_set, min_ps=10, d=7):
    core_objects = {}
    k_cluster = {}
    # 初始化核心对象集合
    for p in range(np.shape(data_set)[0]):
        if p % 100 == 0:
            print "model train data: %d" % p
        scope_set = point_scope_set(data_set.ix[p, "geohash_code"], data_set, d)
        # 如果在该点的半径d域内存在大于min_ps的点,则说明该对象p是核心对象
        if len(scope_set) >= min_ps:
            core_objects[p] = scope_set
    old_core_objects = core_objects.copy()

    # 初始化聚类簇数
    k = 0
    # 初始化未访问的样本集合
    not_access = range(len(data_set))
    while len(core_objects) > 0:
        # 注意此处是参数传递,不能直接赋值
        old_not_access = []
        old_not_access.extend(not_access)
        # 随机选取一个核心对象
        cores = core_objects.keys()
        rand_n = np.random.randint(0, len(cores))
        queue = []
        # 使用一个核心对象初始化队列
        queue.append(cores[rand_n])
        not_access.remove(cores[rand_n])
        while len(queue) > 0:
            p = queue[0]
            del queue[0]
            # 判断队列中的点是否为核心对象,并把核心对象的所有点加入到队列中
            if p in core_objects.keys():
                delta = [q for q in core_objects[p] if q in not_access]
                # 更新未被访问的数据点
                queue.append(delta)
                not_access = [j for j in not_access if j not in delta]
        k += 1
        # 更新簇k中的数据-------数据来源于原始数据集中被访问过的部分
        k_cluster[k] = [p for p in old_not_access if p not in not_access]
        # 更新核心对象
        for i in k_cluster[k]:
            if i in core_objects:
                del core_objects[i]
    return k_cluster, old_core_objects


def data_write_file(data, k_cluster, city, file_name):
    fw = open(file_name, 'a')
    json_dict = dict()
    json_dict.setdefault(str(city), [])
    for k in k_cluster:
        result = {}
        key = str(city) + "@" + str(k)
        lon_list = [data.ix[i, "lon"] for i in k_cluster[k]]
        lat_list = [data.ix[i, "lat"] for i in k_cluster[k]]
        avg_lon = "%.6f" % (sum(lon_list) / float(len(lon_list)))
        avg_lat = "%.6f" % (sum(lat_list) / float(len(lat_list)))
        result[key] = avg_lon + "," + avg_lat + "," + str(len(lon_list))
        json_dict[str(city)].append(result)
    json_str = json.dumps(json_dict)
    fw.write(json_str + "\n")
    fw.close()


def get_smaple_by_city(data, percent=5):
    # 获取司机的userId
    user_id = set(data["user_id"])
    sample_user_id = random.sample(user_id, int(len(user_id) / percent))
    sample_data = data[data["user_id"].isin(sample_user_id)]
    return sample_data.reset_index(drop=True)


def diff_city_model_train(input_path):
    data = load_data(input_path)
    city_list = set(data["city_id"])
    city_list.add(0)
    # 选择同一个区的数据进入训练
    for city in city_list:
        district_city_data = data[data["city_id"] == city]
        # 判断每个时期的司机数量
        user_total = len(set(list(district_city_data["user_id"])))
        # 如果该市的司机数量小于5000 则不进行抽样
        district_city_data=district_city_data.reset_index(drop=True)
        if user_total > 5000:
            district_city_data = get_smaple_by_city(district_city_data)
        # 对于不同活跃数量的司机设置不同的司机密度点
        if user_total <= 500:
            min_point = 3
        elif 500 < user_total <= 2000:
            min_point = 5
        elif 2000 < user_total <= 5000:
            min_point = 8
        else:
            min_point = 10
        # 从市区中过滤重复的数据
        transfrom_position(district_city_data)
        filter_data = filter_repetition_logs(district_city_data)
        # 以区为单位训练样本数据
        print str(city) + " input sample train data: %d" % np.shape(filter_data)[0]
        k_cluster, old_core_objects = positon_dbscan(filter_data, min_point)
        # 计算结果转换为json 字符串
        data_write_file(filter_data, k_cluster, city, "data_set/%s0000.json" % str(city)[0:2])


if __name__ == '__main__':
    diff_city_model_train("data_set/a.csv")