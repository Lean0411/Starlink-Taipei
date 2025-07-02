"""
覆蓋率實體 - 表示衛星覆蓋分析結果
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List

from .observer import Observer
from .satellite import Satellite


@dataclass
class CoverageWindow:
    """衛星覆蓋視窗"""

    satellite_id: str
    start_time: datetime
    end_time: datetime
    max_elevation: float

    @property
    def duration_minutes(self) -> float:
        """覆蓋持續時間（分鐘）"""
        return (self.end_time - self.start_time).total_seconds() / 60.0


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
        observer_name: 觀測者名稱
        start_time: 分析開始時間
        end_time: 分析結束時間
        elevation_mask: 最小仰角限制
        coverage_windows: 覆蓋視窗列表
        snapshots: 時間序列快照
        metadata: 額外的元資料
    """

    observer_name: str
    start_time: datetime
    end_time: datetime
    elevation_mask: float = 25.0
    coverage_windows: List[CoverageWindow] = field(default_factory=list)
    snapshots: List[CoverageSnapshot] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_coverage_window(self, window: CoverageWindow) -> None:
        """添加覆蓋視窗"""
        self.coverage_windows.append(window)

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
        # 計算覆蓋統計
        unique_satellites = set(w.satellite_id for w in self.coverage_windows)
        total_coverage_minutes = sum(w.duration_minutes for w in self.coverage_windows)
        total_duration_minutes = (self.end_time - self.start_time).total_seconds() / 60.0
        coverage_percentage = (total_coverage_minutes / total_duration_minutes * 100) if total_duration_minutes > 0 else 0

        return {
            "total_windows": len(self.coverage_windows),
            "unique_satellites": len(unique_satellites),
            "total_coverage_minutes": total_coverage_minutes,
            "coverage_percentage": coverage_percentage,
            "duration_minutes": self.duration_minutes,
            "average_visible_count": self.average_visible_count,
            "max_visible_count": self.max_visible_count,
            "min_visible_count": self.min_visible_count,
            "total_snapshots": len(self.snapshots),
            "observer_name": self.observer_name,
        }
