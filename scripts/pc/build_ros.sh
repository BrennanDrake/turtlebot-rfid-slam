#!/usr/bin/env bash
# Build the ROS 2 workspace and run package tests (ament linters + pytest).
#
# Ensures symlinks under **ros2_ws/src/** to vendored TurtleBot3 packages:
# - **turtlebot3_description** (RViz `package://` URIs)
# - **turtlebot3_teleop** (keyboard teleop: `ros2 run turtlebot3_teleop teleop_keyboard`)
#
# Usage (from repo root):
#   ./scripts/pc/build_ros.sh              # lint -> colcon build -> colcon test
#   ./scripts/pc/build_workspace.sh        # same as build_ros.sh (alias name)
#   ./scripts/pc/build_ros.sh --skip-test  # lint -> colcon build only
#   ./scripts/pc/build_ros.sh -- --cmake-args -DCMAKE_BUILD_TYPE=Release
#   (Symlinks ./scripts/build_ros.sh and ./scripts/build_workspace.sh also work.)
#
# Requires: ROS 2 environment (e.g. source /opt/ros/$ROS_DISTRO/setup.bash)
# Optional: .venv with ruff (see requirements-dev.txt) for fast pre-checks.

set -euo pipefail

ROOT="$(git -C "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)" rev-parse --show-toplevel)"
SKIP_TEST=0
PASSTHRU=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --skip-test) SKIP_TEST=1; shift ;;
    --) shift; PASSTHRU+=("$@"); break ;;
    *) PASSTHRU+=("$1"); shift ;;
  esac
done

"${ROOT}/scripts/pc/lint.sh"

: "${ROS_DISTRO:?Set ROS_DISTRO or source /opt/ros/<distro>/setup.bash}"
# shellcheck disable=SC1090
source "/opt/ros/${ROS_DISTRO}/setup.bash"

TB3_DESC="${ROOT}/turtlebot3/turtlebot3_description"
TB3_LINK="${ROOT}/ros2_ws/src/turtlebot3_description"
if [[ ! -d "${TB3_DESC}" ]]; then
  echo "[build] missing vendored TurtleBot3 description: ${TB3_DESC}" >&2
  exit 1
fi
mkdir -p "${ROOT}/ros2_ws/src"
ln -sfn "../../turtlebot3/turtlebot3_description" "${TB3_LINK}"
echo "[build] symlink ${TB3_LINK} -> turtlebot3/turtlebot3_description"

TB3_TELEOP="${ROOT}/turtlebot3/turtlebot3_teleop"
TB3_TELEOP_LINK="${ROOT}/ros2_ws/src/turtlebot3_teleop"
if [[ ! -d "${TB3_TELEOP}" ]]; then
  echo "[build] missing vendored turtlebot3_teleop: ${TB3_TELEOP}" >&2
  exit 1
fi
ln -sfn "../../turtlebot3/turtlebot3_teleop" "${TB3_TELEOP_LINK}"
echo "[build] symlink ${TB3_TELEOP_LINK} -> turtlebot3/turtlebot3_teleop"

cd "${ROOT}/ros2_ws"
echo "[build] colcon build ${PASSTHRU[*]}"
colcon build --symlink-install "${PASSTHRU[@]}"

if [[ "${SKIP_TEST}" -eq 1 ]]; then
  echo "[build] skipping colcon test (--skip-test)"
  exit 0
fi

echo "[build] colcon test (linters run as tests in ament packages)"
colcon test --event-handlers console_direct+
colcon test-result --verbose
