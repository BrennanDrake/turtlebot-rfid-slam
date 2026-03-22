# Convenience targets; ROS 2 still required for build/test (see scripts/build_ros.sh).
.PHONY: lint build test

lint:
	@./scripts/lint.sh

# Full workspace build + ament/pytest linters (requires: source /opt/ros/$$ROS_DISTRO/setup.bash)
build:
	@./scripts/build_ros.sh

# Same as build (tests included unless --skip-test)
test:
	@./scripts/build_ros.sh
