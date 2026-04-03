# Agent charter (Cursor)

This repository is a **TurtleBot3 + RFID + SLAM** monorepo. AI agents should follow:

1. **`.cursorrules`** (repo root) — quick project charter; aligns with the [awesome-cursorrules](https://github.com/PatrickJS/awesome-cursorrules) idea of a single project rules file.
2. **`.cursor/rules/*.mdc`** — scoped rules with `globs` / `alwaysApply` (see table below).
3. **User / workspace rules** — when they conflict with this file, prefer explicit user instructions for the current task.

## Layout (where to work)

| Area | Purpose |
|------|---------|
| `ros2_ws/src/` | Canonical ROS 2 packages (`rfid_publisher`, `ros2_rfid_mapping`, …). Primary place for new nodes/launch. |
| `turtlebot3/` | Vendored TurtleBot3 fork; RFID hook in `turtlebot3_bringup/launch/robot.launch.py`. Prefer minimal diffs. |
| `robot/`, `server/` | Docker images (Humble robot stack vs SLAM server). |
| `scripts/` | `lint.sh`, `build_ros.sh` (native colcon + tests), `docker_build_robot.sh` (arm64 push + `:latest`), `run_robot_docker.sh` (Pi: pull + run). |
| `legacy/`, `firmware/` | ROS 1 scripts and Arduino; reference only unless porting. |

## Rule index

| Rule file | When it applies |
|-----------|-----------------|
| `project-core.mdc` | Always — repo map, safety, scope. |
| `git-commits.mdc` | Always — commit message / PR hygiene. |
| `ros2-workspace.mdc` | Files under `ros2_ws/`. |
| `turtlebot3-fork.mdc` | Files under `turtlebot3/`. |
| `docker-deployment.mdc` | Any `Dockerfile` (e.g. `robot/`, `server/`). |
| `python-general.mdc` | Any `*.py`. |
| `shell-scripts.mdc` | `scripts/**/*.sh`. |

Add new `.mdc` files for new subsystems (e.g. `simulation.mdc` with `globs: **/*.world`) instead of growing one mega-rule.

## References

- [PatrickJS/awesome-cursorrules](https://github.com/PatrickJS/awesome-cursorrules) — curated community `.cursorrules` templates (web, mobile, Python, etc.). This repo combines a **root `.cursorrules`** with **scoped `.mdc` rules** for robotics-specific layout; borrow additional patterns from that catalog when adding new stacks.

## Distro note

Robot **Docker** image targets **ROS 2 Humble**; native Ubuntu 24.04 dev hosts often use **Jazzy**. Do not silently change distro pins without stating impact.

## Docker registry / Raspberry Pi

The robot image is **for the Pi only** (default **linux/arm64**). If `docker pull` fails with *no matching manifest for linux/arm64*, the image was built only for amd64. Push an arm64 build: `nas_reg=... TAG=... ./scripts/docker_build_robot.sh`, or `docker build` **on the Pi** and push (fastest). If **push** fails with *HTTP response to HTTPS client* despite `insecure-registries`, the script uses the **`default`** buildx builder (`docker` driver) so the daemon’s insecure list applies. Do not create a second builder with `--driver docker` (Docker allows only one).

If **`exec /bin/bash: exec format error`** during `RUN`, you are cross-building **arm64** on **x86** without **QEMU binfmt**. Run once: `docker run --privileged --rm tonistiigi/binfmt --install all`, or build on the Pi (`docker build` natively).

## Robot container (bringup on start)

The image **ENTRYPOINT** runs `ros2 launch turtlebot3_bringup robot.launch.py` (TurtleBot + LiDAR + RFID). Map USB devices and set **in-container** serial paths if they differ from defaults (`/dev/ttyUSB0` for both LiDAR and RFID).

Example (interactive):

```bash
docker run --rm -it --net=host \
  --device=/dev/ttyACM0:/dev/ttyACM0 \
  --device=/dev/ttyUSB0:/dev/ttyrfid \
  --device=/dev/ttyUSB1:/dev/ttyUSB1 \
  -e TURTLEBOT3_MODEL=burger \
  -e LDS_MODEL=LDS-01 \
  -e RFID_SERIAL_PORT=/dev/ttyrfid \
  -e LIDAR_PORT=/dev/ttyUSB1 \
  192.168.1.203:5000/turtlebot-rfid-robot:1.0
```

For **cron** / boot, drop `-it`, add `-d`, and log to a file or `journald`. Shell for debugging: `docker run --entrypoint bash -it ...` then `source /colcon_ws/install/setup.bash` and launch manually.

**Floating tag (`latest`):** `scripts/docker_build_robot.sh` pushes both `TAG` (e.g. `1.0`) and `:latest`. On the robot, **`docker pull` then `docker run ...:latest`** so a startup script does not need a hardcoded version:

```bash
REGISTRY=192.168.1.203:5000
IMAGE=${REGISTRY}/turtlebot-rfid-robot:latest
docker pull "$IMAGE"
docker run --rm -d --name turtlebot-rfid --net=host \
  --device=/dev/ttyACM0:/dev/ttyACM0 \
  --device=/dev/ttyUSB0:/dev/ttyrfid \
  --device=/dev/ttyUSB1:/dev/ttyUSB1 \
  -e RFID_SERIAL_PORT=/dev/ttyrfid -e LIDAR_PORT=/dev/ttyUSB1 \
  "$IMAGE"
```

Same behavior from the repo on the Pi: `nas_reg=192.168.1.203:5000 ./scripts/run_robot_docker.sh` (override `TAG`, `DEVICE_*`, or `RFID_SERIAL_PORT` / `LIDAR_PORT` as needed).

Docker does not auto-resolve “newest semver” from the registry; you either use a **moving tag** like `latest` (above) or pin `1.0`, `1.1`, etc.
