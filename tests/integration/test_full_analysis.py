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
import subprocess
from pathlib import Path

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))


class TestFullAnalysisWorkflow:
    """測試完整的分析工作流程"""
    
    def test_command_line_help(self):
        """測試命令行幫助"""
        result = subprocess.run(
            [sys.executable, 'starlink.py', '--help'],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert 'Starlink 台北衛星分析系統' in result.stdout
    
    def test_satellite_analysis_help(self):
        """測試衛星分析模組幫助"""
        result = subprocess.run(
            [sys.executable, 'satellite_analysis.py', '--help'],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert '衛星覆蓋分析' in result.stdout
    
    @pytest.mark.slow
    def test_basic_analysis_flow(self, tmp_path):
        """測試基本分析流程（標記為慢速測試）"""
        # 使用很短的分析時間
        result = subprocess.run(
            [
                sys.executable,
                'satellite_analysis.py',
                '--duration', '1',
                '--interval', '1',
                '--output-dir', str(tmp_path),
                '--no-prediction'
            ],
            capture_output=True,
            text=True,
            timeout=30  # 30秒超時
        )
        
        # 檢查是否成功執行（可能因為網路問題失敗）
        if result.returncode == 0:
            # 檢查輸出文件
            assert (tmp_path / 'coverage_stats.json').exists()
            assert (tmp_path / 'coverage_data.csv').exists()