import os
import pathlib
from pprint import pprint

import numpy as np
import pandas as pd
from scipy import stats
from scipy import signal
import matplotlib.pyplot as plt
from matplotlib.pyplot import figure
from matplotlib import animation, rc
import matplotlib as mpl

import trajectorytools as tt
import trajectorytools.plot as ttplot
import trajectorytools.socialcontext as ttsocial

import json
import math
from smallestenclosingcircle import *


class idtcker(object):
    # 初始化
    # @in
    #  path: idtracker session 路径
    def __init__(self, path=None):
        self.initPath = path
        self.tr = None
        self.data = None
        self._tmp = {}

    # 判断 path 文件类型
    def _whatsType(self, path):
        if len(path.split(".csv")) > 1:
            return "csv"
        elif len(path.split(".npy")) > 1:
            return "session"
        return None

    # 加载
    def load(self, **kw):
        assert self.initPath != None
        args = self._args(kw, origin=None, length=None, time=None)
        self.tr = tt.Trajectories.from_idtrackerai(self.initPath)

        # 调整坐标中心
        if args["origin"] != None:
            if type(args["origin"]) == tuple:
                pointOfFrame = np.asarray(list(args["origin"]))
                self.tr.origin_to(pointOfFrame)
            elif args["origin"] == "center":
                center, radius = self.tr.estimate_center_and_radius_from_locations(
                    in_px=True
                )
                self.tr.origin_to(center)

        # 调整 x, y 坐标单位（仅单位转化）
        if args["length"] != None:
            if type(args["length"]) == tuple:
                self.tr.new_length_unit(args["length"][0], args["length"][1])
            elif args["length"] == "radius":
                center, radius = self.tr.estimate_center_and_radius_from_locations(
                    in_px=True
                )
                self.tr.new_length_unit(radius, "R")
            elif args["length"] == "body":
                self.tr.new_length_unit(self.tr.params["body_length_px"], "BL")

        # 调整时间轴单位（仅单位转化）
        if args["time"] != None:
            if type(args["time"]) == tuple:
                self.tr.new_time_unit(args["time"][0], args["time"][1])
            elif type(args["time"]) == str:
                if args["time"][-1] == "s":
                    self.tr.new_time_unit(
                        self.tr.params["frame_rate"] * int(args["time"][:-1]), "s"
                    )
                elif args["time"][-1] == "m":
                    self.tr.new_time_unit(
                        self.tr.params["frame_rate"] * int(args["time"][:-1]) * 60, "m"
                    )
                if args["time"][-1] == "h":
                    self.tr.new_time_unit(
                        self.tr.params["frame_rate"] * int(args["time"][:-1]) * 3600,
                        "h",
                    )

        # 输出配置内容
        print("------------")
        for x in self.tr.params:
            print(f"\033[1;32m{x}: {self.tr.params[x]}\033[0m")
        print("------------")

        self.data = {"filter": [], "split": []}
        self.data["traj"] = self.tr.s
        self.data["spee"] = self.tr.v
        self.data["acce"] = self.tr.a

    # 导出
    # @in
    #  data:str@ 预导出的数据
    #  path:str@ 导出的文件的路径（包含文件名与格式）
    #  name:list@ 导出为 csv 时可自定义列名称
    def out(self, data, path, name=None):
        tmp = self._whatsType(path)
        if tmp == "csv":
            if type(data) == np.ndarray:
                if len(data.shape) == 3:
                    r = self._np2list(data)
                    self._listSave2Csv(r, name).to_csv(path, index=False)
            elif type(data) == list:
                if len(np.array(data).shape) == 3:
                    r = []
                    for i in range(len(data)):
                        for x in data[i]:
                            r.append([i, x[0], x[1]])
                else:
                    r = data
                self._listSave2Csv(r, name).to_csv(path, index=False)
        else:
            with open(path, "w") as f:
                json.dump(data, f)

        print(f"\033[1;36m[saved] {path}\033[0m")

    # 格式化实参列表
    # @in
    #  c: 传入的实参列表
    #  kw: 预获取的参数与其默认值
    # @out
    #  dict
    def _args(self, c, **kw):
        r = {}
        for x in kw:
            if x in c:
                r[x] = c[x]
            else:
                r[x] = kw[x]
        return r

    # 将 2 维列表格式化为 pandas 实例
    def _listSave2Csv(self, c, name=None):
        num = np.array(c).shape[-1]
        tmp = []
        name = range(num) if type(name) == type(None) else name
        for i in range(num):
            tmp.append(pd.Series([x[i] for x in c], name=name[i]))
        final = pd.concat(tmp, axis=1)
        return final

    # 将 3 维 numpy array 转换为 2 维 list
    def _np2list(self, d):
        frame, animalNum, position = d.shape
        outArr = np.column_stack(
            (np.repeat(np.arange(frame), animalNum), d.reshape(frame * animalNum, -1),)
        )
        return (
            pd.DataFrame(outArr, columns=["frame", "x", "y"])
            .replace({np.nan: None})
            .values.tolist()
        )

    # 过滤
    # @in
    #  itype@ 类型名
    #  data@ 数据
    #  inherit@ 是否继承 self.data["filter"] 数组
    #  frame:tuple@ 根据帧（时间）筛选，(type, no1, no2)
    #  number:tuple@ 根据目标数量筛选，(no1, no2)
    #  circle:tuple@ 根据圆筛选，(x, y, r)
    def filter(self, **kw):
        args = self._args(
            kw,
            type="traj",
            data=None,
            inherit=False,
            frame=None,
            number=None,
            circle=None,
        )
        self._tmp["filter"] = args
        if type(args["data"]) != type(None):
            rdata = args["data"].copy()
        else:
            if args["inherit"] and len(self.data["filter"]):
                rdata = self.data["filter"].copy()
            else:
                rdata = self.data[args["type"]].copy()

        if type(args["frame"]) == tuple:
            x = args["frame"]
            frameRange = [0, 0]
            if x[0] == "f":
                frameRange = [x[1], x[2]]
            elif x[0] == "s":
                frameRange[0] = int(x[1]) * int(self.tr.params["frame_rate"])
                frameRange[1] = int(x[2]) * int(self.tr.params["frame_rate"])
            elif x[0] == "m":
                frameRange[0] = int(x[1]) * int(self.tr.params["frame_rate"] * 60)
                frameRange[1] = int(x[2]) * int(self.tr.params["frame_rate"] * 60)
            rdata = rdata[frameRange[0] : frameRange[1], ...]
        if type(args["number"]) == tuple:
            rdata = rdata[:, int(args["number"][0]) : int(args["number"][1]), :]

        if args["circle"] != None:
            _r = int(args["circle"][2])
            _x = int(args["circle"][0])
            _y = int(args["circle"][1])
            for frame in rdata:
                for x in frame:
                    if (x[0] - _x) ** 2 + (x[1] - _y) ** 2 > _r ** 2:
                        x[0] = x[1] = np.nan

        self.data["filter"] = rdata
        return self

    # 求平均值
    # @in
    #  type@ 求值类型
    #  data@ 数据
    #  split:dict@ 分割条件
    def average(self, **kw):
        filterBak = self.data["filter"].copy()
        rel = {"spee": "traj", "acce": "spee"}
        args = self._args(kw, type="spee", data=None, split=None)
        data = (
            self.data[rel[args["type"]]]
            if type(args["data"]) == type(None)
            else args["data"]
        )
        if type(args["split"]) == list:
            r = []
            for x in args["split"]:
                tmp = self.filter(data=data, **x).data["filter"]
                r.append(self._average(tmp, args["type"]))
        self.data["filter"] = filterBak
        return r

    def _average(self, data, itype="spee"):
        r = []
        for i in range(data.shape[1]):
            tmp = data[:, i, :]
            _first = _last = None
            for j in range(len(tmp)):
                if not np.isnan(tmp[j][0]) and not np.isnan(tmp[j][1]):
                    _first = [j, tmp[j][0], tmp[j][1]]
                    break
            for j in range(len(tmp) - 1, -1, -1):
                if not np.isnan(tmp[j][0]) and not np.isnan(tmp[j][1]):
                    _last = [j, tmp[j][0], tmp[j][1]]
                    break
            if type(_first) == type(None) or type(_last) == type(None):
                r.append([None, None])
            else:
                txt = (
                    self.tr.params["length_unit_name"]
                    + "/"
                    + self.tr.params["time_unit_name"]
                )
                if itype == "spee":
                    des = (_first[1] - _last[1]) ** 2 + (_first[2] - _last[2]) ** 2
                    time = ((_last[0] - _first[0]) / self.tr.params["time_unit"]) ** 2
                    ave = math.sqrt(des / time)
                elif itype == "acce":
                    v1 = math.sqrt(_first[1] ** 2 + _first[2] ** 2)
                    v2 = math.sqrt(_last[1] ** 2 + _last[2] ** 2)
                    time = ((_last[0] - _first[0]) / self.tr.params["time_unit"]) ** 2
                    ave = (v2 - v1) / time
                    txt += "^2"
                r.append([ave, txt])
        return r

    # 求最小圆
    # @in
    #  data@ 数据
    #  index@ 具体对象序号
    def smestCircle(self, data=None, index=-1):
        data = self.tr.s if type(data) == type(None) else data
        r = []
        if index != -1:
            r.append(make_circle(data[:, index, :]))
        else:
            for i in range(data.shape[1]):
                tmp = data[:, i, :]
                r.append(make_circle(tmp))
        return r

    # 轨迹动画
    def drawTrajAni(self, data=None):
        data = self.tr.s if type(data) == type(None) else data

        fig, ax_trajectories = plt.subplots(figsize=(5, 5))
        text = ax_trajectories.text(
            -self.tr.params["_center"][0] / self.tr.params["length_unit"] * 2
            + 50 / self.tr.params["length_unit"],
            -self.tr.params["_center"][1] / self.tr.params["length_unit"] * 2
            + 50 / self.tr.params["length_unit"],
            "",
            bbox={"facecolor": "w", "alpha": 0.5, "pad": 3},
        )
        lines = []

        for i in range(data.shape[1]):
            (line,) = ax_trajectories.plot(data[0, i, 0], data[0, i, 1], "o", label=i)
            lines.append((line,))

        def connect(frame):
            tmp = f"frame: {frame}"
            for i in range(data.shape[1]):
                lines[i][0].set_data(data[frame, i, 0], data[frame, i, 1])
                _v = "{:05.2f}".format(
                    round(
                        math.sqrt(
                            self.tr.v[frame, i, 0] ** 2 + self.tr.v[frame, i, 1] ** 2
                        ),
                        2,
                    )
                )
                _a = "{:05.2f}".format(
                    round(
                        math.sqrt(
                            self.tr.a[frame, i, 0] ** 2 + self.tr.a[frame, i, 1] ** 2
                        ),
                        2,
                    )
                )
                tmp += f"\n{i}: {_v} {self.tr.params['length_unit_name']}/{self.tr.params['time_unit_name']}, {_a} {self.tr.params['length_unit_name']}/{self.tr.params['time_unit_name']}^2"
            text.set_text(tmp)

        ax_trajectories.set_xlim(
            -self.tr.params["_center"][0] / self.tr.params["length_unit"] * 2,
            self.tr.params["_center"][0] / self.tr.params["length_unit"] * 2,
        )
        ax_trajectories.set_ylim(
            -self.tr.params["_center"][1] / self.tr.params["length_unit"] * 2,
            self.tr.params["_center"][1] / self.tr.params["length_unit"] * 2,
        )

        ani = animation.FuncAnimation(
            fig,
            connect,
            np.arange(1, data.shape[0]),
            interval=1000 / self.tr.params["time_unit"],
            repeat=False,
        )
        plt.legend(loc="upper left", fontsize=6)
        plt.show()

    # 轨迹
    def drawTraj(self, data=None):
        data = self.tr.s if type(data) == type(None) else data
        fig, ax_trajectories = plt.subplots(figsize=(5, 5))
        frame_range = range(0, data.shape[0], 1,)
        ax_trajectories.set_xlim(
            -self.tr.params["_center"][0] / self.tr.params["length_unit"] * 2,
            self.tr.params["_center"][0] / self.tr.params["length_unit"] * 2,
        )
        ax_trajectories.set_ylim(
            -self.tr.params["_center"][1] / self.tr.params["length_unit"] * 2,
            self.tr.params["_center"][1] / self.tr.params["length_unit"] * 2,
        )
        for num in range(data.shape[1]):
            ax_trajectories.plot(data[frame_range, num, 0], data[frame_range, num, 1])
            _circle = self.smestCircle(data, num)[0]
            c = plt.Circle(tuple(_circle[:2]), _circle[2], fill=False,)
            plt.gcf().gca().add_artist(c)
        ax_trajectories.set_aspect("equal", "box")
        ax_trajectories.set_title("Trajectories", fontsize=12)
        ax_trajectories.set_xlabel(
            f"x ({self.tr.params['length_unit_name']})", fontsize=12
        )
        ax_trajectories.set_ylabel(
            f"y ({self.tr.params['length_unit_name']})", fontsize=12
        )

        plt.show()

    def drawHistogram(self, data, title=None):
        if title != None and type(title) == list:
            titles = []
            for x in title:
                tmp = "filter"
                if x["frame"] != None:
                    tmp += f", time:{x['frame']}/{self.tr.number_of_frames//self.tr.params['time_unit']}{self.tr.params['time_unit_name']}"
                else:
                    tmp += f", time:{self.tr.number_of_frames//self.tr.params['time_unit']}{self.tr.params['time_unit_name']}"
                if x["number"] != None:
                    tmp += f", num:{x['number']}/{self.tr.number_of_individuals}"
                else:
                    tmp += f", num:{self.tr.number_of_individuals}"
                titles.append(tmp)

        f, a = plt.subplots(3, 2)
        a = a.ravel()
        for idx, ax in enumerate(a):
            ax.hist(
                data[idx],
                bins=40,
                histtype="stepfilled",
                color="steelblue",
                edgecolor="none",
            )
            if title != None and type(title) == list:
                ax.set_title(titles[idx], fontsize=6)
            # ax.set_xlim(15, 35)
            # ax.set_ylim(0, 30)
        plt.show()
