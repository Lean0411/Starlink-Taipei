"""
預測服務介面 - 定義預測功能的抽象介面
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

from ..entities.observer import Observer
from ..entities.prediction import Prediction, PredictionTimeScale
from ..entities.satellite import Satellite


class PredictionService(ABC):
    """預測服務抽象介面

    定義了預測衛星覆蓋的核心功能
    """

    @abstractmethod
    def predict_coverage(
        self,
        satellites: List[Satellite],
        observer: Observer,
        time_scale: PredictionTimeScale,
        start_time: Optional[datetime] = None,
    ) -> Prediction:
        """預測衛星覆蓋

        Args:
            satellites: 要預測的衛星列表
            observer: 觀測者
            time_scale: 預測時間尺度
            start_time: 預測開始時間（預設為當前時間）

        Returns:
            Prediction: 預測結果
        """
        pass

    @abstractmethod
    def find_optimal_windows(self, prediction: Prediction, min_satellites: int = 30, min_duration_minutes: int = 30) -> List:
        """從預測結果中找出最佳觀測窗口

        Args:
            prediction: 預測結果
            min_satellites: 最少衛星數閾值
            min_duration_minutes: 最短持續時間（分鐘）

        Returns:
            List[OptimalWindow]: 最佳觀測窗口列表
        """
        pass

    @abstractmethod
    def calculate_prediction_uncertainty(self, prediction_time: datetime, base_time: datetime) -> dict:
        """計算預測不確定性

        Args:
            prediction_time: 預測時間
            base_time: 基準時間（通常是當前時間）

        Returns:
            dict: 包含各種不確定性指標的字典
        """
        pass
