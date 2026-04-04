#!/usr/bin/env bash
# Pull and run the robot image on the TurtleBot (Pi). Intended for boot/cron: TAG=latest by default.
#
# Usage:
#   nas_reg=192.168.1.203:5000 ./scripts/robot/run_robot_docker.sh
#   TAG=1.0 nas_reg=... ./scripts/robot/run_robot_docker.sh
#   INTERACTIVE=1 nas_reg=... ./scripts/robot/run_robot_docker.sh
#   SKIP_PULL=1 nas_reg=... ./scripts/robot/run_robot_docker.sh
#
# DDS domain: defaults to 1 (avoids noisy default 0 on mixed LANs). Override if needed:
#   ROS_DOMAIN_ID=42 nas_reg=... ./scripts/robot/run_robot_docker.sh
# Use the same ROS_DOMAIN_ID on your PC (see scripts/pc/run_rviz_robot.sh).
#
# Override serial layout with DEVICE_* / RFID_SERIAL_PORT / LIDAR_PORT (in-container paths).
#
# By default we do **not** use --rm so if the container crashes you can still run
#   docker logs turtlebot-rfid   or   docker ps -a
# Set DOCKER_RM=1 to remove the container automatically when it stops.

set -euo pipefail

: "${nas_reg:?Set nas_reg to registry host:port, e.g. 192.168.1.203:5000}"

IMAGE="${IMAGE:-turtlebot-rfid-robot}"
TAG="${TAG:-latest}"
FULL_IMAGE="${nas_reg}/${IMAGE}:${TAG}"
CONTAINER_NAME="${CONTAINER_NAME:-turtlebot-rfid}"
SKIP_PULL="${SKIP_PULL:-0}"
INTERACTIVE="${INTERACTIVE:-0}"

DEVICE_ACM="${DEVICE_ACM:-/dev/ttyACM0}"
DEVICE_RFID="${DEVICE_RFID:-/dev/ttyUSB0:/dev/ttyrfid}"
DEVICE_LIDAR="${DEVICE_LIDAR:-/dev/ttyUSB1:/dev/ttyUSB1}"

TURTLEBOT3_MODEL="${TURTLEBOT3_MODEL:-burger}"
# LDS-02 (LD08): set **LDS_MODEL=LDS-01** only if you still have the old Hitachi HLDS ring.
# Upstream ld08_driver discovers a CP2102 USB–serial LiDAR automatically; **LIDAR_PORT** is still
# passed for TurtleBot3 launch compatibility but may not be used like HLDS (see ld08_driver docs).
LDS_MODEL="${LDS_MODEL:-LDS-02}"
RFID_SERIAL_PORT="${RFID_SERIAL_PORT:-/dev/ttyrfid}"
LIDAR_PORT="${LIDAR_PORT:-/dev/ttyUSB1}"
ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-1}"

if [[ "${SKIP_PULL}" != "1" ]]; then
  docker pull "${FULL_IMAGE}"
fi

docker rm -f "${CONTAINER_NAME}" >/dev/null 2>&1 || true

run_args=(--name "${CONTAINER_NAME}" --net=host)
if [[ "${DOCKER_RM:-0}" == "1" ]]; then
  run_args+=(--rm)
fi
run_args+=(--device="${DEVICE_ACM}:${DEVICE_ACM}")
run_args+=(--device="${DEVICE_RFID}")
run_args+=(--device="${DEVICE_LIDAR}")
run_args+=(-e "TURTLEBOT3_MODEL=${TURTLEBOT3_MODEL}")
run_args+=(-e "LDS_MODEL=${LDS_MODEL}")
run_args+=(-e "RFID_SERIAL_PORT=${RFID_SERIAL_PORT}")
run_args+=(-e "LIDAR_PORT=${LIDAR_PORT}")
run_args+=(-e "ROS_DOMAIN_ID=${ROS_DOMAIN_ID}")

if [[ "${INTERACTIVE}" == "1" ]]; then
  run_args+=(-it)
  exec docker run "${run_args[@]}" "${FULL_IMAGE}"
fi

run_args+=(-d)
cid="$(docker run "${run_args[@]}" "${FULL_IMAGE}")"
sleep 2
state="$(docker inspect -f '{{.State.Status}}' "${cid}" 2>/dev/null || echo unknown)"
if [[ "${state}" != "running" ]]; then
  echo "[run_robot_docker] container exited immediately (status=${state}). Logs:" >&2
  docker logs "${cid}" 2>&1 || true
  exit 1
fi
echo "[run_robot_docker] running ${cid}; follow with: docker logs -f ${CONTAINER_NAME}" >&2
echo "[run_robot_docker] No LaserScan in RViz? Driver uses best-effort QoS — set LaserScan display QoS to Best effort. Check data: ./scripts/robot/check_robot_scan.sh" >&2
echo "[run_robot_docker] On the Pi, use ./scripts/robot/robot_ros2.sh topic list (not host ros2). If you see \"Killed\", that is usually OOM: add swap, avoid extra daemons, export ROS_DISABLE_ROS2_DAEMON=1 for host ros2." >&2
echo "[run_robot_docker] ROS_DOMAIN_ID=${ROS_DOMAIN_ID} (default 1). On PC match domain + best-effort echo: ./scripts/pc/echo_robot_scan.sh ; RViz: ./scripts/pc/run_rviz_robot.sh" >&2
