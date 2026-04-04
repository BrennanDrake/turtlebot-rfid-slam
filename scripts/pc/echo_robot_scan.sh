#!/usr/bin/env bash
# On your **dev PC** (same Wi‑Fi/LAN as the robot): subscribe to **/scan** with settings that match
# the LiDAR driver (HLDS for **LDS-01**, ld08_driver for **LDS-02** — both use **SensorDataQoS**):
#   - **ROS_DOMAIN_ID** must match **run_robot_docker.sh** (default **1**).
#   - Uses **`--qos-profile sensor_data`** (not only `--qos-reliability best_effort`).
#   - Uses **`--no-daemon`** so the ROS 2 CLI daemon does not leave subscriptions stuck with no output
#     (a common cause of “hangs” even when `ros2 topic list` shows /scan).
#
# Usage (repo root, on your dev PC):
#   ./scripts/pc/echo_robot_scan.sh
#   ./scripts/pc/echo_robot_scan.sh --once
#   ./scripts/pc/echo_robot_scan.sh --field header --once
#   ROS_DOMAIN_ID=42 ./scripts/pc/echo_robot_scan.sh
#
# If it still hangs: `ros2 daemon stop` once, then retry. Check Wi‑Fi AP isolation / multicast.
#
set -eo pipefail

ROOT="$(git -C "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)" rev-parse --show-toplevel)"
export ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-1}"
if [[ "${ROS_DOMAIN_ID}" == "0" ]]; then
  echo "[echo_robot_scan] warning: ROS_DOMAIN_ID is 0; run_robot_docker defaults to 1. Try: ROS_DOMAIN_ID=1 $0" >&2
fi

if [[ -f "${ROOT}/ros2_ws/install/setup.bash" ]]; then
  # shellcheck disable=SC1090
  source "${ROOT}/ros2_ws/install/setup.bash"
elif [[ -n "${ROS_DISTRO:-}" && -f "/opt/ros/${ROS_DISTRO}/setup.bash" ]]; then
  # shellcheck disable=SC1090
  source "/opt/ros/${ROS_DISTRO}/setup.bash"
else
  echo "[echo_robot_scan] Source ROS 2 first, or build ros2_ws so ${ROOT}/ros2_ws/install/setup.bash exists." >&2
  echo "  Example: export ROS_DISTRO=jazzy && source /opt/ros/jazzy/setup.bash" >&2
  exit 1
fi

if ! command -v ros2 >/dev/null 2>&1; then
  echo "[echo_robot_scan] ros2 not on PATH after sourcing." >&2
  exit 1
fi

echo "[echo_robot_scan] ROS_DOMAIN_ID=${ROS_DOMAIN_ID} (must match robot container)" >&2
echo "[echo_robot_scan] ros2 topic echo /scan --no-daemon --qos-profile sensor_data $*" >&2
exec ros2 topic echo /scan --no-daemon --qos-profile sensor_data "$@"
