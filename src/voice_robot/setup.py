from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'voice_robot'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'),
            glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'urdf'),
            glob('urdf/*')),
        (os.path.join('share', package_name, 'worlds'),
            glob('worlds/*')),
        (os.path.join('share', package_name, 'config'),
            glob('config/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Muhammad Mamoon',
    maintainer_email='mamoon@ucp.edu.pk',
    description='Voice-controlled mobile robot simulation',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'speech_command_node     = voice_robot.speech_command_node:main',
            'command_interpreter_node = voice_robot.command_interpreter_node:main',
            'motor_control_node      = voice_robot.motor_control_node:main',
            'performance_evaluator   = voice_robot.performance_evaluator:main',
        ],
    },
)
