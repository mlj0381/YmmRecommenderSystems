#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/8/23 16:29
# @Author  : ywendeng
# @Description : 根据每个省份的历史司机定位地址和订单来计算搜索半径
import numpy as np
from utils import Utils
from position_etl import PositionETL
import json


class SearchRadius(object):
    def __init__(self, position_dir, order_dir, output_dir):
        self.position_dir = position_dir
        self.order_dir = order_dir
        self.output_dir = output_dir

    def order_etl(self):
        util = Utils()
        order_set = util.load_data(self.order_dir,'order')
        result = {}
        for i in range(np.shape(order_set)[0]):
            order_time = order_set.ix[i, "order_create_time"][:-3]
            start_city = order_set.ix[i, "start_city"]
            end_city = order_set.ix[i, "end_city"]
            key = str(order_set.ix[i, "driver_id"]) + "\001" + order_time
            if key not in result: result.setdefault(key, [])
            # 市之间的距离
            provice_city = (int(str(start_city)[:-2] + "00"), int(str(end_city)[:-2] + "00"))
            # 区之间的距离
            city = (start_city, end_city)
            result[key].append(provice_city)
            result[key].append(city)
        return result

    def merge_order_positon(self):
        ptl = PositionETL(self.position_dir)
        positon_set = ptl.position_etl()
        order_set = self.order_etl()
        prov_city = {}
        city = {}
        for key in order_set:
            line = positon_set[positon_set.ix[:, "driver_id"] == key]
            if len(line) > 0:
                driver_position = str(line.iloc[0, 1])
                # 开始拼接城市列表
                prov_start = str(order_set[key][0][0])
                cargo_start = str(order_set[key][1][0])
                cargo_end = str(order_set[key][1][1])
                if prov_start not in prov_city: prov_city.setdefault(prov_start, [])
                # (司机定位地址到市的关系),(订单发货市到订单结束城市的关系)
                prov_city[prov_start].append((prov_start + driver_position, prov_start + cargo_end))
                if cargo_start not in city: city.setdefault(cargo_start, [])
                # （司机定位地址和发货区之间的关系）,(订单出发地点和结束地之间的关系)
                city[cargo_start].append((cargo_start + driver_position, cargo_start + cargo_end))
            else:
                continue
        return prov_city, city

    def change_to_distance(self, distance_ref):
        util = Utils()
        # 获取到城市之间的静态聚类表
        distance = util.query_distance()
        for key in distance_ref:
            for i, (prov, city) in enumerate(distance_ref[key]):
                prov_dis = distance.get(prov, float("inf"))
                city_dis = distance.get(city, float("inf"))
                distance_ref[key][i] = (prov_dis, city_dis)
        # 根据订单距离对历史司机空载距离进行排序

        return distance_ref

    # 根据订单距离得到不同的区间
    def get_key_by_order(self, dis):
        km_dis = dis / 1000
        if 0 <= km_dis <= 100:
            return "r_100"
        elif 100 < km_dis <= 200:
            return "r_200"
        elif 200 < km_dis <= 500:
            return "r_500"
        elif 500 < km_dis <= 1000:
            return "r_1000"
        elif 1000 < km_dis <= 2000:
            return "r_2000"
        else:
            return "r_2001"

    def get_city_distance_list(self, distance):
        hist_dis = {}
        for dis, order in distance:
            if order != float('inf') and dis != float('inf'):
                key = self.get_key_by_order(order)
                if key not in hist_dis: hist_dis.setdefault(key, [])
                hist_dis[key].append(dis)
            else:
                continue
        # 对于每个距离阶段的历史距离排序
        for key in hist_dis:
            hist_dis[key] = sorted(hist_dis[key])
        return hist_dis

    def get_distance_by_median(self, prov_dis):
        dis_scope = {}
        hist_scope = {}
        for key in prov_dis:
            dis_scope[key] = self.get_city_distance_list(prov_dis[key])
            # 计算空载距离的均值
            for k in dis_scope[key]:
                # 使用中位数来作为搜索半径
                val = dis_scope[key][k][len(dis_scope[key][k]) / 2]
                dis_scope[key][k] = val
                # 保存不同距离区间的历史数据记录
                if k not in hist_scope: hist_scope.setdefault(k, [])
                hist_scope[k].append(val)
        # 对历史数据求解平均值
        for j in hist_scope:
            hist_scope[j] = sum(hist_scope[j]) / len(hist_scope[j])
        return dis_scope, hist_scope

    def checkout_deficiency_key(self, dis_scope, hist_scope):
        keys = ['r_100', 'r_200', 'r_500', 'r_1000', 'r_2000', 'r_2001']
        for key in dis_scope:
            for i in keys:
                if i not in dis_scope[key]:
                    # 从历史数据记录中获取数据来填充
                    if i not in hist_scope and i=='r_2000':
                        val =300000
                    elif i not in hist_scope and i=='r_2001':
                         val=500000
                    else:
                        val = hist_scope[i]
                    dis_scope[key][i] = val
        return dis_scope

    def cal_search_radius(self):
        prov, city = self.merge_order_positon()
        prov_dis = self.change_to_distance(prov)
        city_dis = self.change_to_distance(city)
        prov_dis_scope, prov_hist_scope = self.get_distance_by_median(prov_dis)
        city_dis_scope, city_hist_scope = self.get_distance_by_median(city_dis)
        # 对每个省份的数据处理缺失值
        prov = self.checkout_deficiency_key(prov_dis_scope, prov_hist_scope)
        city = self.checkout_deficiency_key(city_dis_scope, city_hist_scope)
        return prov, city

    def save_data_json(self, data_set, dir_path):
        json_list = []
        for key in data_set:
            result = {}
            result["cityId"] = key
            for k in data_set[key]:
                result[k] = data_set[key][k]
            json_list.append(result)
        json_str = json.dumps(json_list)
        dist_path = self.output_dir + "/" + dir_path
        with open(dist_path, 'w+') as fw:
            fw.write(json_str)


if __name__ == '__main__':
    stl = SearchRadius("data_set/position/position", "data_set/order/order", "data_set/output")
    d1,d2=stl.cal_search_radius()
    stl.save_data_json(d1, "prov.json")
    stl.save_data_json(d2, "city.json")
