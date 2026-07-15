from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
import os

def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'yaml_pattern',
            default_value='~/pose_output.yaml',
            description='Glob pattern matching area waypoint YAML files, e.g. ~/area*.yaml'
        ),
        Node(
            package='path_coverage',
            executable='waypoint_follower_node.py',
            name='waypoint_follower',
            output='screen',
            parameters=[{
                "yaml_pattern": LaunchConfiguration("yaml_pattern"),
                "global_frame": "map",
            }]
        ),
    ])
