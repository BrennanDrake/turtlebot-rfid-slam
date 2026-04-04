# Convenience targets; ROS 2 still required for build/test (see scripts/pc/build_ros.sh).
.PHONY: lint build build-workspace test

lint:
	@./scripts/lint.sh

# Full workspace build + ament/pytest linters (requires: source /opt/ros/$$ROS_DISTRO/setup.bash).
# Ensures ros2_ws/src/turtlebot3_description symlink for RViz package:// paths.
build: build-workspace

build-workspace:
	@./scripts/build_workspace.sh

# Same as build (tests included unless --skip-test)
test:
	@./scripts/build_ros.sh
