#!/usr/bin/env bash
# Print snippets of the URDF the robot uses (same file robot_state_publisher loads).
# Avoids `ros2 topic echo /robot_description` buffer errors on huge std_msgs/String messages.
#
# Usage (inside robot container or Pi with workspace sourced):
#   source /colcon_ws/install/setup.bash
#   ./scripts/robot/dump_robot_description.sh
#
# Optional: TURTLEBOT3_MODEL=waffle ./scripts/robot/dump_robot_description.sh

set -euo pipefail
MODEL="${TURTLEBOT3_MODEL:-burger}"
if ! command -v ros2 >/dev/null 2>&1; then
  echo "ros2 not in PATH; source /colcon_ws/install/setup.bash first" >&2
  exit 1
fi
PREFIX="$(ros2 pkg prefix turtlebot3_description)"
URDF="${PREFIX}/share/turtlebot3_description/urdf/turtlebot3_${MODEL}.urdf"
if [[ ! -f "${URDF}" ]]; then
  echo "Not found: ${URDF}" >&2
  exit 1
fi
echo "[dump_robot_description] ${URDF}"
echo "--- base_link block (visual/collision rpy) ---"
sed -n '/<link name="base_link">/,/<\/link>/p' "${URDF}" | head -30
echo "--- scan_joint ---"
sed -n '/<joint name="scan_joint"/,/<\/joint>/p' "${URDF}"

echo ""
echo "--- live vs disk (robot_state_publisher) ---"
# RSP reads the URDF file once at startup into the parameter; editing the file or pulling a new
# image does not update RViz until RSP / the container is restarted.
# Do not pipe `ros2 param get` to grep: huge string params hit "sequence size exceeds remaining buffer".
# Write to a temp file, then grep. Marker: URDF comment contains "z=pi on base_joint" (LDS-02 fork).
_rsp_tmp="$(mktemp)"
trap 'rm -f "${_rsp_tmp}"' EXIT
if ros2 node list 2>/dev/null | grep -q robot_state_publisher; then
  # Merge stdout+stderr: buffer warnings may land on stderr; body may still be present.
  ros2 param get /robot_state_publisher robot_description >"${_rsp_tmp}" 2>&1 || true
  _bytes="$(wc -c <"${_rsp_tmp}" | tr -d ' ')"
  if [[ "${_bytes}" -ge 500 ]] && grep -q 'z=pi on base_joint' "${_rsp_tmp}"; then
    echo "OK: running /robot_state_publisher parameter contains LDS-02 marker (z=pi on base_joint) — matches current fork."
  elif [[ "${_bytes}" -ge 500 ]] && grep -q 'scan_joint' "${_rsp_tmp}"; then
    echo "WARN: parameter is large (${_bytes} bytes) but missing 'z=pi on base_joint' — RSP may still be on an OLD URDF." >&2
    echo "      Restart bringup or the container, then restart RViz." >&2
  else
    echo "NOTE: could not read robot_description param cleanly (${_bytes} bytes). Compare on-disk URDF above." >&2
    echo "      If RViz is stale, restart the container so RSP reloads the file." >&2
  fi
else
  echo "SKIP: no robot_state_publisher in this ROS graph (normal on a dev PC with no bringup running)."
  echo "      On-disk URDF above is still what your workspace would load. Re-run on the robot"
  echo "      container (or with the same ROS_DOMAIN_ID as the robot) to compare live param vs disk."
fi
