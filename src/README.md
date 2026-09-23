# 源码说明

> 原项目中两个主程序文件名为 `body_xyz_pos_control222(1).py` 和 `body_xyz_pos_control333.py`，
> **命名无法体现内容差异**。整理时按实际功能重命名，并在此说明区别。

---

## 两个版本的区别

两个文件是**同一套任务流程的两个演进阶段**，差异集中在「是否接入视觉闭环」：

| | `mission_waypoint_only.py` | `mission_with_vision.py` |
|---|---|---|
| 原文件名 | `body_xyz_pos_control333.py` | `body_xyz_pos_control222(1).py` |
| 话题订阅 | 无外部话题 | `/best_class_name`、`/target_img1`、`/target_img2`、`/target_land`、`/uav1/spirecv/ellipse_detection` |
| 投放判断 | **直接下降投放**（无判断） | **判断 `best_class_name in [target_img1, target_img2]` 后才投放** |
| 降落方向 | `if 1:` 硬编码（永远走同一分支） | `if targetland == 'left':` **真正读取二维码解析出的方向** |
| 视觉闭环微调 | 无 | 有（读取椭圆检测圆心做对准） |
| 投放机构代码 | **只有注释占位**（`#打开投放装置`） | 有实际逻辑 |

### 结论

- `mission_waypoint_only.py` 是**纯航点飞行的骨架版**：能按预设坐标点飞到各位置，但视觉信息未参与决策，投放动作也没接。
- `mission_with_vision.py` 是**接入视觉与二维码信息的完整版**：任务流程会根据识别结果动态决策。

**保留两个文件的价值**：可以清楚看到从「固定航点执行」到「视觉闭环决策」的功能演进过程。若只保留一份，应保留 `mission_with_vision.py`。

---

## 任务主程序的逻辑结构

两个文件都采用同一套结构：

```python
# 1. 等待 UAV 进入 COMMAND_CONTROL 模式
if uav_control_state_sv.control_state == UAVControlState.COMMAND_CONTROL:
    # 2. 用布尔标志串联 7 个任务阶段
    if not cmd_pub_flag:        # 起飞
    elif not getQRcode_done:    # 飞至二维码区 + 识别
    elif not getimg1_done:      # 飞至图片靶1
    elif not getimg2_done:      # 飞至图片靶2 + 投放
    elif not getimg3_done:      # 飞至图片靶3
    elif not getimg4_done:      # 飞至图片靶4 + 投放
    elif not getspT_done:       # 飞至特殊靶 + 投放
    elif not crosscir_done:     # 穿越圆环
    elif not return0_done:      # 返航
    elif not return1_done:      # 按方向选择降落点
    else:                       # 降落
```

**指令发布模式**（每个阶段重复）：

```python
uav_command_pv.header.stamp = rospy.Time.now()
uav_command_pv.header.frame_id = "ENU"          # 或 "BODY"
uav_command_pv.Agent_CMD  = UAVCommand.Move
uav_command_pv.Move_mode  = UAVCommand.XYZ_POS  # 或 XYZ_POS_BODY
uav_command_pv.position_ref[0] = x
uav_command_pv.position_ref[1] = y
uav_command_pv.position_ref[2] = z
uav_command_pv.yaw_ref = yaw
uav_command_pv.Command_ID += 1                  # 指令序号递增
UavCommandPb.publish(uav_command_pv)
```

> `Command_ID += 1` 是 Prometheus 的协议要求：每条新指令必须递增 ID，接收端据此判断是否为新指令。

---

## 已知代码问题（客观记录）

| 问题 | 位置 | 说明 |
|---|---|---|
| **`rospy.sleep()` 当同步手段** | 全文件 | 用固定睡眠（3s/5s）等待动作完成，无反馈校验。实际耗时变化（如电量低时飞得慢）会导致时序错乱 |
| **坐标硬编码** | `position_ref[0/1/2]` | 目标坐标以魔法数字散落全文，换场地需全改 |
| **重复代码多** | 各 `elif` 分支 | 同一指令发布模式复制十余次，应抽成 `move_to(x,y,z,yaw)` |
| **状态机粗糙** | 布尔标志串联 | 用 `xxx_done` 变量串联，非显式状态机，异常时难以回溯 |
| **异常处理缺失** | 无 try/except | 识别失败/通信中断时无降级逻辑（报告中的"超时跳过"机制未在此体现） |

这些是项目早期的实现方式，也是后续应当重构的方向。

---

## `kf_1d_example.py`

一维卡尔曼滤波教学示例（原文件名 `kf_example.py`）：
- 用「匀速模型」跟踪一个「匀加速运动」的目标，展示滤波效果
- 从定义协方差矩阵 P 开始，逐步实现，公式全部显式写出
- 用途：学习 ESKF（FAST-LIO 的核心滤波方法）的基础铺垫

> 与 FAST-LIO 的 ESKF 实现对照学习，是理解状态估计的入门材料。
