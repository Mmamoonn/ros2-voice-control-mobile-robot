# Requirements

Everything needed to build and run the Voice-Controlled Mobile Robot simulation. After configuring your environment, run **`make help`** from the workspace root to verify available commands.

---

## 1. Platform

| Item | Required | Notes |
| --- | --- | --- |
| Operating system | Ubuntu 24.04 LTS (Noble) | The primary target for this deployment. Other releases are untested.

 |
| ROS 2 | **Jazzy Jalisco** | Ensure a full desktop installation (`ros-jazzy-desktop`) which includes RViz2.

 |
| Simulator | **Gazebo Harmonic** | Installed automatically via `ros-jazzy-ros-gz`.

 |
| Python | 3.12 | Ubuntu 24.04 default system Python. |
| Build tool | colcon | Installed via `python3-colcon-common-extensions`. |
| Graphical session | X11 or Wayland | Gazebo and RViz2 require a display and working OpenGL.

 |

> **Not compatible:** Gazebo Classic plugins (`libgazebo_ros_*.so`). The robot uses Gazebo Harmonic's native `gz-sim-diff-drive-system` plugin. ROS 2 Humble pairs with a different Gazebo release (Fortress) and its `ros_gz` packages differ; do not expect this package to work there unchanged.
> 
> 

---

## 2. Hardware

| Item | Requirement |
| --- | --- |
| CPU / RAM | A machine that comfortably runs Gazebo + RViz2 together. Both are GPU-sensitive; a dedicated or modern integrated GPU is recommended. |
| Graphics | OpenGL 3.3 or newer is generally required by Gazebo's renderer. |
| Microphone | **Optional** - only required for testing live audio with `make mic`.

 |
| Network | **Optional** - only required for microphone mode (routes to Google Web Speech API) and for initially installing packages.

 |
| Robot hardware | **Not required.** The physical Arduino/ESP32, HC-05 Bluetooth module, and L298N motor drivers from the initial proposal are explicitly outside the scope of this simulation deliverable.

 |

---

## 3. System Packages (`apt`)

Running `make deps` from the workspace root installs all required system dependencies automatically:

| Package | Purpose |
| --- | --- |
| `ros-jazzy-ros-gz` | Gazebo Harmonic + `ros_gz_sim` (launch/spawn) + `ros_gz_bridge`.

 |
| `ros-jazzy-xacro` | Processes the URDF/xacro robot description.

 |
| `ros-jazzy-robot-state-publisher` | Publishes the TF tree from the URDF.

 |
| `ros-jazzy-joint-state-publisher` | Publishes simulated wheel joint states.

 |
| `ros-jazzy-rviz2` | Provides 3D trajectory and TF visualization.

 |
| `ros-jazzy-rqt-graph` | Visualizes node/topic relationships (accessible via `make monitor`). |
| `python3-colcon-common-extensions` | Enables building the workspace via `colcon build`. |
| `python3-matplotlib`, `python3-numpy` | Renders performance evaluation graphs.

 |
| `portaudio19-dev`, `python3-pyaudio` | Enables microphone audio capture for the speech node.

 |
| `tilix` | Terminal multiplexer used to run multi-pane simulation sessions (`make sim` / `make eval`). |

Equivalent manual command executed by the Makefile:

```bash
sudo apt update
sudo apt install -y ros-jazzy-ros-gz ros-jazzy-xacro ros-jazzy-robot-state-publisher \
  ros-jazzy-joint-state-publisher ros-jazzy-rviz2 ros-jazzy-rqt-graph \
  python3-colcon-common-extensions python3-matplotlib python3-numpy \
  portaudio19-dev python3-pyaudio tilix

```

---

## 4. Python Packages

| Package | Needed for | Install Method |
| --- | --- | --- |
| `SpeechRecognition` | Microphone mode (`speech_command_node`)

 | `make deps` (pip) |
| `pyaudio` | Microphone mode (`speech_command_node`)

 | `make deps` (apt: `python3-pyaudio`) |
| `matplotlib`, `numpy` | `make graphs` | `make deps` (apt) |

The `make deps` target automatically handles the `SpeechRecognition` library by running `python3 -m pip install --user --break-system-packages SpeechRecognition`. Ubuntu 24.04 marks the system Python as externally managed, necessitating this flag.

Everything else the nodes import (`rclpy`, `std_msgs`, `geometry_msgs`, `threading`) comes standard with ROS 2 or the Python standard library.

---

## 5. ROS Package Dependencies (Declared in `package.xml`)

Core dependencies include `rclpy`, `std_msgs`, `geometry_msgs`, `robot_state_publisher`, `joint_state_publisher`, `xacro`, `ros_gz_sim`, and `ros_gz_bridge`.

The launch files additionally rely on `rviz2` and bridge message packages `nav_msgs`, `tf2_msgs`, and `rosgraph_msgs` (all included within `ros-jazzy-desktop`).

---

## 6. Workspace Layout

* **Expected Path:** `~/ros2_ws/src/voice_robot`
* The `Makefile` expects to be run from the workspace root (e.g., `~/ros2_ws`).
* The automated performance evaluator specifically writes results to the fixed path `~/ros2_ws/evaluation_results/`.


* *Note:* Avoid spaces in the project path. While the shell scripts quote paths, the Tilix `-e` command strings may fail to parse spaces correctly.

---

## 7. Verification Checklist

To confirm your environment is correctly configured, run the following commands sequentially from the workspace root:

```bash
make deps              # Installs all apt and pip requirements
make build             # Builds the voice_robot package
make sim               # Opens a split Tilix session with Gazebo, RViz2, and prompt

```

Once the simulation is running, test the command interpretation pipeline from the Tilix prompt pane or a separate terminal:

```bash
make send CMD=forward  # The robot should move forward in Gazebo
make halt              # The robot should stop

```
