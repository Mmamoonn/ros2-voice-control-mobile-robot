#!/usr/bin/env python3
"""
speech_command_node
-------------------
Publishes : /voice_command (std_msgs/String)

Two operating modes:
  1. Microphone mode (default) — captures speech via SpeechRecognition
  2. Keyboard mode (--keyboard) — type commands in terminal for testing

Recognised phrases → published token:
  "forward" / "move forward" / "go forward"  → "forward"
  "backward" / "go back" / "reverse"         → "backward"
  "left"  / "turn left"                      → "left"
  "right" / "turn right"                     → "right"
  "stop"  / "halt" / "freeze"                → "stop"
"""

import sys
import threading
import rclpy
from rclpy.node import Node
from std_msgs.msg import String


# ── Phrase → canonical command mapping ──
COMMAND_MAP = {
    # forward
    'forward':      'forward',
    'move forward': 'forward',
    'go forward':   'forward',
    'go':           'forward',
    # backward
    'backward':     'backward',
    'back':         'backward',
    'go back':      'backward',
    'move back':    'backward',
    'reverse':      'backward',
    # left
    'left':         'left',
    'turn left':    'left',
    'go left':      'left',
    # right
    'right':        'right',
    'turn right':   'right',
    'go right':     'right',
    # stop
    'stop':         'stop',
    'halt':         'stop',
    'freeze':       'stop',
    'pause':        'stop',
}


class SpeechCommandNode(Node):

    def __init__(self, keyboard_mode: bool = False):
        super().__init__('speech_command_node')

        self.keyboard_mode = keyboard_mode

        self.publisher = self.create_publisher(
            String,
            '/voice_command',
            10
        )

        if self.keyboard_mode:
            self.get_logger().info(
                '\n'
                '═══════════════════════════════════════\n'
                '  KEYBOARD MODE active\n'
                '  Type a command and press Enter:\n'
                '  forward / backward / left / right / stop\n'
                '═══════════════════════════════════════'
            )
            # Run keyboard input in a separate thread so rclpy.spin() is free
            self._kb_thread = threading.Thread(
                target=self._keyboard_loop, daemon=True
            )
            self._kb_thread.start()

        else:
            self.get_logger().info(
                '\n'
                '═══════════════════════════════════════\n'
                '  MICROPHONE MODE active\n'
                '  Speak a command into your microphone.\n'
                '  Commands: forward / backward / left / right / stop\n'
                '═══════════════════════════════════════'
            )
            # Run mic listening in a separate thread
            self._mic_thread = threading.Thread(
                target=self._microphone_loop, daemon=True
            )
            self._mic_thread.start()

    # ── Publish helper ────────────────────────────────────────
    def _publish_command(self, command: str):
        msg = String()
        msg.data = command
        self.publisher.publish(msg)
        self.get_logger().info(f'Published → /voice_command: "{command}"')

    # ── Phrase matcher ────────────────────────────────────────
    def _match_phrase(self, text: str):
        """Return canonical command or None if not recognised."""
        text = text.strip().lower()

        # Direct match first
        if text in COMMAND_MAP:
            return COMMAND_MAP[text]

        # Substring match (handles extra words like "please go forward")
        for phrase, command in COMMAND_MAP.items():
            if phrase in text:
                return command

        return None

    # ── Keyboard loop (runs in thread) ────────────────────────
    def _keyboard_loop(self):
        while rclpy.ok():
            try:
                raw = input('Command > ').strip()
            except EOFError:
                break

            if not raw:
                continue

            command = self._match_phrase(raw)
            if command:
                self._publish_command(command)
            else:
                self.get_logger().warn(
                    f"Not recognised: '{raw}'. "
                    "Try: forward / backward / left / right / stop"
                )

    # ── Microphone loop (runs in thread) ──────────────────────
    def _microphone_loop(self):
        try:
            import speech_recognition as sr
        except ImportError:
            self.get_logger().error(
                'speech_recognition not installed. '
                'Run: pip install SpeechRecognition --break-system-packages\n'
                'Or restart with --keyboard flag for keyboard mode.'
            )
            return

        recogniser = sr.Recognizer()

        # Tune for quiet lab environment — adjust if needed
        recogniser.energy_threshold        = 300
        recogniser.dynamic_energy_threshold = True
        recogniser.pause_threshold          = 0.8

        with sr.Microphone() as source:
            self.get_logger().info(
                'Calibrating microphone for ambient noise (2 seconds)...'
            )
            recogniser.adjust_for_ambient_noise(source, duration=2)
            self.get_logger().info(
                f'Calibration done. Energy threshold = '
                f'{recogniser.energy_threshold:.0f}. Listening...'
            )

            while rclpy.ok():
                try:
                    self.get_logger().info('Waiting for voice command...')
                    audio = recogniser.listen(source, timeout=10, phrase_time_limit=4)

                    text = recogniser.recognize_google(audio)
                    self.get_logger().info(f'Heard: "{text}"')

                    command = self._match_phrase(text)
                    if command:
                        self._publish_command(command)
                    else:
                        self.get_logger().warn(
                            f"Phrase not in command map: '{text}'"
                        )

                except sr.WaitTimeoutError:
                    # No speech detected within timeout — keep looping
                    self.get_logger().debug('Listening timeout, retrying...')

                except sr.UnknownValueError:
                    self.get_logger().warn(
                        'Could not understand audio — please speak clearly.'
                    )

                except sr.RequestError as e:
                    self.get_logger().error(
                        f'Google STT service error: {e}\n'
                        'Check internet connection or switch to --keyboard mode.'
                    )


def main(args=None):
    # Parse --keyboard flag before passing args to rclpy
    keyboard_mode = '--keyboard' in sys.argv
    if keyboard_mode:
        sys.argv.remove('--keyboard')

    rclpy.init(args=args)
    node = SpeechCommandNode(keyboard_mode=keyboard_mode)

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Speech command node shutting down.')
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
