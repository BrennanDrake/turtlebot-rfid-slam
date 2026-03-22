# Robot image: TurtleBot3 fork (with RFID bringup hook) + custom ROS 2 packages from ros2_ws/src.
# Build from repository root:
#   docker build -f robot/Dockerfile -t turtlebot-rfid-robot:humble .
#
# Use host networking so DDS discovery matches the robot LAN (bridge networks often break ROS 2).
# Pass USB devices for LiDAR and RFID serial, e.g. --device /dev/ttyUSB0
#
# Distro note: Humble is pinned here for the current robot deployment. A future move to Jazzy
# (e.g. ros:jazzy-ros-base on Ubuntu 24.04) will require retesting TurtleBot3 + deps and updating
# rosdep/--rosdistro lines below; dev machines on Noble already use Jazzy natively.

FROM ros:humble-ros-base

ENV DEBIAN_FRONTEND=noninteractive
SHELL ["/bin/bash", "-c"]

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        python3-colcon-common-extensions \
        python3-rosdep \
        python3-serial \
    && rm -rf /var/lib/apt/lists/* \
    && (rosdep init || true)

WORKDIR /colcon_ws

# Flatten upstream TurtleBot3 packages into the workspace src/ tree (same layout as a colcon workspace).
COPY turtlebot3 /tmp/turtlebot3_upstream
RUN for pkg in turtlebot3 turtlebot3_bringup turtlebot3_cartographer turtlebot3_description turtlebot3_example turtlebot3_navigation2 turtlebot3_node turtlebot3_teleop; do \
      cp -a "/tmp/turtlebot3_upstream/${pkg}" src/ ; \
    done \
    && rm -rf /tmp/turtlebot3_upstream

COPY ros2_ws/src /colcon_ws/src

# Install non-ROS deps and *external* ROS deps (hls_lfcd_lds_driver, nav2, etc.). TurtleBot3
# packages are vendored under src/; do not apt-install ros-humble-turtlebot3-* or rosdep can
# fail or duplicate the overlay (see package.xml exec_depend chains on turtlebot3 meta).
RUN apt-get update \
    && rosdep update \
    && rosdep install --from-paths src --ignore-src -y -r --rosdistro humble \
        --skip-keys "turtlebot3 turtlebot3_bringup turtlebot3_cartographer turtlebot3_description turtlebot3_example turtlebot3_navigation2 turtlebot3_node turtlebot3_teleop" \
    && rm -rf /var/lib/apt/lists/*

RUN source /opt/ros/humble/setup.bash \
    && colcon build --symlink-install

# Default command only sources the overlay; run your launch files explicitly on the robot.
CMD ["bash", "-c", "source /colcon_ws/install/setup.bash && exec bash"]
