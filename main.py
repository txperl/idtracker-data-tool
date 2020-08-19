from idtckr import *

# 读取并初始化数据
test = idtcker("./ori/zebrafish_trajectories/10/1/trajectories_wo_gaps.npy")
# test.load()  # px、px/frame、px/frame^2
test.load(length=(50, "cm"), time="1s")  # cm、cm/s、cm/s^2

# 过滤
# test.filter(type="traj")
test.filter(type="traj", frame=("s", 0, 18), number=(0, 8), circle=None)
# test.out(test.data["filter"], "./test_traj.csv", ("frame", "x", "y"))

# 求平均速度
ave = test.average(
    type="spee",
    data=test.data["filter"],
    split=[{"frame": ("s", 0, 10)}, {"frame": ("s", 10, 20)},],
)
test.out(ave, "./10s_ave_speed.csv", ("block", "ave", "unit"))

# 求最小圆
cir = test.smestCircle(test.data["filter"])
test.out(cir, "./test_cir.csv", ("x", "y", "r"))

# 轨迹
test.drawTraj(test.data["filter"])

# 轨迹动画
test.drawTrajAni(test.data["filter"])

################

# circles = []
# titles = []
# for i in range(0, test.tr.number_of_frames // test.tr.params["time_unit"], 100)[:6]:
#     test.filter(type="traj", frame=("s", i, i + 100))
#     cir = test.smestCircle(test.data["filter"])
#     tmp = []
#     for x in cir:
#         tmp.append(x[2])
#     circles.append(tmp)
#     titles.append(test._tmp["filter"].copy())
# test.drawHistogram(circles, titles)
