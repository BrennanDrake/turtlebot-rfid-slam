"""
Launch slam_toolbox async mapping plus RFID landmark manager.

Requires full robot TF over DDS (e.g. ``odom`` -> ``base_footprint``) and ``/scan``.

On Jazzy/Humble, ``async_slam_toolbox_node`` is a **lifecycle** node: it does not
subscribe to ``/scan`` or publish ``/map`` until **configure** + **activate**. This
launch triggers those transitions after a short delay (override ``slam_activate_delay``).
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
    declare_slam_activate_delay = DeclareLaunchArgument(
        'slam_activate_delay',
        default_value='3.0',
        description='Seconds to wait before lifecycle configure+activate on slam_toolbox',
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

    return LaunchDescription(
        [
            declare_use_sim_time,
            declare_slam_params,
            declare_landmark_file,
            declare_slam_activate_delay,
            slam_node,
            landmark_node,
            slam_lifecycle_activate,
        ],
    )
