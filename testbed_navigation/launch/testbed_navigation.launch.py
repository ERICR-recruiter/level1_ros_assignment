#!/usr/bin/env python3
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    pkg_testbed_navigation = get_package_share_directory('testbed_navigation')
    pkg_testbed_bringup = get_package_share_directory('testbed_bringup')

    default_map = os.path.join(pkg_testbed_bringup, 'maps', 'testbed_world.yaml')
    default_amcl_params = os.path.join(pkg_testbed_navigation, 'config', 'amcl_params.yaml')
    default_nav2_params = os.path.join(pkg_testbed_navigation, 'config', 'nav2_params.yaml')
    default_rviz_config = os.path.join(pkg_testbed_navigation, 'rviz', 'nav2_default_view.rviz')

    declare_map_cmd = DeclareLaunchArgument(
        'map',
        default_value=default_map,
        description='Full path to map yaml file'
    )

    declare_amcl_params_cmd = DeclareLaunchArgument(
        'amcl_params_file',
        default_value=default_amcl_params,
        description='Full path to AMCL parameter file'
    )

    declare_nav2_params_cmd = DeclareLaunchArgument(
        'nav2_params_file',
        default_value=default_nav2_params,
        description='Full path to Nav2 parameter file'
    )

    declare_use_sim_time_cmd = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation (Gazebo) clock if true'
    )

    declare_autostart_cmd = DeclareLaunchArgument(
        'autostart',
        default_value='true',
        description='Automatically startup the nav2 lifecycle nodes'
    )

    declare_use_rviz_cmd = DeclareLaunchArgument(
        'use_rviz',
        default_value='true',
        description='Whether to launch RViz'
    )

    # Include Localization (with map server enabled)
    localization_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_testbed_navigation, 'launch', 'localization.launch.py')
        ),
        launch_arguments={
            'map': LaunchConfiguration('map'),
            'params_file': LaunchConfiguration('amcl_params_file'),
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            'autostart': LaunchConfiguration('autostart'),
            'include_map': 'true'
        }.items()
    )

    # Include Navigation (Controller, Planner, Behaviors, BT Navigator)
    navigation_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_testbed_navigation, 'launch', 'navigation.launch.py')
        ),
        launch_arguments={
            'params_file': LaunchConfiguration('nav2_params_file'),
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            'autostart': LaunchConfiguration('autostart')
        }.items()
    )

    # RViz node
    rviz_cmd = Node(
        condition=IfCondition(LaunchConfiguration('use_rviz')),
        package='rviz2',
        executable='rviz2',
        name='rviz2_navigation',
        arguments=['-d', default_rviz_config],
        parameters=[{'use_sim_time': LaunchConfiguration('use_sim_time')}],
        output='screen'
    )

    return LaunchDescription([
        declare_map_cmd,
        declare_amcl_params_cmd,
        declare_nav2_params_cmd,
        declare_use_sim_time_cmd,
        declare_autostart_cmd,
        declare_use_rviz_cmd,
        localization_cmd,
        navigation_cmd,
        rviz_cmd
    ])
