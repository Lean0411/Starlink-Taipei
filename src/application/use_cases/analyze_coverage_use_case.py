"""
分析覆蓋率用例
"""
from typing import Optional

from ..dto.coverage_request import CoverageRequest
from ..dto.coverage_response import CoverageResponse
from ...domain.entities.observer import Observer
from ...domain.value_objects.position import Position
from ...domain.repositories.satellite_repository import SatelliteRepository
from ...domain.services.coverage_analyzer import CoverageAnalyzer


class AnalyzeCoverageUseCase:
    """分析衛星覆蓋率的用例
    
    這是應用層的核心用例，協調領域層的實體和服務
    """
    
    def __init__(
        self,
        satellite_repository: SatelliteRepository,
        coverage_analyzer: CoverageAnalyzer
    ):
        """初始化用例
        
        Args:
            satellite_repository: 衛星資料庫
            coverage_analyzer: 覆蓋率分析器
        """
        self.satellite_repository = satellite_repository
        self.coverage_analyzer = coverage_analyzer
    
    async def execute(self, request: CoverageRequest) -> CoverageResponse:
        """執行覆蓋率分析
        
        Args:
            request: 覆蓋率分析請求
            
        Returns:
            CoverageResponse: 分析結果
        """
        # 1. 創建觀測者
        observer_position = Position(
            latitude=request.observer_latitude,
            longitude=request.observer_longitude,
            elevation=request.observer_elevation
        )
        
        observer = Observer(
            observer_id=f"observer-{request.observer_latitude}-{request.observer_longitude}",
            name="User Observer",
            position=observer_position,
            min_elevation=request.min_elevation
        )
        
        # 2. 獲取衛星列表
        if request.satellite_filter:
            satellites = await self.satellite_repository.get_satellites_by_name_pattern(
                request.satellite_filter
            )
        else:
            satellites = await self.satellite_repository.get_active_satellites()
        
        if not satellites:
            raise ValueError("沒有找到符合條件的衛星")
        
        # 3. 執行覆蓋率分析
        coverage = self.coverage_analyzer.analyze_coverage(
            satellites=satellites,
            observer=observer,
            start_time=request.start_time,
            duration_minutes=request.duration_minutes,
            interval_minutes=request.interval_minutes
        )
        
        # 4. 找出最佳觀測窗口
        optimal_windows = self.coverage_analyzer.find_optimal_windows(
            coverage=coverage,
            min_satellites=30,  # 可以從請求中獲取
            min_duration_minutes=30
        )
        
        # 5. 轉換為回應 DTO
        response = CoverageResponse.from_domain(coverage, optimal_windows)
        
        return response