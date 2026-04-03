#!/usr/bin/env bash
# Merge vendored TurtleBot3 packages + ros2_ws/src into a colcon workspace src/ tree.
# Used by robot/Dockerfile and scripts/quick_robot_colcon.sh (single source of truth).
set -euo pipefail
TURTLEBOT3_ROOT="${1:?usage: merge_src.sh TURTLEBOT3_ROOT ROS2_SRC DEST}"
ROS2_SRC="${2:?}"
DEST="${3:?}"
mkdir -p "${DEST}"
for pkg in turtlebot3 turtlebot3_bringup turtlebot3_cartographer turtlebot3_description \
           turtlebot3_example turtlebot3_navigation2 turtlebot3_node turtlebot3_teleop; do
  cp -a "${TURTLEBOT3_ROOT}/${pkg}" "${DEST}/"
done
if compgen -G "${ROS2_SRC}"/\* >/dev/null 2>&1; then
  cp -a "${ROS2_SRC}"/* "${DEST}/"
fi
