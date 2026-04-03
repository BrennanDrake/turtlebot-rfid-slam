#!/usr/bin/env bash
# Pull and run the robot image on the TurtleBot (Pi). Intended for boot/cron: TAG=latest by default.
#
# Usage:
#   nas_reg=192.168.1.203:5000 ./scripts/run_robot_docker.sh
#   TAG=1.0 nas_reg=... ./scripts/run_robot_docker.sh
#   INTERACTIVE=1 nas_reg=... ./scripts/run_robot_docker.sh
#   SKIP_PULL=1 nas_reg=... ./scripts/run_robot_docker.sh
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
LDS_MODEL="${LDS_MODEL:-LDS-01}"
RFID_SERIAL_PORT="${RFID_SERIAL_PORT:-/dev/ttyrfid}"
LIDAR_PORT="${LIDAR_PORT:-/dev/ttyUSB1}"

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
