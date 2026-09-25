#!/usr/bin/env python3
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    pkg_testbed_navigation = get_package_share_directory('testbed_navigation')
    pkg_testbed_bringup = get_package_share_directory('testbed_bringup')

    default_amcl_params = os.path.join(pkg_testbed_navigation, 'config', 'amcl_params.yaml')
    default_map_file = os.path.join(pkg_testbed_bringup, 'maps', 'testbed_world.yaml')

    declare_map_cmd = DeclareLaunchArgument(
        'map',
        default_value=default_map_file,
        description='Full path to map yaml file'
    )

    declare_params_file_cmd = DeclareLaunchArgument(
        'params_file',
        default_value=default_amcl_params,
        description='Full path to the ROS2 parameters file to use for all sustained nodes'
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

    declare_include_map_cmd = DeclareLaunchArgument(
        'include_map',
        default_value='true',
        description='Whether to also launch map_server in this launch file'
    )

    # Map server node (launched if include_map is true)
    map_server_node = Node(
        condition=IfCondition(LaunchConfiguration('include_map')),
        package='nav2_map_server',
        executable='map_server',
        name='map_server',
        output='screen',
        parameters=[{
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            'yaml_filename': LaunchConfiguration('map'),
            'topic_name': 'map',
            'frame_id': 'map'
        }]
    )

    # AMCL node
    amcl_node = Node(
        package='nav2_amcl',
        executable='amcl',
        name='amcl',
        output='screen',
        parameters=[
            LaunchConfiguration('params_file'),
            {'use_sim_time': LaunchConfiguration('use_sim_time')}
        ]
    )

    # Lifecycle manager when including map_server
    lifecycle_manager_with_map = Node(
        condition=IfCondition(LaunchConfiguration('include_map')),
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_localization',
        output='screen',
        parameters=[{
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            'autostart': LaunchConfiguration('autostart'),
            'node_names': ['map_server', 'amcl']
        }]
    )

    # Lifecycle manager when map_server is already running externally
    lifecycle_manager_standalone = Node(
        condition=UnlessCondition(LaunchConfiguration('include_map')),
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_localization',
        output='screen',
        parameters=[{
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            'autostart': LaunchConfiguration('autostart'),
            'node_names': ['amcl']
        }]
    )

    return LaunchDescription([
        declare_map_cmd,
        declare_params_file_cmd,
        declare_use_sim_time_cmd,
        declare_autostart_cmd,
        declare_include_map_cmd,
        map_server_node,
        amcl_node,
        lifecycle_manager_with_map,
        lifecycle_manager_standalone
    ])
