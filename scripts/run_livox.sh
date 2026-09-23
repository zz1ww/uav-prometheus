#!/bin/bash
source /opt/ros/noetic/setup.bash
source ~/Prometheus/devel/setup.bash
cd ~/livox_ws && source devel/setup.bash
roslaunch livox_ros_driver2 msg_MID360.launch
