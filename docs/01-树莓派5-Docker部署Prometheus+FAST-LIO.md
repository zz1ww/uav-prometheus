# 树莓派5上运行 Prometheus 和 Fast-LIO

## 1. 烧录系统

使用 **Raspberry Pi Imager**，选择 **Debian 12 (no desktop)**。

SSH 连接后操作。

## 2. 安装工具和 Docker

```bash
sudo apt update && sudo apt install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings

curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker $USER
exit
```

## 3. 拉取 Ubuntu 20.04 ARM 镜像（无桌面）

```bash
docker pull docker.1ms.run/library/ubuntu:20.04
# 打标签
docker tag docker.1ms.run/library/ubuntu:20.04 ubuntu:20.04
```

## 4. 创建容器

```bash
docker run -it --name ubuntu20 \
  --network host \
  --privileged \
  ubuntu:20.04 bash
```

### 容器内安装基础工具

```bash
apt update && apt install -y curl wget git vim nano sudo iproute2 dnsutils ca-certificates lsb-release iputils-ping net-tools tmux
```

## 5. 安装 ROS1 Noetic

```bash
wget http://fishros.com/install -O fishros && . fishros
```

## 6. 安装 Amov 的 Prometheus 平台

```bash
git clone https://gitee.com/amovlab/Prometheus.git
```

### 安装 prometheus_mavros

```bash
cd Prometheus/Scripts/installation/prometheus_mavros
chmod +x install_prometheus_mavros.sh
./install_prometheus_mavros.sh
```

打开新终端，测试是否安装成功：

```bash
roscd mavros
```

### 编译 Prometheus

```bash
cd Prometheus
chmod +x compile_*
./compile_all.sh
```

**注意**：`~/.bashrc` 添加路径，确认与自己的 Prometheus 路径一致。

## 7. 启动雷达

### Livox-SDK2

```bash
git clone https://github.com/Livox-SDK/Livox-SDK2.git
cd ./Livox-SDK2/
mkdir build
cd build
cmake .. && make -j2
sudo make install
```

### livox_ros_driver2 驱动（ROS1 Noetic）

```bash
cd livox_ws/src
git clone https://github.com/Livox-SDK/livox_ros_driver2.git
cd livox_ros_driver2
source /opt/ros/noetic/setup.sh
./build.sh ROS1
```

### 连接后运行

```bash
cd livox_ws
source devel/setup.bash
roslaunch livox_ros_driver2 rviz_MID360.launch
roslaunch livox_ros_driver2 msg_MID360.launch
```

## 8. MID360 配置

### 手动设置 IP

`ens34` 为网卡名称，用 `ip addr` 查看更改。

```bash
sudo ip addr add 192.168.1.5/24 dev ens34
```

> `192.168.1.5` 需与配置文件匹配，设置不同需在 `MID360_config.json` 里更改 `host_net_info`。

```bash
ping 192.168.1.1XX   # ping 通即完成连接，例：192.168.1.112
```

### 更改配置文件

```bash
vim src/livox_ros_driver2/config/MID360_config.json
# 修改雷达 IP（lidar_configs 处）
```

## 9. 启动流程

```bash
roslaunch livox_ros_driver2 msg_MID360.launch
roslaunch fast_lio mapping_mid360.launch
roslaunch mavros px4.launch
roslaunch prometheus_uav_control uav_control_main_indoor_mid360.launch
```

> 也可用下面脚本先运行 `start_all.sh`，然后在 4 个窗口分别跑 4 个 `run` 开头脚本。

---

## 脚本

以下脚本 `cat` 开头，直接粘贴到终端回车即可。

### 配网脚本

```bash
cat > ~/lidar_net.sh << 'EOF'
#!/bin/bash
IFACE="${1:-eth0}"
HOST_IP="${2:-192.168.1.5}"
LIDAR_IP="${3:-192.168.1.112}"
sudo ip addr add $HOST_IP/24 dev $IFACE 2>/dev/null
sudo ip link set $IFACE up
echo "→ IP: $HOST_IP/24 → $IFACE"
echo -n "→ Ping $LIDAR_IP ... "
ping -c 2 -W 1 $LIDAR_IP &>/dev/null && echo "通" || echo "不通"
EOF
chmod +x ~/lidar_net.sh
```

### 4 个启动脚本

```bash
cat > ~/run_livox.sh << 'EOF'
#!/bin/bash
source /opt/ros/noetic/setup.bash
source ~/Prometheus/devel/setup.bash
cd ~/livox_ws && source devel/setup.bash
roslaunch livox_ros_driver2 msg_MID360.launch
EOF

cat > ~/run_fastlio.sh << 'EOF'
#!/bin/bash
source /opt/ros/noetic/setup.bash
source ~/Prometheus/devel/setup.bash
roslaunch fast_lio mapping_mid360.launch
EOF

cat > ~/run_mavros.sh << 'EOF'
#!/bin/bash
source /opt/ros/noetic/setup.bash
source ~/Prometheus/devel/setup.bash
roslaunch mavros px4.launch
EOF

cat > ~/run_uav.sh << 'EOF'
#!/bin/bash
source /opt/ros/noetic/setup.bash
source ~/Prometheus/devel/setup.bash
roslaunch prometheus_uav_control uav_control_main_indoor_mid360.launch
EOF

chmod +x ~/run_livox.sh ~/run_fastlio.sh ~/run_mavros.sh ~/run_uav.sh
```

### Tmux 一键启动脚本

```bash
cat > ~/start_all.sh << 'SCRIPT'
#!/bin/bash
tmux kill-session -t prometheus 2>/dev/null
tmux new-session -d -s prometheus -n livox
tmux send-keys -t prometheus:1 "source /opt/ros/noetic/setup.bash && source ~/Prometheus/devel/setup.bash && cd ~/livox_ws && source devel/setup.bash && echo 'livox 就绪'" Enter
tmux new-window -t prometheus -n fastlio
tmux send-keys -t prometheus:2 "source /opt/ros/noetic/setup.bash && source ~/Prometheus/devel/setup.bash && echo 'fastlio 就绪'" Enter
tmux new-window -t prometheus -n mavros
tmux send-keys -t prometheus:3 "source /opt/ros/noetic/setup.bash && source ~/Prometheus/devel/setup.bash && echo 'mavros 就绪'" Enter
tmux new-window -t prometheus -n uav_ctrl
tmux send-keys -t prometheus:4 "source /opt/ros/noetic/setup.bash && source ~/Prometheus/devel/setup.bash && echo 'uav_ctrl 就绪'" Enter
tmux new-window -t prometheus -n term
tmux send-keys -t prometheus:5 "echo '备用终端就绪'" Enter
tmux select-window -t prometheus:1
tmux attach -t prometheus
SCRIPT
chmod +x ~/start_all.sh
```

---

## 其他问题

### wstool 未找到

```bash
apt install -y python3-wstool
```

### rosdep 未初始化

```bash
sudo rosdep init
rosdep update
```

> 可使用装 ROS 用的网址脚本来装 rosdep，然后运行 `rosdep update`。

### geographic_msgs 缺失

```bash
apt install -y ros-noetic-geographic-msgs
```

### 代理设置（使用热点时，翻墙并允许局域网连接，替换端口即可）

```bash
echo 'alias proxyon="export http_proxy=http://10.45.230.208:10811; export https_proxy=http://10.45.230.208:10811; echo 代理已开启"' >> ~/.bashrc
echo 'alias proxyoff="unset http_proxy; unset https_proxy; echo 代理已关闭"' >> ~/.bashrc
source ~/.bashrc
# proxyon 开启代理 / proxyoff 关闭代理
```

### Prometheus 编译卡死

```bash
cat compile_all.sh
# 找到卡住的模块编译命令，后面加 -j1 或 -j2 单独运行
```

### 关闭仿真模式

```bash
sed -i 's|sim_mode" default="true"|sim_mode" default="false"|' /root/Prometheus/Modules/uav_control/launch/uav_control_main_indoor_mid360.launch
```

### 关闭雷达 Rviz 可视化

```bash
sed -i 's|"rviz" default="true"|"rviz" default="false"|' ~/Prometheus/Modules/FAST_LIO/launch/mapping_mid360.launch 2>/dev/null
```

> 有桌面且性能有余可开启。

---

## 参考链接

- [Prometheus 配置官方文档](https://wiki.amovlab.com/public/prometheus-wiki/%E5%BF%AB%E9%80%9F%E4%B8%8A%E6%89%8B/Prometheus%E4%BB%BF%E7%9C%9F%E7%8E%AF%E5%A2%83%E9%85%8D%E7%BD%AE_Ubuntu/Prometheus%E9%85%8D%E7%BD%AE.html)
