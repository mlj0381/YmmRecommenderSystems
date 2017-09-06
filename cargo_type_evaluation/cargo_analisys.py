#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/8/7 14:54
# @Author  : ywendeng
# @Description : 货源好坏情况的分析
import pandas as pd
import numpy as np
import sys
import matplotlib.pyplot as plt
from  datetime import datetime


class CargoAnalisys(object):
    def __init__(self, input_path, analysis_input, output_path):
        plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
        plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号
        self.input = input_path
        self.analysis_input = analysis_input
        self.output = output_path
        self.head_name = {0: 'startProvCity', 1: 'endProvCity', 2: 'truckLens', 3: 'truckWeight',
                          4: 'cargoType', 5: 'cargoMsgCnt', 6: 'viewCnt', 7: 'callCnt', 8: 'detailCnt',
                          9: 'isValid', 10: 'createTime', 11: 'showEndTime', 12: "userId"}

    def is_null(self, field):
        if field == "NULL":
            return "0"
        else:
            return field

    def is_bad_cargo(self, cargo):
        is_bad_cargo = []
        for i in range(len(cargo)):
            if cargo.ix[i, "callCnt"] == 0 and cargo.ix[i, "detailCnt"] == 0:
                is_bad_cargo.append(0)
            else:
                is_bad_cargo.append(1)
        return is_bad_cargo

    def origin_data_etl(self, chose_prov, end_time):
        fread = open(self.input)
        fread.readline()
        line = fread.readline()
        data = []
        chose_prov = map(str, chose_prov)
        deline_end_time = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
        while line:
            fields = line.split(",")
            # start=fields[1]
            user_id = fields[0]
            start_prov = fields[3]
            end_prov = fields[5][:2] + "0000"
            # end_prov = fields[5]
            truck_weight = fields[-14]
            cargo_type = fields[-13]
            cargo_msg_cnt = fields[-9]
            view_cnt = self.is_null(fields[-8])
            call_cnt = self.is_null(fields[-7])
            detail_cnt = self.is_null(fields[-6])
            is_valid = fields[-4]
            create_time = fields[-3][:-2]
            show_end_time = fields[-2][:-2]
            fact_end_time = datetime.strptime(show_end_time, "%Y-%m-%d %H:%M:%S")
            # 计算货源是否展现时间结束
            if len(fields) == 22:
                truck_len = fields[7]
            else:
                truck_lens = []
                for i in range(len(fields) - 22):
                    truck_lens.append(fields[7 + i].replace("\"", ""))
                truck_len = " ".join(truck_lens)
            line = fread.readline()
            if start_prov in chose_prov and fact_end_time <= deline_end_time:
                data.append([start_prov, end_prov, truck_len, truck_weight, cargo_type,
                             cargo_msg_cnt, view_cnt, call_cnt, detail_cnt
                                , is_valid, create_time, show_end_time, user_id])
                # data.append(int(start+end_prov))
        fread.close()
        # 将源数据处理之后,转换为多维数组
        with open(self.output, 'w+') as file:
            # file.write(str(data))
            for line in data:
                file.write(",".join(line) + "\n")

    # 分析发货时间对货源的影响
    def diff_date_cargo_view(self, data_set, prov_list):
        # 注意需要使用DataFrame
        data = data_set[data_set["startProvCity"].isin(prov_list)]

        data["createHour"] = [datetime.strptime(d, '%Y-%m-%d %H:%M:%S').hour for d in
                              data["createTime"]]
        data_result = data[["startProvCity", "createHour", "viewCnt"]]

        result = data_result.groupby(["startProvCity", "createHour"]).sum()
        sichuan_prov = result.xs(prov_list[0], level="startProvCity")["viewCnt"]
        hubei_prov = result.xs(prov_list[1], level="startProvCity")["viewCnt"]
        plt.figure(figsize=(15, 8))
        plt.title(u"司机浏览货源量在上午7-8点到达峰值", fontsize=20)
        plt.plot(sichuan_prov / (sichuan_prov.max() - sichuan_prov.min()), 'g', marker='d')
        plt.plot(hubei_prov / (hubei_prov.max() - hubei_prov.min()), 'r', marker='*')
        plt.legend([u"四川省", u"湖北省"], loc='upper right', fontsize=14)
        plt.xticks(range(24))
        plt.show()
        '''
        fig = plt.figure(figsize=(20, 8))
        ax0 = fig.add_subplot(1, 2, 1)
        ax1 = fig.add_subplot(1, 2, 2)
        colors = ['r', 'g']

        
        for i in range(prov_num):
            prov_set = result.xs(prov_list[i], level="startProvCity")
            nomal = prov_set["viewCnt"]
            diff_max_min = nomal.max() - nomal.min()
            ax0.plot(nomal / diff_max_min, color=colors[i], marker='d', label=u"四川省")
            ax0.set_title(u"司机货源浏览量在早上7-8点到达峰值",fontsize=18)
            ax0.set_xticks(range(24))
            ax0.set_xticklabels(map(str, range(24)))
        plt.show()
        '''

    # 分析坏货源的发布时间分布
    def bad_cargo_create_time(self, data_set, provlist):
        data = data_set[data_set["startProvCity"].isin(prov_list)]

        data["createHour"] = [datetime.strptime(d, '%Y-%m-%d %H:%M:%S').hour for d in
                              data["createTime"]]
        data["cargoNum"] = [1] * len(data_set)

        data_result = data[["startProvCity", "createHour", "cargoNum"]]
        result = data_result.groupby(["startProvCity", "createHour"]).sum()
        sichuan_prov = result.xs(prov_list[0], level="startProvCity")["cargoNum"]
        hubei_prov = result.xs(prov_list[1], level="startProvCity")["cargoNum"]

        plt.figure(figsize=(15, 8))
        plt.title(u"没有电话和浏览的货源发布时间分布", fontsize=20)
        plt.plot(sichuan_prov / (sichuan_prov.max() - sichuan_prov.min()), 'g--', marker='d')
        plt.plot(hubei_prov / (hubei_prov.max() - hubei_prov.min()), 'r', marker='*')
        plt.legend([u"四川省", u"湖北省"], loc='upper right', fontsize=14)
        plt.xticks(range(24))
        plt.show()

    def cargo_len_weight(self, data_set, prov):
        good_cargo = data_set[data_set["isBadCargo"] == 1]
        # 重新设置index
        good_cargo = good_cargo.reset_index(drop=True)
        good_len = []
        good_weight = []
        bad_cargo = data_set[data_set["isBadCargo"] == 0]
        bad_cargo = bad_cargo.reset_index(drop=True)
        bad_len = []
        bad_weight = []
        for i in range(len(good_cargo)):
            trunck_len = good_cargo.ix[i, "truckLens"].split(" ")
            trunck_weight = good_cargo.ix[i, "truckWeight"]
            for tl in trunck_len:
                good_len.append(tl)
                good_weight.append(trunck_weight)
        for i in range(len(bad_cargo)):
            trunck_len = bad_cargo.ix[i, "truckLens"].split(" ")
            trunck_weight = bad_cargo.ix[i, "truckWeight"]
            for tl in trunck_len:
                bad_len.append(tl)
                bad_weight.append(trunck_weight)

        xlim = max(good_len + bad_len)
        ylim = max(good_weight + bad_weight)
        plt.xlim(0, float(xlim))
        plt.ylim(0, float(ylim))
        plt.figure(figsize=(15, 10))
        plt.scatter(good_len, good_weight, c="b", marker="d")
        plt.scatter(bad_len, bad_weight, c="r", marker="*")
        plt.title(u"车长和车重不是坏货源的主要影响因素", fontsize=20)
        plt.xlabel(u"车长")
        plt.ylabel(u"车重")
        plt.legend([u"好货源", u"坏货源"], loc='upper right', fontsize=16)
        plt.show()

    def key_difinite(self, val):
        if val < 100:
            keys = '100'
        elif 100 <= val < 200:
            keys = '200'
        elif 200 <= val < 300:
            keys = '300'
        elif 300 <= val < 500:
            keys = '500'
        elif 500 <= val < 1000:
            keys = '1000'
        else:
            keys = '1000<'
        return keys

    def bad_good_distance(self, data_set):
        distance_path = "data_set/distance_result.csv"
        # 过滤在发货时间在7点到10点之间的货源
        data_set = data_set.reset_index(drop=True)
        cargo_data = data_set[data_set["createHour"].isin([7, 8, 9, 10])]
        distance_data = pd.read_csv(distance_path, delimiter=',', usecols=["userId", "distance"],
                                    dtype={"userId": np.int64, "distance": np.int64})
        merge_data = pd.merge(cargo_data, distance_data, on="userId")

        good_cargo = merge_data[merge_data["isBadCargo"] == 1]
        # 重新设置index
        good_cargo = good_cargo.reset_index(drop=True)
        good_dist = {}
        bad_cargo = merge_data[merge_data["isBadCargo"] == 0]
        bad_cargo = bad_cargo.reset_index(drop=True)
        bad_dist = {}
        bad = {}
        good = {}
        ratio = {}
        key_val = ['100', '200', '300', '500', '1000', '1000<']
        for k in key_val:
            bad.setdefault(k, 0)
            good.setdefault(k, 0)
            ratio.setdefault(k, 0)

        for i in good_cargo["distance"]:
            key = str(i)
            if key not in good_dist: good_dist.setdefault(key, 0)
            good_dist[key] += 1
            keys = self.key_difinite(i)
            good[keys] += 1
        for j in bad_cargo["distance"]:
            key_2 = str(j)
            if key_2 not in bad_dist: bad_dist.setdefault(key_2, 0)
            bad_dist[key_2] += 1
            keys_2 = self.key_difinite(j)
            bad[keys_2] += 1
        # 计算好货和坏货不同距离的比值
        for k in ratio:
            ratio[k] = good[k] / bad[k]

        xlim = max(bad_dist.keys() + good_dist.keys())
        ylim = max(bad_dist.values() + good_dist.values())
        x = []
        for i in key_val:
            x.append(ratio[i])
        plt.xlim(0, float(xlim))
        plt.ylim(0, float(ylim))
        fig, ax = plt.subplots(1, 2, figsize=(20, 10))
        ax1 = ax[1]
        ax0 = ax[0]
        ax1.plot(x, 'g', marker='D', label=u"比值")
        ax1.set_title(u"好坏货源在不同距离区间的比值", fontsize=20)
        ax1.set_xticks(range(6))
        ax1.set_xticklabels(key_val)
        ax1.set_xlabel(u"起始城市和结束城市距离区间值")
        ax1.set_ylabel(u"好货源/坏货源")

        ax0.scatter(good_dist.keys(), good_dist.values(), c="b", marker="d", label=u'好货源')
        ax0.scatter(bad_dist.keys(), bad_dist.values(), c="r", marker="*", label=u'坏货源')
        ax0.set_title(u"好坏货源和运输路线距离的关系", fontsize=20)
        ax0.set_xlabel(u"起始城市和结束城市距离")
        ax0.set_ylabel(u"发货量")
        plt.show()

    def bad_good_diff_time_ratio(self, data_set):
        good_cargo = data_set[data_set["isBadCargo"] == 1]
        # 重新设置index
        good_cargo = good_cargo.reset_index(drop=True)
        good_dict = {}
        bad_cargo = data_set[data_set["isBadCargo"] == 0]
        bad_cargo = bad_cargo.reset_index(drop=True)
        bad_dict = {}
        for i in range(len(good_cargo)):
            hour = good_cargo.ix[i, "createHour"]
            if hour not in good_dict: good_dict.setdefault(hour, 0)
            good_dict[hour] += 1
        for i in range(len(bad_cargo)):
            hour = good_cargo.ix[i, "createHour"]
            if hour not in bad_dict: bad_dict.setdefault(hour, 0)
            bad_dict[hour] += 1
        width = 0.35
        p1 = plt.bar(good_dict.keys(), good_dict.values(), width, color='#d62728')
        p2 = plt.bar(bad_dict.keys(), bad_dict.values(), width, bottom=good_dict.values(), color='b')
        plt.xticks(good_dict.keys())
        plt.xlabel(u"一天发货时间", fontsize=14)
        plt.ylabel(u"好坏货源的发货量", fontsize=14)
        plt.legend((p1[0], p2[0]), (u'好货源', u'坏货源'))
        plt.title(u"一天二十四小时好坏货源的发货量", fontsize=20)

        plt.show()

    # 计算每个每个省份的覆盖率

    def coverage_ratio(self, data, prov_list):
        all_ratio = {}
        for prov in prov_list:
            prov_data = data[data["startProvCity"] == prov]
            total_sum = len(prov_data)
            call_cargo_prov_data = prov_data[prov_data["callCnt"] > 0]
            call_total_sum = len(call_cargo_prov_data)
            if call_total_sum != 0:
                ratio = float(call_total_sum) / total_sum * 100
                all_ratio[prov] = ratio
        return all_ratio

    # 计算平均多少个pv能产生一个电话
    def pv_call_ratio(self, data, prov_list):
        pv_call_ratio = {}
        result = data.groupby("startProvCity").sum()
        for prov in prov_list:
            pv_sum = result.loc[prov, "viewCnt"]
            call_sum = result.loc[prov, "callCnt"]
            if call_sum != 0:
                pv_call_ratio[prov] = pv_sum / call_sum
        return pv_call_ratio

    def data_analysis(self, prov_list):
        data_set = pd.read_csv(self.analysis_input, delimiter=",", header=None)
        data_set.rename(columns=self.head_name, inplace=True)

        is_bad_cargo_result = pd.Series(self.is_bad_cargo(data_set[["callCnt", "detailCnt", "showEndTime"]]))
        # data_set.drop(["callCnt", "detailCnt", "isValid"], axis=1, inplace=True)
        # 为货源添加一个货源好坏标签
        data_set["isBadCargo"] = is_bad_cargo_result
        # 分析货源的反馈率
        # coverage_ratio_result = self.coverage_ratio(data_set[["startProvCity", "callCnt"]], prov_list)
        # print coverage_ratio_result
        # 分析每个省份的平均多少个pv能够产生一个电话量
        # pv_call_result = self.pv_call_ratio(data_set[["startProvCity", "viewCnt", "callCnt"]], prov_list)
        # 分析一天时间范围内不同时间段的发货量和以及发货的货物访问量
        # self.diff_date_cargo_view(data_set[["startProvCity", "viewCnt", "createTime"]],
        #                          prov_list)
        # 从中筛选出坏货源
        # bad_cargo_set = data_set[data_set["isBadCargo"] == 0]
        # 分析坏货源的发布创建时间分布
        # self.bad_cargo_create_time(data_set[["startProvCity", "createTime"]], prov_list)
        # 分析好货源和坏货源所要求车长和车重
        # for prov in prov_list:
        #     data_prov = data_set[data_set["startProvCity"] == prov]
        #     self.cargo_len_weight(data_prov[["truckLens", "truckWeight", "isBadCargo"]], prov)
        # =============分析距离对好坏货源的影响==================
        # distance_set = data_set[data_set["startProvCity"].isin(prov_list)]
        # distance_set["createHour"] = [datetime.strptime(d, '%Y-%m-%d %H:%M:%S').hour for d in
        #                               data_set["createTime"]]
        # self.bad_good_distance(distance_set[["isBadCargo", "createHour", "userId"]])
        # ===========================分析好坏货源在不同时刻占比情况==============================
        distance_set = data_set[data_set["startProvCity"].isin(prov_list)]
        distance_set["createHour"] = [datetime.strptime(d, '%Y-%m-%d %H:%M:%S').hour for d in
                                      data_set["createTime"]]
        self.bad_good_diff_time_ratio(distance_set[["isBadCargo", "createHour"]])


if __name__ == '__main__':
    input_path = "data_set/good_bad_cargo.csv"
    # 原始数清洗之后的数据存放地址
    output_path = "data_set/result"
    # 原始数据清洗后作为后续分析的输入
    analysis_path = output_path
    cargo = CargoAnalisys(input_path, analysis_path, output_path)
    # 参数--- 需要分析省份和货物的展示结束时间
    prov_list = [510000, 420000, 320000, 440000, 370000, 230000, 620000, 330000, 410000, 530000, 110000]
    deline_time = "2017-08-01 00:00:00"
    # cargo.origin_data_etl(prov_list, deline_time)
    cargo.data_analysis(prov_list)
