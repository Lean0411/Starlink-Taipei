"""
覆蓋率分析實體
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any
import uuid

from ..value_objects.position import Position


@dataclass
class CoverageSnapshot:
    """覆蓋率快照 - 某個時間點的覆蓋狀況"""
    
    timestamp: datetime
    visible_satellites: List[str]  # 可見衛星的 ID 列表
    satellite_positions: Dict[str, Position]  # 衛星位置
    
    @property
    def visible_count(self) -> int:
        """可見衛星數量"""
        return len(self.visible_satellites)


@dataclass
class CoverageStatistics:
    """覆蓋率統計資訊"""
    
    duration_minutes: int
    average_visible_count: float
    max_visible_count: int
    min_visible_count: int
    coverage_percentage: float  # 有衛星覆蓋的時間百分比
    total_snapshots: int
    
    @classmethod
    def from_snapshots(cls, snapshots: List[CoverageSnapshot], duration_minutes: int) -> "CoverageStatistics":
        """從快照列表計算統計資訊"""
        if not snapshots:
            return cls(
                duration_minutes=duration_minutes,
                average_visible_count=0.0,
                max_visible_count=0,
                min_visible_count=0,
                coverage_percentage=0.0,
                total_snapshots=0
            )
        
        visible_counts = [s.visible_count for s in snapshots]
        covered_snapshots = sum(1 for s in snapshots if s.visible_count > 0)
        
        return cls(
            duration_minutes=duration_minutes,
            average_visible_count=sum(visible_counts) / len(visible_counts),
            max_visible_count=max(visible_counts),
            min_visible_count=min(visible_counts),
            coverage_percentage=(covered_snapshots / len(snapshots)) * 100,
            total_snapshots=len(snapshots)
        )


@dataclass
class OptimalWindow:
    """最佳觀測窗口"""
    
    start_time: datetime
    end_time: datetime
    avg_satellites: float
    max_elevation: float
    
    @property
    def duration_minutes(self) -> int:
        """窗口持續時間（分鐘）"""
        return int((self.end_time - self.start_time).total_seconds() / 60)


@dataclass
class CoverageAnalysis:
    """覆蓋率分析結果實體"""
    
    coverage_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    observer: Any = None  # Observer 實體
    start_time: datetime = None
    end_time: datetime = None
    snapshots: List[CoverageSnapshot] = field(default_factory=list)
    statistics: CoverageStatistics = None
    analyzed_satellites: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """初始化後處理"""
        if self.statistics is None and self.snapshots:
            duration_minutes = int((self.end_time - self.start_time).total_seconds() / 60)
            self.statistics = CoverageStatistics.from_snapshots(self.snapshots, duration_minutes)
    
    def add_snapshot(self, snapshot: CoverageSnapshot):
        """添加快照"""
        self.snapshots.append(snapshot)
        
    def update_statistics(self):
        """更新統計資訊"""
        if self.snapshots and self.start_time and self.end_time:
            duration_minutes = int((self.end_time - self.start_time).total_seconds() / 60)
            self.statistics = CoverageStatistics.from_snapshots(self.snapshots, duration_minutes)