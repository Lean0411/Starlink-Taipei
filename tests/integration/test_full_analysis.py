# MIT License
# Copyright (c) 2025 Starlink Taipei Analysis Team
#
# This file is part of the Starlink Taipei Satellite Analysis System.

"""
完整分析流程的整合測試
"""

import sys
import os
import pytest
import pandas as pd
from pathlib import Path

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from satellite_analysis import StarlinkAnalysis

class TestFullAnalysisWorkflow:
    """測試完整的分析工作流程"""
    
    @pytest.fixture
    def analyzer(self, tmp_path):
        """創建測試用的分析器實例"""
        return StarlinkAnalysis(output_dir=str(tmp_path))
    
    def test_static_analyze_method(self, tmp_path):
        """測試靜態分析方法"""
        # 使用較短的分析時間進行測試
        result = StarlinkAnalysis.analyze(
            lat=25.0330,
            lon=121.5654,
            interval_minutes=5,
            analysis_duration_minutes=10,  # 只分析10分鐘
            min_elevation_threshold=25,
            output_dir=str(tmp_path),
            num_cpus=1  # 使用單核以避免並行處理問題
        )
        
        # 驗證返回結果結構
        assert isinstance(result, dict)
        assert 'stats_path' in result
        assert 'report_path' in result
        assert 'data_path' in result
        assert 'plots_paths' in result
        
        # 如果成功下載了 TLE 數據，應該有結果文件
        if result['stats_path'] is not None:
            assert Path(result['stats_path']).exists()
            assert Path(result['data_path']).exists()
            assert Path(result['report_path']).exists()
    
    @pytest.mark.slow
    def test_download_and_analyze(self, analyzer):
        """測試下載 TLE 數據和分析（標記為慢速測試）"""
        # 嘗試下載 TLE 數據
        analyzer.download_tle_data()
        
        # 如果成功下載，應該有衛星數據
        if analyzer.satellites:
            assert len(analyzer.satellites) > 0
            
            # 執行短時間分析
            coverage_df = analyzer.analyze_coverage(
                interval_minutes=5,
                analysis_duration_minutes=10,
                num_cpus=1,
                min_elevation_threshold=25
            )
            
            # 驗證結果
            if not coverage_df.empty:
                assert 'timestamp' in coverage_df.columns
                assert 'visible_count' in coverage_df.columns
                
                # 計算統計
                stats = analyzer.calculate_stats(coverage_df)
                assert isinstance(stats, dict)
                assert 'avg_visible_satellites' in stats
                assert 'coverage_percentage' in stats
    
    def test_error_handling(self, analyzer):
        """測試錯誤處理"""
        # 測試空衛星列表的分析
        coverage_df = analyzer.analyze_coverage(
            interval_minutes=1,
            analysis_duration_minutes=5,
            num_cpus=1
        )
        
        assert coverage_df.empty
        
        # 測試空 DataFrame 的統計計算
        stats = analyzer.calculate_stats(pd.DataFrame())
        assert stats['avg_visible_satellites'] == 0
        assert stats['coverage_percentage'] == 0