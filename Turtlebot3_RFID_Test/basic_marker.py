#!/usr/bin/env python3

#Origin: The Construct Advanced Rviz Markers Class

import rospy
from visualization_msgs.msg import Marker
from visualization_msgs.msg import MarkerArray
from geometry_msgs.msg import Point


class MarkerBasics(object):

    def __init__(self):
        self.marker_arraypub = rospy.Publisher('/marker_array', MarkerArray, queue_size=1)
        self.rate = rospy.Rate(1)
        self.init_marker(index=0,z_val=0)
        self.marker_array = MarkerArray()    

    def init_marker(self,index=0, z_val=0):
        self.marker_object = Marker()
        self.marker_object.header.frame_id = "base_footprint"
        self.marker_object.header.stamp    = rospy.get_rostime()
        self.marker_object.ns = "haro"
        self.marker_object.id = index
        self.marker_object.type = Marker.CUBE
        self.marker_object.action = Marker.ADD
        
        my_point = Point()
        my_point.z = .12
        my_point.x = -.15
        my_point.y = .12
        self.marker_object.pose.position = my_point
        

        self.marker_object.pose.orientation.x = 0
        self.marker_object.pose.orientation.y = 0
        self.marker_object.pose.orientation.z = 0
        self.marker_object.pose.orientation.w = 1.0
        self.marker_object.scale.x = .1
        self.marker_object.scale.y = .025
        self.marker_object.scale.z = .1
    
        self.marker_object.color.r = 0.0
        self.marker_object.color.g = 0.0
        self.marker_object.color.b = 1.0
        # This has to be, otherwise it will be transparent
        self.marker_object.color.a = 1.0
            
        # If we want it for ever, 0, otherwise seconds before desapearing
        self.marker_object.lifetime = rospy.Duration(0)
    
    def start(self):
        while not rospy.is_shutdown():
            self.marker_array.markers.append(self.marker_object)
            self.marker_arraypub.publish(self.marker_array)
            self.rate.sleep()
   

if __name__ == '__main__':
    rospy.init_node('marker_basic_node', anonymous=True)
    markerbasics_object = MarkerBasics()
    try:
        markerbasics_object.start()
    except rospy.ROSInterruptException:
        pass
