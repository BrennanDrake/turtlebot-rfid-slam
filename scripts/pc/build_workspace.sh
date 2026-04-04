#!/usr/bin/env bash
# Same as **build_ros.sh** — workspace build + optional tests; creates the turtlebot3_description
# symlink under ros2_ws/src automatically. Prefer this name if you only remember "build workspace".
#
# Usage (from repo root, with ROS_DISTRO set or after sourcing /opt/ros/...):
#   ./scripts/pc/build_workspace.sh
#   ./scripts/pc/build_workspace.sh --skip-test
#
set -euo pipefail
ROOT="$(git -C "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)" rev-parse --show-toplevel)"
exec "${ROOT}/scripts/pc/build_ros.sh" "$@"
