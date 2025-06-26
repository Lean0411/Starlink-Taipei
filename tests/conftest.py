# MIT License
# Copyright (c) 2025 Starlink Taipei Analysis Team
#
# This file is part of the Starlink Taipei Satellite Analysis System.

"""
pytest 共用設定和 fixtures
"""

import pytest
import os
import sys
import tempfile
from pathlib import Path
from datetime import datetime, timezone

# 將專案根目錄加入 Python 路徑
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def temp_output_dir():
    """創建臨時輸出目錄"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_tle_data():
    """提供範例 TLE 數據"""
    return """STARLINK-1007
1 44713U 19074A   24001.50000000  .00001234  00000-0  12345-4 0  9991
2 44713  53.0540 123.4567  0001234  90.1234 270.1234 15.12345678 12345
STARLINK-1008  
1 44714U 19074B   24001.50000000  .00001234  00000-0  12345-4 0  9992
2 44714  53.0540 123.4567  0001234  90.1234 270.1234 15.12345678 12346
STARLINK-1009
1 44715U 19074C   24001.50000000  .00001234  00000-0  12345-4 0  9993
2 44715  53.0540 123.4567  0001234  90.1234 270.1234 15.12345678 12347"""


@pytest.fixture
def mock_observer_location():
    """提供測試用觀測者位置（台北）"""
    return {
        'latitude': 25.0330,
        'longitude': 121.5654,
        'elevation': 10.0
    }


@pytest.fixture
def analysis_params():
    """提供預設分析參數"""
    return {
        'duration': 10,  # 分鐘
        'interval': 1.0,  # 分鐘
        'min_elevation': 25.0,  # 度
        'cpu_count': 2
    }


@pytest.fixture(autouse=True)
def reset_environment():
    """每個測試前重置環境"""
    # 清理可能的環境變數
    env_vars_to_clean = ['TLE_CACHE_DIR', 'OUTPUT_DIR']
    original_env = {}
    
    for var in env_vars_to_clean:
        original_env[var] = os.environ.get(var)
        if var in os.environ:
            del os.environ[var]
    
    yield
    
    # 恢復環境變數
    for var, value in original_env.items():
        if value is not None:
            os.environ[var] = value


@pytest.fixture
def mock_datetime(monkeypatch):
    """Mock datetime 以提供固定時間"""
    class MockDatetime:
        @staticmethod
        def now(tz=None):
            return datetime(2024, 1, 1, 12, 0, 0, tzinfo=tz or timezone.utc)
        
        @staticmethod
        def utcnow():
            return datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    
    monkeypatch.setattr('datetime.datetime', MockDatetime)
    yield MockDatetime


@pytest.fixture
def sample_coverage_df():
    """提供範例覆蓋率 DataFrame"""
    import pandas as pd
    data = {
        'timestamp': pd.date_range('2024-01-01 12:00:00', periods=10, freq='1min'),
        'visible_count': [25, 30, 20, 25, 30, 20, 25, 30, 20, 25],
        'elevation': [45.0, 50.0, 40.0, 45.0, 50.0, 40.0, 45.0, 50.0, 40.0, 45.0],
        'azimuth': [180.0, 190.0, 170.0, 180.0, 190.0, 170.0, 180.0, 190.0, 170.0, 180.0],
        'distance_km': [550.0, 500.0, 600.0, 550.0, 500.0, 600.0, 550.0, 500.0, 600.0, 550.0]
    }
    return pd.DataFrame(data)