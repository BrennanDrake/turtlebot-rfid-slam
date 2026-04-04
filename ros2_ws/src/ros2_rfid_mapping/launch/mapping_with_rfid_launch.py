"""
Launch slam_toolbox async mapping plus RFID landmark manager.

Requires ``map`` and full robot TF (e.g. from the robot over DDS, including
``base_link`` -> ``rfid_sensor_link`` from ``turtlebot3_description``).
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time')
    slam_params_file = LaunchConfiguration('slam_params_file')
    landmark_file = LaunchConfiguration('landmark_file')

    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation clock',
    )
    declare_slam_params = DeclareLaunchArgument(
        'slam_params_file',
        default_value=os.path.join(
            get_package_share_directory('ros2_rfid_mapping'),
            'config',
            'mapper_params_online_async.yaml',
        ),
        description='slam_toolbox YAML',
    )
    declare_landmark_file = DeclareLaunchArgument(
        'landmark_file',
        default_value='',
        description='Optional path to YAML for RFID landmark save/load',
    )

    slam_node = Node(
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name='slam_toolbox',
        output='screen',
        parameters=[
            slam_params_file,
            {'use_sim_time': use_sim_time},
        ],
    )

    landmark_node = Node(
        package='rfid_landmarks',
        executable='rfid_landmark_manager',
        name='rfid_landmark_manager',
        output='screen',
        parameters=[
            {'use_sim_time': use_sim_time},
            {'landmark_file': landmark_file},
        ],
    )

    return LaunchDescription(
        [
            declare_use_sim_time,
            declare_slam_params,
            declare_landmark_file,
            slam_node,
            landmark_node,
        ],
    )
