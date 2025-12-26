#! /usr/bin/env python3

import time
import rospy
from std_msgs.msg import String
from geometry_msgs.msg import Twist

class Rfid_Test():
    def __init__(self):
        self.pub = rospy.Publisher("/cmd_vel", Twist, queue_size=1)
        self.cmd = Twist()
        self.rate = rospy.Rate(10)
        self.rfid_sub = rospy.Subscriber("/rfid", String, self.rfid_handler)
        self.tag_id = ""
        self.ctrl_c = False

    def shutdownhook(self):
        self.cmd.angular.z = 0
        self.cmd.linear.x = 0
        self.ctrl_c = True

    def rfid_handler(self, data):
        self.tag_id = data.data

    def control(self):
        while not rospy.is_shutdown():
            if self.tag_id == "00:0:0000000000":
                self.cmd.linear.x = 0
                self.cmd.angular.z = 0
                self.pub.publish(self.cmd)
            elif self.tag_id == "E0:4:10888CE126":
                self.cmd.linear.x = 0.5
                self.cmd.angular.z = 0
                self.pub.publish(self.cmd)
                time.sleep(1)
            elif self.tag_id == "E0:4:10888CA1D7":
                self.cmd.linear.x = 0
                self.cmd.angular.z = 0.5
                self.pub.publish(self.cmd)
                time.sleep(1)
            else:
                rospy.loginfo("Initializing")


if __name__ == "__main__":
    rospy.init_node("rfid_control_node")
    rfid_robo_obj = Rfid_Test()
    rfid_robo_obj.control()
