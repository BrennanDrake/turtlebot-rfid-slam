#!/usr/bin/env python3
# Copyright 2026 Brennan Drake
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""ROS 2 node: parse PN5180 serial lines and publish ``rfid_msgs/RfidDetection``."""

import re
import rclpy
from geometry_msgs.msg import PoseWithCovariance
from rclpy.node import Node
import serial
from std_msgs.msg import String

from rfid_msgs.msg import RfidDetection

# R<reader>,<hex_uid>  e.g. R0,E00401005E231B26
_RE_DETECT = re.compile(r'^R(\d+),([0-9A-Fa-f]+)\s*$')
# X<reader>
_RE_REMOVE = re.compile(r'^X(\d+)\s*$')


class RfidSerialPublisher(Node):
    """Reads machine-parseable lines from Arduino and publishes structured detections."""

    def __init__(self):
        super().__init__('rfid_serial_publisher')
        self.declare_parameter('serial_port', '/dev/ttyUSB0')
        self.declare_parameter('serial_baud', 115200)
        self.declare_parameter('timer_period_sec', 0.05)

        port = self.get_parameter('serial_port').value
        baud = int(self.get_parameter('serial_baud').value)
        timer_period = float(self.get_parameter('timer_period_sec').value)
        if timer_period <= 0.0:
            timer_period = 0.05

        self._pub_detection = self.create_publisher(RfidDetection, 'rfid/detections', 10)
        self._pub_string = self.create_publisher(String, 'rfid', 10)
        self._last_tag_id = ''
        self.timer = self.create_timer(timer_period, self.timer_callback)

        self.ser = serial.Serial(port, baud, timeout=1)
        self.get_logger().info('RFID serial open: %s @ %d' % (port, baud))

    def timer_callback(self):
        if self.ser.in_waiting > 0:
            raw = self.ser.readline()
            line = raw.decode('utf-8', errors='replace').strip()
            if not line or line == 'READY':
                pass
            else:
                self._process_line(line)

        msg = String()
        msg.data = self._last_tag_id
        self._pub_string.publish(msg)

    def _process_line(self, line: str) -> None:
        m = _RE_DETECT.match(line)
        if m:
            reader_index = int(m.group(1))
            tag_id = m.group(2).upper()
            self._last_tag_id = tag_id
            det = RfidDetection()
            det.header.stamp = self.get_clock().now().to_msg()
            det.header.frame_id = ''
            det.tag_id = tag_id
            det.reader_index = reader_index
            det.present = True
            det.pose = PoseWithCovariance()
            self._pub_detection.publish(det)
            self.get_logger().info('RFID detect reader=%d tag=%s' % (reader_index, tag_id))
            return

        m = _RE_REMOVE.match(line)
        if m:
            reader_index = int(m.group(1))
            self._last_tag_id = ''
            det = RfidDetection()
            det.header.stamp = self.get_clock().now().to_msg()
            det.header.frame_id = ''
            det.tag_id = ''
            det.reader_index = reader_index
            det.present = False
            det.pose = PoseWithCovariance()
            self._pub_detection.publish(det)
            self.get_logger().info('RFID remove reader=%d' % reader_index)
            return

        self.get_logger().debug('RFID unparsed line: %s' % line)


def main(args=None):
    rclpy.init(args=args)
    node = RfidSerialPublisher()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
