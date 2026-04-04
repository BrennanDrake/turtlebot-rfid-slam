"""
Include Nav2 ``navigation_launch`` with this package's ``nav2_params.yaml``.

Prerequisites: ``map_server`` (or SLAM) publishing ``/map``, ``/odometry/filtered``, ``/scan``.

Install: ``sudo apt install ros-${ROS_DISTRO}-nav2-bringup ros-${ROS_DISTRO}-navigation2``
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    nav2_bringup_share = get_package_share_directory('nav2_bringup')
    params_file = LaunchConfiguration('params_file')
    use_sim_time = LaunchConfiguration('use_sim_time')

    declare_params = DeclareLaunchArgument(
        'params_file',
        default_value=os.path.join(
            get_package_share_directory('ros2_rfid_mapping'),
            'config',
            'nav2_params.yaml',
        ),
        description='Merged Nav2 parameters YAML',
    )
    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation clock',
    )

    navigation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nav2_bringup_share, 'launch', 'navigation_launch.py'),
        ),
        launch_arguments={
            'params_file': params_file,
            'use_sim_time': use_sim_time,
            'autostart': 'true',
        }.items(),
    )

    return LaunchDescription(
        [
            declare_params,
            declare_use_sim_time,
            navigation,
        ],
    )
