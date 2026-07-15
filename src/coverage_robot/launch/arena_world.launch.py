import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch.actions import AppendEnvironmentVariable


def generate_launch_description():
    ld = LaunchDescription()

    world_path = os.path.join(
            get_package_share_directory('coverage_robot'),
            'worlds',
            'arena.sdf'
        )

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('ros_gz_sim'),
                'launch',
                'gz_sim.launch.py'
            )
        ),
        launch_arguments={'gz_args': ['-r ', world_path]}.items()
    )

    ld.add_action(gazebo)

    os.environ['TURTLEBOT3_MODEL'] = 'waffle'

    turtlebot3_spawn = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('turtlebot3_gazebo'),
                'launch',
                'spawn_turtlebot3.launch.py'
            )
        ),
        launch_arguments={
            'x_pose': '0.0',
            'y_pose': '0.0'
        }.items()
    )

    ld.add_action(turtlebot3_spawn)

    robot_state_publisher = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('turtlebot3_gazebo'),
                'launch',
                'robot_state_publisher.launch.py'
            )
        ),
        launch_arguments={'use_sim_time': 'true'}.items()
    )
    ld.add_action(robot_state_publisher)

    set_env_vars_resources = AppendEnvironmentVariable(
        'GZ_SIM_RESOURCE_PATH',
        os.path.join(
            get_package_share_directory('turtlebot3_gazebo'),
            'models'
        )
    )
    ld.add_action(set_env_vars_resources)

    return ld

