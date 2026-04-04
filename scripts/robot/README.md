# Scripts — TurtleBot (Raspberry Pi)

Run these on the **robot host** over SSH (or locally on the Pi). They assume **Docker** is installed and, in most cases, that the robot container is already running.

| Script | Purpose |
|--------|---------|
| **`run_robot_docker.sh`** | `docker pull` + `docker run` the robot image (`nas_reg`, `TAG`, device mappings, `LDS_MODEL`, `LIDAR_PORT`, `RFID_SERIAL_PORT`, `ROS_DOMAIN_ID`). Primary bringup helper for boot/cron. |
| **`robot_ros2.sh`** | `docker exec` into the container and run **`ros2`** (topics, nodes, etc.) with the same environment as bringup. Prefer this over a host-installed `ros2` on the Pi (distro/domain mismatch, OOM). |
| **`check_robot_scan.sh`** | Quick checks that **`/scan`** is publishing (uses `sensor_data` echo; Humble `hz` is limited). |
| **`dump_robot_description.sh`** | Prints **`base_link`** / **`scan_joint`** snippets from the **installed** URDF (avoids `ros2 topic echo /robot_description` “sequence size exceeds remaining buffer” on huge messages). |
| **`get_robot_description_param.py`** | Writes the **live** `robot_description` **parameter** from `/robot_state_publisher` to a file via the **parameter service** (works when `ros2 param get` prints only “sequence size exceeds remaining buffer” / “Node not found” from wrong shell). |

**Typical flow:** `nas_reg=... ./scripts/robot/run_robot_docker.sh` → `./scripts/robot/check_robot_scan.sh` (optional). For anything else: `docker logs`, `./scripts/robot/robot_ros2.sh topic list`.

After you change **`turtlebot3_description` URDF** (e.g. **`base_joint`** / **`scan_joint`** for LDS-02), **rebuild the robot image**, **`docker pull`** on the Pi, and **restart** the container so **`/robot_description`** and TF match. Validation: **AGENTS.md** → *LiDAR TF: `base_scan` vs `base_link`*. The dump script’s live check greps for **`z=pi on base_joint`** in the URDF text.

**RViz looks unchanged after a deploy:** `robot_state_publisher` loads the URDF **once at startup** into a **parameter**. New files on disk (or a new image) do **not** refresh RViz until you **restart** bringup / the container (and usually **restart RViz**). Run **`./scripts/robot/dump_robot_description.sh`** — if it prints **WARN** about old `robot_description`, RSP is still serving stale XML.

**Do not rely on** `ros2 param get ... robot_description` for huge strings — the CLI often prints only “sequence size exceeds remaining buffer”. Use **`get_robot_description_param.py -o /tmp/rd.xml`** on the robot with bringup running, then **`grep`** the file. **“Node not found”** means you are not in the same ROS graph as the robot (source **`setup.bash`**, match **`ROS_DOMAIN_ID`**, run **inside** the container or on the Pi with bringup).

On your **PC**, use `scripts/pc/echo_robot_scan.sh` and `scripts/pc/run_rviz_robot.sh` with the same `ROS_DOMAIN_ID` as the container.
