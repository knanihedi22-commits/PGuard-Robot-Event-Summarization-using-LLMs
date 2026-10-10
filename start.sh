#!/bin/bash
source /opt/ros/humble/setup.bash
python3 fake_publisher.py &
sleep 2
python3 subscriber.py
