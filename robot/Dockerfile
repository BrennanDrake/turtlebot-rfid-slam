# syntax=docker/dockerfile:1
# Robot image: TurtleBot3 fork (with RFID bringup hook) + custom ROS 2 packages from ros2_ws/src.
# Build from repository root:
#   docker build -f robot/Dockerfile -t turtlebot-rfid-robot:humble .
# Pi is linux/arm64. From an x86 PC use buildx (arm64) or build on the Pi; see scripts/pc/docker_build_robot.sh
#
# Fast iteration (rebuild one package only, after deps image exists):
#   ./scripts/pc/quick_robot_colcon.sh turtlebot3_node
#   docker build -f robot/Dockerfile --target robotdeps -t turtlebot-rfid-robot:deps .
#
# Use host networking so DDS discovery matches the robot LAN (bridge networks often break ROS 2).
# Pass USB devices for LiDAR and RFID serial, e.g. --device /dev/ttyUSB1 (LDS) and --device /dev/ttyUSB0:/dev/ttyrfid (RFID)
#
# Distro note: Humble is pinned here for the current robot deployment. A future move to Jazzy
# (e.g. ros:jazzy-ros-base on Ubuntu 24.04) will require retesting TurtleBot3 + deps and updating
# rosdep/--rosdistro lines below; dev machines on Noble already use Jazzy natively.
# Pi is arm64. Cross-building on x86 requires host QEMU/binfmt or RUN steps fail with
# "exec /bin/bash: exec format error" — see scripts/pc/docker_build_robot.sh.
ARG TARGETPLATFORM=linux/arm64
FROM --platform=$TARGETPLATFORM ros:humble-ros-base AS robotdeps

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
SHELL ["/bin/bash", "-c"]

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        python3-colcon-common-extensions \
        python3-rosdep \
        python3-serial \
    && rm -rf /var/lib/apt/lists/* \
    && (rosdep init || true)

WORKDIR /colcon_ws

COPY robot/merge_src.sh /merge_src.sh
COPY turtlebot3 /tmp/turtlebot3
COPY ros2_ws/src /tmp/ros2_src
RUN chmod +x /merge_src.sh \
    && /merge_src.sh /tmp/turtlebot3 /tmp/ros2_src /colcon_ws/src \
    && rm -rf /tmp/turtlebot3 /tmp/ros2_src

# Install non-ROS deps and *external* ROS deps (hls_lfcd_lds_driver, nav2, etc.). TurtleBot3
# packages are vendored under src/; do not apt-install ros-humble-turtlebot3-* or rosdep can
# fail or duplicate the overlay (see package.xml exec_depend chains on turtlebot3 meta).
# cartographer_ros: turtlebot3_cartographer exec_depends it; apt package is often missing or
# uninstallable on linux/arm64 — skip so the image builds. Default bringup does not launch Cartographer.
RUN apt-get update \
    && rosdep update \
    && rosdep install --from-paths src --ignore-src -y -r --rosdistro humble \
        --skip-keys "turtlebot3 turtlebot3_bringup turtlebot3_cartographer turtlebot3_description turtlebot3_example turtlebot3_navigation2 turtlebot3_node turtlebot3_teleop cartographer_ros" \
    && apt-get install -y --no-install-recommends libtinyxml2-dev libssl-dev \
    && rm -rf /var/lib/apt/lists/*
# libtinyxml2-dev / libssl-dev: slim ros-base; needed for some vendored builds / CMake.

# Final application image (default build target).
FROM robotdeps AS robot

# docker buildx linux/arm64 on amd64 uses QEMU: CMake can spuriously fail find_package/rcutils with
# "library ... couldn't be found" even though /opt/ros/humble/lib/librcutils.so exists (heap/QEMU
# interaction; not a missing package). See https://github.com/ros2/rcutils/issues/525
ENV MALLOC_ARENA_MAX=1
# Raspberry Pi / low-RAM: default `ros2` CLI spawns a caching daemon; combined with Docker +
# bringup it can trigger OOM ("Killed"). Safe for launch; CLI falls back to direct calls (slightly slower).
ENV ROS_DISABLE_ROS2_DAEMON=1
# Match scripts/robot/run_robot_docker.sh default; override with docker run -e ROS_DOMAIN_ID=...
ENV ROS_DOMAIN_ID=1
# Match run_robot_docker / entrypoint; LDS-01 = HLDS, LDS-02 = ld08_driver.
ENV LDS_MODEL=LDS-02

# Do not pass global --cmake-args -DOPENSSL_* here: it breaks underlay packages (e.g. rcutils
# during rosidl) even though nothing in src/ builds Fast-DDS from source. If a future package
# needs OpenSSL on arm64, scope flags to that package (colcon.meta) or set OPENSSL_ROOT_DIR.
# Do not use `set -u`: humble setup.bash touches optional env vars (e.g. AMENT_TRACE_SETUP_FILES).
RUN set -eo pipefail \
    && source /opt/ros/humble/setup.bash \
    && n=1 \
    && max=5 \
    && while [ "${n}" -le "${max}" ]; do \
         if colcon build --symlink-install --merge-install; then \
           break; \
         fi; \
         if [ "${n}" -eq "${max}" ]; then \
           echo "colcon failed after ${max} attempts (try building on a native arm64 host; see ros2/rcutils#525)" >&2; \
           exit 1; \
         fi; \
         echo "[dockerfile] colcon failed (attempt ${n}/${max}), cleaning workspace and retrying..." >&2; \
         rm -rf build install log; \
         n=$((n + 1)); \
       done \
    && source /colcon_ws/install/setup.bash \
    && ros2 pkg prefix turtlebot3_bringup \
    && ros2 pkg prefix rfid_msgs \
    && ros2 pkg prefix rfid_publisher

COPY robot/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
