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
| `scripts/` | `lint.sh`, `build_ros.sh` (native colcon + tests). |
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
