#!/bin/bash

source devel/setup.bash

pkill -9 gzserver
pkill -9 gzclient

sleep 1

roslaunch one_dof_arm start_gazebo.launch




