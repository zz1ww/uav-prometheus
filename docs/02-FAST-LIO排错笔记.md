# FAST-LIO 无人机系统排错笔记

> 时间：2026-07-31 晚（实验室）
> 系统：树莓派 5 / Docker 容器 / ROS1 Noetic / Prometheus + FAST-LIO + Livox Mid-360
> 本次解决两个问题：**① 里程计被判定 Invalid ② FAST-LIO 内存暴涨崩溃**

---

## 问题一：Odom Status 一直 [ Invalid ]，控制状态卡 INIT

### 现象

FAST-LIO 里程计稳定输出 10Hz（`/Odometry` 正常），uav_control 却显示：

```
MID360_pos [X Y Z] : +0.01 [ m ] +0.04 [ m ] -0.00 [ m ]
Odom Status        : [ Invalid ]          ← 问题在这
CONTROL_STATE      : [ INIT ]             ← 控制状态机卡死，拒绝起飞
```

### 排查过程

**第 1 步：确认数据链路是通的（排除"没数据"）**

```bash
rostopic hz /livox/lidar          # ✅ 10Hz，雷达点云正常
rostopic hz /Odometry             # ✅ 10Hz，FAST-LIO 正常
rostopic hz /uav1/mavros/odometry/in   # ✅ 7-8Hz，里程计送进 MAVROS
```

> 注意命名空间是 `/uav1/mavros/...`（带 uav1 前缀），直接查 `/mavros/...` 会查不到。

**第 2 步：翻源码，找 odom_valid 的判定逻辑**

```bash
grep -rn "Odom Status" /root/Prometheus/Modules/   # 找到 uav_estimator.cpp
```

关键代码（uav_estimator.cpp:1054-1060）：

```cpp
if (odom_state == 9 || odom_state == 5) {
    uav_state.odom_valid = true;
} else {
    uav_state.odom_valid = false;
}
```

→ 只有 `odom_state` 等于 5 或 9 才算有效，其他全 Invalid。

**第 3 步：找 odom_state 是怎么定的（check_uav_odom 函数）**

MID360 相关的无效分支有两个：

```cpp
// 超时 → return 1（收不到里程计）
// MID360 协方差错误 → return 11
if (location_source == prometheus_msgs::UAVState::MID360 && covariance_error)
    return 11;
```

**第 4 步：看协方差是否异常（排除 return 11）**

```bash
rostopic echo -n1 /Odometry/pose/covariance
```

结果：数值全是 1e-5~1e-6 量级，正常 → **排除协方差问题**。

**第 5 步：看 covariance_error 的定义（uav_estimator.cpp:395-404）**

```cpp
bool pose_error = (pose_cov[0] > 0.05) || (pose_cov[7] > 0.05) || (pose_cov[14] > 0.05);
bool twist_error = (twist_cov[0] > 0.2) || (twist_cov[7] > 0.2);
covariance_error = pose_error || twist_error;
```

阈值是 0.05 / 0.2，实测协方差远小于阈值 → 确认不是这条。

**第 6 步：发现还有一个 vision_pose_error（uav_estimator.cpp:380-388）**

```cpp
if ((pos_vision - pos_px4).norm() > maximum_vel_error_for_vision) {
    vision_pose_error = true;   // ← 视觉/激光位姿 vs 飞控位姿 差太远
}
```

**第 7 步：对比 FAST-LIO 和飞控的位置（决定性一步）**

```bash
rostopic echo -n1 /Odometry/pose/pose/position          # FAST-LIO
rostopic echo -n1 /uav1/mavros/local_position/pose/pose/position   # 飞控
```

结果：

```
FAST-LIO: z = 0.00 m
飞控:     z = 4.55 m    ← 差了 4.5 米！
```

→ **Z 轴差了 4.5 米，触发 vision_pose_error，里程计被判定无效。**

### 找到原因

**飞控的高度是"海拔"，雷达的高度是"相对原点"，坐标系基准不同：**

- PX4 飞控的高度来自**气压计**，测的是绝对气压 → 海拔高度。实验室海拔约 4.5m，开机就是 4.55m
- FAST-LIO 的 Z 是雷达上电时的位置 → 地面 = 0m
- uav_control 直接拿两者相减判误差，4.5m 远超阈值 → Invalid

**雪上加霜：气压计被拆过。** 检查发现：

```bash
rostopic echo -n1 /uav1/mavros/imu/pressure
# WARNING: topic does not appear to be published yet  ← 气压计没数据！
```

没有气压计 = 飞控高度只能靠 IMU 积分 = **Z 会持续漂移**（实测重启后 -0.1m → 一分钟漂到 -1.2m）。这就是为什么 X/Y 对齐得很好（都是里程计给的）但 Z 永远对不上。

### 解决方案

1. **重启飞控（已解决本次问题）**：飞控上电静止时会把当前高度设为基准（归零），与 FAST-LIO 的 Z=0 对齐 → Odom Status 变 Valid
2. **换场地/每次上电后**：静止放几秒再启动 FAST-LIO，让飞控完成高度初始化
3. **长期方案（三选一）**：
   - 装回气压计（最省事，一劳永逸）
   - 用激光测距仪（hrlv_ez4）当高度源，配 PX4 参数 `SENS_EN_XXX`
   - 让 FAST-LIO 的 Z 作为飞控高度源（通过 vision_pose 喂给飞控，目前 uav_control 已经在往 `/uav1/mavros/vision_pose/pose` 发）

---

## 问题二：FAST-LIO 运行中崩溃（std::bad_alloc）

### 现象

拿着无人机模拟姿态时，FAST-LIO 窗口报：

```
terminate called after throwing an instance of 'std::bad_alloc'
what():  std::bad_alloc
```

随后 roslaunch 报 `required SIGKILL`，Odometry 断流。

### 排查过程

**第 1 步（踩坑）：崩溃后看内存——被误导**

```bash
free -h    # 显示 used 只有 311M，available 3.6G，内存充足
```

→ **假象**：崩溃后进程已死、内存已释放，所以看内存永远充足。**必须看崩溃瞬间的内存。**

**第 2 步（正确做法）：挂监控循环，抓崩溃瞬间**

```bash
while true; do date +%T; free -h | grep Mem; ps -o pid,rss,cmd -C laserMapping 2>/dev/null; echo ---; sleep 2; done
```

监控输出（节选）：

```
00:23:38  used 2.6G        ← 内存开始涨
00:25:09  used 3.6G 可用只剩 307M   ← 逼近极限
00:25:26  used 3.6G        ← 峰值，吃满
00:25:29  used 212M        ← FAST-LIO 崩了，内存瞬间释放
```

→ **铁证：FAST-LIO 内存从 2.6G 一路涨到 3.6G 吃满后崩溃。**

### 找到原因

**FAST-LIO 的体素地图（voxel map）无限累积：**

- 拿着无人机到处晃 → 雷达不断扫到新区域 → 地图不断膨胀 → 内存持续上涨
- 涨到 4G 上限（树莓派 5 总内存）→ 分配失败 → `std::bad_alloc` → 崩溃
- 飞行时正常航线地图增长慢；**拿着乱晃增长最快**，最容易触发

### 解决方案

1. **每次飞行前重启 FAST-LIO**（地图从零开始，内存回到 ~600M，短时飞行够用）——零成本先保命
2. **别长时间拿着乱晃**——正常飞行/小范围移动内存增长很慢
3. **治本：限制地图大小**——找 FAST-LIO 配置文件（`config/*.yaml`），调小地图范围/体素参数（如 `voxel_size`、关闭 `map_accumulate`），防止无限增长
4. **监控保底**：飞行时挂一条 `free -h` 循环，看内存异常上涨就提前重启

---

## 顺带发现：雷达时间戳偏移 ~10 秒

排查时发现雷达点云时间戳比系统时间晚约 10 秒（`/livox/lidar/header/stamp` 落后 `/Odometry/header/stamp`），且 `MID360_config.json` 里没有任何 time/sync 字段（`grep -i -E "btms|time|sync"` 返回 exit=1）。

**结论：livox 驱动默认不开时间同步，自己维持时间基准（每次上电从 0 累积）。** 因为 FAST-LIO 用自己的时间处理点云，这个偏移不影响定位，暂时不用管。

---

## 附录：本次排错命令速查

```bash
# ---------- 数据链路检查 ----------
rostopic hz /livox/lidar                    # 雷达点云频率（应 10Hz）
rostopic hz /Odometry                       # FAST-LIO 里程计（应 10Hz）
rostopic hz /uav1/mavros/odometry/in        # 送进 MAVROS 的里程计
rostopic hz /uav1/mavros/odometry/out       # MAVROS 转发后的里程计

# ---------- 位置/协方差对比 ----------
rostopic echo -n1 /Odometry/pose/pose/position              # FAST-LIO 位置
rostopic echo -n1 /uav1/mavros/local_position/pose/pose/position  # 飞控位置
rostopic echo -n1 /Odometry/pose/covariance                 # 里程计协方差

# ---------- 传感器状态 ----------
rostopic echo -n1 /uav1/mavros/imu/pressure                 # 气压计（无输出=气压计失效）
rostopic echo -n1 /uav1/mavros/distance_sensor/hrlv_ez4_pub # 激光测距仪

# ---------- 源码定位 ----------
grep -rn "Odom Status" /root/Prometheus/Modules/            # 找判定打印位置
grep -rn "covariance_error" /root/Prometheus/Modules/uav_control/src/uav_estimator.cpp
sed -n '380,410p'  /root/Prometheus/Modules/uav_control/src/uav_estimator.cpp   # 看判定代码
sed -n '1040,1070p' /root/Prometheus/Modules/uav_control/src/uav_estimator.cpp  # 看状态打印

# ---------- 内存监控（崩溃现场取证） ----------
while true; do date +%T; free -h | grep Mem; ps -o pid,rss,cmd -C laserMapping 2>/dev/null; echo ---; sleep 2; done

# ---------- 进程清理 ----------
ps aux | grep laserMapping | grep -v grep   # 确认进程状态
```

## 经验总结（下次直接避坑）

1. **崩溃后看内存会被骗**——进程死了内存早释放了，要挂监控看崩溃瞬间
2. **飞控 Z 是海拔、雷达 Z 是相对原点**——两者天然差一个常数，起飞前先对齐（重启飞控/静止初始化）
3. **气压计拆了**——飞控高度靠 IMU 裸积分会持续漂移，这是系统级隐患，装回气压计或让 FAST-LIO 当高度源是长期方向
4. **所有 Prometheus 话题都带 `/uav1` 前缀**——查主题先 `rostopic list` 看真实名字
5. **飞行前重启 FAST-LIO**——地图归零，防内存崩溃，顺手也保证定位基准干净
