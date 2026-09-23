#!/bin/bash
# Livox Mid-360 网络配置 + 连通性检查
# 用法: ./lidar_net.sh [网卡] [主机IP] [雷达IP]
# 例:   ./lidar_net.sh eth0 192.168.1.5 192.168.1.112

IFACE="${1:-eth0}"
HOST_IP="${2:-192.168.1.5}"
LIDAR_IP="${3:-192.168.1.112}"

sudo ip addr add $HOST_IP/24 dev $IFACE 2>/dev/null
sudo ip link set $IFACE up

echo "→ IP: $HOST_IP/24 → $IFACE"
echo -n "→ Ping $LIDAR_IP ... "
ping -c 2 -W 1 $LIDAR_IP &>/dev/null && echo "通" || echo "不通"
