# Server / workstation image: slam_toolbox + RFID mapping packages from this repo.
# Build from repository root:
#   docker build -f server/Dockerfile -t turtlebot-rfid-server:humble .
#
# Run with host networking and the same ROS_DOMAIN_ID as the robot. RViz is optional:
#   docker run --rm -it --net=host turtlebot-rfid-server:humble \
#     bash -lc 'source /opt/ros/humble/setup.bash && source /colcon_ws/install/setup.bash && \
#       ros2 launch ros2_rfid_mapping mapping_with_rfid_launch.py'

FROM ros:humble-ros-base

ENV DEBIAN_FRONTEND=noninteractive
SHELL ["/bin/bash", "-c"]

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        python3-colcon-common-extensions \
        ros-humble-slam-toolbox \
        ros-humble-nav2-bringup \
        ros-humble-navigation2 \
        ros-humble-nav2-map-server \
        ros-humble-robot-localization \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /colcon_ws
COPY ros2_ws/src /colcon_ws/src

RUN source /opt/ros/humble/setup.bash \
    && colcon build --symlink-install \
        --packages-up-to rfid_landmarks ros2_rfid_mapping

CMD ["bash", "-c", "source /colcon_ws/install/setup.bash && exec bash"]
