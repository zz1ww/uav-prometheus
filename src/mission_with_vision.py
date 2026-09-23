#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ============================================================================
# 无人机比赛任务主程序 —— 完整版（接入视觉闭环）
# ----------------------------------------------------------------------------
# 原文件名: body_xyz_pos_control222(1).py
#
# 功能: 按顺序执行 7 个比赛任务
#       起飞 -> 二维码识别 -> 绕障 -> 图片靶投放 -> 特殊靶投放
#       -> 穿越圆环 -> 按方向降落
#
# 与骨架版的区别:
#   - 订阅视觉话题: /best_class_name, /target_img1, /target_img2,
#                   /target_land, /uav1/spirecv/ellipse_detection
#   - 投放前判断目标类别是否匹配二维码信息
#   - 降落方向读取二维码解析结果 (targetland == 'left')
#
# 详见同目录 README.md
# ============================================================================

from math import cos, fabs, sin
import rospy
from prometheus_msgs.msg import UAVCommand, UAVControlState, UAVState
from std_msgs.msg import String, Int32
from spirecv_msgs.msg import TargetsInFrame
#阶段发布
current_stage = -1
pub = None
best_class_name = ""
target_img1 = ""
target_img2 = ""
target_land = ""
classname = ""
targetimg1 = ""
targetimg2 = ""
targetland = ""
cx=0
cy=0
safe_count=0
has_target = False
de_move=0.05

# 创建无人机相关数据变量
uav_control_state_sv = UAVControlState()
uav_command_pv = UAVCommand()
uav_state_sv = UAVState()
count = 0
move_count = 0
Pi = 3.1415926
detect_height=1.3

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

def best_class_cb(msg):
    global best_class_name
    best_class_name = msg.data

def target_img1_cb(msg):
    global target_img1
    target_img1 = msg.data

def target_img2_cb(msg):
    global target_img2
    target_img2 = msg.data

def target_land_cb(msg):
    global target_land
    target_land = msg.data

def target_callback(msg):
    global cx, cy, has_target

    if len(msg.targets) == 0:
        has_target = False
        return

    max_target = max(msg.targets, key=lambda t: t.w * t.h)

    cx = max_target.cx
    cy = max_target.cy
    has_target = True

def main():
    global count, move_count, velocity, angle_increment, circle_start_x, circle_start_y, circle_start_z
    global pub,classname ,targetimg1,targetimg2 ,targetland ,best_class_name ,target_img1,target_img2 ,target_land,cx,cy,safe_count,has_target,current_stage

    rospy.init_node('mav_control', anonymous=True)
    cmd_pub_flag = False
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

    rospy.Subscriber("/best_class_name", String, best_class_cb)
    rospy.Subscriber("/target_img1", String, target_img1_cb)
    rospy.Subscriber("/target_img2", String, target_img2_cb)
    rospy.Subscriber("/target_land", String, target_land_cb)
    rospy.Subscriber("/uav1/spirecv/ellipse_detection", TargetsInFrame, target_callback, queue_size=1)

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
                    rospy.sleep(3)
                    current_stage=0
                    rospy.sleep(2)
                    targetimg1=target_img1
                    targetimg2=target_img2
                    targetland=target_land
                    rospy.loginfo(f"target_img1: {targetimg1}, target_img2: {targetimg2}, target_land: {targetland}")
                    getQRcode_done=True 
                    rospy.loginfo("Moving to QRcode")

            



            elif not getimg1_done:
                uav_command_pv.position_ref[0] = 1.8
                uav_command_pv.position_ref[1] = -1.6
                uav_command_pv.position_ref[2] = detect_height
                uav_command_pv.yaw_ref = 0
                uav_command_pv.Command_ID += 1
                UavCommandPb.publish(uav_command_pv)
                rospy.sleep(5)
                current_stage=1
                rospy.sleep(3)
                #判断，yes对准获取
                classname=best_class_name
                rospy.loginfo("img1 calss name:{classname}")
                rospy.loginfo("circle point ({cx},{cy})")
                if best_class_name in [targetimg1, targetimg2]:
                    rospy.loginfo("img1 put")
                    rospy.loginfo("circle point ({cx},{cy})")
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
                rospy.sleep(5)
                current_stage=2
                rospy.sleep(3)
                #判断，yes对准获取
                classname=best_class_name
                rospy.loginfo("img2 calss name:{classname}")
                rospy.loginfo("circle point ({cx},{cy})")
                if best_class_name in [targetimg1, targetimg2]:
                    rospy.loginfo("img2 put")
                    rospy.loginfo("circle point ({cx},{cy})")
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
                current_stage=3
                rospy.sleep(3)
                #判断，yes对准获取
                classname=best_class_name
                rospy.loginfo("img3 calss name:{classname}")
                rospy.loginfo("circle point ({cx},{cy})")
                if best_class_name in [targetimg1, targetimg2]:
                    rospy.loginfo("img3 put")
                    rospy.loginfo("circle point ({cx},{cy})")
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
                rospy.sleep(5)
                current_stage=4
                rospy.sleep(3)
                #判断，yes对准获取
                classname=best_class_name
                rospy.loginfo("img4 calss name:{classname}")
                rospy.loginfo("circle point ({cx},{cy})")
                if best_class_name in [targetimg1, targetimg2]:
                    rospy.loginfo("img4 put")
                    rospy.loginfo("circle point ({cx},{cy})")
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
                if targetland=='left':
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
                    rospy.loginfo("circle point ({cx},{cy})")
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
                    rospy.loginfo("circle point ({cx},{cy})")
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