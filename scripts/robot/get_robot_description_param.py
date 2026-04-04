#!/usr/bin/env python3
"""Fetch robot_description from /robot_state_publisher via the parameter service.

Use when `ros2 param get ... robot_description` fails with
"sequence size exceeds remaining buffer" (huge string).

Usage (robot container or Pi, bringup running):
  source /colcon_ws/install/setup.bash
  ./scripts/robot/get_robot_description_param.py -o /tmp/rd_param.xml
  grep -B2 burger_base.stl /tmp/rd_param.xml

Optional: ROS_DOMAIN_ID must match the robot.
"""
from __future__ import annotations

import argparse
import sys

import rclpy
from rcl_interfaces.srv import GetParameters
from rclpy.node import Node


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '-o',
        '--output',
        metavar='FILE',
        help='Write XML to this file (default: print size to stderr only if -q)',
    )
    parser.add_argument(
        '-q',
        '--quiet',
        action='store_true',
        help='With -o, only print byte count to stderr',
    )
    args = parser.parse_args()

    rclpy.init()
    node = Node('get_robot_description_param')
    cli = node.create_client(GetParameters, '/robot_state_publisher/get_parameters')
    if not cli.wait_for_service(timeout_sec=15.0):
        print(
            'ERROR: /robot_state_publisher/get_parameters not available. '
            'Is bringup running in this ROS graph?',
            file=sys.stderr,
        )
        node.destroy_node()
        rclpy.shutdown()
        return 1

    req = GetParameters.Request()
    req.names = ['robot_description']
    future = cli.call_async(req)
    rclpy.spin_until_future_complete(node, future)
    result = future.result()
    if result is None or not result.values:
        print('ERROR: empty GetParameters response', file=sys.stderr)
        node.destroy_node()
        rclpy.shutdown()
        return 1

    s = result.values[0].string_value
    if not s:
        print('ERROR: robot_description string empty', file=sys.stderr)
        node.destroy_node()
        rclpy.shutdown()
        return 1

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as out:
            out.write(s)
        if not args.quiet:
            print(f'Wrote {len(s)} bytes to {args.output}', file=sys.stderr)
    else:
        sys.stdout.write(s)

    node.destroy_node()
    rclpy.shutdown()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
