#!/usr/bin/env bash
# Run RViz2 with a config from repo **rviz_configs/** and the same default DDS domain as
# **run_robot_docker.sh** (ROS_DOMAIN_ID=1 unless overridden).
#
# RViz resolves **package://turtlebot3_description/...** mesh paths on *this* PC. Run
# **./scripts/pc/build_workspace.sh** (or **make build**) once — it symlinks vendored turtlebot3_description
# into ros2_ws and builds — then source **ros2_ws/install/setup.bash** (this script does if present).
#
# Usage (repo root, on your dev PC):
#   ./scripts/pc/run_rviz_robot.sh
#   ./scripts/pc/run_rviz_robot.sh rviz_1.rviz
#   ROS_DOMAIN_ID=42 ./scripts/pc/run_rviz_robot.sh
#
# Do not use `set -u`: colcon's install/setup.bash references unset optional vars (e.g. COLCON_TRACE).
set -eo pipefail

ROOT="$(git -C "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)" rev-parse --show-toplevel)"
CFG_DIR="${ROOT}/rviz_configs"

export ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-1}"

# Overlay: vendored TurtleBot3 meshes for package:// URIs (robot_description from the bot references these).
if [[ -f "${ROOT}/ros2_ws/install/setup.bash" ]]; then
  # shellcheck disable=SC1090
  source "${ROOT}/ros2_ws/install/setup.bash"
elif [[ -n "${ROS_DISTRO:-}" && -f "/opt/ros/${ROS_DISTRO}/setup.bash" ]]; then
  # shellcheck disable=SC1090
  source "/opt/ros/${ROS_DISTRO}/setup.bash"
fi

CONFIG_NAME="${1:-rviz_1.rviz}"
CONFIG_PATH="${CFG_DIR}/${CONFIG_NAME}"

if [[ ! -d "${CFG_DIR}" ]]; then
  echo "[run_rviz_robot] missing config directory: ${CFG_DIR}" >&2
  exit 1
fi

if [[ ! -f "${CONFIG_PATH}" ]]; then
  echo "[run_rviz_robot] config not found: ${CONFIG_PATH}" >&2
  echo "  Available under ${CFG_DIR}:" >&2
  shopt -s nullglob
  for f in "${CFG_DIR}"/*.rviz; do
    echo "    $(basename "$f")" >&2
  done
  exit 1
fi

if ! command -v rviz2 >/dev/null 2>&1; then
  echo "[run_rviz_robot] rviz2 not in PATH — install ros-jazzy-rviz (or humble) or source /opt/ros/\$ROS_DISTRO/setup.bash." >&2
  exit 1
fi

if ! command -v ros2 >/dev/null 2>&1 || ! ros2 pkg prefix turtlebot3_description &>/dev/null; then
  echo "[run_rviz_robot] turtlebot3_description is not in your environment (needed for package:// mesh paths)." >&2
  echo "  From repo root (with ROS_DISTRO set):" >&2
  echo "    ./scripts/pc/build_workspace.sh --skip-test" >&2
  echo "    source ${ROOT}/ros2_ws/install/setup.bash" >&2
  exit 1
fi

echo "[run_rviz_robot] ROS_DOMAIN_ID=${ROS_DOMAIN_ID} turtlebot3_description=$(ros2 pkg prefix turtlebot3_description)" >&2
echo "[run_rviz_robot] Note: rviz_configs default uses RobotModel → Description Topic /robot_description from the **robot**." >&2
echo "[run_rviz_robot]   Wheel spin / URDF changes apply after **rebuilding & running the robot Docker image**, not only PC colcon." >&2
echo "[run_rviz_robot] rviz2 -d ${CONFIG_PATH}" >&2
exec rviz2 -d "${CONFIG_PATH}"
