"""預測實體的單元測試"""

import pytest
from datetime import datetime, timezone, timedelta
from src.domain.entities.prediction import (
    Prediction, PredictionPoint, OptimalWindow, PredictionTimeScale
)


class TestPredictionPoint:
    """測試預測點"""
    
    def test_prediction_point_creation(self):
        """測試預測點創建"""
        point = PredictionPoint(
            timestamp=datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            predicted_satellites=35,
            predicted_elevation=45.0,
            coverage_probability=87.5,
            uncertainty={"satellites": 3.0, "elevation": 2.0, "coverage": 5.0},
            confidence_interval={"lower": 32, "upper": 38}
        )
        
        assert point.predicted_satellites == 35
        assert point.predicted_elevation == 45.0
        assert point.coverage_probability == 87.5
        assert point.is_high_coverage is True
    
    def test_reliability_score(self):
        """測試可靠性分數計算"""
        # 低不確定性 = 高可靠性
        point1 = PredictionPoint(
            timestamp=datetime.now(timezone.utc),
            predicted_satellites=30,
            predicted_elevation=40.0,
            coverage_probability=75.0,
            uncertainty={"satellites": 1.0, "elevation": 1.0, "coverage": 1.0},
            confidence_interval={"lower": 29, "upper": 31}
        )
        
        # 高不確定性 = 低可靠性
        point2 = PredictionPoint(
            timestamp=datetime.now(timezone.utc),
            predicted_satellites=30,
            predicted_elevation=40.0,
            coverage_probability=75.0,
            uncertainty={"satellites": 5.0, "elevation": 5.0, "coverage": 5.0},
            confidence_interval={"lower": 25, "upper": 35}
        )
        
        assert point1.reliability_score > point2.reliability_score


class TestOptimalWindow:
    """測試最佳觀測窗口"""
    
    def test_optimal_window_creation(self):
        """測試最佳窗口創建"""
        window = OptimalWindow(
            start_time=datetime(2025, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
            end_time=datetime(2025, 1, 1, 11, 30, 0, tzinfo=timezone.utc),
            avg_satellites=42.5,
            max_elevation=65.0,
            duration_minutes=90
        )
        
        assert window.avg_satellites == 42.5
        assert window.max_elevation == 65.0
        assert window.duration_minutes == 90
        assert window.is_extended_window is True
    
    def test_window_overlap(self):
        """測試窗口重疊檢測"""
        window1 = OptimalWindow(
            start_time=datetime(2025, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
            end_time=datetime(2025, 1, 1, 11, 0, 0, tzinfo=timezone.utc),
            avg_satellites=30.0,
            max_elevation=50.0,
            duration_minutes=60
        )
        
        # 重疊窗口
        window2 = OptimalWindow(
            start_time=datetime(2025, 1, 1, 10, 30, 0, tzinfo=timezone.utc),
            end_time=datetime(2025, 1, 1, 11, 30, 0, tzinfo=timezone.utc),
            avg_satellites=35.0,
            max_elevation=55.0,
            duration_minutes=60
        )
        
        # 不重疊窗口
        window3 = OptimalWindow(
            start_time=datetime(2025, 1, 1, 11, 30, 0, tzinfo=timezone.utc),
            end_time=datetime(2025, 1, 1, 12, 30, 0, tzinfo=timezone.utc),
            avg_satellites=32.0,
            max_elevation=52.0,
            duration_minutes=60
        )
        
        assert window1.overlaps_with(window2) is True
        assert window1.overlaps_with(window3) is False


class TestPrediction:
    """測試預測實體"""
    
    def test_prediction_creation(self):
        """測試預測創建"""
        prediction = Prediction(
            prediction_id="test-123",
            observer_name="台北觀測站",
            time_scale=PredictionTimeScale.MEDIUM_TERM,
            created_at=datetime.now(timezone.utc),
            start_time=datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            end_time=datetime(2025, 1, 2, 0, 0, 0, tzinfo=timezone.utc)
        )
        
        assert prediction.prediction_id == "test-123"
        assert prediction.observer_name == "台北觀測站"
        assert prediction.time_scale == PredictionTimeScale.MEDIUM_TERM
        assert prediction.duration_hours == 24.0
    
    def test_add_prediction_points(self):
        """測試添加預測點"""
        prediction = Prediction(
            prediction_id="test-123",
            observer_name="台北觀測站",
            time_scale=PredictionTimeScale.SHORT_TERM,
            created_at=datetime.now(timezone.utc),
            start_time=datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            end_time=datetime(2025, 1, 1, 1, 0, 0, tzinfo=timezone.utc)
        )
        
        # 添加預測點
        for i in range(3):
            point = PredictionPoint(
                timestamp=datetime(2025, 1, 1, 0, i * 20, 0, tzinfo=timezone.utc),
                predicted_satellites=30 + i * 5,
                predicted_elevation=40.0 + i * 5,
                coverage_probability=75.0 + i * 5,
                uncertainty={"satellites": 2.0, "elevation": 1.5, "coverage": 3.0},
                confidence_interval={"lower": 28 + i * 5, "upper": 32 + i * 5}
            )
            prediction.add_prediction_point(point)
        
        assert len(prediction.prediction_points) == 3
        assert prediction.average_satellites == 35.0  # (30 + 35 + 40) / 3
    
    def test_coverage_availability(self):
        """測試覆蓋可用性計算"""
        prediction = Prediction(
            prediction_id="test-123",
            observer_name="台北觀測站",
            time_scale=PredictionTimeScale.SHORT_TERM,
            created_at=datetime.now(timezone.utc),
            start_time=datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            end_time=datetime(2025, 1, 1, 1, 0, 0, tzinfo=timezone.utc)
        )
        
        # 添加混合的預測點（部分高覆蓋，部分低覆蓋）
        high_coverage_points = 3
        low_coverage_points = 2
        
        for i in range(high_coverage_points):
            prediction.add_prediction_point(PredictionPoint(
                timestamp=datetime.now(timezone.utc),
                predicted_satellites=40,
                predicted_elevation=50.0,
                coverage_probability=85.0,  # 高於80%
                uncertainty={},
                confidence_interval={}
            ))
        
        for i in range(low_coverage_points):
            prediction.add_prediction_point(PredictionPoint(
                timestamp=datetime.now(timezone.utc),
                predicted_satellites=20,
                predicted_elevation=30.0,
                coverage_probability=50.0,  # 低於80%
                uncertainty={},
                confidence_interval={}
            ))
        
        assert prediction.coverage_availability == 60.0  # 3/5 * 100
    
    def test_calculate_statistics(self):
        """測試統計計算"""
        prediction = Prediction(
            prediction_id="test-123",
            observer_name="台北觀測站",
            time_scale=PredictionTimeScale.MEDIUM_TERM,
            created_at=datetime.now(timezone.utc),
            start_time=datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            end_time=datetime(2025, 1, 1, 3, 0, 0, tzinfo=timezone.utc)
        )
        
        # 添加預測點
        for hour in range(3):
            for minute in [0, 30]:
                point = PredictionPoint(
                    timestamp=datetime(2025, 1, 1, hour, minute, 0, tzinfo=timezone.utc),
                    predicted_satellites=30 + hour * 5,
                    predicted_elevation=40.0 + hour * 3,
                    coverage_probability=75.0 + hour * 5,
                    uncertainty={"satellites": 2.0, "elevation": 1.5, "coverage": 3.0},
                    confidence_interval={"lower": 28, "upper": 32}
                )
                prediction.add_prediction_point(point)
        
        # 添加最佳窗口
        window = OptimalWindow(
            start_time=datetime(2025, 1, 1, 0, 30, 0, tzinfo=timezone.utc),
            end_time=datetime(2025, 1, 1, 1, 30, 0, tzinfo=timezone.utc),
            avg_satellites=35.0,
            max_elevation=50.0,
            duration_minutes=60
        )
        prediction.add_optimal_window(window)
        
        stats = prediction.calculate_statistics()
        
        assert "satellites" in stats
        assert stats["satellites"]["mean"] == 35.0  # 平均值
        assert stats["satellites"]["max"] == 40  # 最大值
        assert stats["satellites"]["min"] == 30  # 最小值
        assert stats["optimal_windows_count"] == 1
        assert 2 in stats["peak_hours"]  # 第2小時的衛星數最多