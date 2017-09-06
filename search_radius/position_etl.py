#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/8/25 10:11
# @Author  : ywendeng
# @Description : 根据司机订单时间和定位时间，选择订单时间和定位时间相差最远的城市，作为司机承运下单时刻所在的城市
from utils import Utils
from datetime import datetime
import numpy as np
import pandas as pd


class PositionETL(object):
    def __init__(self, in_path):
        self.in_path = in_path
        self.columns = ["driver_id", "start_city"]

    def position_etl(self):
        util = Utils()
        data_set = util.load_data(self.in_path,'position')
        result = {}
        for i in range(np.shape(data_set)[0]):
            order_time = data_set.ix[i, "order_create_time"][:-3]
            position_time = data_set.ix[i, "position_time"][:-3]
            key = str(data_set.ix[i, "driver_id"]) + "\001" + order_time
            time_diff = datetime.strptime(order_time, "%Y-%m-%d %H:%M").hour - \
                        datetime.strptime(position_time, "%Y-%m-%d %H:%M").hour
            if key not in result: result.setdefault(key, [])
            val = (time_diff, data_set.ix[i, "city_id"])
            result[key].append(val)
        # 根据距离订单时间长度进行排序,取出时间最长的城市
        transform_result = []
        for key in result:
            city = sorted(result[key], key=lambda x: x[0])[0][1]
            transform_result.append([key, city])
        return pd.DataFrame(transform_result, columns=self.columns)

