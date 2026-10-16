# Voice-Controlled Mobile Robot

A voice-controlled differential-drive robot built on **ROS 2 Jazzy** and simulated in **Gazebo Harmonic**.
A spoken (or typed) command such as *forward*, *left* or *stop* travels through independent ROS 2 nodes and
ends up as wheel motion in the simulator. The robot is a teleoperated system: the human is the feedback loop
(reactive open-loop control), not an autonomous navigator.

> **Scope:** simulation-based implementation and evaluation with ROS 2. Physical hardware (ESP32/Arduino, HC-05,
> L298N) was in the original proposal but is out of scope for this deliverable.

| | |
|---|---|
| **Quick start** | `make sim` (from the workspace root) |
| **Day-to-day use** | [USAGE.md](USAGE.md) |
| **What to install** | [REQUIREMENTS.md](REQUIREMENTS.md) |

---

## Table of contents

1. [Project status](#project-status)
2. [How it works](#how-it-works)
3. [Repository layout](#repository-layout)
4. [Quick start](#quick-start)
5. [Robot and world](#robot-and-world)
6. [Evaluation and results](#evaluation-and-results)
7. [Relation to the project proposal](#relation-to-the-project-proposal)
8. [Known limitations](#known-limitations)
9. [Future work](#future-work)
10. [Authors and licence](#authors-and-licence)

---

## Project status

| Component | Status |
|---|---|
| URDF/xacro model (`check_urdf` passes) | Verified |
| Gazebo world, robot spawn, native DiffDrive plugin | Verified (robot moves on `/cmd_vel`) |
| ROS-GZ bridge (`/cmd_vel`, `/odom`, `/clock`, `/tf`) | Verified |
| Keyboard pipeline: speech node -> interpreter -> `/cmd_vel` -> Gazebo | Verified |
| Motor monitor (`/motor_status`, `/cmd_vel_safe`) | Verified |
| RViz2 configuration (robot model, TF, odometry trail) | Verified |
| Microphone mode (Google Web Speech API) | Verified in a live session (see [observed behaviour](#microphone-mode-observed-behaviour)); recognition rate not quantified |
| Performance evaluator + graphs | Verified (13-command run, results below) |
| Simplified `Makefile` + Tilix split session | Needs first-run validation on the target machine (`make -n sim` previews, `make sim` runs) |

---

## How it works

```
 keyboard / microphone
          |
          v
 +----------------------+  /voice_command   +--------------------------+
 |  speech_command_node | ----------------> | command_interpreter_node |
 |  text -> command word|  (std_msgs/String)|  word -> velocity        |
 +----------------------+                   +------------+-------------+
                                                         | /cmd_vel (geometry_msgs/Twist)
                              +--------------------------+--------------------------+
                              v                                                     v
                  +----------------------+                              +-------------------+
                  |   motor_control_node |                              |   ros_gz_bridge   |
                  |  clamp + monitor     |                              |  ROS 2 -> Gazebo  |
                  +----------+-----------+                              +---------+---------+
                             |                                                    v
              /cmd_vel_safe, /motor_status                          Gazebo DiffDrive plugin
                                                                    (wheels, physics, odometry)
                                                                                  |
                                              /odom, /tf, /clock  (bridge: Gazebo -> ROS 2)
                                                                                  v
                                                                       RViz2 / other nodes
```

### Nodes

| Node | Executable | Role |
|---|---|---|
| Speech command | `speech_command_node` | Reads typed (`--keyboard`) or spoken input, normalises it to `forward / backward / left / right / stop`, publishes `/voice_command`. Input runs in a daemon thread so `rclpy.spin()` stays free. |
| Command interpreter | `command_interpreter_node` | Maps each command word to a `Twist` (0.3 m/s linear, 0.8 rad/s angular) and publishes `/cmd_vel`. Unknown input becomes a stop. Also accepts the single letters `f b l r s` when published directly. |
| Motor control | `motor_control_node` | Clamps velocity (1.0 m/s, 2.0 rad/s), republishes on `/cmd_vel_safe`, reports a readable state on `/motor_status`. In simulation Gazebo's DiffDrive plugin replaces the hardware motor driver; this node is a safety/monitoring layer. |
| Performance evaluator | `performance_evaluator` | Injects a scripted 13-command sequence, times the response, writes CSVs and a summary. |

Infrastructure started by `robot_sim.launch.py`: Gazebo Harmonic, `robot_state_publisher`, `joint_state_publisher`,
robot spawner (`ros_gz_sim create`), `ros_gz_bridge`, RViz2 (with `config/rviz_config.rviz`).

### Topics

| Topic | Type | Publisher | Subscribers |
|---|---|---|---|
| `/voice_command` | `std_msgs/String` | `speech_command_node` (and the evaluator) | `command_interpreter_node` |
| `/cmd_vel` | `geometry_msgs/Twist` | `command_interpreter_node` | `motor_control_node`, `ros_gz_bridge`, evaluator |
| `/cmd_vel_safe` | `geometry_msgs/Twist` | `motor_control_node` | none (where a hardware driver would attach) |
| `/motor_status` | `std_msgs/String` | `motor_control_node` | none (human monitoring) |
| `/odom` | `nav_msgs/Odometry` | `ros_gz_bridge` (30 Hz from the plugin) | RViz2 |
| `/tf`, `/tf_static` | `tf2_msgs/TFMessage` | `ros_gz_bridge`, `robot_state_publisher` | RViz2 |
| `/clock` | `rosgraph_msgs/Clock` | `ros_gz_bridge` | all nodes (`use_sim_time`) |
| `/robot_description` | `std_msgs/String` | `robot_state_publisher` | spawner, `joint_state_publisher`, RViz2 |
| `/joint_states` | `sensor_msgs/JointState` | `joint_state_publisher` | `robot_state_publisher` |

Services and actions are not used: the system is pure asynchronous publish-subscribe. QoS is the default
profile (reliable, volatile, depth 10); the evaluator sets reliable explicitly.

---

## Repository layout

The repository root is the ROS 2 workspace. The `Makefile` lives here and must be run from here.

```
ros2_ws/                           <- run make from this folder
├── Makefile                       build / run / demo / evaluation targets   (make help)
├── README.md  USAGE.md  REQUIREMENTS.md  .gitignore
└── src/voice_robot/
    ├── package.xml  setup.py  setup.cfg
    ├── resource/voice_robot
    ├── voice_robot/               Python package
    │   ├── speech_command_node.py
    │   ├── command_interpreter_node.py
    │   ├── motor_control_node.py
    │   ├── performance_evaluator.py
    │   └── generate_graphs.py     run with python3 (no ROS entry point)
    ├── launch/
    │   ├── robot_sim.launch.py    full simulation
    │   └── nodes_only.launch.py   software nodes without Gazebo
    ├── urdf/diff_robot.urdf.xacro
    ├── worlds/robot_world.sdf
    └── config/rviz_config.rviz
```

`build/`, `install/`, `log/` are generated by colcon and ignored by git.

---

## Quick start

```bash
cd ~/ros2_ws

make deps          # one-time: apt + pip dependencies (sudo)
make sim           # builds, then opens a split Tilix session
```

In the **voice prompt** pane type a command and press Enter:

```
Command > forward
Command > left
Command > stop
```

No Tilix? Run `make run` in one terminal and `make speech` in another.
Preview any target without running it: `make -n sim`. Full guide: [USAGE.md](USAGE.md).

---

## Robot and world

| Parameter | Value |
|---|---|
| Drive | Differential, passive caster at the rear |
| Body | 0.40 x 0.30 x 0.10 m box, 2.0 kg |
| Wheels | radius 0.07 m, width 0.05 m, 0.3 kg each; caster 0.1 kg |
| Wheel separation (track width) | 0.35 m (`wheel_offset_y x 2`) |
| Friction | drive wheels mu1 = mu2 = 1.0, caster 0.01 |
| Command speeds | 0.3 m/s forward/backward, 0.8 rad/s turning |
| Plugin limits | 1.0 m/s and 2.0 rad/s velocity; 2.0 acceleration |
| Odometry | 30 Hz |
| World | 4 m x 4 m walled arena; static obstacle 0.3 x 0.3 x 0.5 m at (1, 1, 0.25) |
| Physics | 1 ms step; the Gazebo GUI reports the DART engine plugin with ODE collision detection |

TF frames: `odom -> base_footprint -> base_link -> {left_wheel, right_wheel, caster_wheel}`.
RViz2 uses `odom` as the fixed frame and keeps the last 50 odometry messages as a trail.

Kinematics used by the DiffDrive plugin (L = track width, r = wheel radius):

```
v_right = v + w*L/2        v_left = v - w*L/2
w_right = v_right / r      w_left = v_left / r
```

---

## Evaluation and results

`make eval` runs a scripted 13-command sequence (3 x forward, 1 x backward, 2 x left, 2 x right, 5 x stop) and records
per command:

* **Latency** - from publishing on `/voice_command` until the resulting message is seen on `/cmd_vel`.
* **Accuracy** - whether that `Twist` matches the expected velocity for the command (tolerance 0.05).

Outputs: `~/ros2_ws/evaluation_results/` (`latency_log.csv`, `accuracy_log.csv`, `summary_report.txt`);
`make graphs` renders four PNGs into `evaluation_results/graphs/`.

### Results of the recorded run (from the project report)

| Metric | Target (proposal) | Measured |
|---|---|---|
| Command-to-velocity accuracy | > 90 % | 13 / 13 (100 %) |
| Pipeline latency, mean | < 500 ms | 11.5 ms |
| Pipeline latency, median | | 11.3 ms |
| Mean latency by command | | forward 14.3, backward 9.5, left 7.2, right 12.5, stop 11.6 ms |
| Worst single sample | | about 21 ms (first command of the run) |

### How to read these numbers

The evaluator publishes on `/voice_command` itself, so it bypasses the speech node, and it stops its clock at
`/cmd_vel`, **not** at wheel motion or `/odom`. The figures therefore describe the ROS 2 software pipeline
(transport + interpreter). They do not include speech recognition, Google STT round-trip time, Gazebo's
acceleration limits, or physical response. "Accuracy" compares velocity values and is expected to be 100 % for a
deterministic mapping; it is not speech-recognition accuracy. Say so explicitly when quoting them.
Measuring motion latency would additionally require timing the first `/odom` change after the command.

### Microphone mode: observed behaviour

A live session (Google Web Speech API, ambient-noise threshold calibrated to 143) recognised single words
(`forward`, `stop`, `backward`, `left`, `right`) and produced many `Could not understand audio` warnings.
Observed resolutions of longer phrases: *"backward right"* -> `backward`, *"stop the car"* -> `stop`.
No recognition-rate figure was collected, so the proposal's ">90 % voice recognition" target is **not** demonstrated
for the microphone path. ALSA / JACK lines printed at start-up are harmless audio-backend noise.

---

## Relation to the project proposal

| Proposal item | Implementation |
|---|---|
| Speech Command Interface Node (`/voice_command`) | `speech_command_node` (keyboard + microphone) |
| Command Interpreter Node (`/voice_command` -> `/cmd_vel`) | `command_interpreter_node` |
| Motor Control Node | Gazebo DiffDrive plugin actuates the wheels; `motor_control_node` adds clamping and status reporting |
| Bluetooth Communication Node | Not implemented (hardware out of scope); the speech node publishes to ROS 2 directly |
| TF tree `map / base_link / left_wheel / right_wheel` | `odom -> base_footprint -> base_link -> wheels`; no `map` frame because there is no localisation |
| Gazebo and RViz simulation | Gazebo Harmonic + RViz2 |
| Accuracy, latency, reliability evaluation | `performance_evaluator` + `generate_graphs.py` (scope caveats above) |
| Energy consumption, +-5 cm navigation accuracy | Not measured in simulation |
| Arduino/ESP32, HC-05, L298N hardware | Out of scope |

---

## Known limitations

* **Phrase matching is simple.** An exact phrase resolves directly. Anything else falls back to substring matching in
  dictionary order, so extra words are tolerated (`backwardd` -> `backward`) but can resolve wrongly: the short phrase
  `go` precedes `go left`, so *"please go left"* maps to `forward`. Keep commands short.
* **Open loop.** No obstacle avoidance, no velocity timeout; the last command stays active until `stop`.
* **Microphone mode needs internet** (Google Web Speech API) and a working audio input.
* **`ros2 launch` does not forward stdin**, so the keyboard prompt cannot run inside a launch file. Use `make speech`
  or the Tilix pane. `nodes_only.launch.py` declares a `mode` argument that it does not use and starts the speech
  node in keyboard mode, which therefore ends immediately without input; use `make send` with it.
* `/cmd_vel_safe` and `/motor_status` have no programmatic subscribers.
* The evaluator keeps spinning after it finishes; stop it with Ctrl+C.
* `speech_command_node` calls `rclpy.shutdown()` without the `if rclpy.ok()` guard the other nodes have, so Ctrl+C may
  print an `rcl_shutdown already called` traceback. It is cosmetic.

---

## Future work

Hardware deployment (ESP32/Arduino, HC-05, L298N), offline speech-to-text (for example Whisper or Vosk) with noise
filtering, odometry-based closed-loop distance control, and LiDAR + IMU with Nav2 for higher-level commands.

---

## Author

* Muhammad Mamoon
