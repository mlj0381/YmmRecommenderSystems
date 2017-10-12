#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/10/11 11:11
# @Author  : ywendeng
# @Description : 数据处理通用方法


def load_origin_data(file_name):
    active = {}
    with open(file_name, 'r') as fread:
        line = fread.readline().strip()
        while line:
            active_days = line.split(",")
            active[active_days[0]] = active_days[1:]
            line = fread.readline().strip()
    return active

