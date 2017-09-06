#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/8/18 17:45
# @Author  : ywendeng
# @Description : 密度聚类算法实现

# 计算两个向量之间的欧式距离
import math
import numpy as np
import matplotlib.pyplot as plt

# 密度聚类算法
'''
输入：样本集D={x1,x2,...,xm}
    邻域参数(ε,MinPts).
过程：
初始化核心对象集合：Ω = Ø
for j=1,2,...,m do
    确定样本xj的ε-邻域N(xj);
    if |N(xj)|>=MinPts then
        将样本xj加入核心对象集合Ω
    end if
end for
初始化聚类簇数：k=0
初始化未访问样本集合：Γ =D
while Ω != Ø do
    记录当前未访问样本集合：Γold = Γ;
    随机选取一个核心对象 o ∈ Ω，初始化队列Q=<o>
    Γ = Γ\{o};
    while Q != Ø do
        取出队列Q中首个样本q;
        if |N(q)|<=MinPts then
            令Δ = N(q)∩Γ；
            将Δ中的样本加入队列Q;
            Γ = Γ\Δ；
        end if
    end while
    k = k+1,生成聚类簇Ck = Γold\Γ;
    Ω = Ω\Ck
end while
输出：
簇划分C = {C1,C2,...,Ck}
'''


# 加载数据集
def load_data(file_name):
    data = np.loadtxt(file_name, delimiter=',', dtype=np.float64)
    return data


# 使用欧几里德计算两点之间的距离
def cal_dist(x1, x2):
    dist = sum([math.pow(a - b, 2) for a, b in zip(x1, x2)])
    return math.sqrt(dist)


# 计算一个点在£域的点集合
def point_scope_set(point, data_set, d):
    res = []
    for i in range(np.shape(data_set)[0]):
        if cal_dist(point, data_set[i]) < d:
            res.append(i)
    return res


# 密度聚类算法
def dbscan(data_set, min_ps=6, d=0.2):
    core_objects = {}
    k_cluster = {}
    # 初始化核心对象集合
    for p in range(np.shape(data_set)[0]):
        scope_set = point_scope_set(data_set[p], data_set, d)
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


# 主要使用密度最大值聚类算法来计算聚类中心和异常点
def maxmum_dbscan(data_set, d=0.2):
    p = {}
    # 计算每个样本点在距离d范围类的样本点
    for i in range(np.shape(data_set)[0]):
        res = []
        for j in range(np.shape(data_set)[0]):
            dist = cal_dist(data_set[i], data_set[j])
            if i != j and dist < d:
                res.append(j)
        p[i] = res
    # 找到每个样本点密度最大值距离δ
    result = {}
    for i in p:
        delta = float('inf')
        q = len(p[i])
        for j in p:
            # 找到密度比自己大的最小密度
            if i != j and len(p[j]) > q:
                dist_point = cal_dist(data_set[i], data_set[j])
                if delta > dist_point:
                    delta = dist_point
        result[i] = [q, delta]
    return result


def draw_max_dbscan_visal(data_set):
    X = []
    Y = []
    for i in data_set:
        Y.append(data_set[i][0])
        X.append(data_set[i][1])
    plt.scatter(X, Y, color="b", marker='o')
    plt.show()


def draw_visal(data_set, k_cluster, cores):
    color = ['r', 'y', 'g', 'b', 'c', 'k', 'm']
    cluster = []
    for k in k_cluster:
        cluster.extend(k_cluster[k])
        x = []
        y = []
        for j in k_cluster[k]:
            x.append(data_set[j][0])
            y.append(data_set[j][1])
        plt.scatter(x, y, color=color[k % len(color)], marker='o')
    # 计算出离散点
    border = [i for i in range(len(data_set)) if i not in cluster]
    X = []
    Y = []
    for i in border:
        X.append(data_set[i][0])
        Y.append(data_set[i][1])
    plt.scatter(X, Y, color="#000000", marker="^")
    # 将核心对象加上
    x1 = []
    y1 = []
    for val in cores:
        x1.append(data_set[val][0])
        y1.append(data_set[val][1])
    plt.scatter(x1, y1, color="r", marker="*")
    plt.show()


if __name__ == '__main__':
    data = load_data("data_set/density_based_data")
    # plt.scatter(data[:,0],data[:,1],color='b',marker='o')
    # plt.show()

    k_cluster, cores = dbscan(data)
    # draw_visal(data, k_cluster, cores)
    result = maxmum_dbscan(data)
    print result
    draw_max_dbscan_visal(result)
