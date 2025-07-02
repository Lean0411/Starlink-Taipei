#!/usr/bin/env python3
"""
整合測試腳本 - 測試 API 功能
"""

import pytest
import time
import subprocess
import requests
import json
from datetime import datetime


def wait_for_api(url, max_retries=10):
    """等待 API 啟動"""
    for i in range(max_retries):
        try:
            response = requests.get(f"{url}/health")
            if response.status_code == 200:
                print("✓ API 已啟動")
                return True
        except Exception:
            pass
        time.sleep(1)
    return False


@pytest.mark.integration
@pytest.mark.skip(reason="需要手動啟動 API 服務")
def test_health_endpoint():
    """測試健康檢查端點"""
    base_url = "http://localhost:8001"
    print("\n測試健康檢查端點...")
    response = requests.get(f"{base_url}/health")
    print(f"狀態碼: {response.status_code}")
    print(f"響應: {response.json()}")
    assert response.status_code == 200
    print("✓ 健康檢查通過")


@pytest.mark.integration
@pytest.mark.skip(reason="需要手動啟動 API 服務")
def test_prediction_endpoint():
    """測試預測端點"""
    base_url = "http://localhost:8001"
    print("\n測試預測端點...")

    # 測試短期預測
    print("\n1. 短期預測（1小時）")
    payload = {
        "observer_latitude": 25.0330,
        "observer_longitude": 121.5654,
        "observer_altitude": 10.0,
        "time_scale": "short_term",
        "min_elevation": 25.0,
    }

    response = requests.post(f"{base_url}/api/v1/predict", json=payload)
    print(f"狀態碼: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"預測ID: {data['data']['prediction_id']}")
        print(f"時間尺度: {data['data']['time_scale']}")
        print(f"分析衛星數: {data['data']['analyzed_satellites']}")
        print(f"預測點數量: {data['data']['prediction_points_count']}")
        if data["data"]["optimal_windows"]:
            print(f"最佳觀測窗口: {len(data['data']['optimal_windows'])} 個")
        print("✓ 短期預測成功")
    else:
        print(f"✗ 錯誤: {response.text}")

    # 測試中期預測
    print("\n2. 中期預測（24小時）")
    payload["time_scale"] = "medium_term"

    response = requests.post(f"{base_url}/api/v1/predict", json=payload)
    if response.status_code == 200:
        data = response.json()
        print(f"預測點數量: {data['data']['prediction_points_count']}")
        if data["data"]["statistics"]:
            stats = data["data"]["statistics"]
            print(f"平均衛星數: {stats['satellites'].get('mean', 'N/A')}")
            print(f"峰值時段: {stats.get('peak_hours', [])}")
        print("✓ 中期預測成功")
    else:
        print(f"✗ 錯誤: {response.text}")


@pytest.mark.integration
@pytest.mark.skip(reason="需要手動啟動 API 服務")
def test_coverage_endpoint():
    """測試覆蓋分析端點"""
    base_url = "http://localhost:8001"
    print("\n測試覆蓋分析端點...")

    payload = {
        "observer_latitude": 25.0330,
        "observer_longitude": 121.5654,
        "observer_elevation": 10.0,
        "duration_minutes": 60,
        "interval_minutes": 5,
        "min_elevation": 25.0,
    }

    response = requests.post(f"{base_url}/api/v1/coverage/analyze", json=payload)
    print(f"狀態碼: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"覆蓋ID: {data['data']['coverage_id']}")
        print("✓ 覆蓋分析成功")
    else:
        print(f"✗ 錯誤: {response.text}")


# 注釋掉 main 函數，因為我們現在使用 pytest
# 如果需要啟動 API 服務，應該在 pytest fixture 中處理
# 或者手動啟動 API 服務後再執行測試
