#!/usr/bin/env python3
"""
motor_control_node
Subscribes : /cmd_vel       (geometry_msgs/Twist)
Publishes  : /cmd_vel_safe  (geometry_msgs/Twist)
             /motor_status  (std_msgs/String)
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import Twist

MAX_LINEAR  = 1.0
MAX_ANGULAR = 2.0


class MotorControlNode(Node):

    def __init__(self):
        super().__init__('motor_control_node')
        self.subscription = self.create_subscription(
            Twist, '/cmd_vel', self.cmd_vel_callback, 10)
        self.safe_pub   = self.create_publisher(Twist,  '/cmd_vel_safe', 10)
        self.status_pub = self.create_publisher(String, '/motor_status',  10)
        self._last_status = ''
        self.get_logger().info(
            'Motor control node active. Monitoring /cmd_vel, publishing /motor_status')

    @staticmethod
    def _clamp(value: float, limit: float) -> float:
        return max(-limit, min(limit, value))

    def cmd_vel_callback(self, msg: Twist):
        safe = Twist()
        safe.linear.x  = self._clamp(msg.linear.x,  MAX_LINEAR)
        safe.linear.y  = self._clamp(msg.linear.y,  MAX_LINEAR)
        safe.angular.z = self._clamp(msg.angular.z, MAX_ANGULAR)
        self.safe_pub.publish(safe)

        lin = safe.linear.x
        ang = safe.angular.z

        if   abs(lin) < 0.01 and abs(ang) < 0.01:  status = 'STOPPED'
        elif lin > 0 and abs(ang) < 0.01:           status = f'FORWARD  @ {lin:.2f} m/s'
        elif lin < 0 and abs(ang) < 0.01:           status = f'BACKWARD @ {abs(lin):.2f} m/s'
        elif ang > 0 and abs(lin) < 0.01:           status = f'TURN LEFT  @ {ang:.2f} rad/s'
        elif ang < 0 and abs(lin) < 0.01:           status = f'TURN RIGHT @ {abs(ang):.2f} rad/s'
        else:                                        status = f'MIXED  lin={lin:.2f} ang={ang:.2f}'

        if status != self._last_status:
            self.get_logger().info(f'Motor status: {status}')
            self._last_status = status

        status_msg      = String()
        status_msg.data = status
        self.status_pub.publish(status_msg)


def main(args=None):
    rclpy.init(args=args)
    node = MotorControlNode()
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
