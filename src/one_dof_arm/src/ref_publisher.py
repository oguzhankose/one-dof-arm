#!/usr/bin/env python3
import rospy
from std_msgs.msg import Float32
import time
import math
import numpy as np
import dynamic_reconfigure.client


class ReferenceSignalPublisher():
    def __init__(self, topic_name="/robot_control/reference"):

        self.ref_pub = rospy.Publisher("/robot_control/reference", Float32, queue_size=100)
        client = dynamic_reconfigure.client.Client("/OneDofArm_DynamicParameters", 
                                        timeout=30, config_callback=self.param_callback)

        # Initial values of parameters
        self.reference_type = "step"
        self.ref_angle = 0.0
        self.sin_ref_gain = 1.0
        self.sin_ref_f = 1.0
        self.start = start = time.time()

    def param_callback(self, config):
        if '0' == "{reference_type}".format(**config):
            self.reference_type = "step" 
        else:
            self.reference_type = "trajectory" 
            
        self.ref_angle = float("{ref_angle}".format(**config))
        self.sin_ref_gain = float("{sin_ref_gain}".format(**config))
        self.sin_ref_f = float("{sin_ref_f}".format(**config))

        #print(self.reference_type, self.ref_angle, self.sin_ref_gain, self.sin_ref_f)

    def pub_ref(self):
        if self.reference_type == "step":
            self.ref_pub.publish(self.ref_angle)
        elif self.reference_type == "trajectory":
            u_t = np.sin(2*np.pi*self.sin_ref_f*(time.time()-self.start))*self.sin_ref_gain
            self.ref_pub.publish(u_t)
        else:
            print("ERROR! Unknown Reference Type!!")

if __name__ == '__main__':
    
    rospy.init_node("ref_publisher_node")
    publisher = ReferenceSignalPublisher()
    rate = rospy.Rate(50)

    while not rospy.is_shutdown():
        publisher.pub_ref()
        rate.sleep()
