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
import sklearn.cluster as skc
import threading

def load_data(file_name):
    data = pd.read_csv(file_name, delimiter='\001', header=None,
                       usecols=[0, 1, 2, 3],
                       names=["user_id", "lon", "lat", "city_id"],
                       dtype={"user_id": str})
    return data


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


# 使用欧几里德计算两点之间的距离
def cal_dist(x1, x2):
    dist = sum([math.pow(a - b, 2) for a, b in zip(x1, x2)])
    return math.sqrt(dist)


# 使用司机的位置进行密度聚类,其中min_ps表示其周围的最少车辆数,d 表示geohash第几位相等
def positon_dbscan(data_set, min_ps=2):
    trian = []
    for i in range(np.shape(data_set)[0]):
        trian.append([data_set.ix[i, "lon"], data_set.ix[i, "lat"]])
    model = skc.DBSCAN(eps=0.001, min_samples=min_ps, n_jobs=-1)
    model.fit(trian)
    y_hats = model.labels_
    return y_hats


def data_write_file(data, k_cluster, city, file_name):
    fw = open(file_name, 'a')
    json_dict = dict()
    # 为每一行数据加上聚类标签
    data["labels"] = k_cluster
    label = set(k_cluster)
    print label
    if -1 in label:
        label.remove(-1)
    if label is None:
        city_key = str(city) + "@" + str(0)
    else:
        city_key = str(city) + "@" + str(len(label))
    if label is not None:
        json_dict.setdefault(str(city_key), [])
        for k in label:
            result = {}
            key = str(city) + "@" + str(k)
            clustering_data = data[data["labels"] == k]
            clustering_data = clustering_data.reset_index(drop=True)
            lon_list = []
            lat_list = []
            for i in range(np.shape(clustering_data)[0]):
                lon_list.append(clustering_data.ix[i, "lon"])
                lat_list.append(clustering_data.ix[i, "lat"])
            avg_lon = "%.6f" % (sum(lon_list) / float(len(lon_list)))
            avg_lat = "%.6f" % (sum(lat_list) / float(len(lat_list)))
            result[key] = avg_lon + "," + avg_lat + "," + str(len(lon_list))
            json_dict[city_key].append(result)
        json_str = json.dumps(json_dict)
        fw.write(json_str + "\n")
        fw.close()


def get_smaple_by_city(data, percent=5):
    # 获取司机的userId
    user_id = set(data["user_id"])
    sample_user_id = random.sample(user_id, int(len(user_id) / percent))
    sample_data = data[data["user_id"].isin(sample_user_id)]
    return sample_data.reset_index(drop=True)


# 使用多线程来实现
class ThreadFunc(object):
    def __init__(self, func, args, name=''):
        self.name = name
        self.func = func
        self.args = args

    def __call__(self, *args, **kwargs):
        self.func(*self.args)


def thread_process(data, city,input_path):
    district_city_data = data[data["city_id"] == city]
    # 判断每个时期的司机数量
    # delta_data = data[True - data["city_id"] == city]
    # data = delta_data.reset_index(drop=True)
    user_total = len(set(list(district_city_data["user_id"])))
    # 如果该市的司机数量小于5000 则不进行抽样
    district_city_data = district_city_data.reset_index(drop=True)
    if user_total > 5000:
        district_city_data = get_smaple_by_city(district_city_data)
    # 将经纬度二维转换成一维
    transfrom_position(district_city_data)
    # 对于不同活跃数量的司机设置不同的司机密度点
    if user_total <= 500:
        min_point = 3
    elif 500 < user_total <= 2000:
        min_point = 5
    elif 2000 < user_total <= 5000:
        min_point = 8
    else:
        min_point = 10
    filter_data = filter_repetition_logs(district_city_data)
    # 以区为单位训练样本数据
    print str(city) + " input sample train data: %d" % np.shape(filter_data)[0]
    k_cluster = positon_dbscan(filter_data, min_point)
    # 计算结果转换为json 字符串
    data_write_file(filter_data, k_cluster, city, input_path+"/cluster/%s0000.json" % str(city)[0:2])


def diff_city_model_train(input_path):
    data = load_data(input_path+"/position_logs.csv")
    city_list = set(data["city_id"])
    city_list.add(0)
    # 选择同一个区的数据进入训练
    threads = []
    for city in city_list:
        t = threading.Thread(
            target=ThreadFunc(thread_process, (data, city,input_path))
        )
        threads.append(t)
    for i in range(len(city_list)):
        threads[i].start()
    for i in range(len(city_list)):
        threads[i].join()


if __name__ == '__main__':
    root_path = "/home/dev/data/dengyuanwen/data"
    diff_city_model_train(root_path)
