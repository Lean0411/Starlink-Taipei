"""
覆蓋率分析回應 DTO
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List

from ...domain.entities.coverage import Coverage


@dataclass
class SatelliteVisibilityDTO:
    """衛星可見性 DTO"""

    satellite_name: str
    azimuth: float
    elevation: float
    distance: float
    is_sunlit: bool


@dataclass
class CoverageSnapshotDTO:
    """覆蓋快照 DTO"""

    timestamp: str
    visible_count: int
    visible_satellites: List[SatelliteVisibilityDTO]
    max_elevation: float
    average_elevation: float


@dataclass
class CoverageStatisticsDTO:
    """覆蓋統計 DTO"""

    duration_minutes: float
    average_visible_count: float
    max_visible_count: int
    min_visible_count: int
    coverage_percentage: float
    total_snapshots: int


@dataclass
class CoverageResponse:
    """覆蓋率分析回應

    Attributes:
        coverage_id: 覆蓋分析 ID
        observer: 觀測者資訊
        start_time: 開始時間
        end_time: 結束時間
        statistics: 統計資訊
        snapshots: 時間序列快照
        optimal_windows: 最佳觀測窗口
    """

    coverage_id: str
    observer: Dict[str, Any]
    start_time: str
    end_time: str
    statistics: CoverageStatisticsDTO
    snapshots: List[CoverageSnapshotDTO] = field(default_factory=list)
    optimal_windows: List[Dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_domain(cls, coverage: Coverage, optimal_windows: List[dict] = None) -> "CoverageResponse":
        """從領域實體轉換為 DTO

        Args:
            coverage: 領域覆蓋實體
            optimal_windows: 最佳觀測窗口

        Returns:
            CoverageResponse: 回應 DTO
        """
        # 轉換統計資訊
        stats = coverage.get_statistics()
        statistics_dto = CoverageStatisticsDTO(
            duration_minutes=stats["duration_minutes"],
            average_visible_count=stats["average_visible_count"],
            max_visible_count=stats["max_visible_count"],
            min_visible_count=stats["min_visible_count"],
            coverage_percentage=stats["coverage_percentage"],
            total_snapshots=stats["total_snapshots"],
        )

        # 轉換快照
        snapshots_dto = []
        for snapshot in coverage.snapshots:
            visible_satellites_dto = [
                SatelliteVisibilityDTO(
                    satellite_name=vis.satellite.name,
                    azimuth=vis.azimuth,
                    elevation=vis.elevation,
                    distance=vis.distance,
                    is_sunlit=vis.is_sunlit,
                )
                for vis in snapshot.visible_satellites
                if vis.is_visible
            ]

            snapshot_dto = CoverageSnapshotDTO(
                timestamp=snapshot.timestamp.isoformat(),
                visible_count=snapshot.visible_count,
                visible_satellites=visible_satellites_dto,
                max_elevation=snapshot.max_elevation,
                average_elevation=snapshot.average_elevation,
            )
            snapshots_dto.append(snapshot_dto)

        return cls(
            coverage_id=coverage.coverage_id,
            observer=stats["observer"],
            start_time=coverage.start_time.isoformat(),
            end_time=coverage.end_time.isoformat(),
            statistics=statistics_dto,
            snapshots=snapshots_dto,
            optimal_windows=optimal_windows or [],
        )
