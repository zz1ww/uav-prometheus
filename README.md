# 微型无人机自主飞行系统（PX4 + Prometheus + Livox Mid-360）

> 一套室内无 GNSS 环境下自主完成**起飞 → 视觉识别 → 绕障 → 精准投放 → 穿环 → 定向降落**全流程的四旋翼无人机系统。
> 参赛项目：**第二十八届中国机器人及人工智能大赛 · 微型无人机赛项**
>
> 平台：Pixhawk 4（PX4 1.15）+ Jetson Xavier NX ｜ 系统：Ubuntu 20.04 + ROS1 Noetic
> 定位：Livox Mid-360 + FAST-LIO2 ｜ 上层：Prometheus ｜ 视觉：SpireCV + YOLOv5 + OpenCV

---

## 一、项目做了什么

在 9m × 6m × 3m 的室内场地中，无人机全自主完成 7 个串行任务，任务之间通过**二维码传递信息**形成闭环：

```
① 携带物块起飞(1.3m)
        │
        ▼
② 识别二维码 ──▶ 解析出【图片类别1 / 图片类别2 / 降落方向】
        │              │
        ▼              │
③ 顺时针绕障飞行        │  (半径1.2m, 40s)
        │              │
        ▼              │
④ 投放小物块 → 图片靶 ◀─┤  (按二维码类别选靶, 0.7m释放)
        │              │
        ▼              │
⑤ 投放大物块 → 特殊靶   │  (红蓝信号灯靶)
        │              │
        ▼              │
⑥ 穿越随机位置圆环      │  (正前方相机对准, 1.6m)
        │              │
        ▼              │
⑦ 按二维码方向降落 ◀────┘  (left/right 选降落区)
```

**核心设计思想**：二维码是整条任务链的**信息源** —— 它在第 2 步产生「两个图片类别 + 一个降落方向」，被第 4/5 步（选哪个靶投放）和第 7 步（往哪个方向降）消费。任务之间不是简单串行，而是**有数据依赖**的。

---

## 二、系统架构

采用「感知层 — 决策层 — 执行层」三层结构：

```
┌──────────────────────── 感知层 ────────────────────────┐
│  Livox Mid-360(顶部)    RealSense D455(机头前下10°)     │
│     └ 3D点云/定位          └ 下视:二维码/图片靶/特殊靶   │
│                            └ 前视:圆环检测               │
│  Pixhawk 4 内置 IMU + 气压计                            │
└───────────────────────┬────────────────────────────────┘
                        │ ROS Topic
┌───────────────────────▼──── 决策层 (Jetson Xavier NX) ──┐
│  FAST-LIO2 ──▶ 实时位姿                                 │
│  OpenCV QRCodeDetector ──▶ 任务信息                     │
│  SpireCV 椭圆检测 ──▶ 目标圆心(topic)                   │
│  YOLOv5(cifar100.pt) ──▶ 图片靶分类                     │
│  任务状态机 ──▶ 位置/速度指令                           │
└───────────────────────┬────────────────────────────────┘
                        │ MAVROS
┌───────────────────────▼──── 执行层 ─────────────────────┐
│  Pixhawk 4(PX4 1.15) ──▶ 电调 ──▶ 电机                  │
│  舵机投放机构(3通道) ──▶ 物块释放                        │
└─────────────────────────────────────────────────────────┘
```

**分层控制**：
- 板载机（Jetson）负责**高层决策**：任务规划、指令生成
- 飞控（Pixhawk 4）负责**底层控制**：姿态解算、动力输出
- 起飞/悬停/投放/降落用**位置控制**；绕障/穿环用**速度控制**

---

## 三、硬件配置

| 部件 | 型号 | 关键参数 |
|---|---|---|
| 飞控 | Pixhawk 4 | PX4 1.15，双 IMU 冗余 |
| 板载计算机 | Jetson Xavier NX 16GB | Ubuntu 20.04 + ROS Noetic |
| 激光雷达 | Livox Mid-360 | 40m / 360°，机身顶部中心，减震支架 |
| 双目相机 | Intel RealSense D455 | 机头前下 10° 倾角 |
| 电池 | 4S 5200mAh | 16.8V / 60C |
| 电调 | 好盈 XROTOR 40A | DShot600 |
| 电机 | 2212 kv980 + 7×4.5" 三叶桨 | 单轴最大推力 1.8kg |
| 机架 | 330 模具 | X 型对称布局 |
| 投放装置 | 舵机拨杆式（PLA 3D 打印） | 3 通道独立舵机，PWM 50Hz |

**实测数据：**

| 指标 | 数值 |
|---|---|
| 整机重量 | **1850 g** |
| 轴距 | **330 mm** |
| 悬停续航 | **8 分 30 秒** |
| 全流程任务飞行 | **4 分 20 秒** |
| 满载连续飞行成功率 | **10 次中 9 次** |
| 定位误差 | **< 5 cm** |
| 投放响应时间 | **约 200 ms** |

**实物与场地照片**（完整 18 张见 [`reports/images/`](reports/images/README.md)）：

| | |
|---|---|
| [整机轴距测量](reports/images/01-轴距测量_卷尺量330mm.jpeg) | [Pixhawk 4 飞控](reports/images/04-Pixhawk4飞控实物.jpeg) |
| [Jetson Xavier NX](reports/images/05-Jetson-Xavier-NX开发板.jpeg) | [Livox Mid-360 安装位置](reports/images/08-Livox-Mid360雷达机腹安装.jpeg) |
| [舵机拨杆式投放装置](reports/images/14-投放装置_舵机拨杆.jpeg) | [电调 / 电机实物](reports/images/13-电机_X2212_KV980.jpeg) |
| [比赛场地全景](reports/images/15-比赛场地实景_全景.png) | **[场地坐标示意图](reports/images/16-场地坐标示意图.png)** |

---

## 四、任务实现要点

| 任务 | 技术实现 | 关键参数 |
|---|---|---|
| ① 携带物块起飞 | 遥控切 Offboard → 板载机发自主起飞指令 → 垂直缓慢上升 | 高度 1.3m，上升 0.5m/s，悬停误差 ±10cm |
| ② 识别二维码 | `cv2.QRCodeDetector` 检测解码 → 解析「类别1,类别2,方向」 | 悬停 1.3m，分辨率 1280×720，30s 超时 |
| ③ 顺时针绕障 | 速度控制沿圆周轨迹飞行，实时算 X/Y 速度分量 | 半径 1.2m，高 1.3m，约 40s，半圈处转向 180° |
| ④ 投放至图片靶 | SpireCV 检测圆环轮廓 → 发布圆心 topic → 裁剪图像 → YOLOv5 分类 → 视觉闭环微调 → 下降释放 | 检测 1.5m，投放 0.7m，下降 0.3m/s |
| ⑤ 投放至特殊靶 | SpireCV 椭圆检测定位圆心 → 微调 → 下降释放大物块 | 检测 1.3m，投放 0.7m |
| ⑥ 穿越圆环 | 正前方相机检测圆环中心 → 动态调整航向与横向偏移 → 对准后直线穿越 | 高 1.6m，速度 0.8m/s |
| ⑦ 定向降落 | 按二维码 left/right 选点 → SpireCV 精定位微调 → 匀速下降 | 下降 0.3m/s，误差 ±10cm，10cm 处闭锁电机 |

**视觉模块的改造（关键工作）**：
修改开源项目 **SpireCV** 的椭圆检测代码，使其额外**发布圆环/靶标圆心位置的 ROS 话题**，从而让控制节点能拿到目标像素坐标做视觉闭环。这是图像识别与飞行控制之间的关键桥梁 —— 原版 SpireCV 只做检测可视化，不对外提供位置接口。

---

## 五、目录结构

```
.
├── README.md
├── docs/                                    # 项目文档（精华所在）
│   ├── 00-原始部署流程（虚拟机+板载机）.md        # 第一版方案：原生安装
│   ├── 01-树莓派5-Docker部署Prometheus+FAST-LIO.md  # 第二版方案：容器化复刻 ★
│   ├── 02-FAST-LIO排错笔记.md                  # 两个深度排障案例 ★
│   ├── 03-PyQt地面站学习路线.md                 # 地面站开发技术储备
│   └── 04-容器化说明.md                        # 为什么用容器 + 代价与收益
├── src/
│   ├── mission_with_vision.py               # 任务主程序（完整版，接视觉闭环）★
│   ├── mission_waypoint_only.py             # 任务主程序（骨架版，纯航点）
│   └── kf_1d_example.py                     # 一维卡尔曼滤波教学示例
├── config/
│   ├── px4_params_1.12.3.params             # PX4 参数备份（历史版本）
│   ├── px4_params_1.13.params
│   ├── px4_params_1.15.params               # ★ 实际使用版本
│   └── px4_fmu-v5_default-1.15.4.px4        # PX4 固件
├── scripts/
│   ├── lidar_net.sh                         # 雷达配网 + 连通性检查
│   ├── run_livox.sh / run_fastlio.sh        # 各模块单独启动
│   ├── run_mavros.sh / run_uav.sh
│   ├── start_all.sh                         # tmux 一键启动全部模块
│   └── watch_mem.sh                         # FAST-LIO 内存监控
├── reports/
│   ├── 技术报告_终版.docx                     # 比赛技术报告（完整版）
│   ├── 技术报告_提交版.pdf                     # 提交用（含图）
│   └── images/                              # 从 docx 导出的 18 张插图（按内容重命名）
└── hardware/
    ├── Pixhawk4引脚定义.pdf
    ├── QGC地面站教学无人机使用教程.pdf
    └── 优象科技光流激光使用手册.zip
```

---

## 六、两条部署路线（项目的重要背景）

本项目**不是一次性做完的**，中途经历了硬件故障与方案重建：

```
第一版：板载计算机原生部署
   Jetson Xavier NX + Ubuntu 20.04 + ROS Noetic
   从源码编译 Prometheus
        │
        │  ✗ 板载计算机损坏
        ▼
第二版：树莓派 5 + Docker 容器化复刻
   Debian 12 宿主 + Ubuntu 20.04 ARM 容器
   导入预编译镜像，绕开重新编译
```

| | 第一版（原生） | 第二版（容器） |
|---|---|---|
| 硬件 | Jetson Xavier NX | 树莓派 5 |
| 环境安装 | 源码编译（数小时，易卡死） | `docker import` 镜像（数分钟） |
| 依赖获取 | 需挂代理 | 换国内镜像源 |
| 多窗口管理 | 手动开 4 个终端 | tmux 一键 `start_all.sh` |
| 恢复成本 | 重装重编 | 导入镜像 |

**容器化的核心价值**：环境即镜像 —— 换硬件时不必重新编译 Prometheus（ARM 平台重编代价极大），几分钟即可恢复整套环境。

**但容器也带来了代价**（详见 `docs/04-容器化说明.md`）：
- 树莓派内存有限 → FAST-LIO 体素地图无限累积 → 内存吃满崩溃（`std::bad_alloc`）
- 无桌面环境 → 必须关闭 RViz 可视化
- 硬件访问需 `--network host --privileged`

---

## 七、重点技术记录

### 7.1 FAST-LIO 排障（`docs/02`）

两个有代表性的问题，都做到了**从现象到根因的完整定位**：

**问题一：里程计被判定 Invalid，控制状态卡在 INIT**

- 现象：`/Odometry` 稳定 10Hz，但 `uav_control` 显示 `Odom Status: [Invalid]`
- 排查：逐层排除（数据链路 → 源码 `odom_valid` 判定 → 协方差分支 → 发现 `vision_pose_error` 分支）
- 根因：**飞控高度是气压海拔（约 4.55m），FAST-LIO 的 Z 是相对原点（0.00m）**，两者相差 4.5m，触发位姿误差判据
- 加剧因素：**气压计已拆除**，飞控高度只能靠 IMU 积分，Z 持续漂移
- 解决：飞控上电静止时完成高度初始化归零；长期方案是装回气压计或用激光测距仪做高度源

**问题二：FAST-LIO 运行中崩溃（`std::bad_alloc`）**

- 现象：拿着无人机模拟姿态时 FAST-LIO 崩溃，`roslaunch` 报 `required SIGKILL`
- 关键教训：**崩溃后看 `free -h` 会被误导** —— 进程已死、内存早已释放，显示"内存充足"
- 正确做法：挂监控循环抓崩溃瞬间，实测记录到内存 `2.6G → 3.6G 吃满 → 崩溃 → 释放 212M`
- 根因：**FAST-LIO 体素地图无限累积**，拿着到处晃时地图膨胀最快
- 解决：每次飞行前重启 FAST-LIO；长期方案是限制地图范围/体素参数

### 7.2 容器化迁移（`docs/01`、`docs/04`）

完整记录了树莓派 + Docker 复刻过程，包括：
- Docker 安装与镜像源配置
- 容器创建（`--network host --privileged` 的原因）
- ROS Noetic + Prometheus 安装
- Livox Mid-360 网络配置与驱动编译
- 关键启动参数调整（关仿真、关 RViz）
- 编译卡死、rosdep 未初始化、geographic_msgs 缺失等坑的处理

---

## 八、已知问题与改进方向

### 代码层面（客观记录）

| 问题 | 说明 | 改进方向 |
|---|---|---|
| **同步依赖 `rospy.sleep()`** | 主程序用固定睡眠时间（3s/5s）等待动作完成，无反馈校验；实际耗时变化时会导致时序错乱 | 改为监听到位状态（位置误差 < 阈值）再进入下一阶段 |
| **坐标硬编码** | 目标点坐标以魔法数字散落全文件 | 抽成参数或 YAML 配置 |
| **重复代码多** | 每个任务的指令发布逻辑重复十余次 | 抽取 `move_to(x, y, z, yaw)` 函数封装 |
| **状态机实现粗糙** | 用一组布尔标志（`xxx_done`）串联任务 | 改为显式状态机（或行为树） |
| **投放机构未接入** | 骨架版 `mission_waypoint_only.py` 中投放代码只有注释占位 | 完整版 `mission_with_vision.py` 已接视觉判断 |

> `src/` 下保留了**两个版本**：`mission_waypoint_only.py` 是纯航点骨架（投放动作未接），`mission_with_vision.py` 是接入视觉闭环与二维码方向的完整版。**对照两个文件可以清楚看到功能的演进过程。**

### 系统层面

| 问题 | 影响 | 方向 |
|---|---|---|
| 气压计缺失 | 飞控高度靠 IMU 积分会漂移 | 装回气压计 / 用激光测距仪做高度源 |
| 树莓派算力有限 | FAST-LIO 地图大时内存崩溃 | 限制地图大小；或换回算力更强的板载机 |
| 雷达时间戳偏移 | 点云时间戳比系统时间晚约 10s | 不影响 FAST-LIO（自带时间基准），可暂不处理；如需多传感器融合则要开硬件同步 |

---

## 九、技术栈总结

```
飞控        PX4 1.15 (Pixhawk 4)
通信        MAVROS / MAVLink (波特率 921600)
中间件      ROS1 Noetic
上层框架    Prometheus (amovlab)
定位        FAST-LIO2 + Livox Mid-360
视觉        OpenCV (QRCodeDetector) + SpireCV (椭圆检测) + YOLOv5 (cifar100.pt)
部署        树莓派5 + Docker (Debian 12 宿主 / Ubuntu 20.04 ARM 容器)
仿真        Gazebo (Prometheus 自带)
地面站      QGroundControl
```

---

## 十、相关项目

本项目的技术底座（Livox Mid-360 + FAST-LIO 激光 SLAM）与另一套**地面 AGV 小车**项目同源：

| | 本项目（空中） | AGV 项目（地面） |
|---|---|---|
| 载体 | 四旋翼 | 差速小车 |
| 系统 | ROS1 Noetic | ROS2 Humble |
| 控制 | PX4 + MAVROS | Arduino 电机驱动 |
| 上层 | Prometheus | Nav2 + OpenTCS (VDA5050) |
| 定位 | FAST-LIO2 | FAST-LIO + 3D ICP 重定位 |
| 部署 | 树莓派5 + Docker | 机载 Linux 原生 |

**同一套「Livox Mid-360 + FAST-LIO」激光 SLAM 方案，在陆地和空中两个载体上都完成了落地** —— 一份传感器与算法资产支撑两种形态的机器人。

---

## 附：快速上手

```bash
# 1. 导入容器镜像
cat prometheus-image.tar | docker import - prometheus-image:latest

# 2. 启动容器（必须 host 网络 + 特权，才能访问雷达和串口）
docker run -it --name ubuntu20 --network host --privileged \
  prometheus-image:latest bash

# 3. 配置雷达网络
sudo ip addr add 192.168.1.5/24 dev eth0
ping 192.168.1.112

# 4. 一键启动四大模块（雷达/FAST-LIO/MAVROS/UAV控制）
~/start_all.sh
```

详细步骤见 `docs/01-树莓派5-Docker部署Prometheus+FAST-LIO.md`。
