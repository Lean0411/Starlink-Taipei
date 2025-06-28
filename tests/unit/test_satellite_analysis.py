# MIT License
# Copyright (c) 2025 Starlink Taipei Analysis Team
#
# This file is part of the Starlink Taipei Satellite Analysis System.

"""
衛星分析模組的單元測試
"""

import sys
import os
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from pathlib import Path

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from satellite_analysis import StarlinkAnalysis, process_time_point_worker

class TestStarlinkAnalysis:
    """StarlinkAnalysis 類別的測試"""
    
    @pytest.fixture
    def analyzer(self, tmp_path):
        """創建測試用的分析器實例"""
        return StarlinkAnalysis(output_dir=str(tmp_path))
    
    def test_init(self, analyzer, tmp_path):
        """測試初始化"""
        assert analyzer.output_dir == Path(tmp_path)
        assert analyzer.satellites == []
        assert analyzer.raw_tle_data == []
        assert analyzer.observer is not None
        
    def test_set_observer_location(self, analyzer):
        """測試設置觀察者位置"""
        lat, lon = 25.0330, 121.5654
        analyzer.set_observer_location(lat, lon)
        
        assert analyzer.observer.latitude.degrees == pytest.approx(lat, rel=1e-4)
        assert analyzer.observer.longitude.degrees == pytest.approx(lon, rel=1e-4)
    
    def test_calculate_stats_empty_dataframe(self, analyzer):
        """測試空 DataFrame 的統計計算"""
        empty_df = pd.DataFrame()
        stats = analyzer.calculate_stats(empty_df)
        
        assert stats['avg_visible_satellites'] == 0
        assert stats['max_visible_satellites'] == 0
        assert stats['min_visible_satellites'] == 0
        assert stats['coverage_percentage'] == 0
    
    def test_calculate_stats_with_data(self, analyzer):
        """測試有數據的統計計算"""
        data = {
            'visible_count': [10, 15, 20, 25, 30],
            'elevation': [45.0, 50.0, 55.0, 60.0, 65.0]
        }
        df = pd.DataFrame(data)
        stats = analyzer.calculate_stats(df)
        
        assert stats['avg_visible_satellites'] == 20.0
        assert stats['max_visible_satellites'] == 30
        assert stats['min_visible_satellites'] == 10
        assert stats['coverage_percentage'] == 100.0
        assert stats['avg_elevation'] == 55.0
        assert stats['max_elevation'] == 65.0
    
    def test_save_results(self, analyzer, tmp_path):
        """測試保存結果"""
        # 準備測試數據
        data = {
            'timestamp': pd.date_range('2025-06-28', periods=5, freq='1min'),
            'visible_count': [10, 15, 20, 25, 30],
            'elevation': [45.0, 50.0, 55.0, 60.0, 65.0]
        }
        df = pd.DataFrame(data)
        
        stats = {
            'avg_visible_satellites': 20.0,
            'max_visible_satellites': 30,
            'coverage_percentage': 100.0,
            'avg_elevation': 55.0
        }
        
        file_paths = analyzer.save_results(df, stats)
        
        # 驗證文件是否被創建
        assert Path(file_paths['data_path']).exists()
        assert Path(file_paths['stats_path']).exists()
        assert Path(file_paths['report_path']).exists()
        
        # 驗證 CSV 內容
        saved_df = pd.read_csv(file_paths['data_path'])
        assert len(saved_df) == 5
        assert 'visible_count' in saved_df.columns
        
    def test_generate_plots(self, analyzer, tmp_path):
        """測試圖表生成"""
        data = {
            'timestamp': pd.date_range('2025-06-28', periods=10, freq='1min'),
            'visible_count': np.random.randint(10, 40, 10),
            'elevation': np.random.uniform(30, 80, 10)
        }
        df = pd.DataFrame(data)
        
        plots_paths = analyzer.generate_plots(df)
        
        # 應該生成至少一個圖表
        assert len(plots_paths) >= 1
        
        # 驗證圖表文件存在
        for plot_path in plots_paths:
            assert Path(plot_path).exists()
            assert plot_path.endswith('.png')


class TestProcessTimePointWorker:
    """測試時間點處理函數"""
    
    def test_process_time_point_with_no_satellites(self):
        """測試沒有衛星數據的情況"""
        # 創建空的 TLE 數據
        empty_tle_data = []
        
        # 模擬時間點
        from skyfield.api import load
        ts = load.timescale()
        time_point = ts.now()
        time_point_dt = datetime.now(timezone.utc)
        
        result = process_time_point_worker(
            (time_point, time_point_dt),
            empty_tle_data,
            25.0330,  # 台北緯度
            121.5654,  # 台北經度
            10.0,  # 海拔
            {},
            25.0  # 最小仰角
        )
        
        assert result['visible_count'] == 0
        assert result['elevation'] == 0
        assert result['best_satellite'] is None
        assert result['distance_km'] == 0


@pytest.mark.parametrize("lat,lon", [
    (25.0330, 121.5654),  # 台北
    (22.6273, 120.3014),  # 高雄
    (24.1477, 120.6736),  # 台中
])
def test_different_locations(lat, lon, tmp_path):
    """測試不同位置的分析"""
    analyzer = StarlinkAnalysis(output_dir=str(tmp_path))
    analyzer.set_observer_location(lat, lon)
    
    assert analyzer.observer.latitude.degrees == pytest.approx(lat, rel=1e-4)
    assert analyzer.observer.longitude.degrees == pytest.approx(lon, rel=1e-4)