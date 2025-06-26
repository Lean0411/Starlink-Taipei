# MIT License
# Copyright (c) 2025 Starlink Taipei Analysis Team
#
# This file is part of the Starlink Taipei Satellite Analysis System.

"""
satellite_analysis.py 的單元測試（修復版）
"""

import pytest
import json
import os
import sys
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta, timezone

# 添加專案路徑到 Python 路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestSatelliteAnalysis:
    """測試衛星分析核心功能"""
    
    @pytest.mark.unit
    @patch('satellite_analysis.wgs84')
    @patch('satellite_analysis.load')
    @patch('satellite_analysis.EarthSatellite')
    def test_process_time_point_worker_with_visible_satellite(self, mock_earth_satellite, mock_load, mock_wgs84, mock_observer_location):
        """測試當有可見衛星時的處理"""
        # 導入模組（在 patch 之後）
        import satellite_analysis
        
        # 準備測試數據
        mock_ts = MagicMock()
        mock_load.timescale.return_value = mock_ts
        
        mock_time = MagicMock()
        time_datetime = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        time_data = (mock_time, time_datetime)
        
        # Mock TLE 數據
        tle_list = [
            ("STARLINK-TEST", "1 44713U 19074A   24001.50000000", "2 44713  53.0540 123.4567")
        ]
        
        # Mock 衛星物件
        mock_sat = MagicMock()
        mock_sat.name = "STARLINK-TEST"
        mock_earth_satellite.return_value = mock_sat
        
        # Mock 觀測者位置
        mock_observer = MagicMock()
        mock_wgs84.latlon.return_value = mock_observer
        
        # Mock 位置計算
        mock_topocentric = MagicMock()
        mock_alt = MagicMock()
        mock_alt.degrees = 45.0  # 高於最小仰角
        mock_az = MagicMock()
        mock_az.degrees = 180.0
        mock_distance = MagicMock()
        mock_distance.km = 550.0
        mock_topocentric.altaz.return_value = (mock_alt, mock_az, mock_distance)
        
        mock_difference = MagicMock()
        mock_difference.at.return_value = mock_topocentric
        mock_sat.__sub__.return_value = mock_difference
        
        # Mock geocentric 和 subpoint
        mock_geocentric = MagicMock()
        mock_sat.at.return_value = mock_geocentric
        mock_wgs84.subpoint.return_value = MagicMock()
        
        # 執行測試
        result = satellite_analysis.process_time_point_worker(
            time_data,
            tle_list,
            mock_observer_location['latitude'],
            mock_observer_location['longitude'], 
            mock_observer_location['elevation'],
            None,
            min_elevation_threshold=25
        )
        
        # 驗證結果
        assert 'visible_satellites' in result
        assert 'visible_count' in result
        assert result['visible_count'] == 1
        assert len(result['visible_satellites']) == 1
        assert result['visible_satellites'][0]['name'] == "STARLINK-TEST"
        assert result['visible_satellites'][0]['elevation'] == 45.0

    @pytest.mark.unit
    @patch('satellite_analysis.wgs84')
    @patch('satellite_analysis.load')
    @patch('satellite_analysis.EarthSatellite')
    def test_process_time_point_worker_no_visible_satellites(self, mock_earth_satellite, mock_load, mock_wgs84, mock_observer_location):
        """測試當沒有可見衛星時的處理"""
        # 導入模組
        import satellite_analysis
        
        mock_ts = MagicMock()
        mock_load.timescale.return_value = mock_ts
        
        mock_time = MagicMock()
        time_datetime = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        time_data = (mock_time, time_datetime)
        
        tle_list = [
            ("STARLINK-TEST", "1 44713U 19074A   24001.50000000", "2 44713  53.0540 123.4567")
        ]
        
        mock_sat = MagicMock()
        mock_sat.name = "STARLINK-TEST"
        mock_earth_satellite.return_value = mock_sat
        
        mock_observer = MagicMock()
        mock_wgs84.latlon.return_value = mock_observer
        
        # Mock 低仰角（不可見）
        mock_topocentric = MagicMock()
        mock_alt = MagicMock()
        mock_alt.degrees = 10.0  # 低於最小仰角
        mock_az = MagicMock()
        mock_az.degrees = 180.0
        mock_distance = MagicMock()
        mock_distance.km = 550.0
        mock_topocentric.altaz.return_value = (mock_alt, mock_az, mock_distance)
        
        mock_difference = MagicMock()
        mock_difference.at.return_value = mock_topocentric
        mock_sat.__sub__.return_value = mock_difference
        
        mock_geocentric = MagicMock()
        mock_sat.at.return_value = mock_geocentric
        mock_wgs84.subpoint.return_value = MagicMock()
        
        # 執行測試
        result = satellite_analysis.process_time_point_worker(
            time_data,
            tle_list,
            mock_observer_location['latitude'],
            mock_observer_location['longitude'],
            mock_observer_location['elevation'],
            None,
            min_elevation_threshold=25
        )
        
        # 驗證結果
        assert result['visible_count'] == 0
        assert len(result['visible_satellites']) == 0


class TestStarlinkAnalysisClass:
    """測試 StarlinkAnalysis 類別"""
    
    @pytest.mark.unit
    def test_init(self, temp_output_dir):
        """測試初始化"""
        with patch('satellite_analysis.load') as mock_load:
            with patch('satellite_analysis.wgs84') as mock_wgs84:
                with patch('satellite_analysis.Loader'):
                    import satellite_analysis
                    
                    # 創建實例
                    analyzer = satellite_analysis.StarlinkAnalysis(output_dir=temp_output_dir)
                    
                    # 驗證
                    assert analyzer.output_dir.exists()
                    assert analyzer.satellites == []
                    assert analyzer.raw_tle_data == []
                    mock_load.timescale.assert_called_once()
    
    @pytest.mark.unit
    def test_calculate_stats_basic(self, sample_coverage_df):
        """測試基本統計計算"""
        with patch('satellite_analysis.load'):
            with patch('satellite_analysis.wgs84'):
                with patch('satellite_analysis.Loader'):
                    import satellite_analysis
                    
                    analyzer = satellite_analysis.StarlinkAnalysis()
                    stats = analyzer.calculate_stats(sample_coverage_df)
                    
                    assert 'avg_visible_satellites' in stats
                    assert 'max_visible_satellites' in stats
                    assert 'min_visible_satellites' in stats
                    assert 'coverage_percentage' in stats
                    assert stats['avg_visible_satellites'] == pytest.approx(25.0, 0.1)
                    assert stats['max_visible_satellites'] == 30
                    assert stats['min_visible_satellites'] == 20
    
    @pytest.mark.unit
    def test_calculate_stats_empty_dataframe(self):
        """測試空 DataFrame 的統計計算"""
        with patch('satellite_analysis.load'):
            with patch('satellite_analysis.wgs84'):
                with patch('satellite_analysis.Loader'):
                    import satellite_analysis
                    import pandas as pd
                    
                    analyzer = satellite_analysis.StarlinkAnalysis()
                    empty_df = pd.DataFrame()
                    stats = analyzer.calculate_stats(empty_df)
                    
                    assert stats['avg_visible_satellites'] == 0
                    assert stats['max_visible_satellites'] == 0
                    assert stats['min_visible_satellites'] == 0
                    assert stats['coverage_percentage'] == 0


class TestModuleLevelFunctions:
    """測試模組層級的函數"""
    
    @pytest.mark.unit
    @patch('requests.get')
    def test_download_tle_data_success(self, mock_get, temp_output_dir):
        """測試成功下載 TLE 數據"""
        with patch('satellite_analysis.load'):
            with patch('satellite_analysis.wgs84'):
                with patch('satellite_analysis.EarthSatellite'):
                    import satellite_analysis
                    
                    # Mock 回應
                    mock_response = Mock()
                    mock_response.status_code = 200
                    mock_response.text = """STARLINK-1
1 44713U 19074A   24001.50000000  .00000000  00000-0  00000-0 0  0000
2 44713  53.0540 123.4567 0001234 123.4567 234.5678 15.40000000000000
STARLINK-2
1 44714U 19074B   24001.50000000  .00000000  00000-0  00000-0 0  0000
2 44714  53.0540 123.4567 0001234 123.4567 234.5678 15.40000000000000"""
                    mock_get.return_value = mock_response
                    
                    analyzer = satellite_analysis.StarlinkAnalysis(output_dir=temp_output_dir)
                    analyzer.download_tle_data()
                    
                    # 驗證
                    assert len(analyzer.satellites) == 2
                    assert len(analyzer.raw_tle_data) == 2
                    assert (temp_output_dir / 'starlink_latest.tle').exists()
    
    @pytest.mark.unit
    @patch('requests.get')
    def test_download_tle_data_failure(self, mock_get, temp_output_dir):
        """測試下載 TLE 數據失敗"""
        with patch('satellite_analysis.load'):
            with patch('satellite_analysis.wgs84'):
                import satellite_analysis
                
                # Mock 失敗回應
                mock_get.side_effect = Exception("Network error")
                
                analyzer = satellite_analysis.StarlinkAnalysis(output_dir=temp_output_dir)
                analyzer.download_tle_data()
                
                # 驗證
                assert len(analyzer.satellites) == 0
                assert len(analyzer.raw_tle_data) == 0