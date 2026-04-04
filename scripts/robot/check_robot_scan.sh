#!/usr/bin/env bash
# Run on the TurtleBot (host shell). Diagnoses why LaserScan may be invisible in RViz / CLI.
#
# HLDS publishes /scan with sensor/best-effort QoS. On **ROS 2 Humble**, `ros2 topic hz /scan` often
# shows **no output** (hz cannot set QoS to match sensor_data). This script uses **`ros2 topic echo`**
# with **`--qos-profile sensor_data`** as the real check; RViz: LaserScan → QoS → Best effort.
#
# Usage (on the Pi; container must be running):
#   ./scripts/robot/check_robot_scan.sh
#   CONTAINER_NAME=mybot ./scripts/robot/check_robot_scan.sh
#
set -euo pipefail

CONTAINER_NAME="${CONTAINER_NAME:-turtlebot-rfid}"

if ! docker ps --format '{{.Names}}' | grep -qx "${CONTAINER_NAME}"; then
  echo "[check_robot_scan] container '${CONTAINER_NAME}' is not running." >&2
  echo "  Start it (e.g. run_robot_docker.sh) or set CONTAINER_NAME=..." >&2
  exit 1
fi

docker exec "${CONTAINER_NAME}" bash -c '
  set -eo pipefail
  export ROS_DISABLE_ROS2_DAEMON=1
  source /opt/ros/humble/setup.bash
  source /colcon_ws/install/setup.bash
  _f() { grep -v "sequence size exceeds remaining buffer" || true; }

  echo "[check_robot_scan] topics matching scan (inside container):" >&2
  ros2 topic list 2>&1 | _f | grep -E "scan|Scan" || true

  echo "" >&2
  echo "[check_robot_scan] one LaserScan message (sensor_data QoS — authoritative on Humble):" >&2
  timeout 10 ros2 topic echo /scan --once --no-daemon --qos-profile sensor_data 2>&1 | _f || true

  echo "" >&2
  echo "[check_robot_scan] optional: hz /scan (often empty on Humble; ignore if echo above worked):" >&2
  timeout 6 ros2 topic hz /scan --window 20 2>&1 | _f || true
'

echo "" >&2
echo "[check_robot_scan] If echo shows ranges but RViz is empty: LaserScan display → QoS → Best effort." >&2
echo "[check_robot_scan] If echo is empty: LDS_MODEL (LDS-01 vs LDS-02), USB mapping, docker logs. Use ./scripts/robot/robot_ros2.sh topic list / node list." >&2
