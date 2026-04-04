#!/usr/bin/env bash
# Run `ros2` inside the robot container (same graph as bringup). Prefer this over host `ros2` on the Pi.
#
# Why not plain `ros2` on the robot?
# - Host ROS may be another distro / ROS_DOMAIN_ID → different topic list than the container.
# - Low RAM: host `ros2 topic list` can be OOM-killed ("Killed"); image sets ROS_DISABLE_ROS2_DAEMON=1.
#   On the host only, use: ROS_DISABLE_ROS2_DAEMON=1 ros2 ...
#
# Subcommands are `ros2 topic …`, `ros2 node …`, not `ros2 echo` (that will error).
#
# If `ros2 topic echo /scan` prints "sequence size exceeds remaining buffer", another machine on the
# LAN is usually polluting the same ROS_DOMAIN_ID (e.g. Jazzy PC + Humble robot both default to 0).
# run_robot_docker.sh defaults ROS_DOMAIN_ID=1; use the same on your PC (scripts/pc/run_rviz_robot.sh).
# Prefer `topic hz` to verify LaserScan without huge messages:
#   ./scripts/robot/robot_ros2.sh topic hz /scan --qos-reliability best_effort
#
# Usage (on the Pi / SSH to robot; container must be running):
#   ./scripts/robot/robot_ros2.sh topic list
#   ./scripts/robot/robot_ros2.sh topic hz /scan --qos-reliability best_effort
#   ./scripts/robot/robot_ros2.sh topic echo /scan --once --qos-reliability best_effort
#
set -euo pipefail

CONTAINER_NAME="${CONTAINER_NAME:-turtlebot-rfid}"

if ! docker ps --format '{{.Names}}' | grep -qx "${CONTAINER_NAME}"; then
  echo "[robot_ros2] container '${CONTAINER_NAME}' is not running." >&2
  exit 1
fi

exec docker exec -it "${CONTAINER_NAME}" bash -lc '
  export ROS_DISABLE_ROS2_DAEMON=1
  source /opt/ros/humble/setup.bash
  source /colcon_ws/install/setup.bash
  exec ros2 "$@"
' _ "$@"
