#!/usr/bin/env python3
import rospy
import gazebo_ros
from gazebo_msgs.srv import ApplyJointEffort, JointRequest, GetJointProperties
from gazebo_msgs.msg import LinkStates
from std_msgs.msg import Float32
import time
import math
import tf
import dynamic_reconfigure.client


class ArmControlNode():

    def __init__(self, joint_name = "bear_joint"):

        self.joint_name = joint_name

        rospy.Subscriber("/robot_control/reference", Float32, self.ref_cb)

        self.control_pub = rospy.Publisher("/robot_control/control_signal", Float32, queue_size=100)
        self.ang_pub = rospy.Publisher("/robot_control/joint_angle", Float32, queue_size=100)
        self.error_pub = rospy.Publisher("/robot_control/error", Float32, queue_size=100)

        rospy.wait_for_service('/gazebo/apply_joint_effort')
        rospy.wait_for_service('/gazebo/clear_joint_forces')
        rospy.wait_for_service('/gazebo/get_joint_properties')

        self.effort_service = rospy.ServiceProxy('/gazebo/apply_joint_effort', ApplyJointEffort)
        self.clear_effort = rospy.ServiceProxy('/gazebo/clear_joint_forces', JointRequest)
        self.get_angle_srv = rospy.ServiceProxy('/gazebo/get_joint_properties', GetJointProperties)

        client = dynamic_reconfigure.client.Client("/OneDofArm_DynamicParameters", timeout=30, config_callback=self.param_callback)

        # initialization of default parameters
        self.ref_angle = 0
        self.Kp = 8.0
        self.Ki = 1.2
        self.Kd = 1.0
        self.windup_guard = 20
        self.lim_control = 700
        self.current_time = time.time()
        self.last_time = self.current_time
        self.PTerm = 0.0
        self.ITerm = 0.0
        self.DTerm = 0.0
        self.last_error = 0.0

    def ref_cb(self, msg):
        self.ref_angle = float(msg.data)
        
    def param_callback(self, config):
        c_type = float("{controller_type}".format(**config))
        if c_type == 0:
            self.Kp, self.Ki, self.Kd = float("{ss_Kp}".format(**config)), float("{ss_Ki}".format(**config)), float("{ss_Kd}".format(**config))
        elif c_type == 1:
            self.Kp, self.Ki, self.Kd = float("{tr_Kp}".format(**config)), float("{tr_Ki}".format(**config)), float("{tr_Kd}".format(**config))
        else:
            print("ERROR! Unknown Controller Type!!")

    def get_control_signal(self, feedback_value, setpoint, current_time=None):
        
        error = setpoint - feedback_value

        self.current_time = time.time()
        delta_time = self.current_time - self.last_time
        delta_error = error - self.last_error  
        self.PTerm = self.Kp * error
        self.ITerm += error * delta_time

        if (self.ITerm < -self.windup_guard):
            self.ITerm = -self.windup_guard
        elif (self.ITerm > self.windup_guard):
            self.ITerm = self.windup_guard

        self.DTerm = 0.0
        if delta_time > 0:
            self.DTerm = delta_error / delta_time

        # Remember last time and last error for next calculation
        self.last_time = self.current_time
        self.last_error = error

        self.output = self.PTerm + (self.Ki * self.ITerm) + (self.Kd * self.DTerm)
        self.output = max(-self.lim_control, min(self.lim_control, self.output))
        return self.output

    def make_effort(self):

        error = self.ref_angle - self.joint_angle
        effort = self.get_control_signal(self.joint_angle, self.ref_angle)
        self.error_pub.publish(error)
        self.control_pub.publish(effort)
        start_time = rospy.Duration.from_sec(0)
        duration = rospy.Duration.from_sec(0.1)
        return self.effort_service(self.joint_name, effort, start_time, duration)

    
    def clear_effort(self):
        return self.clear_effort(self.joint_name)

    def get_joint_angle(self):
        self.joint_angle = math.degrees(self.get_angle_srv(self.joint_name).position[0])
        self.joint_der = math.degrees(self.get_angle_srv(self.joint_name).rate[0])
        self.ang_pub.publish(self.joint_angle)
        return self.joint_angle


if __name__ == '__main__':

    rospy.init_node("arm_controller_node")
    controller = ArmControlNode()
    while not rospy.is_shutdown():
        
        controller.get_joint_angle()

        controller.make_effort()
