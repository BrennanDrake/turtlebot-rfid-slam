#!/usr/bin/env bash
# Build the ROS 2 workspace and run package tests (ament linters + pytest).
#
# Usage (from repo root):
#   ./scripts/build_ros.sh              # lint -> colcon build -> colcon test
#   ./scripts/build_ros.sh --skip-test  # lint -> colcon build only
#   ./scripts/build_ros.sh -- --cmake-args -DCMAKE_BUILD_TYPE=Release
#
# Requires: ROS 2 environment (e.g. source /opt/ros/$ROS_DISTRO/setup.bash)
# Optional: .venv with ruff (see requirements-dev.txt) for fast pre-checks.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKIP_TEST=0
PASSTHRU=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --skip-test) SKIP_TEST=1; shift ;;
    --) shift; PASSTHRU+=("$@"); break ;;
    *) PASSTHRU+=("$1"); shift ;;
  esac
done

"${ROOT}/scripts/lint.sh"

: "${ROS_DISTRO:?Set ROS_DISTRO or source /opt/ros/<distro>/setup.bash}"
# shellcheck disable=SC1090
source "/opt/ros/${ROS_DISTRO}/setup.bash"

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
