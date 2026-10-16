import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument,
                             IncludeLaunchDescription, TimerAction)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, Command
from launch_ros.actions import Node


def generate_launch_description():

    pkg_share         = get_package_share_directory('voice_robot')
    urdf_file         = os.path.join(pkg_share, 'urdf',   'diff_robot.urdf.xacro')
    world_file        = os.path.join(pkg_share, 'worlds', 'robot_world.sdf')
    rviz_config_file  = os.path.join(pkg_share, 'config', 'rviz_config.rviz')
    use_sim_time      = LaunchConfiguration('use_sim_time', default='true')
    robot_description = Command(['xacro ', urdf_file])

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(get_package_share_directory('ros_gz_sim'),
                         'launch', 'gz_sim.launch.py')]),
        launch_arguments={
            'gz_args': f'-r {world_file}',
            'on_exit_shutdown': 'true'
        }.items()
    )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{
            'robot_description': robot_description,
            'use_sim_time': use_sim_time
        }],
        output='screen'
    )

    joint_state_publisher = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        parameters=[{'use_sim_time': use_sim_time}]
    )

    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=['-name', 'diff_robot', '-topic', 'robot_description',
                   '-x', '0.0', '-y', '0.0', '-z', '0.1'],
        output='screen'
    )

    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='ros_gz_bridge',
        arguments=[
            '/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist',
            '/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry',
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
            '/tf@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V',
        ],
        parameters=[{'use_sim_time': use_sim_time}],
        output='screen'
    )

    command_interpreter_node = Node(
        package='voice_robot', executable='command_interpreter_node',
        name='command_interpreter_node', output='screen')

    motor_control_node = Node(
        package='voice_robot', executable='motor_control_node',
        name='motor_control_node', output='screen')

    # RViz2 now loads the saved config automatically
    rviz2 = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config_file],
        parameters=[{'use_sim_time': use_sim_time}],
        output='screen'
    )

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='true',
                              description='Use simulation clock'),
        gazebo,
        robot_state_publisher,
        joint_state_publisher,
        TimerAction(period=2.0, actions=[spawn_robot]),
        TimerAction(period=3.5, actions=[bridge]),
        TimerAction(period=4.0, actions=[command_interpreter_node,
                                         motor_control_node]),
        TimerAction(period=6.0, actions=[rviz2]),
    ])
