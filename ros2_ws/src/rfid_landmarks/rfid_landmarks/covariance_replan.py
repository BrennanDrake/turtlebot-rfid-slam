# Copyright 2026 Brennan Drake
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Monitor EKF covariance and send Nav2 goals toward nearest mature RFID landmark."""

from __future__ import annotations

import math
from typing import List, Optional, Tuple

import rclpy
from geometry_msgs.msg import PoseStamped, Quaternion
from nav_msgs.msg import Odometry
from nav2_msgs.action import NavigateToPose
from rclpy.action import ActionClient
from rclpy.node import Node
from sensor_msgs.msg import OccupancyGrid

from rfid_msgs.msg import RfidLandmark, RfidLandmarkArray


def _yaw_to_quat(yaw: float) -> Quaternion:
    q = Quaternion()
    q.x = 0.0
    q.y = 0.0
    q.z = math.sin(yaw * 0.5)
    q.w = math.cos(yaw * 0.5)
    return q


def _dist2d(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


class CovarianceReplanNode(Node):
    def __init__(self) -> None:
        super().__init__('covariance_replan_node')

        self.declare_parameter('replan_threshold', 0.5)
        self.declare_parameter('approach_distance', 0.05)
        self.declare_parameter('map_frame', 'map')
        self.declare_parameter('action_name', 'navigate_to_pose')
        self.declare_parameter('enabled', True)
        self.declare_parameter('cooldown_sec', 30.0)

        self._map: Optional[OccupancyGrid] = None
        self._landmarks: List[RfidLandmark] = []
        self._robot_xy: Tuple[float, float] = (0.0, 0.0)
        self._last_odom: Optional[Odometry] = None
        self._last_goal_ns = 0

        self.create_subscription(OccupancyGrid, 'map', self._on_map, 1)
        self.create_subscription(RfidLandmarkArray, 'rfid/landmarks', self._on_landmarks, 10)
        self.create_subscription(Odometry, 'odometry/filtered', self._on_odom, 10)

        action_name = str(self.get_parameter('action_name').value)
        self._action = ActionClient(self, NavigateToPose, action_name)

        self.create_timer(1.0, self._on_timer)

    def _on_map(self, msg: OccupancyGrid) -> None:
        self._map = msg

    def _on_landmarks(self, msg: RfidLandmarkArray) -> None:
        self._landmarks = [lm for lm in msg.landmarks if lm.mature]

    def _on_odom(self, msg: Odometry) -> None:
        self._last_odom = msg
        self._robot_xy = (msg.pose.pose.position.x, msg.pose.pose.position.y)

    @staticmethod
    def _cov_xy(msg: Odometry) -> float:
        c = msg.pose.covariance
        return math.sqrt(max(0.0, c[0]) + max(0.0, c[7]))

    def _world_to_cell(self, mx: float, my: float) -> Optional[Tuple[int, int]]:
        if self._map is None:
            return None
        info = self._map.info
        ox = info.origin.position.x
        oy = info.origin.position.y
        res = info.resolution
        ix = int((mx - ox) / res)
        iy = int((my - oy) / res)
        if ix < 0 or iy < 0 or ix >= info.width or iy >= info.height:
            return None
        return ix, iy

    def _nearest_occupied(
        self, ix: int, iy: int, max_radius: int = 40,
    ) -> Optional[Tuple[int, int]]:
        if self._map is None:
            return None
        w = self._map.info.width
        h = self._map.info.height
        data = self._map.data
        best = None
        best_d2 = 1e18
        for r in range(1, max_radius):
            for dx in range(-r, r + 1):
                for dy in range(-r, r + 1):
                    if abs(dx) != r and abs(dy) != r:
                        continue
                    u, v = ix + dx, iy + dy
                    if u < 0 or v < 0 or u >= w or v >= h:
                        continue
                    val = data[u + v * w]
                    if val < 0:
                        continue
                    if val >= 50:
                        d2 = float(dx * dx + dy * dy)
                        if d2 < best_d2:
                            best_d2 = d2
                            best = (u, v)
            if best is not None:
                break
        return best

    def _wall_normal_world(self, tag_x: float, tag_y: float) -> Tuple[float, float]:
        cell = self._world_to_cell(tag_x, tag_y)
        if cell is None or self._map is None:
            return (1.0, 0.0)
        ix, iy = cell
        occ = self._nearest_occupied(ix, iy)
        if occ is None:
            return (1.0, 0.0)
        ox, oy = occ
        res = self._map.info.resolution
        owx = self._map.info.origin.position.x + (ox + 0.5) * res
        owy = self._map.info.origin.position.y + (oy + 0.5) * res
        vx = tag_x - owx
        vy = tag_y - owy
        n = math.hypot(vx, vy)
        if n < 1e-6:
            return (1.0, 0.0)
        return (vx / n, vy / n)

    def _goal_for_tag(self, lm: RfidLandmark) -> PoseStamped:
        px = lm.pose.pose.position.x
        py = lm.pose.pose.position.y
        nx, ny = self._wall_normal_world(px, py)
        ad = float(self.get_parameter('approach_distance').value)
        ps = PoseStamped()
        ps.header.frame_id = str(self.get_parameter('map_frame').value)
        ps.header.stamp = self.get_clock().now().to_msg()
        ps.pose.position.x = px + nx * ad
        ps.pose.position.y = py + ny * ad
        ps.pose.position.z = 0.0
        yaw = math.atan2(-ny, -nx)
        ps.pose.orientation = _yaw_to_quat(yaw)
        return ps

    def _nearest_landmark(self) -> Optional[RfidLandmark]:
        if not self._landmarks:
            return None
        rx, ry = self._robot_xy
        best: Optional[RfidLandmark] = None
        best_d = 1e18
        for lm in self._landmarks:
            px = lm.pose.pose.position.x
            py = lm.pose.pose.position.y
            d = _dist2d((rx, ry), (px, py))
            if d < best_d:
                best_d = d
                best = lm
        return best

    def _on_timer(self) -> None:
        if not bool(self.get_parameter('enabled').value):
            return
        if self._last_odom is None:
            return
        cov = self._cov_xy(self._last_odom)
        thr = float(self.get_parameter('replan_threshold').value)
        if cov < thr:
            return
        now = self.get_clock().now().nanoseconds
        cool = int(float(self.get_parameter('cooldown_sec').value) * 1e9)
        if now - self._last_goal_ns < cool:
            return
        lm = self._nearest_landmark()
        if lm is None:
            self.get_logger().warn(
                'Covariance %.3f exceeds threshold but no mature landmarks' % cov,
            )
            return
        if not self._action.wait_for_server(timeout_sec=0.5):
            self.get_logger().warn('NavigateToPose action server not ready')
            return
        goal = NavigateToPose.Goal()
        goal.pose = self._goal_for_tag(lm)
        self._last_goal_ns = now
        self.get_logger().info(
            'Covariance %.3f — navigating to tag %s' % (cov, lm.tag_id),
        )
        send_future = self._action.send_goal_async(goal)
        send_future.add_done_callback(self._goal_sent_cb)

    def _goal_sent_cb(self, future) -> None:
        goal_handle = future.result()
        if goal_handle is None:
            self.get_logger().error('NavigateToPose goal future failed')
            return
        if not goal_handle.accepted:
            self.get_logger().warn('NavigateToPose goal rejected')
            return
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self._goal_result_cb)

    def _goal_result_cb(self, future) -> None:
        try:
            future.result()
        except Exception as exc:
            self.get_logger().warn('NavigateToPose result: %s' % exc)


def main(args=None) -> None:
    rclpy.init(args=args)
    node = CovarianceReplanNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
