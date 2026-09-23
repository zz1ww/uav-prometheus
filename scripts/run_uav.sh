#!/bin/bash
source /opt/ros/noetic/setup.bash
source ~/Prometheus/devel/setup.bash
roslaunch prometheus_uav_control uav_control_main_indoor_mid360.launch
