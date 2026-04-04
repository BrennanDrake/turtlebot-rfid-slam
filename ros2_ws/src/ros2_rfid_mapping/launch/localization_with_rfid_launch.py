"""
Localization stack: map_server, slam_toolbox (localization, no map TF), RFID landmarks, EKF.

Robot must publish ``/odom`` and static/joint TF including ``rfid_sensor_link``.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time')
    map_yaml = LaunchConfiguration('map')
    slam_params_file = LaunchConfiguration('slam_params_file')
    ekf_params_file = LaunchConfiguration('ekf_params_file')
    landmark_file = LaunchConfiguration('landmark_file')

    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation clock',
    )
    declare_map = DeclareLaunchArgument(
        'map',
        default_value='',
        description='Full path to saved map YAML (nav2 map_server format)',
    )
    declare_slam_params = DeclareLaunchArgument(
        'slam_params_file',
        default_value=os.path.join(
            get_package_share_directory('ros2_rfid_mapping'),
            'config',
            'mapper_params_localization.yaml',
        ),
        description='slam_toolbox localization YAML',
    )
    declare_ekf = DeclareLaunchArgument(
        'ekf_params_file',
        default_value=os.path.join(
            get_package_share_directory('ros2_rfid_mapping'),
            'config',
            'ekf_rfid.yaml',
        ),
        description='robot_localization EKF parameters',
    )
    declare_landmark_file = DeclareLaunchArgument(
        'landmark_file',
        default_value='',
        description='Path to RFID landmarks YAML',
    )

    map_server_node = Node(
        package='nav2_map_server',
        executable='map_server',
        name='map_server',
        output='screen',
        parameters=[
            {'use_sim_time': use_sim_time},
            {'yaml_filename': map_yaml},
        ],
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

    ekf_node = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_global',
        output='screen',
        parameters=[ekf_params_file, {'use_sim_time': use_sim_time}],
    )

    return LaunchDescription(
        [
            declare_use_sim_time,
            declare_map,
            declare_slam_params,
            declare_ekf,
            declare_landmark_file,
            map_server_node,
            slam_node,
            landmark_node,
            ekf_node,
        ],
    )
