#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試錯誤處理和日誌系統
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.utils import (
    get_logger, log_info, log_error, log_warning,
    handle_errors, validate_input, ErrorContext,
    DataValidationError, SatelliteCalculationError
)

# 獲取日誌器
logger = get_logger('test')


@handle_errors(retry_count=2, retry_delay=1.0)
def test_retry_function(should_fail=True):
    """測試重試機制"""
    log_info("執行可能失敗的函數")
    
    if should_fail:
        raise SatelliteCalculationError(
            "模擬的計算錯誤",
            details={'test': True}
        )
    
    return "成功!"


@validate_input(value=(0, 100), name=str)
def test_validation(value, name):
    """測試輸入驗證"""
    log_info(f"處理數據: value={value}, name={name}")
    return f"Hello {name}, your value is {value}"


def test_error_context():
    """測試錯誤上下文"""
    with ErrorContext("test_operation", user_id="test_user", operation_type="demo"):
        log_info("在上下文中執行操作")
        # 模擬一些工作
        result = 42
        log_info(f"操作結果: {result}")
    
    # 測試錯誤情況
    try:
        with ErrorContext("failing_operation", will_fail=True):
            raise ValueError("這是一個測試錯誤")
    except ValueError:
        log_warning("捕獲了預期的錯誤")


def main():
    """主測試函數"""
    print("🧪 測試錯誤處理和日誌系統\n")
    
    # 測試基本日誌
    print("1. 測試基本日誌功能...")
    log_info("這是一條信息日誌", extra_data="test")
    log_warning("這是一條警告日誌", warning_code="W001")
    log_error("這是一條錯誤日誌（無異常）", error_code="E001")
    print("   ✅ 完成\n")
    
    # 測試輸入驗證
    print("2. 測試輸入驗證...")
    try:
        result = test_validation(50, "測試用戶")
        print(f"   ✅ 驗證通過: {result}")
    except DataValidationError as e:
        print(f"   ❌ 驗證失敗: {e}")
    
    try:
        result = test_validation(150, "測試用戶")  # 超出範圍
    except DataValidationError as e:
        print(f"   ✅ 正確捕獲驗證錯誤: {e}")
    print()
    
    # 測試重試機制
    print("3. 測試重試機制...")
    try:
        result = test_retry_function(should_fail=True)
    except SatelliteCalculationError as e:
        print(f"   ✅ 重試後仍然失敗（預期行為）: {e.error_code}")
    
    result = test_retry_function(should_fail=False)
    print(f"   ✅ 成功執行: {result}\n")
    
    # 測試錯誤上下文
    print("4. 測試錯誤上下文...")
    test_error_context()
    print("   ✅ 完成\n")
    
    # 測試結構化日誌
    print("5. 測試結構化日誌...")
    log_info(
        "分析完成",
        user_id="user123",
        trace_id="trace456",
        duration=125.3,
        satellite_count=7500
    )
    print("   ✅ 完成\n")
    
    print("📁 日誌文件位置:")
    print("   - logs/starlink.log (JSON 格式)")
    print("   - logs/error.log (僅錯誤)")
    print("\n✅ 所有測試完成!")


if __name__ == "__main__":
    main()