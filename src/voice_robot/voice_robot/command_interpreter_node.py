#!/usr/bin/env python3
"""
command_interpreter_node
Subscribes : /voice_command  (std_msgs/String)
Publishes  : /cmd_vel        (geometry_msgs/Twist)
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import Twist

LINEAR_SPEED  = 0.3
ANGULAR_SPEED = 0.8


class CommandInterpreterNode(Node):

    def __init__(self):
        super().__init__('command_interpreter_node')
        self.subscription = self.create_subscription(
            String, '/voice_command', self.voice_command_callback, 10)
        self.publisher = self.create_publisher(Twist, '/cmd_vel', 10)
        self.get_logger().info(
            'Command interpreter ready. '
            'Listening on /voice_command → publishing to /cmd_vel')

    def voice_command_callback(self, msg: String):
        raw    = msg.data.strip().lower()
        twist  = Twist()
        action = 'STOP'

        if raw in ('f', 'forward'):
            twist.linear.x  =  LINEAR_SPEED;  action = 'FORWARD'
        elif raw in ('b', 'backward', 'back'):
            twist.linear.x  = -LINEAR_SPEED;  action = 'BACKWARD'
        elif raw in ('l', 'left'):
            twist.angular.z =  ANGULAR_SPEED; action = 'LEFT'
        elif raw in ('r', 'right'):
            twist.angular.z = -ANGULAR_SPEED; action = 'RIGHT'
        elif raw in ('s', 'stop'):
            action = 'STOP'
        else:
            self.get_logger().warn(f"Unknown command: '{raw}' — sending STOP")

        self.publisher.publish(twist)
        self.get_logger().info(
            f"CMD: '{raw}' → {action} "
            f"(linear.x={twist.linear.x:.2f}, angular.z={twist.angular.z:.2f})")


def main(args=None):
    rclpy.init(args=args)
    node = CommandInterpreterNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
