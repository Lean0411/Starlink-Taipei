"""
預測覆蓋用例 - 處理預測請求的應用層邏輯
"""

from datetime import datetime
from typing import Optional

from ...domain.entities.observer import Observer
from ...domain.entities.prediction import PredictionTimeScale
from ...domain.repositories.satellite_repository import SatelliteRepository
from ...domain.services.prediction_service import PredictionService
from ...domain.value_objects.position import Position
from ..dto.prediction_request import PredictionRequest
from ..dto.prediction_response import PredictionResponse


class PredictCoverageUseCase:
    """預測覆蓋用例

    協調領域服務和資料庫來執行預測分析
    """

    def __init__(self, satellite_repository: SatelliteRepository, prediction_service: PredictionService):
        """初始化用例

        Args:
            satellite_repository: 衛星資料庫
            prediction_service: 預測服務
        """
        self.satellite_repository = satellite_repository
        self.prediction_service = prediction_service

    def execute(self, request: PredictionRequest) -> PredictionResponse:
        """執行預測

        Args:
            request: 預測請求

        Returns:
            PredictionResponse: 預測響應
        """
        # 獲取活躍衛星
        satellites = self.satellite_repository.get_active_satellites()

        # 如果指定了衛星子集，進行過濾
        if request.satellite_ids:
            satellites = [s for s in satellites if s.satellite_id in request.satellite_ids]

        # 創建觀測者
        observer = Observer(
            observer_id=f"observer-{request.observer.latitude}-{request.observer.longitude}",
            name="預測觀測者",
            position=Position(
                latitude=request.observer.latitude, longitude=request.observer.longitude, elevation=request.observer.altitude
            ),
            min_elevation=request.min_elevation,
        )

        # 執行預測
        prediction = self.prediction_service.predict_coverage(
            satellites=satellites, observer=observer, time_scale=request.time_scale, start_time=request.start_time
        )

        # 構建響應
        response = PredictionResponse.from_domain(
            prediction=prediction, total_satellites=len(satellites), analyzed_satellites=len(satellites)
        )

        return response
