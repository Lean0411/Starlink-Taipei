# MIT License
# Copyright (c) 2025 Starlink Taipei Analysis Team
#
# This file is part of the Starlink Taipei Satellite Analysis System.

"""
基本測試 - 驗證測試框架正常運作
"""


def test_import_main_module():
    """測試主模組可以被導入"""
    import satellite_analysis

    assert satellite_analysis is not None
    assert hasattr(satellite_analysis, "analyze_satellite_coverage")
    assert hasattr(satellite_analysis, "process_time_point_worker")


def test_constants():
    """測試常數定義"""
    from satellite_analysis import ELEVATION, TAIPEI_LAT, TAIPEI_LON

    assert TAIPEI_LAT == 25.0330
    assert TAIPEI_LON == 121.5654
    assert ELEVATION == 10.0


def test_basic_math():
    """基本數學測試以確認 pytest 正常運作"""
    assert 2 + 2 == 4
    assert 10 * 10 == 100
    assert 100 / 4 == 25
