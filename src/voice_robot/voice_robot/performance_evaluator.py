#!/usr/bin/env python3
"""
performance_evaluator.py
------------------------
Automated performance evaluation for the voice-controlled mobile robot.

Measures (per your project proposal):
  1. Command execution latency  (voice_command publish → cmd_vel received)
  2. Command recognition accuracy (correct / total)
  3. Motor status response time
  4. Per-command statistics

Saves results to:
  ~/ros2_ws/evaluation_results/
    latency_log.csv
    accuracy_log.csv
    summary_report.txt

Run WHILE the simulation is running:
  ros2 run voice_robot performance_evaluator
"""

import os
import csv
import time
import threading
import statistics
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
from std_msgs.msg import String
from geometry_msgs.msg import Twist


# ── Output directory ──────────────────────────────────────────
OUTPUT_DIR = os.path.expanduser('~/ros2_ws/evaluation_results')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Test sequence: (command, expected_action, hold_seconds) ──
TEST_SEQUENCE = [
    ('forward',  'FORWARD',  2.0),
    ('stop',     'STOP',     1.0),
    ('backward', 'BACKWARD', 2.0),
    ('stop',     'STOP',     1.0),
    ('left',     'LEFT',     2.0),
    ('stop',     'STOP',     1.0),
    ('right',    'RIGHT',    2.0),
    ('stop',     'STOP',     1.0),
    ('forward',  'FORWARD',  2.0),
    ('left',     'LEFT',     1.5),
    ('forward',  'FORWARD',  2.0),
    ('right',    'RIGHT',    1.5),
    ('stop',     'STOP',     1.0),
]

# Map command → expected Twist signature for accuracy check
EXPECTED_TWIST = {
    'forward':  {'linear_x':  0.3,  'angular_z':  0.0},
    'backward': {'linear_x': -0.3,  'angular_z':  0.0},
    'left':     {'linear_x':  0.0,  'angular_z':  0.8},
    'right':    {'linear_x':  0.0,  'angular_z': -0.8},
    'stop':     {'linear_x':  0.0,  'angular_z':  0.0},
}


class PerformanceEvaluator(Node):

    def __init__(self):
        super().__init__('performance_evaluator')

        qos = QoSProfile(depth=10,
                         reliability=ReliabilityPolicy.RELIABLE)

        # Publisher — injects commands into the pipeline
        self.cmd_pub = self.create_publisher(String, '/voice_command', qos)

        # Subscriber — listens for the resulting /cmd_vel
        self.twist_sub = self.create_subscription(
            Twist, '/cmd_vel', self._twist_callback, qos)

        # State tracking
        self._pending_command   = None
        self._publish_timestamp = None
        self._latency_received  = threading.Event()
        self._received_twist    = None

        # Results storage
        self.latency_records  = []   # [{command, latency_ms, accurate}]
        self.accuracy_records = []   # [{command, expected, received, correct}]

        self.get_logger().info(
            '\n'
            '══════════════════════════════════════════════\n'
            '  Performance Evaluator starting in 3 seconds\n'
            '  Keep the simulation running in Terminal 1\n'
            '══════════════════════════════════════════════'
        )

    # ── /cmd_vel callback ─────────────────────────────────────
    def _twist_callback(self, msg: Twist):
        if self._pending_command is None:
            return

        receive_time = time.perf_counter()
        latency_ms   = (receive_time - self._publish_timestamp) * 1000.0

        self._received_twist = msg
        self._latency_ms     = latency_ms
        self._latency_received.set()

    # ── Send one command and measure response ─────────────────
    def _send_and_measure(self, command: str, hold: float):
        self._latency_received.clear()
        self._pending_command   = command
        self._received_twist    = None
        self._latency_ms        = None

        # Publish the voice command and timestamp it
        msg = String()
        msg.data = command
        self._publish_timestamp = time.perf_counter()
        self.cmd_pub.publish(msg)

        # Wait up to 1 second for /cmd_vel response
        got_response = self._latency_received.wait(timeout=1.0)

        if not got_response:
            self.get_logger().warn(f'TIMEOUT waiting for cmd_vel on: {command}')
            self._pending_command = None
            return

        latency_ms = self._latency_ms
        twist      = self._received_twist

        # Accuracy check
        expected = EXPECTED_TWIST[command]
        lin_ok   = abs(twist.linear.x  - expected['linear_x'])  < 0.05
        ang_ok   = abs(twist.angular.z - expected['angular_z'])  < 0.05
        accurate = lin_ok and ang_ok

        # Log
        self.get_logger().info(
            f'  CMD: {command:10s} | '
            f'latency: {latency_ms:6.1f} ms | '
            f'accurate: {"✓" if accurate else "✗"} | '
            f'lin={twist.linear.x:+.2f} ang={twist.angular.z:+.2f}'
        )

        self.latency_records.append({
            'command':    command,
            'latency_ms': round(latency_ms, 3),
            'accurate':   accurate,
        })
        self.accuracy_records.append({
            'command':          command,
            'expected_linear':  expected['linear_x'],
            'expected_angular': expected['angular_z'],
            'received_linear':  round(twist.linear.x, 3),
            'received_angular': round(twist.angular.z, 3),
            'correct':          accurate,
        })

        self._pending_command = None

        # Hold the command for the specified duration
        time.sleep(hold)

    # ── Run full test sequence ────────────────────────────────
    def run_evaluation(self):
        time.sleep(3.0)   # wait for nodes to settle

        self.get_logger().info(
            f'\n  Running {len(TEST_SEQUENCE)} command test sequence...\n'
        )

        for command, expected_action, hold in TEST_SEQUENCE:
            if not rclpy.ok():
                break
            self._send_and_measure(command, hold)

        self._save_results()
        self._print_summary()

    # ── Save CSV results ──────────────────────────────────────
    def _save_results(self):
        # Latency CSV
        latency_path = os.path.join(OUTPUT_DIR, 'latency_log.csv')
        with open(latency_path, 'w', newline='') as f:
            writer = csv.DictWriter(
                f, fieldnames=['command', 'latency_ms', 'accurate'])
            writer.writeheader()
            writer.writerows(self.latency_records)

        # Accuracy CSV
        accuracy_path = os.path.join(OUTPUT_DIR, 'accuracy_log.csv')
        with open(accuracy_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'command', 'expected_linear', 'expected_angular',
                'received_linear', 'received_angular', 'correct'])
            writer.writeheader()
            writer.writerows(self.accuracy_records)

        self.get_logger().info(f'Results saved to {OUTPUT_DIR}/')

    # ── Print summary ─────────────────────────────────────────
    def _print_summary(self):
        if not self.latency_records:
            return

        latencies = [r['latency_ms'] for r in self.latency_records]
        correct   = sum(1 for r in self.latency_records if r['accurate'])
        total     = len(self.latency_records)
        accuracy  = (correct / total) * 100

        summary = (
            '\n'
            '══════════════════════════════════════════════\n'
            '  PERFORMANCE EVALUATION SUMMARY\n'
            '══════════════════════════════════════════════\n'
            f'  Total commands tested  : {total}\n'
            f'  Correct executions     : {correct}\n'
            f'  Command accuracy       : {accuracy:.1f}%\n'
            f'\n'
            f'  Latency (ms)\n'
            f'    Min     : {min(latencies):.1f}\n'
            f'    Max     : {max(latencies):.1f}\n'
            f'    Mean    : {statistics.mean(latencies):.1f}\n'
            f'    Median  : {statistics.median(latencies):.1f}\n'
            f'    Std Dev : {statistics.stdev(latencies):.1f}\n'
            '══════════════════════════════════════════════\n'
        )

        self.get_logger().info(summary)

        # Save summary text
        summary_path = os.path.join(OUTPUT_DIR, 'summary_report.txt')
        with open(summary_path, 'w') as f:
            f.write(summary)
            f.write('\nPer-command breakdown:\n')
            for cmd in ['forward', 'backward', 'left', 'right', 'stop']:
                records = [r for r in self.latency_records
                           if r['command'] == cmd]
                if records:
                    lats = [r['latency_ms'] for r in records]
                    acc  = sum(1 for r in records if r['accurate'])
                    f.write(
                        f'  {cmd:10s}: n={len(records):2d}  '
                        f'mean={statistics.mean(lats):6.1f}ms  '
                        f'accuracy={acc}/{len(records)}\n'
                    )

        self.get_logger().info(f'Summary saved to {summary_path}')


def main(args=None):
    rclpy.init(args=args)
    node = PerformanceEvaluator()

    # Run evaluation in a thread so rclpy.spin() can process callbacks
    eval_thread = threading.Thread(target=node.run_evaluation, daemon=True)
    eval_thread.start()

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
