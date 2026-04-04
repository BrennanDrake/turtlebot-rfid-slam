"""Launch covariance-aware Nav2 replanner (requires Nav2 + ``/odometry/filtered`` + ``/map``)."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time')

    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation clock',
    )

    node = Node(
        package='rfid_landmarks',
        executable='covariance_replan_node',
        name='covariance_replan_node',
        output='screen',
        parameters=[{'use_sim_time': use_sim_time}],
    )

    return LaunchDescription([declare_use_sim_time, node])
