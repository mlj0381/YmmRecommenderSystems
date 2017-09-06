#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/8/3 11:04
# @Author  : ywendeng
# @Description : 使用pandas来做数据处理和计算
import pandas as pd


class EvaluationModel(object):
    def read_data(self, driver_path, cargo_path):
        driver = pd.read_csv(driver_path, delimiter='\t')
        cargo = pd.read_csv(cargo_path, delimiter='\t')
        return driver, cargo

    def sim_driver_cargo(self, driver_cargo_matrix):
        # 获取司机的特征Series
        driver = driver_cargo_matrix.iloc[len(driver_cargo_matrix) - 1, :]
        subscribe_list = driver["subscribe"].split(",")
        truck_lens = driver["truckLens"].split(",")
        truck_type = driver["truckType"]
        score_list = []
        for i in range(len(driver_cargo_matrix) - 1):
            distinct = []
            delta = []
            cargo_subscribe = driver_cargo_matrix.ix[i, "subscribe"]
            cargo_truck_len = driver_cargo_matrix.ix[i, "truckLens"]
            cargo_truck_type = driver_cargo_matrix.ix[i, "truckType"]

            if cargo_subscribe != "" and len(subscribe_list) > 0:
                delta.append(1)
                if cargo_subscribe in subscribe_list:
                    distinct.append(1)
                else:
                    distinct.append(0)
            else:
                delta.append(0)

            # 判断司机车长是否符合
            if cargo_truck_len != "" and len(truck_lens) > 0:
                delta.append(1)
                if cargo_truck_len in truck_lens:
                    distinct.append(1)
                else:
                    distinct.append(0)
            else:
                delta.append(0)

            # 判断司机车型是否符合
            if cargo_truck_type != "" and truck_type != "":
                delta.append(1)
                if cargo_truck_type == truck_type:
                    distinct.append(1)
                else:
                    distinct.append(0)
            else:
                delta.append(0)

            num = sum([i * j for i, j in zip(delta, distinct)])
            den = sum(delta)
            if den != 0:
                sim = float(num) / den
                score_list.append(sim * 100)
        return score_list

    def calculate_score(self, driver_set, cargo_set):
        all_driver_score = []
        for i in range(len(driver_set)):
            # 处理司机的特有属性
            user_id = driver_set.ix[i, "userId"]
            # 如果司机没有推荐货物则不需要进行计算
            rec_cargo = cargo_set[cargo_set["userId"] == user_id]
            driver_cargo_matrix = rec_cargo.append(driver_set.iloc[i, :], ignore_index=True)
            if len(rec_cargo) > 0:
                # 将司机和推荐货源的相似度
                score_list = self.sim_driver_cargo(driver_cargo_matrix)
                score_len = len(score_list)
                if score_len != 0:
                    all_driver_score.append(sum(score_list) / score_len)
                    # 返回整个系统的平均分
        return sum(all_driver_score) / len(all_driver_score)

    # 计算整个推荐系统的覆盖率
    def rec_coverage_ratios(self, all_cargo, rec_cargo):
        rec_cargo_num = len(rec_cargo)
        all_cargo_num = len(all_cargo)
        ratio = 0.0
        if all_cargo_num != 0:
            ratio = float(rec_cargo_num) / all_cargo_num
        return ratio * 100


if __name__ == '__main__':
    model = EvaluationModel()
    driver_data, cargo_data = model.read_data("data_set/dri", "data_set/cargo")
    sim_score = model.calculate_score(driver_data, cargo_data)
    print "推荐系统综合推荐得分: %.2f" % sim_score
