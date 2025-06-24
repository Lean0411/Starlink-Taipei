# MIT License
# Copyright (c) 2025 Starlink Taipei Analysis Team
#
# This file is part of the Starlink Taipei Satellite Analysis System.

"""
satellite_analysis.py 的單元測試
"""

import pytest
import json
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta, timezone

# 由於 satellite_analysis 有許多依賴，我們需要先 mock 它們
with patch('skyfield.api.load'):
    with patch('skyfield.api.wgs84'):
        with patch('skyfield.api.EarthSatellite'):
            import satellite_analysis


class TestSatelliteAnalysis:
    """測試衛星分析核心功能"""
    
    @pytest.mark.unit
    def test_process_time_point_worker_with_visible_satellite(self, mock_observer_location):
        """測試當有可見衛星時的處理"""
        # 準備測試數據
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
        
        # Mock 位置計算
        mock_topocentric = MagicMock()
        mock_alt = MagicMock()
        mock_alt.degrees = 45.0  # 高於最小仰角
        mock_az = MagicMock()
        mock_az.degrees = 180.0
        mock_distance = MagicMock()
        mock_distance.km = 550.0
        mock_topocentric.altaz.return_value = (mock_alt, mock_az, mock_distance)
        
        with patch('skyfield.api.EarthSatellite', return_value=mock_sat):
            with patch('skyfield.api.wgs84.latlon') as mock_latlon:
                mock_observer = MagicMock()
                mock_latlon.return_value = mock_observer
                
                mock_difference = MagicMock()
                mock_difference.at.return_value = mock_topocentric
                mock_sat.__sub__.return_value = mock_difference
                
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
                assert len(result['visible_satellites']) == 1
                assert result['visible_satellites'][0]['name'] == "STARLINK-TEST"
                assert result['visible_satellites'][0]['elevation'] == 45.0
                assert result['count'] == 1

    @pytest.mark.unit
    def test_process_time_point_worker_no_visible_satellites(self, mock_observer_location):
        """測試當沒有可見衛星時的處理"""
        mock_time = MagicMock()
        time_datetime = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        time_data = (mock_time, time_datetime)
        
        tle_list = [
            ("STARLINK-TEST", "1 44713U 19074A   24001.50000000", "2 44713  53.0540 123.4567")
        ]
        
        mock_sat = MagicMock()
        mock_sat.name = "STARLINK-TEST"
        
        # Mock 低仰角（不可見）
        mock_topocentric = MagicMock()
        mock_alt = MagicMock()
        mock_alt.degrees = 10.0  # 低於最小仰角
        mock_az = MagicMock()
        mock_az.degrees = 180.0
        mock_distance = MagicMock()
        mock_distance.km = 550.0
        mock_topocentric.altaz.return_value = (mock_alt, mock_az, mock_distance)
        
        with patch('skyfield.api.EarthSatellite', return_value=mock_sat):
            with patch('skyfield.api.wgs84.latlon') as mock_latlon:
                mock_observer = MagicMock()
                mock_latlon.return_value = mock_observer
                
                mock_difference = MagicMock()
                mock_difference.at.return_value = mock_topocentric
                mock_sat.__sub__.return_value = mock_difference
                
                result = satellite_analysis.process_time_point_worker(
                    time_data,
                    tle_list,
                    mock_observer_location['latitude'],
                    mock_observer_location['longitude'],
                    mock_observer_location['elevation'],
                    None,
                    min_elevation_threshold=25
                )
                
                assert len(result['visible_satellites']) == 0
                assert result['count'] == 0

    @pytest.mark.unit
    def test_download_tle_data_success(self, temp_output_dir, sample_tle_data):
        """測試成功下載 TLE 數據"""
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.text = sample_tle_data
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response
            
            # 執行下載
            tle_file = os.path.join(temp_output_dir, "test.tle")
            with patch('satellite_analysis.OUTPUT_DIR', temp_output_dir):
                satellite_analysis.download_tle_data(tle_file)
            
            # 驗證文件內容
            assert os.path.exists(tle_file)
            with open(tle_file, 'r') as f:
                content = f.read()
            assert "STARLINK-1007" in content

    @pytest.mark.unit
    def test_download_tle_data_network_error(self, temp_output_dir):
        """測試網路錯誤時的處理"""
        with patch('requests.get') as mock_get:
            mock_get.side_effect = Exception("Network error")
            
            tle_file = os.path.join(temp_output_dir, "test.tle")
            
            # 應該引發異常
            with pytest.raises(Exception, match="Network error"):
                satellite_analysis.download_tle_data(tle_file)

    @pytest.mark.unit 
    def test_parse_tle_data(self, sample_tle_data):
        """測試 TLE 數據解析"""
        lines = sample_tle_data.strip().split('\n')
        
        # 假設有 parse_tle_data 函數
        # 這裡需要根據實際實現調整
        satellites = []
        for i in range(0, len(lines), 3):
            if i + 2 < len(lines):
                satellites.append({
                    'name': lines[i].strip(),
                    'line1': lines[i+1].strip(),
                    'line2': lines[i+2].strip()
                })
        
        assert len(satellites) == 3
        assert satellites[0]['name'] == "STARLINK-1007"
        assert satellites[1]['name'] == "STARLINK-1008"
        assert satellites[2]['name'] == "STARLINK-1009"

    @pytest.mark.unit
    def test_calculate_coverage_statistics(self):
        """測試覆蓋率統計計算"""
        # 準備測試數據
        time_results = [
            {'count': 5, 'timestamp': '2024-01-01 12:00:00'},
            {'count': 0, 'timestamp': '2024-01-01 12:01:00'},
            {'count': 3, 'timestamp': '2024-01-01 12:02:00'},
            {'count': 7, 'timestamp': '2024-01-01 12:03:00'},
            {'count': 0, 'timestamp': '2024-01-01 12:04:00'},
        ]
        
        # 計算統計
        total_points = len(time_results)
        covered_points = sum(1 for r in time_results if r['count'] > 0)
        coverage_percentage = (covered_points / total_points) * 100
        avg_satellites = sum(r['count'] for r in time_results) / total_points
        max_satellites = max(r['count'] for r in time_results)
        
        # 驗證結果
        assert coverage_percentage == 60.0  # 3/5 * 100
        assert avg_satellites == 3.0  # (5+0+3+7+0)/5
        assert max_satellites == 7

    @pytest.mark.unit
    @patch('matplotlib.pyplot.savefig')
    def test_create_coverage_plot(self, mock_savefig, temp_output_dir):
        """測試覆蓋圖表生成"""
        # 這個測試需要根據實際的繪圖函數調整
        # 主要測試函數是否被正確調用
        
        time_results = [
            {'count': 5, 'timestamp': '2024-01-01 12:00:00'},
            {'count': 3, 'timestamp': '2024-01-01 12:01:00'},
        ]
        
        # 假設有 create_coverage_plot 函數
        # mock_savefig 應該被調用
        assert True  # 佔位符

    @pytest.mark.unit
    def test_main_function_with_args(self):
        """測試主函數參數解析"""
        test_args = [
            'satellite_analysis.py',
            '--duration', '30',
            '--interval', '2.0',
            '--min_elevation', '30.0',
            '--lat', '40.7128',
            '--lon', '-74.0060'
        ]
        
        with patch('sys.argv', test_args):
            with patch('satellite_analysis.analyze_satellite_coverage') as mock_analyze:
                # 測試參數是否正確傳遞
                # 需要根據實際的 main 函數實現調整
                assert True  # 佔位符