#!/bin/bash

source devel/setup.bash

pkill -9 rqt_qui

roscd one_dof_arm

roslaunch one_dof_arm control_robot.launch




