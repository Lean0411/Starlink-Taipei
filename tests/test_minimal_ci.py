# MIT License
# Copyright (c) 2025 Starlink Taipei Analysis Team
#
# This file is part of the Starlink Taipei Satellite Analysis System.

"""
最小化測試 - 不需要任何依賴的基本測試
"""

import os
import sys


def test_basic_math():
    """測試基本數學運算"""
    assert 2 + 2 == 4
    assert 10 * 5 == 50
    assert 100 / 4 == 25


def test_python_version():
    """測試 Python 版本"""
    assert sys.version_info >= (3, 9)
    assert sys.version_info.major == 3


def test_project_files_exist():
    """測試專案檔案存在"""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # 檢查重要檔案存在
    assert os.path.exists(os.path.join(project_root, "README.md"))
    assert os.path.exists(os.path.join(project_root, ".github", "workflows", "test.yml"))
    
    # 檢查新的 Clean Architecture 目錄結構
    assert os.path.exists(os.path.join(project_root, "src"))
    assert os.path.exists(os.path.join(project_root, "src", "domain"))
    assert os.path.exists(os.path.join(project_root, "src", "application"))
    assert os.path.exists(os.path.join(project_root, "src", "infrastructure"))
    assert os.path.exists(os.path.join(project_root, "src", "interfaces"))
    
    # 檢查舊檔案在 legacy 目錄中
    assert os.path.exists(os.path.join(project_root, "legacy", "python", "satellite_analysis.py"))
    assert os.path.exists(os.path.join(project_root, "legacy", "python", "starlink.py"))
    assert os.path.exists(os.path.join(project_root, "legacy", "python", "simple_analysis.py"))


def test_environment():
    """測試環境變數"""
    # 測試基本環境
    assert "PATH" in os.environ
    assert os.path.exists(sys.executable)

    # 測試 Python 可執行
    import subprocess

    result = subprocess.run([sys.executable, "--version"], capture_output=True)
    assert result.returncode == 0
