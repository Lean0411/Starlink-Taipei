#!/usr/bin/env python3
"""
遷移腳本：從 requirements.txt 遷移到 pyproject.toml
"""

import subprocess
import sys


def main():
    print("=== 開始遷移到 pyproject.toml ===\n")
    
    # 檢查 pip 版本
    print("1. 檢查 pip 版本...")
    subprocess.run([sys.executable, "-m", "pip", "--version"])
    
    # 升級 pip
    print("\n2. 升級 pip...")
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    
    # 安裝 build 工具
    print("\n3. 安裝 build 工具...")
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "setuptools", "wheel", "build"])
    
    # 安裝專案（開發模式）
    print("\n4. 以開發模式安裝專案...")
    result = subprocess.run([sys.executable, "-m", "pip", "install", "-e", ".[dev]"], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"錯誤：{result.stderr}")
        print("\n嘗試先安裝基本依賴...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-e", "."])
    
    # 安裝可選依賴
    print("\n5. 安裝可選依賴（R 整合）...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-e", ".[r-integration]"], check=True)
    except subprocess.CalledProcessError:
        print("警告：R 整合依賴安裝失敗，這是可選的。")
    
    # 驗證安裝
    print("\n6. 驗證安裝...")
    subprocess.run([sys.executable, "-m", "pip", "list"])
    
    print("\n=== 遷移完成 ===")
    print("\n後續步驟：")
    print("1. 測試應用程式是否正常運行")
    print("2. 運行測試：pytest")
    print("3. 如果一切正常，可以刪除 requirements.txt")
    print("4. 更新 CI/CD 配置使用 pyproject.toml")


if __name__ == "__main__":
    main()