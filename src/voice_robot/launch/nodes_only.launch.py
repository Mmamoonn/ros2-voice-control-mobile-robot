"""
nodes_only.launch.py
--------------------
Launches all three ROS2 software nodes without Gazebo.
Use this for pipeline testing and demonstration.

Usage:
  ros2 launch voice_robot nodes_only.launch.py
  ros2 launch voice_robot nodes_only.launch.py mode:=keyboard
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():

    mode = LaunchConfiguration('mode', default='keyboard')

    return LaunchDescription([

        DeclareLaunchArgument(
            'mode',
            default_value='keyboard',
            description='Input mode: keyboard or microphone'
        ),

        # ── Node 1: Speech Command ──
        Node(
            package='voice_robot',
            executable='speech_command_node',
            name='speech_command_node',
            arguments=['--keyboard'],
            output='screen',
            emulate_tty=True,
        ),

        # ── Node 2: Command Interpreter ──
        Node(
            package='voice_robot',
            executable='command_interpreter_node',
            name='command_interpreter_node',
            output='screen',
        ),

        # ── Node 3: Motor Control Monitor ──
        Node(
            package='voice_robot',
            executable='motor_control_node',
            name='motor_control_node',
            output='screen',
        ),

    ])
