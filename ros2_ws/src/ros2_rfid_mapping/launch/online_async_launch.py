"""
Launch slam_toolbox in asynchronous online mapping mode.

Typical deployment: run this on the **control server** (or a powerful machine) while the robot
publishes ``/scan``, TF, and odometry over the ROS 2 network. Set ``ROS_DOMAIN_ID`` the same on
robot and server so nodes discover each other.

This file only starts ``async_slam_toolbox_node``; robot drivers live in ``turtlebot3_bringup``.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, TimerAction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time')
    slam_params_file = LaunchConfiguration('slam_params_file')

    declare_use_sim_time_argument = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation/Gazebo clock')
    declare_slam_params_file_cmd = DeclareLaunchArgument(
        'slam_params_file',
        default_value=os.path.join(
            get_package_share_directory('ros2_rfid_mapping'),
            'config',
            'mapper_params_online_async.yaml'),
        description='Full path to the ROS 2 YAML for slam_toolbox parameters')
    declare_slam_activate_delay = DeclareLaunchArgument(
        'slam_activate_delay',
        default_value='3.0',
        description='Seconds to wait before lifecycle configure+activate on slam_toolbox',
    )

    # slam_toolbox async node: processes laser scans and publishes map -> odom TF and /map.
    start_async_slam_toolbox_node = Node(
        parameters=[
            slam_params_file,
            {'use_sim_time': use_sim_time}
        ],
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name='slam_toolbox',
        output='screen')

    slam_lifecycle_activate = TimerAction(
        period=LaunchConfiguration('slam_activate_delay'),
        actions=[
            ExecuteProcess(
                cmd=[
                    'bash',
                    '-c',
                    (
                        'ros2 lifecycle set /slam_toolbox configure --no-daemon && '
                        'sleep 0.5 && ros2 lifecycle set /slam_toolbox activate --no-daemon'
                    ),
                ],
                output='screen',
            ),
        ],
    )

    ld = LaunchDescription()

    ld.add_action(declare_use_sim_time_argument)
    ld.add_action(declare_slam_params_file_cmd)
    ld.add_action(declare_slam_activate_delay)
    ld.add_action(start_async_slam_toolbox_node)
    ld.add_action(slam_lifecycle_activate)

    return ld
