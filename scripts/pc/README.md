# Scripts — development PC

Run these on your **workstation** (or a CI builder), not on the TurtleBot. You need the repo cloned and, for build scripts, ROS 2 sourced (`ROS_DISTRO`).

| Script | Purpose |
|--------|---------|
| **`lint.sh`** | Fast checks without a full ROS build: `compileall`, `xmllint` on `package.xml`, Ruff on Python under `ros2_ws/src/`. |
| **`build_ros.sh`** | Lint → `colcon build` → `colcon test` in `ros2_ws/`. Symlinks **`turtlebot3_description`** and **`turtlebot3_teleop`** from `turtlebot3/` into `ros2_ws/src/` so RViz and teleop resolve without duplicating packages. |
| **`build_workspace.sh`** | Same as `build_ros.sh` (alias name). |
| **`docker_build_robot.sh`** | `docker buildx` for **`linux/arm64`**, push `turtlebot-rfid-robot` to your registry (`nas_reg`, `TAG`). Optional quick colcon via `quick_robot_colcon.sh`. |
| **`quick_robot_colcon.sh`** | Build selected packages inside a **robotdeps** image (fast iteration before a full image build). |
| **`echo_robot_scan.sh`** | On the PC, `ros2 topic echo /scan` with **`sensor_data`** QoS and **`ROS_DOMAIN_ID`** matching the robot (default **1**). Use when debugging LiDAR over Wi‑Fi. |
| **`run_rviz_robot.sh`** | Launch RViz2 with configs from `rviz_configs/`, same DDS domain as the robot. Requires a built workspace so `turtlebot3_description` resolves. |
| **`teleop_keyboard.sh`** | Run **`turtlebot3_teleop`** / **`teleop_keyboard`** after `colcon build --packages-select turtlebot3_teleop` (or `sudo apt install ros-$ROS_DISTRO-turtlebot3-teleop`). Publishes **`/cmd_vel`**; match **`ROS_DOMAIN_ID`** and **`TURTLEBOT3_MODEL`** to the robot. Use **`./scripts/pc/teleop_keyboard.sh --sim`** (or **`TELEOP_INVERT_LINEAR=1`**) when Gazebo drives opposite to hardware. |

**Typical flow:** `./scripts/pc/lint.sh` → `./scripts/pc/build_workspace.sh` → `./scripts/pc/docker_build_robot.sh` (after robot code changes).
