#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/10/11 14:43
# @Author  : ywendeng
# @Description : 根据用户活跃的天数做相应的数据聚集处理，特征结果如下：
# 用户ID,最近7天活跃次数,最近30天活跃次数,最近60天活跃次数,用户是否流失（0表示流失,1表示活跃）
import utils
import json
import numpy as np


def get_active_tag(data, model):
    interval_days = {}
    for key in data:
        if model == "train":
            active = data.get(key)[0:-30]
        elif model == "test":
            active = data.get(key)
        day_7 = sum([float(day) for day in active[-7:]])
        day_15 = sum([float(day) for day in active[-15:]])
        day_60 = sum([float(day) for day in active[-60:]])
        # 给活跃司机加上是否流失的标签
        avg_active = day_60 / 60
        loss_tag = 0.0
        if day_7 >= avg_active and day_15 >= 2.0:
            loss_tag = 1.0
        active.append(loss_tag)
        # 为用户加上tag 标签
        interval_days[key] = active[-61:]
    return interval_days


if __name__ == '__main__':
    active_data = utils.load_origin_data("train")
    test = get_active_tag(active_data, "test")
    train = get_active_tag(active_data, "train")
