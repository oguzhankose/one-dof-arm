#!/usr/bin/env python3

import rospy

from dynamic_reconfigure.server import Server
from dynamic_parameters.cfg import TutorialsConfig

def callback(config, level):
    ## do something with dynamic params
    return config

if __name__ == "__main__":
    rospy.init_node("Arm_Dynamic_Parameters", anonymous = False)

    srv = Server(TutorialsConfig, callback)
    rospy.spin()
