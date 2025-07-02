"""
覆蓋率分析領域服務
"""

import uuid
from datetime import datetime, timedelta
from typing import List

from ..entities.coverage import Coverage, CoverageSnapshot, SatelliteVisibility
from ..entities.observer import Observer
from ..entities.satellite import Satellite
from .orbit_calculator import OrbitCalculator


class CoverageAnalyzer:
    """覆蓋率分析服務

    負責分析衛星覆蓋率的核心業務邏輯
    """

    def __init__(self, orbit_calculator: OrbitCalculator):
        """初始化覆蓋率分析器

        Args:
            orbit_calculator: 軌道計算器
        """
        self.orbit_calculator = orbit_calculator

    def analyze_coverage(
        self,
        satellites: List[Satellite],
        observer: Observer,
        start_time: datetime,
        duration_minutes: int,
        interval_minutes: int = 1,
    ) -> Coverage:
        """分析衛星覆蓋率

        Args:
            satellites: 衛星列表
            observer: 觀測者
            start_time: 開始時間
            duration_minutes: 持續時間（分鐘）
            interval_minutes: 時間間隔（分鐘）

        Returns:
            Coverage: 覆蓋率分析結果
        """
        end_time = start_time + timedelta(minutes=duration_minutes)
        coverage_id = str(uuid.uuid4())

        coverage = Coverage(
            coverage_id=coverage_id,
            observer=observer,
            start_time=start_time,
            end_time=end_time,
            metadata={"total_satellites": len(satellites), "interval_minutes": interval_minutes},
        )

        # 生成時間點
        current_time = start_time
        while current_time <= end_time:
            snapshot = self._analyze_at_time(satellites, observer, current_time)
            coverage.snapshots.append(snapshot)
            current_time += timedelta(minutes=interval_minutes)

        return coverage

    def _analyze_at_time(self, satellites: List[Satellite], observer: Observer, time: datetime) -> CoverageSnapshot:
        """分析特定時間點的覆蓋情況

        Args:
            satellites: 衛星列表
            observer: 觀測者
            time: 分析時間

        Returns:
            CoverageSnapshot: 覆蓋快照
        """
        snapshot = CoverageSnapshot(timestamp=time, observer=observer)

        for satellite in satellites:
            if not satellite.is_active:
                continue

            try:
                # 計算衛星位置和可見性
                azimuth, elevation, distance = self.orbit_calculator.calculate_pass_details(satellite, observer.position, time)

                # 檢查是否滿足最小仰角要求
                if observer.can_observe(elevation):
                    is_sunlit = self.orbit_calculator.is_sunlit(satellite, time)

                    visibility = SatelliteVisibility(
                        satellite=satellite, azimuth=azimuth, elevation=elevation, distance=distance, is_sunlit=is_sunlit
                    )

                    snapshot.visible_satellites.append(visibility)

            except Exception:
                # 如果計算失敗，跳過這顆衛星
                # 在領域層，我們不處理具體的技術異常
                continue

        return snapshot

    def find_optimal_windows(self, coverage: Coverage, min_satellites: int = 30, min_duration_minutes: int = 30) -> List[dict]:
        """找出最佳觀測窗口

        Args:
            coverage: 覆蓋率分析結果
            min_satellites: 最少衛星數量
            min_duration_minutes: 最短持續時間（分鐘）

        Returns:
            List[dict]: 最佳觀測窗口列表
        """
        windows = []
        current_window = None

        for i, snapshot in enumerate(coverage.snapshots):
            if snapshot.visible_count >= min_satellites:
                if current_window is None:
                    current_window = {
                        "start_time": snapshot.timestamp,
                        "start_index": i,
                        "satellite_counts": [snapshot.visible_count],
                        "max_elevation": snapshot.max_elevation,
                    }
                else:
                    current_window["satellite_counts"].append(snapshot.visible_count)
                    current_window["max_elevation"] = max(current_window["max_elevation"], snapshot.max_elevation)
            else:
                if current_window is not None:
                    # 結束當前窗口
                    duration = (i - current_window["start_index"]) * coverage.metadata.get("interval_minutes", 1)
                    if duration >= min_duration_minutes:
                        current_window["end_time"] = coverage.snapshots[i - 1].timestamp
                        current_window["duration_minutes"] = duration
                        current_window["avg_satellites"] = sum(current_window["satellite_counts"]) / len(
                            current_window["satellite_counts"]
                        )
                        windows.append(current_window)
                    current_window = None

        # 處理最後一個窗口
        if current_window is not None:
            duration = (len(coverage.snapshots) - current_window["start_index"]) * coverage.metadata.get("interval_minutes", 1)
            if duration >= min_duration_minutes:
                current_window["end_time"] = coverage.snapshots[-1].timestamp
                current_window["duration_minutes"] = duration
                current_window["avg_satellites"] = sum(current_window["satellite_counts"]) / len(
                    current_window["satellite_counts"]
                )
                windows.append(current_window)

        # 按平均衛星數排序
        windows.sort(key=lambda w: w["avg_satellites"], reverse=True)

        return windows
