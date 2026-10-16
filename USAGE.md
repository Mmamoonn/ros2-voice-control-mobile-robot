# Usage Guide

How to build, run, drive, evaluate, and troubleshoot the Voice-Controlled Mobile Robot.
For system and hardware prerequisites, see [REQUIREMENTS.md](REQUIREMENTS.md); for a project overview, see [README.md](README.md).

All commands must be executed from the root of your ROS 2 workspace (normally `~/ros2_ws`).

---

## 1. First-Time Setup

```bash
cd ~/ros2_ws
make deps        # Installs required apt and pip dependencies (requests sudo)
make build       # Builds the voice_robot package via colcon
source install/setup.bash

```

> **Note on Builds:** `make build` utilizes `--symlink-install`, meaning changes to Python scripts (`*.py`) take effect immediately without rebuilding. You only need to run `make rebuild` or `make build` after modifying `setup.py`, URDF/xacro files, launch files, or adding new node entry points.

---

## 2. Three Ways to Run the Simulation

### A. Automated Tilix Session (Recommended)

```bash
make sim

```

This builds the package and launches a unified Tilix window divided into four synchronized panes:

```text
+-----------------------------------+-----------------------------------+
|                                   | Voice input                       |  <- Type commands here
|                                   | (speech_command_node)             |
| Gazebo Harmonic & RViz2           +-----------------------------------+
| (robot_sim.launch.py)             | /motor_status                     |  <- Live robot state
|                                   +-----------------------------------+
|                                   | /cmd_vel                          |  <- Live velocity vectors
+-----------------------------------+-----------------------------------+

```

Type `forward`, `left`, `right`, `backward`, or `stop` in the **Voice input** pane and press Enter to drive the robot.

### B. Standard Terminals (No Tilix)

If you prefer to manage your own terminal windows:

```bash
# Terminal 1: Launch the simulated world and ROS-Gazebo bridge
make run

# Terminal 2: Launch the interactive keyboard prompt
make speech

```

### C. Live Microphone Mode

To control the robot via spoken commands (requires a working microphone and an active internet connection for the Google Web Speech API):

```bash
# Terminal 1
make run

# Terminal 2
make mic

```

*Wait for the 2-second ambient noise calibration to complete before speaking.*

---

## 3. Makefile Targets Reference

Run `make help` in your terminal for a live summary of these commands.

| Target | Description |
| --- | --- |
| `build` | Compiles the package using `colcon build --packages-select voice_robot --symlink-install`. |
| `clean` | Removes the `build/voice_robot` and `install/voice_robot` directories. |
| `rebuild` | Executes `clean`, followed immediately by `build`. |
| `sim` | Opens the 4-pane Tilix simulation session (Gazebo, RViz2, Prompt, Topic monitors). |
| `run` | Launches `robot_sim.launch.py` in the current terminal (no Tilix). |
| `speech` | Starts the `speech_command_node` in interactive keyboard mode. |
| `mic` | Starts the `speech_command_node` in live microphone listening mode. |
| `send CMD=<word>` | Injects a single command bypassing the speech node. Default: `make send CMD=forward`. |
| `halt` | Publishes a zero-velocity vector directly to `/cmd_vel` for an emergency stop. |
| `monitor` | Opens `rqt_graph` in a new window to visualize active nodes and topics. |
| `eval` | Launches a split Tilix session running the automated 13-command performance evaluator. |
| `graphs` | Executes `generate_graphs.py` to render PNGs from the latest evaluation CSV data. |
| `kill` | Sends a `pkill` signal to safely force-stop orphaned Gazebo, RViz2, or ROS 2 processes. |
| `deps` | Installs all `apt` and `pip` system dependencies required for the project. |

---

## 4. Voice Commands & Interpretation

The `speech_command_node` normalizes recognized text into strict canonical commands before broadcasting to `/voice_command`.

| Canonical Command | Accepted Input Phrases | Resulting Kinematic Action |
| --- | --- | --- |
| `forward` | forward, move forward, go forward, go | +0.3 m/s linear velocity ($x$) |
| `backward` | backward, back, go back, move back, reverse | -0.3 m/s linear velocity ($x$) |
| `left` | left, turn left, go left | +0.8 rad/s angular velocity ($z$) |
| `right` | right, turn right, go right | -0.8 rad/s angular velocity ($z$) |
| `stop` | stop, halt, freeze, pause | 0.0 m/s, 0.0 rad/s (Immediate halt) |

**Operational Notes:**

* The robotic control logic utilizes **reactive open-loop teleoperation**. The last issued command remains continuously active until a new command or a `stop` command is received.
* Unrecognized phrases trigger a warning in the node log and do not publish any velocity changes.

---

## 5. Tilix Session Architecture & Timing

The `make sim` and `make eval` targets rely on inline `tilix --action` arguments to rapidly construct the workspace layout.

* **Pane Sequencing:** The Makefile uses `sleep $(DELAY)` between pane generation commands to ensure the core simulation (Gazebo/RViz2) is fully initialized before the dependent nodes (speech, interpreter, and monitors) attempt to attach to the DDS network.
* **Adjusting for Slow Hardware:** If the terminal splits appear out of order or close unexpectedly because Gazebo takes too long to load, override the default 2-second delay at runtime:
```bash
make sim DELAY=4

```



---

## 6. Performance Evaluation

The project includes an automated pipeline to benchmark ROS 2 command latency and kinematic accuracy.

1. **Run the sequence:**
```bash
make eval

```


This launches the simulation alongside the `performance_evaluator` node. The script pauses for initialization, then injects a predefined sequence of 13 commands, monitoring `/cmd_vel` to calculate topic latency.
2. **Close the evaluator:** Once the summary prints to the terminal, press **Ctrl+C** in the evaluator pane to stop the spinning node.
3. **Generate Visualizations:**
```bash
make graphs

```


This processes the generated `latency_log.csv` and `accuracy_log.csv` files.

Outputs are written directly to `~/ros2_ws/evaluation_results/`. Check `~/ros2_ws/evaluation_results/graphs/` for the rendered PNG reports detailing command accuracy, latency distribution, and latency by command type.

---

## 7. Troubleshooting

| Symptom | Probable Cause | Resolution |
| --- | --- | --- |
| `Package 'voice_robot' not found` | Workspace not built or sourced. | Run `make build` (the Makefile automatically sources the workspace environment). |
| Robot does not move | Commands aren't reaching the differential drive plugin. | Ensure the Gazebo bridge is running. Test manually: `make halt` then `make send CMD=forward`. |
| No `Command >` prompt appears | `ros2 launch` does not forward standard input (stdin). | Do not try to type inside the `make run` terminal. Use `make sim` or run `make speech` in a separate terminal. |
| `Command >` prompt visible but typing does nothing | Wrong terminal pane has focus. | Click inside the dedicated *Voice input* pane before typing. |
| Tilix panes close instantly | Pane command failed on boot. | Close the window, execute `make kill`, and relaunch with a higher delay: `make sim DELAY=4`. |
| `error: tilix not found` | The Tilix multiplexer is not installed. | Run `make deps`, or fall back to manual terminal execution (`make run` + `make speech`). |
| `rcl_shutdown already called` traceback on `Ctrl+C` | Harmless lifecycle timing issue in older node logic. | Ignore (cosmetic error), or run `make build` to ensure you have the latest code featuring the `if rclpy.ok()` guard. |
| `ModuleNotFoundError: speech_recognition` | Missing pip dependencies. | Run `make deps` to automatically install `SpeechRecognition` via pip. |
| Leftover background processes | Simulation crashed or was closed improperly. | Run `make kill` to execute the cleanup `pkill` sequence. |
