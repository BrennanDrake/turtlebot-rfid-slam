#!/usr/bin/env bash
# Fast colcon: build only named package(s) using a cached **robotdeps** image (skips long rosdep).
#
# First time (or after Dockerfile deps layer changes):
#   docker build -f robot/Dockerfile --target robotdeps -t turtlebot-rfid-robot:deps .
# Or let this script build that image (same command).
#
# Usage (repo root):
#   ./scripts/quick_robot_colcon.sh turtlebot3_node
#   ./scripts/quick_robot_colcon.sh turtlebot3_node rfid_publisher
#
# Env:
#   DEPS_IMAGE=turtlebot-rfid-robot:deps   image tag for robotdeps stage
#   PLATFORM=linux/arm64                 default; set for your build target
#   SKIP_DEPS_BUILD=1                    do not run docker build (use existing DEPS_IMAGE)
#
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <package> [package...]" >&2
  echo "Example: $0 turtlebot3_node" >&2
  exit 1
fi

DEPS_IMAGE="${DEPS_IMAGE:-turtlebot-rfid-robot:deps}"
PLATFORM="${PLATFORM:-linux/arm64}"
SKIP_DEPS_BUILD="${SKIP_DEPS_BUILD:-0}"

if [[ "${SKIP_DEPS_BUILD}" != "1" ]]; then
  echo "[quick_robot_colcon] building ${DEPS_IMAGE} (target robotdeps) ..." >&2
  docker buildx build --platform "${PLATFORM}" -f robot/Dockerfile \
    --target robotdeps -t "${DEPS_IMAGE}" "${ROOT}" --load
fi

export QUICK_ROBOT_PACKAGES="$*"
docker run --rm --platform "${PLATFORM}" \
  -e QUICK_ROBOT_PACKAGES \
  -v "${ROOT}:/repo:ro" \
  -w /colcon_ws \
  "${DEPS_IMAGE}" \
  bash -c '
    set -eo pipefail
    rm -rf /colcon_ws/src/* /colcon_ws/build /colcon_ws/install /colcon_ws/log
    mkdir -p /colcon_ws/src
    /merge_src.sh /repo/turtlebot3 /repo/ros2_ws/src /colcon_ws/src
    # Do not use set -u here: humble setup.bash references optional env vars.
    source /opt/ros/humble/setup.bash
    m=$(uname -m)
    case "$m" in
      aarch64) LIBDIR=/usr/lib/aarch64-linux-gnu ;;
      x86_64)  LIBDIR=/usr/lib/x86_64-linux-gnu ;;
      *)       LIBDIR=/usr/lib/"$m"-linux-gnu ;;
    esac
    # shellcheck disable=SC2086
    colcon build --symlink-install --merge-install \
      --packages-select ${QUICK_ROBOT_PACKAGES} \
      --cmake-args \
        "-DOPENSSL_CRYPTO_LIBRARY=${LIBDIR}/libcrypto.so" \
        "-DOPENSSL_SSL_LIBRARY=${LIBDIR}/libssl.so"
  '

echo "[quick_robot_colcon] OK: $*" >&2
