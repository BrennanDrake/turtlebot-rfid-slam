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

"""RFID landmark manager: TF-based mapping, Kalman refinement, visualization, EKF feed."""

from __future__ import annotations

import math

import rclpy
from geometry_msgs.msg import Pose, PoseWithCovariance, Quaternion
from nav_msgs.msg import Odometry
from rclpy.duration import Duration
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from tf2_ros import Buffer, TransformException, TransformListener

from rfid_msgs.msg import RfidDetection, RfidLandmark, RfidLandmarkArray
from rfid_msgs.srv import LoadLandmarks, SaveLandmarks
from visualization_msgs.msg import Marker, MarkerArray

from rfid_landmarks.landmark_store import LandmarkEntry, LandmarkStore


def _yaw_from_quat(q: Quaternion) -> float:
    """Yaw from geometry_msgs Quaternion (ZYX)."""
    siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
    cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
    return math.atan2(siny_cosp, cosy_cosp)


def _quat_from_yaw(yaw: float) -> Quaternion:
    q = Quaternion()
    q.x = 0.0
    q.y = 0.0
    q.z = math.sin(yaw * 0.5)
    q.w = math.cos(yaw * 0.5)
    return q


class LandmarkManagerNode(Node):
    def __init__(self) -> None:
        super().__init__('rfid_landmark_manager')

        self.declare_parameter('sensor_frame', 'rfid_sensor_link')
        self.declare_parameter('base_frame', 'base_footprint')
        self.declare_parameter('map_frame', 'map')
        self.declare_parameter('initial_covariance', 0.1)
        self.declare_parameter('measurement_covariance', 0.0025)
        self.declare_parameter('landmark_file', '')
        self.declare_parameter('mature_threshold', 3)
        self.declare_parameter('debounce_sec', 1.0)
        self.declare_parameter('publish_rate', 2.0)
        self.declare_parameter('tf_timeout_sec', 0.5)

        self._store = LandmarkStore()
        self._debounce: dict[str, int] = {}

        qos_latched = QoSProfile(
            depth=1,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            reliability=ReliabilityPolicy.RELIABLE,
        )

        self._pub_landmarks = self.create_publisher(
            RfidLandmarkArray, 'rfid/landmarks', qos_latched,
        )
        self._pub_markers = self.create_publisher(MarkerArray, 'rfid/markers', 10)
        self._pub_odom = self.create_publisher(Odometry, 'rfid/odom', 10)

        self._tf_buffer = Buffer()
        self._tf_listener = TransformListener(self._tf_buffer, self)

        self.create_subscription(RfidDetection, 'rfid/detections', self._on_detection, 10)

        self.create_service(SaveLandmarks, 'rfid/save_landmarks', self._on_save)
        self.create_service(LoadLandmarks, 'rfid/load_landmarks', self._on_load)

        rate = float(self.get_parameter('publish_rate').value)
        if rate > 0.0:
            self.create_timer(1.0 / rate, self._on_timer)

        path = str(self.get_parameter('landmark_file').value).strip()
        if path:
            ok, msg, count = self._store.load_yaml(path)
            if ok and count > 0:
                self.get_logger().info('Loaded %d landmarks from %s' % (count, path))
            elif not ok:
                self.get_logger().warn('Could not load landmarks: %s' % msg)

    def _sensor_frame(self) -> str:
        return str(self.get_parameter('sensor_frame').value)

    def _map_frame(self) -> str:
        return str(self.get_parameter('map_frame').value)

    def _base_frame(self) -> str:
        return str(self.get_parameter('base_frame').value)

    def _on_timer(self) -> None:
        self._publish_landmarks()
        self._publish_markers()

    def _on_save(self, request: SaveLandmarks.Request, response: SaveLandmarks.Response):
        ok, msg = self._store.save_yaml(request.filepath)
        response.success = ok
        response.message = msg
        return response

    def _on_load(self, request: LoadLandmarks.Request, response: LoadLandmarks.Response):
        ok, msg, count = self._store.load_yaml(request.filepath)
        response.success = ok
        response.landmark_count = count
        response.message = msg
        if ok:
            self._publish_landmarks()
            self._publish_markers()
        return response

    def _lookup_map_sensor(self) -> tuple[float, float] | None:
        timeout = Duration(seconds=float(self.get_parameter('tf_timeout_sec').value))
        try:
            t = self._tf_buffer.lookup_transform(
                self._map_frame(),
                self._sensor_frame(),
                rclpy.time.Time(),
                timeout=timeout,
            )
        except TransformException as exc:
            self.get_logger().warn('TF map->sensor failed: %s' % exc)
            return None
        return (t.transform.translation.x, t.transform.translation.y)

    def _lookup_map_base(self) -> tuple[Pose, float] | None:
        timeout = Duration(seconds=float(self.get_parameter('tf_timeout_sec').value))
        try:
            t = self._tf_buffer.lookup_transform(
                self._map_frame(),
                self._base_frame(),
                rclpy.time.Time(),
                timeout=timeout,
            )
        except TransformException as exc:
            self.get_logger().warn('TF map->base failed: %s' % exc)
            return None
        p = Pose()
        p.position = t.transform.translation
        p.orientation = t.transform.rotation
        yaw = _yaw_from_quat(p.orientation)
        return p, yaw

    def _debounced(self, tag_id: str) -> bool:
        if not tag_id:
            return True
        now = self.get_clock().now().nanoseconds
        debounce_ns = int(float(self.get_parameter('debounce_sec').value) * 1e9)
        last = self._debounce.get(tag_id, 0)
        if now - last < debounce_ns:
            return True
        self._debounce[tag_id] = now
        return False

    def _on_detection(self, msg: RfidDetection) -> None:
        if not msg.present:
            self.get_logger().info('Tag removed on reader %d' % msg.reader_index)
            return

        tag_id = msg.tag_id.strip().upper()
        if not tag_id:
            return

        if self._debounced(tag_id):
            return

        pos = self._lookup_map_sensor()
        if pos is None:
            return

        mx, my = pos
        meas_var = float(self.get_parameter('measurement_covariance').value)
        init_var = float(self.get_parameter('initial_covariance').value)
        mature_n = int(self.get_parameter('mature_threshold').value)
        now_ns = self.get_clock().now().nanoseconds

        existing = self._store.get(tag_id)
        if existing is None:
            entry = LandmarkEntry(
                tag_id=tag_id,
                x=mx,
                y=my,
                cov_xx=init_var,
                cov_yy=init_var,
                observation_count=1,
                first_seen_ns=now_ns,
                last_seen_ns=now_ns,
            )
            self._store.upsert_entry(entry)
            self.get_logger().info('New landmark %s at (%.3f, %.3f)' % (tag_id, mx, my))
        else:
            lx, ly = existing.x, existing.y
            cxx, cyy = existing.cov_xx, existing.cov_yy

            kx = cxx / (cxx + meas_var) if (cxx + meas_var) > 0 else 0.0
            ky = cyy / (cyy + meas_var) if (cyy + meas_var) > 0 else 0.0
            nx = lx + kx * (mx - lx)
            ny = ly + ky * (my - ly)
            ncx = (1.0 - kx) * cxx
            ncy = (1.0 - ky) * cyy

            existing.x = nx
            existing.y = ny
            existing.cov_xx = ncx
            existing.cov_yy = ncy
            existing.observation_count += 1
            existing.last_seen_ns = now_ns
            self._store.upsert_entry(existing)

        self._publish_landmarks()
        self._publish_markers()

        # Mature tag: publish pose for robot_localization
        ent = self._store.get(tag_id)
        if ent is not None and ent.observation_count >= mature_n:
            pose_base = self._lookup_map_base()
            if pose_base is None:
                return
            pose, _y = pose_base
            odom = Odometry()
            odom.header.stamp = self.get_clock().now().to_msg()
            odom.header.frame_id = self._map_frame()
            odom.child_frame_id = self._base_frame()
            odom.pose.pose = pose
            # Large uncertainty on z, roll, pitch; yaw moderate
            c = [0.0] * 36
            c[0] = ent.cov_xx + meas_var
            c[7] = ent.cov_yy + meas_var
            c[14] = 1e4
            c[21] = 1e4
            c[28] = 1e4
            c[35] = 0.5
            odom.pose.covariance = c
            self._pub_odom.publish(odom)

    def _fill_pose_cov(self, cxx: float, cyy: float) -> list[float]:
        c = [0.0] * 36
        c[0] = cxx
        c[7] = cyy
        c[14] = 1e6
        c[21] = 1e6
        c[28] = 1e6
        c[35] = 1e6
        return c

    def _publish_landmarks(self) -> None:
        out = RfidLandmarkArray()
        out.header.stamp = self.get_clock().now().to_msg()
        out.header.frame_id = self._map_frame()
        mature_n = int(self.get_parameter('mature_threshold').value)
        for e in self._store.all_entries():
            lm = RfidLandmark()
            lm.tag_id = e.tag_id
            lm.observation_count = e.observation_count
            if e.first_seen_ns > 0:
                lm.first_seen = rclpy.time.Time(nanoseconds=e.first_seen_ns).to_msg()
            else:
                lm.first_seen = self.get_clock().now().to_msg()
            if e.last_seen_ns > 0:
                lm.last_seen = rclpy.time.Time(nanoseconds=e.last_seen_ns).to_msg()
            else:
                lm.last_seen = self.get_clock().now().to_msg()
            lm.mature = e.observation_count >= mature_n
            lm.pose = PoseWithCovariance()
            lm.pose.pose.position.x = e.x
            lm.pose.pose.position.y = e.y
            lm.pose.pose.position.z = 0.0
            lm.pose.pose.orientation = _quat_from_yaw(0.0)
            lm.pose.covariance = self._fill_pose_cov(e.cov_xx, e.cov_yy)
            out.landmarks.append(lm)
        self._pub_landmarks.publish(out)

    def _publish_markers(self) -> None:
        arr = MarkerArray()
        mature_n = int(self.get_parameter('mature_threshold').value)
        mid = 0
        for e in self._store.all_entries():
            m = Marker()
            m.header.frame_id = self._map_frame()
            m.header.stamp = self.get_clock().now().to_msg()
            m.ns = 'rfid_landmarks'
            m.id = mid
            m.type = Marker.CYLINDER
            m.action = Marker.ADD
            m.pose.position.x = e.x
            m.pose.position.y = e.y
            m.pose.position.z = 0.05
            m.pose.orientation.w = 1.0
            scale = max(0.02, 0.15 * math.sqrt(e.cov_xx + e.cov_yy))
            m.scale.x = scale
            m.scale.y = scale
            m.scale.z = 0.08
            if e.observation_count >= mature_n:
                m.color.r = 0.1
                m.color.g = 0.9
                m.color.b = 0.1
            else:
                m.color.r = 0.9
                m.color.g = 0.2
                m.color.b = 0.1
            m.color.a = 0.85
            arr.markers.append(m)
            mid += 1

            txt = Marker()
            txt.header = m.header
            txt.ns = 'rfid_labels'
            txt.id = mid
            mid += 1
            txt.type = Marker.TEXT_VIEW_FACING
            txt.action = Marker.ADD
            txt.pose.position.x = e.x
            txt.pose.position.y = e.y
            txt.pose.position.z = 0.25
            txt.pose.orientation.w = 1.0
            short = e.tag_id[-8:] if len(e.tag_id) > 8 else e.tag_id
            txt.text = '%s (x%d)' % (short, e.observation_count)
            txt.scale.z = 0.12
            txt.color.r = 1.0
            txt.color.g = 1.0
            txt.color.b = 1.0
            txt.color.a = 1.0
            arr.markers.append(txt)

        self._pub_markers.publish(arr)

    def destroy_node(self) -> bool:
        path = str(self.get_parameter('landmark_file').value).strip()
        if path:
            ok, msg = self._store.save_yaml(path)
            if ok:
                self.get_logger().info('Saved landmarks to %s' % path)
            else:
                self.get_logger().error('Failed to save landmarks: %s' % msg)
        return super().destroy_node()


def main(args=None) -> None:
    rclpy.init(args=args)
    node = LandmarkManagerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
