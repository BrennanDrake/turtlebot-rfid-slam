#!/usr/bin/env bash
# Build and push the **robot** image for the TurtleBot (Raspberry Pi) only: **linux/arm64**.
#
# If you previously built on x86 without --platform, the registry had amd64 only and the Pi
# could not pull — this script defaults to arm64.
#
# Usage (from repo root):
#   nas_reg=192.168.1.203:5000 TAG=1.0 ./scripts/pc/docker_build_robot.sh
#
# Force a full rebuild (ignore BuildKit layer cache), e.g. after URDF edits that still show CACHED:
#   NO_CACHE=1 nas_reg=... ./scripts/pc/docker_build_robot.sh
#
# Speed: cross-building **linux/arm64** on x86 uses QEMU and is **slow** (especially `colcon` with
# NO_CACHE). Prefer **native** `docker build -f robot/Dockerfile` **on the Pi** when iterating, or
# keep **NO_CACHE** off so BuildKit reuses layers. Use `./scripts/pc/quick_robot_colcon.sh <pkg>`
# to validate a single package against a **robotdeps** image without rebuilding the full final stage.
#
# Optional fast path (uses scripts/pc/quick_robot_colcon.sh + robot/Dockerfile target robotdeps):
#   QUICK_PACKAGES="turtlebot3_node" nas_reg=... ./scripts/pc/docker_build_robot.sh
#   Runs a package-scoped colcon first (fail fast). SKIP_QUICK=1 to disable.
#   SKIP_QUICK_DEPS_BUILD=1 reuse existing DEPS_IMAGE (default turtlebot-rfid-robot:deps).
#
# Optional: also push the long rosdep layer as a separate tag (cache / CI):
#   PUSH_ROBOTDEPS=1 nas_reg=... ./scripts/pc/docker_build_robot.sh
#   Pushes ${nas_reg}/${IMAGE}:robotdeps-${TAG} (override with ROBOTDEPS_TAG=...).
#
# Cross-building arm64 on an x86_64 PC uses QEMU (slow). Faster: run plain `docker build` on the Pi
# and push. For multi-arch (rare): PLATFORMS=linux/arm64,linux/amd64 ./scripts/pc/docker_build_robot.sh
#
# QEMU colcon can intermittently fail with "rcutils ... couldn't be found" (CMake+QEMU; not missing
# deps). robot/Dockerfile mitigates with MALLOC_ARENA_MAX and colcon retries; native arm64 avoids it.
#
# Cross-build x86 -> arm64 REQUIRES QEMU binfmt or every RUN fails with:
#   exec /bin/bash: exec format error
# Install once on the build host:
#   docker run --privileged --rm tonistiigi/binfmt --install all
# Or set SKIP_BINFMT_CHECK=1 to skip the preflight (not recommended).
#
# Push error: "http: server gave HTTP response to HTTPS client" — the client is using HTTPS but
# your registry is plain HTTP. `insecure-registries` in /etc/docker/daemon.json applies to the
# **Docker daemon**, but Buildx's **docker-container** driver runs BuildKit in another container and
# pushes can still hit HTTPS. This script defaults to `--driver docker` so push uses the host
# daemon (respects insecure-registries). This script uses the **default** builder for driver
# `docker` (only one `docker` driver is allowed). Rootless Docker: ~/.config/docker/daemon.json + restart.

set -euo pipefail
ROOT="$(git -C "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)" rev-parse --show-toplevel)"
cd "$ROOT"

: "${nas_reg:?Set nas_reg to registry host:port, e.g. 192.168.1.203:5000}"
IMAGE="${IMAGE:-turtlebot-rfid-robot}"
TAG="${TAG:-1.0}"
# Robot-only: Pi is arm64. Override only if you need a multi-arch manifest.
PLATFORMS="${PLATFORMS:-linux/arm64}"

_host="$(uname -m)"
if [[ "${PLATFORMS}" == *arm64* ]] && [[ "${_host}" == "x86_64" || "${_host}" == "amd64" ]] && [[ -z "${SKIP_BINFMT_CHECK:-}" ]]; then
  if ! docker run --rm --platform linux/arm64 alpine:3.20 uname -m 2>/dev/null | grep -q aarch64; then
    echo "[docker_build_robot] Cross-building for linux/arm64 on ${_host} needs QEMU binfmt." >&2
    echo "  Run once: docker run --privileged --rm tonistiigi/binfmt --install all" >&2
    echo "  Or build on the Pi with: docker build -f robot/Dockerfile ..." >&2
    exit 1
  fi
fi

BUILDX_BUILDER="${BUILDX_BUILDER:-turtlebot-rfid-builder}"
# `docker` driver: push goes through host daemon (honours insecure-registries). Docker only allows
# **one** builder with driver `docker` (the built-in `default`) — do not create a second named builder.
# `docker-container` can break HTTP registries; set BUILDX_DRIVER=docker-container to use a named builder.
BUILDX_DRIVER="${BUILDX_DRIVER:-docker}"

if [[ "${BUILDX_DRIVER}" == "docker" ]]; then
  docker buildx use default
else
  if ! docker buildx inspect "${BUILDX_BUILDER}" >/dev/null 2>&1; then
    docker buildx create --name "${BUILDX_BUILDER}" --driver "${BUILDX_DRIVER}" --use
  else
    docker buildx use "${BUILDX_BUILDER}"
  fi
fi
docker buildx inspect --bootstrap

FULL_TAG="${nas_reg}/${IMAGE}:${TAG}"
# Also tag :latest so robots can `docker pull ...:latest` without hardcoding a version.
LATEST_TAG="${LATEST_TAG:-latest}"
FULL_LATEST="${nas_reg}/${IMAGE}:${LATEST_TAG}"
ROBOTDEPS_TAG="${ROBOTDEPS_TAG:-robotdeps-${TAG}}"

BUILDX_NO_CACHE=()
if [[ "${NO_CACHE:-0}" == "1" ]]; then
  BUILDX_NO_CACHE=(--no-cache)
  echo "[docker_build_robot] NO_CACHE=1: building without layer cache" >&2
fi

# First platform string only (quick_robot_colcon uses a single --platform).
_primary_platform="${PLATFORMS%%,*}"

if [[ -n "${QUICK_PACKAGES:-}" && "${SKIP_QUICK:-0}" != "1" ]]; then
  echo "[docker_build_robot] quick colcon: ${QUICK_PACKAGES}" >&2
  export PLATFORM="${_primary_platform}"
  export DEPS_IMAGE="${DEPS_IMAGE:-turtlebot-rfid-robot:deps}"
  export SKIP_DEPS_BUILD="${SKIP_QUICK_DEPS_BUILD:-0}"
  read -ra _quick_pkgs <<< "${QUICK_PACKAGES}"
  "${ROOT}/scripts/pc/quick_robot_colcon.sh" "${_quick_pkgs[@]}"
fi

if [[ "${PUSH_ROBOTDEPS:-0}" == "1" ]]; then
  echo "[docker_build_robot] pushing robotdeps stage as ${nas_reg}/${IMAGE}:${ROBOTDEPS_TAG}" >&2
  docker buildx build \
    "${BUILDX_NO_CACHE[@]}" \
    --platform "${PLATFORMS}" \
    -f robot/Dockerfile \
    --target robotdeps \
    -t "${nas_reg}/${IMAGE}:${ROBOTDEPS_TAG}" \
    --push \
    .
fi

echo "[docker_build_robot] building ${FULL_TAG} (+ ${FULL_LATEST}) for --platform ${PLATFORMS}"

docker buildx build \
  "${BUILDX_NO_CACHE[@]}" \
  --platform "${PLATFORMS}" \
  -f robot/Dockerfile \
  -t "${FULL_TAG}" \
  -t "${FULL_LATEST}" \
  --push \
  .

echo "[docker_build_robot] pushed ${FULL_TAG} and ${FULL_LATEST}"
