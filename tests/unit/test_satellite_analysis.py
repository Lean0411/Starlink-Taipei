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
from unittest.mock import patch, MagicMock

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from satellite_analysis import (
    analyze_satellite_coverage,
    process_time_point_worker,
    calculate_statistics,
    load_starlink_tle_data,
    TAIPEI_LAT,
    TAIPEI_LON,
    ELEVATION
)


class TestConstants:
    """測試常數定義"""
    
    def test_default_location(self):
        """測試預設位置常數"""
        assert TAIPEI_LAT == 25.0330
        assert TAIPEI_LON == 121.5654
        assert ELEVATION == 10.0


class TestProcessTimePointWorker:
    """測試時間點處理函數"""
    
    def test_process_time_point_with_empty_tle(self):
        """測試空的 TLE 數據"""
        from datetime import datetime
        now = datetime.now(timezone.utc)
        
        result = process_time_point_worker(
            (0, now),
            [],  # 空的 TLE 列表
            TAIPEI_LAT,
            TAIPEI_LON,
            ELEVATION,
            {'builtin': True},
            25
        )
        
        assert result[0] == 0  # index
        assert result[1] == 0  # visible count
        assert result[2] == []  # visible satellites
    
    def test_process_time_point_with_invalid_tle(self):
        """測試無效的 TLE 數據"""
        from datetime import datetime
        now = datetime.now(timezone.utc)
        
        # 無效的 TLE 數據
        invalid_tle = [
            ("invalid_line1", "invalid_line2")
        ]
        
        result = process_time_point_worker(
            (0, now),
            invalid_tle,
            TAIPEI_LAT,
            TAIPEI_LON,
            ELEVATION,
            {'builtin': True},
            25
        )
        
        assert result[0] == 0
        assert result[1] == 0  # 應該沒有可見衛星
        assert result[2] == []


class TestCalculateStatistics:
    """測試統計計算函數"""
    
    def test_calculate_statistics_with_data(self):
        """測試有數據的統計計算"""
        analysis_data = {
            'visible_counts': [10, 15, 20, 25, 30],
            'visible_satellites': [
                [{'elevation': 30}],
                [{'elevation': 40}],
                [{'elevation': 50}],
                [{'elevation': 60}],
                [{'elevation': 70}]
            ]
        }
        
        stats = calculate_statistics(analysis_data, TAIPEI_LAT, TAIPEI_LON, 25)
        
        assert stats['avg_visible_satellites'] == 20.0
        assert stats['max_visible_satellites'] == 30
        assert stats['min_visible_satellites'] == 10
        assert stats['coverage_percentage'] == 100.0
        assert stats['avg_elevation'] == 50.0
        assert stats['max_elevation'] == 70.0
    
    def test_calculate_statistics_with_empty_data(self):
        """測試空數據的統計計算"""
        analysis_data = {
            'visible_counts': [],
            'visible_satellites': []
        }
        
        # 應該能處理空數據而不崩潰
        stats = calculate_statistics(analysis_data, TAIPEI_LAT, TAIPEI_LON, 25)
        assert isinstance(stats, dict)


class TestLoadStarlinkTLEData:
    """測試 TLE 數據載入"""
    
    @patch('requests.get')
    def test_load_tle_from_network(self, mock_get):
        """測試從網路載入 TLE 數據"""
        # 模擬網路回應
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """STARLINK-1007
1 44713U 19074A   25180.50000000  .00000100  00000-0  10000-3 0  9990
2 44713  53.0530 100.0000 0001000  90.0000 270.0000 15.05500000100000
STARLINK-1008
1 44714U 19074B   25180.50000000  .00000100  00000-0  10000-3 0  9990
2 44714  53.0530 100.1000 0001000  90.0000 270.0000 15.05500000100000"""
        mock_get.return_value = mock_response
        
        satellites = load_starlink_tle_data()
        
        assert len(satellites) == 2
        assert satellites[0]['name'] == 'STARLINK-1007'
        assert satellites[1]['name'] == 'STARLINK-1008'
    
    def test_load_tle_from_file(self, tmp_path):
        """測試從文件載入 TLE 數據"""
        # 創建測試 TLE 文件
        tle_file = tmp_path / "test.tle"
        tle_content = """STARLINK-TEST
1 99999U 99999A   25180.50000000  .00000100  00000-0  10000-3 0  9990
2 99999  53.0530 100.0000 0001000  90.0000 270.0000 15.05500000100000"""
        tle_file.write_text(tle_content)
        
        satellites = load_starlink_tle_data(str(tle_file))
        
        assert len(satellites) == 1
        assert satellites[0]['name'] == 'STARLINK-TEST'


class TestAnalyzeSatelliteCoverage:
    """測試主要的衛星覆蓋分析函數"""
    
    @patch('satellite_analysis.load_starlink_tle_data')
    @patch('concurrent.futures.ProcessPoolExecutor')
    def test_analyze_basic(self, mock_executor, mock_load_tle, tmp_path):
        """測試基本分析流程"""
        # 模擬 TLE 數據
        mock_load_tle.return_value = [
            {
                'name': 'STARLINK-TEST',
                'tle_line1': '1 99999U 99999A   25180.50000000  .00000100  00000-0  10000-3 0  9990',
                'tle_line2': '2 99999  53.0530 100.0000 0001000  90.0000 270.0000 15.05500000100000'
            }
        ]
        
        # 模擬並行處理結果
        mock_future = MagicMock()
        mock_future.result.return_value = (0, 5, [])
        mock_executor.return_value.__enter__.return_value.submit.return_value = mock_future
        
        # 執行分析
        result = analyze_satellite_coverage(
            duration_minutes=10,
            time_interval_minutes=5,
            output_dir=str(tmp_path),
            include_prediction=False
        )
        
        assert 'stats' in result
        assert 'data' in result
        assert 'metadata' in result
        assert result['metadata']['duration_minutes'] == 10