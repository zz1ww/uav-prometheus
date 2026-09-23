#!/bin/bash
# ============================================================
# tmux 一键启动：雷达 / FAST-LIO / MAVROS / UAV控制
# ------------------------------------------------------------
# 原项目脚本只会开好 4 个窗口并 source 环境，
# 然后需要人工在每个窗口跑 run_xxx.sh。
# 此处改进为：直接在每个窗口里执行对应的 roslaunch，
# 真正做到"一键启动"。
# ============================================================

SESSION=prometheus
WS_LIVOX=~/livox_ws

# ROS 环境的通用 source 前缀
ROS_SETUP="source /opt/ros/noetic/setup.bash && \
           source ~/Prometheus/devel/setup.bash && \
           echo '环境就绪'"

# 清理旧会话
tmux kill-session -t $SESSION 2>/dev/null

# ---------- 窗口1: 雷达驱动 ----------
tmux new-session -d -s $SESSION -n livox
tmux send-keys -t $SESSION:1 \
  "source /opt/ros/noetic/setup.bash && \
   source ~/Prometheus/devel/setup.bash && \
   cd $WS_LIVOX && source devel/setup.bash && \
   roslaunch livox_ros_driver2 msg_MID360.launch" Enter

# 等雷达起来
sleep 5

# ---------- 窗口2: FAST-LIO ----------
tmux new-window -t $SESSION -n fastlio
tmux send-keys -t $SESSION:2 \
  "source /opt/ros/noetic/setup.bash && \
   source ~/Prometheus/devel/setup.bash && \
   roslaunch fast_lio mapping_mid360.launch" Enter

# 等 FAST-LIO 初始化
sleep 5

# ---------- 窗口3: MAVROS ----------
tmux new-window -t $SESSION -n mavros
tmux send-keys -t $SESSION:3 \
  "source /opt/ros/noetic/setup.bash && \
   source ~/Prometheus/devel/setup.bash && \
   roslaunch mavros px4.launch" Enter

sleep 5

# ---------- 窗口4: UAV 控制 ----------
tmux new-window -t $SESSION -n uav_ctrl
tmux send-keys -t $SESSION:4 \
  "source /opt/ros/noetic/setup.bash && \
   source ~/Prometheus/devel/setup.bash && \
   roslaunch prometheus_uav_control uav_control_main_indoor_mid360.launch" Enter

# ---------- 窗口5: 备用终端 ----------
tmux new-window -t $SESSION -n term
tmux send-keys -t $SESSION:5 "echo '备用终端就绪（可用于 rostopic / 内存监控）'" Enter

# 默认停在雷达窗口
tmux select-window -t $SESSION:1

echo "已启动 5 个窗口，正在 attach..."
tmux attach -t $SESSION
