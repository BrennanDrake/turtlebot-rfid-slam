#!/usr/bin/env bash
# Merge vendored TurtleBot3 packages + ros2_ws/src into a colcon workspace src/ tree.
# Used by robot/Dockerfile and scripts/pc/quick_robot_colcon.sh (single source of truth).
set -euo pipefail
TURTLEBOT3_ROOT="${1:?usage: merge_src.sh TURTLEBOT3_ROOT ROS2_SRC DEST}"
ROS2_SRC="${2:?}"
DEST="${3:?}"
mkdir -p "${DEST}"
for pkg in turtlebot3 turtlebot3_bringup turtlebot3_cartographer turtlebot3_description \
           turtlebot3_example turtlebot3_navigation2 turtlebot3_node turtlebot3_teleop; do
  cp -a "${TURTLEBOT3_ROOT}/${pkg}" "${DEST}/"
done
# ros2_ws/src may contain a **symlink** to vendored packages (e.g. turtlebot3_description for
# local colcon). Vendored dirs are copied above; skip same basename so we do not `cp` a symlink
# onto a directory (cp: cannot overwrite directory … with non-directory).
if compgen -G "${ROS2_SRC}"/\* >/dev/null 2>&1; then
  for item in "${ROS2_SRC}"/*; do
    base="$(basename "${item}")"
    # Colcon must run from ros2_ws/, not ros2_ws/src/. If build/install/log were created
    # under src/ by mistake, copying them breaks rosdep (nested install/share paths).
    case "${base}" in
      install|build|log) continue ;;
    esac
    if [[ -e "${DEST}/${base}" ]]; then
      continue
    fi
    cp -a "${item}" "${DEST}/"
  done
fi
