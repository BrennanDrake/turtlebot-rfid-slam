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

"""ROS 2 node: read RFID tag IDs from serial and publish on topic ``rfid``."""

import rclpy
from rclpy.node import Node
import serial
from std_msgs.msg import String


class MinimalPublisher(Node):
    """Timer-driven publisher: polls serial and republishes the last seen tag id on each tick."""

    def __init__(self):
        super().__init__('minimal_publisher')
        # Default device matches common USB-serial layout on TurtleBot setups; override via params.
        self.declare_parameter('serial_port', '/dev/ttyUSB0')
        self.declare_parameter('serial_baud', 115200)
        self.declare_parameter('timer_period_sec', 0.05)

        port = self.get_parameter('serial_port').value
        baud = int(self.get_parameter('serial_baud').value)
        timer_period = float(self.get_parameter('timer_period_sec').value)
        if timer_period <= 0.0:
            timer_period = 0.05

        self.publisher_ = self.create_publisher(String, 'rfid', 10)
        self.timer = self.create_timer(timer_period, self.timer_callback)

        # Last payload published; keeps behavior stable when no new bytes arrive (same as repeating
        # the previous line) and avoids use-before-assign on the first timer tick.
        self._last_tag_id = ''

        # pyserial: timeout=1 so readline() returns after up to 1s if incomplete (rare here).
        self.ser = serial.Serial(port, baud, timeout=1)
        self.get_logger().info('RFID serial open: %s @ %d' % (port, baud))

    def timer_callback(self):
        # Drain at most one line per tick to avoid blocking the executor if the reader floods.
        if self.ser.in_waiting > 0:
            raw = self.ser.readline()
            self._last_tag_id = raw.decode('utf-8').rstrip()
            self.get_logger().info('RFID tag: "%s"' % self._last_tag_id)

        msg = String()
        msg.data = self._last_tag_id
        self.publisher_.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = MinimalPublisher()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
