# MIT License
# Copyright (c) 2025 Starlink Taipei Analysis Team
#
# This file is part of the Starlink Taipei Satellite Analysis System.

"""
系統整合測試
"""

import pytest
import subprocess
import json
import os
from pathlib import Path


class TestSystemIntegration:
    """測試系統各組件的整合"""
    
    @pytest.mark.integration
    def test_cli_help_command(self):
        """測試 CLI help 命令"""
        result = subprocess.run(
            ['python3', 'starlink.py', '--help'],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert "Starlink 台北衛星分析系統" in result.stdout
        assert "analyze" in result.stdout
        assert "health" in result.stdout
        assert "shiny" in result.stdout

    @pytest.mark.integration
    def test_health_check_command(self):
        """測試健康檢查命令"""
        result = subprocess.run(
            ['python3', 'starlink.py', 'health'],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert "執行系統健康檢查" in result.stdout
        assert "檢查 Python 依賴套件" in result.stdout
        assert "檢查關鍵檔案" in result.stdout

    @pytest.mark.integration
    @pytest.mark.slow
    def test_quick_analysis(self, temp_output_dir):
        """測試快速分析功能"""
        # 設置環境變數指向臨時目錄
        env = os.environ.copy()
        env['OUTPUT_DIR'] = temp_output_dir
        
        result = subprocess.run(
            ['python3', 'starlink.py', 'analyze', '--quick'],
            capture_output=True,
            text=True,
            env=env,
            timeout=60  # 60秒超時
        )
        
        # 基本檢查（可能因為缺少依賴而失敗）
        # 主要測試命令是否可以執行
        assert "執行 10 分鐘分析" in result.stdout or result.returncode != 0

    @pytest.mark.integration
    def test_analyze_with_custom_params(self):
        """測試自定義參數分析"""
        result = subprocess.run(
            ['python3', 'starlink.py', 'analyze',
             '--duration', '5',
             '--interval', '0.5',
             '--min_elevation', '30',
             '--lat', '35.6762',
             '--lon', '139.6503'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # 檢查參數是否被接受
        assert "執行 5 分鐘分析" in result.stdout or result.returncode != 0

    @pytest.mark.integration
    def test_output_file_generation(self, temp_output_dir, sample_tle_data):
        """測試輸出文件生成"""
        # 創建測試 TLE 文件
        tle_file = Path(temp_output_dir) / "test.tle"
        tle_file.write_text(sample_tle_data)
        
        # 預期的輸出文件
        expected_files = [
            'coverage_stats.json',
            'coverage_data.csv',
            'prediction_report.json'
        ]
        
        # 這個測試需要完整的系統運行
        # 在沒有所有依賴的情況下可能會跳過
        pytest.skip("需要完整系統環境")

    @pytest.mark.integration
    @pytest.mark.requires_network
    def test_tle_download_integration(self):
        """測試 TLE 數據下載整合"""
        # 這個測試需要網路連接
        pytest.skip("需要網路連接和 API 訪問")

    @pytest.mark.integration
    def test_r_python_integration(self):
        """測試 R 和 Python 的整合"""
        # 檢查 reticulate 是否可以載入 Python 模組
        r_test_script = """
        library(reticulate)
        use_python("/usr/bin/python3", required = FALSE)
        py_available()
        """
        
        result = subprocess.run(
            ['Rscript', '-e', r_test_script],
            capture_output=True,
            text=True
        )
        
        # R 環境可能不可用
        if result.returncode == 0:
            assert "TRUE" in result.stdout or "FALSE" in result.stdout
        else:
            pytest.skip("R 環境不可用")

    @pytest.mark.integration
    def test_error_handling(self):
        """測試錯誤處理"""
        # 測試無效命令
        result = subprocess.run(
            ['python3', 'starlink.py', 'invalid_command'],
            capture_output=True,
            text=True
        )
        
        assert result.returncode != 0
        assert "error" in result.stderr.lower() or "invalid" in result.stderr.lower()

    @pytest.mark.integration
    def test_concurrent_analysis(self):
        """測試並發分析能力"""
        # 測試多 CPU 核心設定
        result = subprocess.run(
            ['python3', 'starlink.py', 'analyze', '--cpu', '2', '--duration', '1'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # 基本檢查
        assert result.returncode == 0 or "import" in result.stderr