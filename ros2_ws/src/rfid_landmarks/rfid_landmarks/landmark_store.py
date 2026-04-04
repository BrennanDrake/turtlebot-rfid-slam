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

"""In-memory landmark database and YAML persistence."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

import yaml


@dataclass
class LandmarkEntry:
    """Scalar 2D landmark with diagonal covariance in map frame."""

    tag_id: str
    x: float
    y: float
    cov_xx: float
    cov_yy: float
    observation_count: int = 0
    first_seen_ns: int = 0
    last_seen_ns: int = 0


class LandmarkStore:
    """Stores tag_id -> LandmarkEntry."""

    def __init__(self) -> None:
        self._landmarks: Dict[str, LandmarkEntry] = {}

    def get(self, tag_id: str) -> Optional[LandmarkEntry]:
        return self._landmarks.get(tag_id)

    def all_entries(self) -> List[LandmarkEntry]:
        return list(self._landmarks.values())

    def upsert_entry(self, entry: LandmarkEntry) -> None:
        self._landmarks[entry.tag_id] = entry

    def clear(self) -> None:
        self._landmarks.clear()

    def load_yaml(self, filepath: str) -> tuple[bool, str, int]:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
        except OSError as exc:
            return False, str(exc), 0
        if data is None:
            return True, 'empty file', 0
        landmarks = data.get('landmarks', [])
        self.clear()
        count = 0
        for item in landmarks:
            tag_id = str(item.get('tag_id', ''))
            if not tag_id:
                continue
            entry = LandmarkEntry(
                tag_id=tag_id,
                x=float(item.get('x', 0.0)),
                y=float(item.get('y', 0.0)),
                cov_xx=float(item.get('cov_xx', 0.1)),
                cov_yy=float(item.get('cov_yy', 0.1)),
                observation_count=int(item.get('observation_count', 0)),
                first_seen_ns=int(item.get('first_seen_ns', 0)),
                last_seen_ns=int(item.get('last_seen_ns', 0)),
            )
            self.upsert_entry(entry)
            count += 1
        return True, 'ok', count

    def save_yaml(self, filepath: str) -> tuple[bool, str]:
        rows = []
        for e in sorted(self._landmarks.values(), key=lambda x: x.tag_id):
            rows.append({
                'tag_id': e.tag_id,
                'x': e.x,
                'y': e.y,
                'cov_xx': e.cov_xx,
                'cov_yy': e.cov_yy,
                'observation_count': e.observation_count,
                'first_seen_ns': e.first_seen_ns,
                'last_seen_ns': e.last_seen_ns,
            })
        payload = {'landmarks': rows}
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                yaml.safe_dump(payload, f, default_flow_style=False, sort_keys=False)
        except OSError as exc:
            return False, str(exc)
        return True, 'ok'
