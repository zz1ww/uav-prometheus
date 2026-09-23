#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ============================================================================
# 无人机比赛任务主程序 —— 骨架版（纯航点飞行）
# ----------------------------------------------------------------------------
# 原文件名: body_xyz_pos_control333.py
#
# 功能: 按预设坐标点顺序飞行的骨架流程
#
# 注意: 本版本为早期实现
#   - 无视觉话题订阅，投放不判断目标类别
#   - 投放机构代码仅有注释占位 (#打开投放装置)
#   - 降落方向判断为 if 1: 硬编码
#
# 完整版见 mission_with_vision.py
# ============================================================================

from math import cos, fabs, sin
import rospy
from prometheus_msgs.msg import UAVCommand, UAVControlState, UAVState

# 创建无人机相关数据变量
uav_control_state_sv = UAVControlState()
uav_command_pv = UAVCommand()
uav_state_sv = UAVState()
count = 0
move_count = 0
Pi = 3.1415926
detect_height=1.3
put_height=0.7

# 创建圆形跟踪的相关变量
circular_time = 20
control_rate = 30
radius = 1.1
velocity = 0.0
angle_increment = 0.0

# 记录画圆开始点
circle_start_x = 0.0
circle_start_y = 0.0
circle_start_z = 0.0

def get_circular_property(circular_time, control_rate, radius):
    global w, velocity, angle_increment
    w = (2 * Pi) / circular_time
    velocity = radius * w
    angle_increment = w / control_rate

def uavStateCb(msg):
    global uav_state_sv
    uav_state_sv = msg

def uavControlStateCb(msg):
    global uav_control_state_sv
    uav_control_state_sv = msg

def main():
    global count, move_count, velocity, angle_increment, circle_start_x, circle_start_y, circle_start_z
    
    rospy.init_node('mav_control', anonymous=True)
    cmd_pub_flag = False
    move_done = False
    circle_done = False
    getQRcode_done=False
    getimg1_done=False
    getimg2_done=False
    getimg3_done=False
    getimg4_done=False
    getspT_done =False
    crosscir_done=False
    return0_done=False
    return1_done=False
    
    UavCommandPb = rospy.Publisher("/uav1/prometheus/command", UAVCommand, queue_size=10)
    rospy.Subscriber("/uav1/prometheus/control_state", UAVControlState, uavControlStateCb)
    rospy.Subscriber("/uav1/prometheus/state", UAVState, uavStateCb)
    rate = rospy.Rate(control_rate)
    
    while not rospy.is_shutdown():
        # rospy.spinOnce()
        
        if uav_control_state_sv.control_state == UAVControlState.COMMAND_CONTROL:
            if not cmd_pub_flag:
                # 起飞
                uav_command_pv.header.stamp = rospy.Time.now()
                uav_command_pv.header.frame_id = 'ENU'
                uav_command_pv.Agent_CMD = 1
                uav_command_pv.Command_ID = 1
                UavCommandPb.publish(uav_command_pv)
                cmd_pub_flag = True
                rospy.loginfo("Takeoff command published")
                
            elif not getQRcode_done:
                # 等待起飞完成
                takeoff_height = rospy.get_param('/uav_control_main_1/control/Takeoff_height', 1.0)
                if fabs(uav_state_sv.position[2] - takeoff_height) <= 0.1:
                    uav_command_pv.header.stamp = rospy.Time.now()
                    uav_command_pv.header.frame_id = "ENU"
                    uav_command_pv.Agent_CMD = UAVCommand.Move
                    uav_command_pv.Move_mode = UAVCommand.XYZ_POS
                    uav_command_pv.position_ref[0] = 1.8
                    uav_command_pv.position_ref[1] = 0
                    uav_command_pv.position_ref[2] = detect_height
                    uav_command_pv.yaw_ref = 0
                    uav_command_pv.Command_ID += 1
                    UavCommandPb.publish(uav_command_pv)
                    rospy.sleep(5)
                    getQRcode_done=True 
                    rospy.loginfo("Moving to QRcode")

            
         

            elif not getimg1_done:
                uav_command_pv.header.stamp = rospy.Time.now()
                uav_command_pv.header.frame_id = "ENU"
                uav_command_pv.Agent_CMD = UAVCommand.Move
                uav_command_pv.Move_mode = UAVCommand.XYZ_POS
                uav_command_pv.position_ref[0] = 1.8
                uav_command_pv.position_ref[1] = -1.6
                uav_command_pv.position_ref[2] = detect_height
                uav_command_pv.yaw_ref = 0
                uav_command_pv.Command_ID += 1
                UavCommandPb.publish(uav_command_pv)
                rospy.sleep(5)
                getimg1_done=True 
                rospy.loginfo("Moving to img1")

            elif not getimg2_done:
                uav_command_pv.header.stamp = rospy.Time.now()
                uav_command_pv.header.frame_id = "ENU"
                uav_command_pv.Agent_CMD = UAVCommand.Move
                uav_command_pv.Move_mode = UAVCommand.XYZ_POS
                uav_command_pv.position_ref[0] = 3.6
                uav_command_pv.position_ref[1] = -1.6
                uav_command_pv.position_ref[2] = detect_height
                uav_command_pv.yaw_ref = 0
                uav_command_pv.Command_ID += 1
                UavCommandPb.publish(uav_command_pv)
                rospy.sleep(4)
                #投放
                #下降
                uav_command_pv.position_ref[0] = 3.6
                uav_command_pv.position_ref[1] = -1.6
                uav_command_pv.position_ref[2] = put_height
                uav_command_pv.yaw_ref = 0
                uav_command_pv.Command_ID += 1
                UavCommandPb.publish(uav_command_pv)
                rospy.sleep(3)
                #打开投放装置

                #投放完毕上升
                uav_command_pv.position_ref[0] = 3.6
                uav_command_pv.position_ref[1] = -1.6
                uav_command_pv.position_ref[2] = detect_height
                uav_command_pv.yaw_ref = 0
                uav_command_pv.Command_ID += 1
                UavCommandPb.publish(uav_command_pv)
                rospy.sleep(4)

                getimg2_done=True 
                rospy.loginfo("Moving to img2")

            elif not getimg3_done:
                uav_command_pv.header.stamp = rospy.Time.now()
                uav_command_pv.header.frame_id = "ENU"
                uav_command_pv.Agent_CMD = UAVCommand.Move
                uav_command_pv.Move_mode = UAVCommand.XYZ_POS
                uav_command_pv.position_ref[0] = 3.6
                uav_command_pv.position_ref[1] = -1.6
                uav_command_pv.position_ref[2] = detect_height
                uav_command_pv.yaw_ref = 1.5708
                uav_command_pv.Command_ID += 1
                UavCommandPb.publish(uav_command_pv)
                rospy.sleep(3)
                uav_command_pv.position_ref[0] = 1.8
                uav_command_pv.position_ref[1] = 1.6
                uav_command_pv.position_ref[2] = detect_height
                uav_command_pv.yaw_ref = 1.5708
                uav_command_pv.Command_ID += 1
                UavCommandPb.publish(uav_command_pv)
                rospy.sleep(3)
                uav_command_pv.position_ref[0] = 1.8
                uav_command_pv.position_ref[1] = 1.6
                uav_command_pv.position_ref[2] = detect_height
                uav_command_pv.yaw_ref = 0
                uav_command_pv.Command_ID += 1
                UavCommandPb.publish(uav_command_pv)
                rospy.sleep(5)
                getimg3_done=True 
                rospy.loginfo("Moving to img3")

            elif not getimg4_done:
                uav_command_pv.header.stamp = rospy.Time.now()
                uav_command_pv.header.frame_id = "ENU"
                uav_command_pv.Agent_CMD = UAVCommand.Move
                uav_command_pv.Move_mode = UAVCommand.XYZ_POS
                uav_command_pv.position_ref[0] = 3.6
                uav_command_pv.position_ref[1] = 1.6
                uav_command_pv.position_ref[2] = detect_height
                uav_command_pv.yaw_ref = 0
                uav_command_pv.Command_ID += 1
                UavCommandPb.publish(uav_command_pv)
                rospy.sleep(4)
                #投放
                #下降
                uav_command_pv.position_ref[0] = 3.6
                uav_command_pv.position_ref[1] = 1.6
                uav_command_pv.position_ref[2] = put_height
                uav_command_pv.yaw_ref = 0
                uav_command_pv.Command_ID += 1
                UavCommandPb.publish(uav_command_pv)
                rospy.sleep(3)
                #打开投放装置

                #投放完毕上升
                uav_command_pv.position_ref[0] = 3.6
                uav_command_pv.position_ref[1] = 1.6
                uav_command_pv.position_ref[2] = detect_height
                uav_command_pv.yaw_ref = 0
                uav_command_pv.Command_ID += 1
                UavCommandPb.publish(uav_command_pv)
                rospy.sleep(4)
                getimg4_done=True 
                rospy.loginfo("Moving to img4")

            elif not getspT_done:
                uav_command_pv.header.stamp = rospy.Time.now()
                uav_command_pv.header.frame_id = "ENU"
                uav_command_pv.Agent_CMD = UAVCommand.Move
                uav_command_pv.Move_mode = UAVCommand.XYZ_POS
                uav_command_pv.position_ref[0] = 6
                uav_command_pv.position_ref[1] = 1
                uav_command_pv.position_ref[2] = detect_height
                uav_command_pv.yaw_ref = 0
                uav_command_pv.Command_ID += 1
                UavCommandPb.publish(uav_command_pv)
                rospy.sleep(5)
                #投放
                #下降
                uav_command_pv.position_ref[0] = 6
                uav_command_pv.position_ref[1] = 1
                uav_command_pv.position_ref[2] = put_height
                uav_command_pv.yaw_ref = 0
                uav_command_pv.Command_ID += 1
                UavCommandPb.publish(uav_command_pv)
                rospy.sleep(3)
                #打开投放装置

                #投放完毕上升
                uav_command_pv.position_ref[0] = 6
                uav_command_pv.position_ref[1] = 1
                uav_command_pv.position_ref[2] = detect_height
                uav_command_pv.yaw_ref = 0
                uav_command_pv.Command_ID += 1
                UavCommandPb.publish(uav_command_pv)
                rospy.sleep(4)
                getspT_done=True 
                rospy.loginfo("Moving to Special Target")

            elif not crosscir_done:
                uav_command_pv.header.stamp = rospy.Time.now()
                uav_command_pv.header.frame_id = "ENU"
                uav_command_pv.Agent_CMD = UAVCommand.Move
                uav_command_pv.Move_mode = UAVCommand.XYZ_POS
                uav_command_pv.position_ref[0] = 6
                uav_command_pv.position_ref[1] = 1
                uav_command_pv.position_ref[2] = detect_height
                uav_command_pv.yaw_ref = -1.5708
                uav_command_pv.Command_ID += 1
                UavCommandPb.publish(uav_command_pv)
                rospy.sleep(3)
                uav_command_pv.position_ref[0] = 6
                uav_command_pv.position_ref[1] = 1
                uav_command_pv.position_ref[2] = 1.6
                uav_command_pv.yaw_ref = -1.5708
                uav_command_pv.Command_ID += 1
                UavCommandPb.publish(uav_command_pv)
                rospy.sleep(3)
                uav_command_pv.position_ref[0] = 6
                uav_command_pv.position_ref[1] = -0.6
                uav_command_pv.position_ref[2] = 1.6
                uav_command_pv.yaw_ref = -1.5708
                uav_command_pv.Command_ID += 1
                UavCommandPb.publish(uav_command_pv)
                rospy.sleep(3)
                rospy.loginfo("Moving to cross circle 0")

                #对准圆心检测

                #穿过
                uav_command_pv.header.stamp = rospy.Time.now()
                uav_command_pv.header.frame_id = "BODY"
                uav_command_pv.Agent_CMD = UAVCommand.Move
                uav_command_pv.Move_mode = UAVCommand.XYZ_POS_BODY
                uav_command_pv.position_ref[0] = 1.2
                uav_command_pv.position_ref[1] = 0.0
                uav_command_pv.position_ref[2] = 0.0
                uav_command_pv.yaw_ref = 0.0
                uav_command_pv.Command_ID += 1
                UavCommandPb.publish(uav_command_pv)
                rospy.sleep(3)
                crosscir_done=True 
                rospy.loginfo("Moving to cross circle 1")


            elif not return0_done:
                uav_command_pv.header.stamp = rospy.Time.now()
                uav_command_pv.header.frame_id = "ENU"
                uav_command_pv.Agent_CMD = UAVCommand.Move
                uav_command_pv.Move_mode = UAVCommand.XYZ_POS
                uav_command_pv.position_ref[0] = 6
                uav_command_pv.position_ref[1] = -2.2
                uav_command_pv.position_ref[2] = 1.6
                uav_command_pv.yaw_ref = -1.5708
                uav_command_pv.Command_ID += 1
                UavCommandPb.publish(uav_command_pv)
                rospy.sleep(3)
                uav_command_pv.position_ref[0] = 6
                uav_command_pv.position_ref[1] = -2.3
                uav_command_pv.position_ref[2] = 1.6
                uav_command_pv.yaw_ref = 3.14159
                uav_command_pv.Command_ID += 1
                UavCommandPb.publish(uav_command_pv)
                rospy.sleep(3)
                uav_command_pv.position_ref[0] =3
                uav_command_pv.position_ref[1] = -2.3
                uav_command_pv.position_ref[2] = 1.6
                uav_command_pv.yaw_ref = 3.14159
                uav_command_pv.Command_ID += 1
                UavCommandPb.publish(uav_command_pv)
                rospy.sleep(3)
                uav_command_pv.position_ref[0] = 1.8
                uav_command_pv.position_ref[1] = 0
                uav_command_pv.position_ref[2] = 1.6
                uav_command_pv.yaw_ref = 3.14159
                uav_command_pv.Command_ID += 1
                UavCommandPb.publish(uav_command_pv)
                rospy.sleep(3)
                uav_command_pv.position_ref[0] = 1.8
                uav_command_pv.position_ref[1] = 0
                uav_command_pv.position_ref[2] = detect_height
                uav_command_pv.yaw_ref = 3.14159
                uav_command_pv.Command_ID += 1
                UavCommandPb.publish(uav_command_pv)
                rospy.sleep(3)
                return0_done=True
                rospy.loginfo("Moving to return point 0")

            elif not return1_done:
                if 1:
                    uav_command_pv.header.stamp = rospy.Time.now()
                    uav_command_pv.header.frame_id = "ENU"
                    uav_command_pv.Agent_CMD = UAVCommand.Move
                    uav_command_pv.Move_mode = UAVCommand.XYZ_POS
                    uav_command_pv.position_ref[0] = 0
                    uav_command_pv.position_ref[1] = 1.6
                    uav_command_pv.position_ref[2] = detect_height
                    uav_command_pv.yaw_ref = 3.14159
                    uav_command_pv.Command_ID += 1
                    UavCommandPb.publish(uav_command_pv)
                    
                    rospy.sleep(5)
                    #检测是否在降落圆心

                    return1_done=True
                    rospy.loginfo("Moving to land point")

                else:
                    uav_command_pv.header.stamp = rospy.Time.now()
                    uav_command_pv.header.frame_id = "ENU"
                    uav_command_pv.Agent_CMD = UAVCommand.Move
                    uav_command_pv.Move_mode = UAVCommand.XYZ_POS
                    uav_command_pv.position_ref[0] = 0
                    uav_command_pv.position_ref[1] = -1.6
                    uav_command_pv.position_ref[2] = detect_height
                    uav_command_pv.yaw_ref = 3.14159
                    uav_command_pv.Command_ID += 1
                    UavCommandPb.publish(uav_command_pv)
                    rospy.sleep(5)
                   
                    #检测是否在降落圆心

                    return1_done=True
                    rospy.loginfo("Moving to land point")

                

                
            else:
                # 降落
                uav_command_pv.header.stamp = rospy.Time.now()
                uav_command_pv.header.frame_id = "ENU"
                uav_command_pv.Agent_CMD = 3
                uav_command_pv.Command_ID += 1
                UavCommandPb.publish(uav_command_pv)
                rospy.loginfo("[circular trajectory control] demo completed")
                rospy.signal_shutdown("shutdown time")
        else:
            if cmd_pub_flag:
                rospy.logfatal("Unknown error! tutorial_demo aborted")
            else:
                rospy.logwarn("Wait for UAV to enter [COMMAND_CONTROL] MODE")
                rospy.sleep(2)
        rate.sleep()
    rospy.spin()

if __name__ == "__main__":
    try:
        main()
    except rospy.ROSInterruptException:
        pass