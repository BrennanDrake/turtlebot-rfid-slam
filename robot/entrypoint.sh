#!/usr/bin/env bash
# Start TurtleBot3 + LiDAR + RFID inside the robot image. Override devices with env (see AGENTS.md).
set -eo pipefail

source /opt/ros/humble/setup.bash
source /colcon_ws/install/setup.bash

export TURTLEBOT3_MODEL="${TURTLEBOT3_MODEL:-burger}"
export LDS_MODEL="${LDS_MODEL:-LDS-02}"

RFID_SERIAL_PORT="${RFID_SERIAL_PORT:-/dev/ttyUSB0}"
LIDAR_PORT="${LIDAR_PORT:-/dev/ttyUSB1}"

if [[ ! -c "${LIDAR_PORT}" ]]; then
  echo "[entrypoint] WARNING: LIDAR_PORT=${LIDAR_PORT} is not a character device — check docker --device and host tty (empty /scan)." >&2
fi
if [[ ! -c "${RFID_SERIAL_PORT}" ]]; then
  echo "[entrypoint] WARNING: RFID_SERIAL_PORT=${RFID_SERIAL_PORT} is not a character device — check docker --device." >&2
fi

echo "[entrypoint] starting turtlebot3_bringup (LIDAR_PORT=${LIDAR_PORT} RFID_SERIAL_PORT=${RFID_SERIAL_PORT})" >&2
if ! command -v ros2 >/dev/null 2>&1; then
  echo "[entrypoint] error: ros2 not on PATH after sourcing install" >&2
  exit 1
fi

exec ros2 launch turtlebot3_bringup robot.launch.py \
  "lidar_port:=${LIDAR_PORT}" \
  "rfid_serial_port:=${RFID_SERIAL_PORT}" \
  "$@"
