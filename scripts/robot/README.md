# Scripts — TurtleBot (Raspberry Pi)

Run these on the **robot host** over SSH (or locally on the Pi). They assume **Docker** is installed and, in most cases, that the robot container is already running.

| Script | Purpose |
|--------|---------|
| **`run_robot_docker.sh`** | `docker pull` + `docker run` the robot image (`nas_reg`, `TAG`, device mappings, `LDS_MODEL`, `LIDAR_PORT`, `RFID_SERIAL_PORT`, `ROS_DOMAIN_ID`). Primary bringup helper for boot/cron. |
| **`robot_ros2.sh`** | `docker exec` into the container and run **`ros2`** (topics, nodes, etc.) with the same environment as bringup. Prefer this over a host-installed `ros2` on the Pi (distro/domain mismatch, OOM). |
| **`check_robot_scan.sh`** | Quick checks that **`/scan`** is publishing (uses `sensor_data` echo; Humble `hz` is limited). |

**Typical flow:** `nas_reg=... ./scripts/robot/run_robot_docker.sh` → `./scripts/robot/check_robot_scan.sh` (optional). For anything else: `docker logs`, `./scripts/robot/robot_ros2.sh topic list`.

On your **PC**, use `scripts/pc/echo_robot_scan.sh` and `scripts/pc/run_rviz_robot.sh` with the same `ROS_DOMAIN_ID` as the container.
