"""
覆蓋率實體 - 表示衛星覆蓋分析結果
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any

from .satellite import Satellite
from .observer import Observer


@dataclass
class SatelliteVisibility:
    """單個衛星的可見性資訊"""

    satellite: Satellite
    azimuth: float  # 方位角（度）
    elevation: float  # 仰角（度）
    distance: float  # 距離（公里）
    is_sunlit: bool = True  # 是否被太陽照射

    @property
    def is_visible(self) -> bool:
        """衛星是否可見"""
        return self.elevation > 0 and self.is_sunlit


@dataclass
class CoverageSnapshot:
    """特定時間點的覆蓋快照"""

    timestamp: datetime
    observer: Observer
    visible_satellites: List[SatelliteVisibility] = field(default_factory=list)

    @property
    def visible_count(self) -> int:
        """可見衛星數量"""
        return len([sat for sat in self.visible_satellites if sat.is_visible])

    @property
    def max_elevation(self) -> float:
        """最大仰角"""
        if not self.visible_satellites:
            return 0.0
        return max(sat.elevation for sat in self.visible_satellites)

    @property
    def average_elevation(self) -> float:
        """平均仰角"""
        visible = [sat.elevation for sat in self.visible_satellites if sat.is_visible]
        if not visible:
            return 0.0
        return sum(visible) / len(visible)


@dataclass
class Coverage:
    """覆蓋率分析結果實體

    Attributes:
        coverage_id: 覆蓋分析唯一識別碼
        observer: 觀測者
        start_time: 分析開始時間
        end_time: 分析結束時間
        snapshots: 時間序列快照
        metadata: 額外的元資料
    """

    coverage_id: str
    observer: Observer
    start_time: datetime
    end_time: datetime
    snapshots: List[CoverageSnapshot] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def duration_minutes(self) -> float:
        """分析持續時間（分鐘）"""
        return (self.end_time - self.start_time).total_seconds() / 60

    @property
    def average_visible_count(self) -> float:
        """平均可見衛星數"""
        if not self.snapshots:
            return 0.0
        return sum(s.visible_count for s in self.snapshots) / len(self.snapshots)

    @property
    def max_visible_count(self) -> int:
        """最大可見衛星數"""
        if not self.snapshots:
            return 0
        return max(s.visible_count for s in self.snapshots)

    @property
    def min_visible_count(self) -> int:
        """最小可見衛星數"""
        if not self.snapshots:
            return 0
        return min(s.visible_count for s in self.snapshots)

    @property
    def coverage_percentage(self) -> float:
        """覆蓋率百分比（至少有一顆衛星可見的時間比例）"""
        if not self.snapshots:
            return 0.0
        covered = sum(1 for s in self.snapshots if s.visible_count > 0)
        return (covered / len(self.snapshots)) * 100

    def get_statistics(self) -> Dict[str, Any]:
        """獲取統計資訊

        Returns:
            Dict: 統計資訊字典
        """
        return {
            "duration_minutes": self.duration_minutes,
            "average_visible_count": self.average_visible_count,
            "max_visible_count": self.max_visible_count,
            "min_visible_count": self.min_visible_count,
            "coverage_percentage": self.coverage_percentage,
            "total_snapshots": len(self.snapshots),
            "observer": {
                "name": self.observer.name,
                "latitude": self.observer.position.latitude,
                "longitude": self.observer.position.longitude,
                "elevation": self.observer.position.elevation,
                "min_elevation": self.observer.min_elevation,
            },
        }

