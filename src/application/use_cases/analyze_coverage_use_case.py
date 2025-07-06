"""
分析覆蓋率用例
"""

from ...domain.entities.observer import Observer
from ...domain.exceptions import NoSatellitesAvailableError, InvalidTimeRangeError
from ...domain.repositories.coverage_repository import CoverageRepository
from ...domain.repositories.satellite_repository import SatelliteRepository
from ...domain.services.coverage_analyzer import CoverageAnalyzer
from ...domain.value_objects.position import Position
from ..dto.coverage_request import CoverageRequest
from ..dto.coverage_response import CoverageResponse
from ..exceptions import convert_domain_exception, CoverageAnalysisError


class AnalyzeCoverageUseCase:
    """分析衛星覆蓋率的用例

    這是應用層的核心用例，協調領域層的實體和服務
    """

    def __init__(
        self, 
        satellite_repository: SatelliteRepository, 
        coverage_analyzer: CoverageAnalyzer,
        coverage_repository: CoverageRepository
    ):
        """初始化用例

        Args:
            satellite_repository: 衛星資料庫
            coverage_analyzer: 覆蓋率分析器
            coverage_repository: 覆蓋率儲存庫
        """
        self.satellite_repository = satellite_repository
        self.coverage_analyzer = coverage_analyzer
        self.coverage_repository = coverage_repository

    async def execute(self, request: CoverageRequest) -> CoverageResponse:
        """執行覆蓋率分析

        Args:
            request: 覆蓋率分析請求

        Returns:
            CoverageResponse: 分析結果
            
        Raises:
            NoSatellitesAvailableError: 沒有可用的衛星
            InvalidTimeRangeError: 無效的時間範圍
            CoverageAnalysisError: 分析過程中的錯誤
        """
        try:
            # 1. 創建觀測者
            observer_position = Position(
                latitude=request.observer.latitude, 
                longitude=request.observer.longitude, 
                elevation=request.observer.altitude
            )

            observer = Observer(
                observer_id=f"observer-{request.observer.latitude}-{request.observer.longitude}",
                name="User Observer",
                position=observer_position,
                min_elevation=request.elevation_mask,
            )

            # 2. 獲取衛星列表
            if hasattr(request, 'satellite_filter') and request.satellite_filter:
                satellites = await self.satellite_repository.get_satellites_by_name_pattern(request.satellite_filter)
            else:
                satellites = await self.satellite_repository.get_active_satellites()

            if not satellites:
                raise NoSatellitesAvailableError(
                    filter_criteria={"filter": request.satellite_filter if hasattr(request, 'satellite_filter') else None}
                )

            # 3. 執行覆蓋率分析
            coverage = self.coverage_analyzer.analyze_coverage(
                satellites=satellites,
                observer=observer,
                start_time=request.start_time,
                duration_minutes=int((request.end_time - request.start_time).total_seconds() / 60),
                interval_minutes=request.time_step_minutes,
            )

            # 4. 找出最佳觀測窗口
            optimal_windows = self.coverage_analyzer.find_optimal_windows(
                coverage=coverage, min_satellites=30, min_duration_minutes=30  # 可以從請求中獲取
            )

            # 5. 保存分析結果
            self.coverage_repository.save(coverage)
            
            # 6. 轉換為回應 DTO
            response = CoverageResponse.from_domain(coverage, optimal_windows)

            return response
            
        except (NoSatellitesAvailableError, InvalidTimeRangeError):
            # 領域例外直接拋出，讓中間件處理
            raise
        except Exception as e:
            # 其他例外包裝為應用層例外
            raise CoverageAnalysisError(
                reason=str(e),
                details={"original_error": type(e).__name__}
            )
