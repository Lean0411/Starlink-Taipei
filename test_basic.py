#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# MIT License
# Copyright (c) 2025 Starlink Taipei Analysis Team

"""
基本測試檔案，用於驗證測試框架設置
"""

def test_import():
    """測試能否導入基本模組"""
    import sys
    import os
    assert sys.version_info >= (3, 8)
    assert os.path.exists('setup.py')
    assert os.path.exists('requirements.txt')

def test_project_structure():
    """測試專案結構"""
    import os
    expected_dirs = ['app', 'docs', 'tests', 'R']
    for dir_name in expected_dirs:
        assert os.path.isdir(dir_name), f"Missing directory: {dir_name}"

def test_license():
    """測試授權檔案存在"""
    import os
    assert os.path.exists('LICENSE')
    with open('LICENSE', 'r') as f:
        content = f.read()
        assert 'MIT License' in content
        assert 'Starlink Taipei Analysis Team' in content

if __name__ == "__main__":
    test_import()
    test_project_structure()
    test_license()
    print("All basic tests passed!")