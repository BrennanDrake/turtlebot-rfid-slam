#!/usr/bin/env bash
# Keyboard teleop for TurtleBot3: publishes to **/cmd_vel** (same DDS graph as the robot).
#
# Requires **turtlebot3_teleop** in your workspace (symlinked by **build_ros.sh**) or:
#   sudo apt install ros-${ROS_DISTRO}-turtlebot3-teleop
#
# Usage (repo root, after **source ros2_ws/install/setup.bash**):
#   ./scripts/pc/teleop_keyboard.sh
#   ./scripts/pc/teleop_keyboard.sh --sim          # invert linear.x for Gazebo (see TELEOP_INVERT_* below)
#   TURTLEBOT3_MODEL=waffle ./scripts/pc/teleop_keyboard.sh
#   ROS_DOMAIN_ID=1 ./scripts/pc/teleop_keyboard.sh
#
# Simulation (Gazebo / gz) often drives the opposite way to the real robot for the same keys.
# Use **--sim** or **TELEOP_INVERT_LINEAR=1** only when teleoping sim; keep defaults for hardware.
# Optional: **TELEOP_INVERT_ANGULAR=1** if turn keys are reversed in sim only.
#
set -euo pipefail

while [[ $# -gt 0 ]]; do
  case "$1" in
    --sim)
      export TELEOP_INVERT_LINEAR=1
      shift
      ;;
    *)
      break
      ;;
  esac
done

ROOT="$(git -C "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)" rev-parse --show-toplevel)"
export ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-1}"
export TURTLEBOT3_MODEL="${TURTLEBOT3_MODEL:-burger}"

if [[ -f "${ROOT}/ros2_ws/install/setup.bash" ]]; then
  # shellcheck disable=SC1090
  source "${ROOT}/ros2_ws/install/setup.bash"
elif [[ -n "${ROS_DISTRO:-}" && -f "/opt/ros/${ROS_DISTRO}/setup.bash" ]]; then
  # shellcheck disable=SC1090
  source "/opt/ros/${ROS_DISTRO}/setup.bash"
else
  echo "[teleop_keyboard] Source ROS 2 and build ros2_ws (need turtlebot3_teleop), or apt install ros-\$ROS_DISTRO-turtlebot3-teleop." >&2
  exit 1
fi

if ! ros2 pkg prefix turtlebot3_teleop &>/dev/null; then
  echo "[teleop_keyboard] Package turtlebot3_teleop not found." >&2
  echo "  Build: (cd ${ROOT}/ros2_ws && colcon build --symlink-install --packages-select turtlebot3_teleop)" >&2
  echo "  Or:   sudo apt install ros-\${ROS_DISTRO}-turtlebot3-teleop" >&2
  exit 1
fi

echo "[teleop_keyboard] ROS_DOMAIN_ID=${ROS_DOMAIN_ID} TURTLEBOT3_MODEL=${TURTLEBOT3_MODEL} TELEOP_INVERT_LINEAR=${TELEOP_INVERT_LINEAR:-0} TELEOP_INVERT_ANGULAR=${TELEOP_INVERT_ANGULAR:-0} — keep this terminal focused." >&2
exec ros2 run turtlebot3_teleop teleop_keyboard
