# Voice-Controlled Mobile Robot - Makefile
# ROS 2 Jazzy / Gazebo Harmonic / Ubuntu 24.04
#
# Run make from the workspace root (the folder that contains src/, build/, install/).

SHELL         := /bin/bash
WORKSPACE_DIR := $(shell pwd)
ROS_SETUP     := /opt/ros/jazzy/setup.bash
WS_SETUP      := $(WORKSPACE_DIR)/install/setup.bash
PKG           := voice_robot
ENV           := source $(ROS_SETUP) && source $(WS_SETUP)

# Overridable:  make send CMD=left   |   make sim DELAY=4   |   make sim SPEECH_ARGS=
CMD           ?= forward
DELAY         ?= 2
SPEECH_ARGS   ?= --keyboard

# Blocks until the simulation nodes are up (used by panes that need them).
WAIT_SIM      := until ros2 node list 2>/dev/null | grep -q command_interpreter_node; do sleep 1; done

.PHONY: all build clean rebuild sim run speech mic send halt eval graphs monitor kill deps help

# Default target
all: build

# Build
build:
	@echo "Building $(PKG)..."
	@source $(ROS_SETUP) && colcon build --packages-select $(PKG) --symlink-install

# Clean (this package only - other packages in the workspace are untouched)
clean:
	@echo "Cleaning $(PKG) build and install directories..."
	rm -rf build/$(PKG) install/$(PKG)

rebuild: clean build

# Simulation
# Opens a new Tilix session split into four panes:
#   left  : Gazebo + RViz2 + interpreter + motor monitor
#   right : voice input prompt / /motor_status / /cmd_vel
# Each split acts on the focused pane, so the calls are sequential with a short delay.
sim: build
	@echo "Launching simulation..."
	tilix --action=app-new-session -e "bash -c '$(ENV) && ros2 launch $(PKG) robot_sim.launch.py; exec bash'"
	@sleep $(DELAY)
	tilix --action=session-add-right -e "bash -c '$(ENV) && $(WAIT_SIM); ros2 run $(PKG) speech_command_node $(SPEECH_ARGS); exec bash'"
	@sleep $(DELAY)
	tilix --action=session-add-down -e "bash -c '$(ENV) && ros2 topic echo /motor_status std_msgs/msg/String; exec bash'"
	@sleep $(DELAY)
	tilix --action=session-add-down -e "bash -c '$(ENV) && ros2 topic echo /cmd_vel geometry_msgs/msg/Twist; exec bash'"

# Run simulation in THIS terminal (no Tilix). Use 'make speech' in a second terminal.
run: build
	@echo "Launching simulation in this terminal..."
	@$(ENV) && ros2 launch $(PKG) robot_sim.launch.py

# Voice input in this terminal (simulation must be running)
speech:
	@$(ENV) && ros2 run $(PKG) speech_command_node $(SPEECH_ARGS)

mic:
	@$(ENV) && ros2 run $(PKG) speech_command_node

# Inject one command without the speech node:  make send CMD=left
send:
	@$(ENV) && ros2 topic pub --once /voice_command std_msgs/msg/String "{data: '$(CMD)'}"

# Zero velocity straight to /cmd_vel
halt:
	@$(ENV) && ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.0}, angular: {z: 0.0}}"

# Performance evaluation
# Opens a new Tilix session: simulation | evaluator / shell (for 'make graphs').
# The evaluator keeps spinning after it prints the summary - press Ctrl+C in its pane.
eval: build
	@echo "Launching evaluation session..."
	tilix --action=app-new-session -e "bash -c '$(ENV) && ros2 launch $(PKG) robot_sim.launch.py; exec bash'"
	@sleep $(DELAY)
	tilix --action=session-add-right -e "bash -c '$(ENV) && $(WAIT_SIM); sleep 2; ros2 run $(PKG) performance_evaluator; exec bash'"
	@sleep $(DELAY)
	tilix --action=session-add-down -e "bash -c 'cd $(WORKSPACE_DIR) && $(ENV); exec bash'"

# Graphs from the latest evaluation CSVs (~/ros2_ws/evaluation_results/graphs)
graphs:
	@python3 $(WORKSPACE_DIR)/src/$(PKG)/$(PKG)/generate_graphs.py

# Node / topic graph
monitor:
	@echo "Launching rqt_graph..."
	tilix --action=app-new-session -e "bash -c '$(ENV) && ros2 run rqt_graph rqt_graph; exec bash'"

# Force-stop leftover Gazebo / ROS processes of this project
kill:
	-@pkill -f '[g]z[- ]sim|[p]arameter_bridge|[r]viz2|[r]obot_state_publisher|[j]oint_state_publisher|[c]ommand_interpreter_node|[m]otor_control_node|[s]peech_command_node|[p]erformance_evaluator'; echo "Stop signal sent (if anything was running)."

# One-time dependency install (needs sudo)
deps:
	sudo apt update
	sudo apt install -y ros-jazzy-ros-gz ros-jazzy-xacro ros-jazzy-robot-state-publisher \
	  ros-jazzy-joint-state-publisher ros-jazzy-rviz2 ros-jazzy-rqt-graph \
	  python3-colcon-common-extensions python3-matplotlib python3-numpy \
	  portaudio19-dev python3-pyaudio tilix
	python3 -m pip install --user --break-system-packages SpeechRecognition

# Help
help:
	@echo ""
	@echo "Voice-Controlled Mobile Robot"
	@echo "============================="
	@echo ""
	@echo "Available commands (run from the workspace root):"
	@echo ""
	@echo "  make build      Build the voice_robot package with colcon."
	@echo "  make clean      Remove this package's build and install directories."
	@echo "  make rebuild    Clean, then build."
	@echo ""
	@echo "  make sim        Build, then open a split Tilix session: Gazebo/RViz2,"
	@echo "                  voice prompt, /motor_status and /cmd_vel."
	@echo "                  (SPEECH_ARGS= for microphone mode, DELAY=4 on slow machines)"
	@echo "  make run        Build and run the simulation in this terminal only."
	@echo "  make speech     Keyboard voice prompt in this terminal."
	@echo "  make mic        Microphone voice input (needs internet)."
	@echo "  make send       Publish one command, e.g. make send CMD=left"
	@echo "  make halt       Publish zero velocity on /cmd_vel."
	@echo ""
	@echo "  make eval       Open a Tilix session: simulation, evaluator, shell."
	@echo "  make graphs     Generate the report graphs from the latest results."
	@echo "  make monitor    Open rqt_graph in a new Tilix session."
	@echo ""
	@echo "  make kill       Force-stop leftover Gazebo / ROS processes."
	@echo "  make deps       Install apt and pip dependencies (sudo)."
	@echo "  make help       Display this help message."
	@echo ""
	@echo "Environment:"
	@echo "  ROS 2      : Jazzy"
	@echo "  Workspace  : $(WORKSPACE_DIR)"
	@echo ""
