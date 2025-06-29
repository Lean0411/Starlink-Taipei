#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# MIT License
# Copyright (c) 2025 Starlink Taipei Analysis Team
#
# This file is part of the Starlink Taipei Satellite Analysis System.

"""
🛰️ Starlink 台北衛星分析系統 - 主命令行工具
整合統一錯誤處理和日誌系統
"""

import argparse
import sys
import os
import subprocess
from pathlib import Path
import json
import time

# 導入錯誤處理和日誌系統
from app.utils import (
    get_logger,
    log_info,
    log_error,
    log_warning,
    handle_errors,
    ErrorContext,
    ConfigurationError,
)

# 初始化日誌器
logger = get_logger("starlink_cli")


@handle_errors(retry_count=1)
def main():
    parser = argparse.ArgumentParser(
        description="🛰️ Starlink 台北衛星分析系統",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用範例:
  %(prog)s analyze --duration 30     # 執行30分鐘分析
  %(prog)s analyze --quick           # 快速10分鐘分析
  %(prog)s shiny                     # 啟動 Shiny 網頁介面
  %(prog)s health                    # 健康檢查
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="可用指令", required=True)

    # 分析指令
    analyze_parser = subparsers.add_parser("analyze", help="執行衛星覆蓋分析")
    analyze_parser.add_argument(
        "--duration", type=int, default=30, help="分析時間長度（分鐘），預設30分鐘"
    )
    analyze_parser.add_argument(
        "--quick", action="store_true", help="快速分析（10分鐘）"
    )
    analyze_parser.add_argument(
        "--interval", type=float, default=1.0, help="時間間隔（分鐘），預設1.0分鐘"
    )
    analyze_parser.add_argument(
        "--min_elevation",
        type=float,
        default=25.0,
        help="最小衛星仰角閾值（度），預設25.0度",
    )
    analyze_parser.add_argument(
        "--cpu",
        type=int,
        default=None,
        help="用於並行處理的 CPU 核心數 (預設使用所有可用核心)",
    )
    analyze_parser.add_argument(
        "--lat", type=float, default=25.0330, help="觀察者緯度，預設台北"
    )
    analyze_parser.add_argument(
        "--lon", type=float, default=121.5654, help="觀察者經度，預設台北"
    )

    # Shiny 應用指令
    shiny_parser = subparsers.add_parser("shiny", help="啟動 Shiny 網頁介面")
    shiny_parser.add_argument(
        "--port", type=int, default=3838, help="網頁應用端口（預設3838）"
    )
    shiny_parser.add_argument(
        "--host", type=str, default="0.0.0.0", help="網頁應用主機（預設0.0.0.0）"
    )
    shiny_parser.add_argument("--simple", action="store_true", help="啟動簡化版界面")

    # 更新數據指令
    update_parser = subparsers.add_parser("update", help="更新衛星軌道數據")

    # 健康檢查指令
    health_parser = subparsers.add_parser("health", help="系統健康檢查")

    args = parser.parse_args()

    # 記錄命令執行
    log_info(f"執行命令: {args.command}", command=args.command)

    try:
        if args.command == "analyze":
            run_analyze(args)
        elif args.command == "shiny":
            run_shiny(args)
        elif args.command == "update":
            run_update()
        elif args.command == "health":
            run_health_check()
    except Exception as e:
        log_error(f"命令執行失敗: {str(e)}", exc_info=True)
        print(f"\n❌ 錯誤: {str(e)}")
        sys.exit(1)


@handle_errors(retry_count=2)
def run_analyze(args):
    """執行衛星分析"""
    with ErrorContext(
        "satellite_analysis", duration=args.duration, lat=args.lat, lon=args.lon
    ):

        # 如果是快速分析，覆蓋持續時間
        if args.quick:
            args.duration = 10
            log_info("使用快速分析模式（10分鐘）")

        print(f"\n🚀 開始 Starlink 衛星分析...")
        print(f"📍 位置: ({args.lat:.4f}, {args.lon:.4f})")
        print(f"⏱️  持續時間: {args.duration} 分鐘")
        print(f"📐 最小仰角: {args.min_elevation}°")
        print(f"🔄 時間間隔: {args.interval} 分鐘")

        if args.cpu:
            print(f"💻 CPU 核心數: {args.cpu}")

        # 檢查 satellite_analysis.py 是否存在
        if not Path("satellite_analysis_updated.py").exists():
            if not Path("satellite_analysis.py").exists():
                raise ConfigurationError(
                    "找不到衛星分析模組",
                    details={
                        "files_checked": [
                            "satellite_analysis_updated.py",
                            "satellite_analysis.py",
                        ]
                    },
                )
            analysis_script = "satellite_analysis.py"
        else:
            analysis_script = "satellite_analysis_updated.py"

        # 構建命令
        cmd = [
            sys.executable,
            analysis_script,
            "--lat",
            str(args.lat),
            "--lon",
            str(args.lon),
            "--duration",
            str(args.duration),
            "--interval",
            str(args.interval),
            "--min-elevation",
            str(args.min_elevation),
        ]

        if args.cpu:
            cmd.extend(["--workers", str(args.cpu)])

        # 執行分析
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True)
        duration = time.time() - start_time

        if result.returncode != 0:
            log_error(f"分析失敗: {result.stderr}")
            print(f"\n❌ 分析失敗:")
            print(result.stderr)
            sys.exit(1)
        else:
            log_info(f"分析成功完成", duration=duration)
            print(result.stdout)

            # 載入並顯示結果摘要
            try:
                stats_file = Path("output/coverage_stats.json")
                if stats_file.exists():
                    with open(stats_file, "r") as f:
                        stats = json.load(f)

                    print("\n📊 分析結果摘要:")
                    print(f"  • 平均可見衛星數: {stats['avg_visible_satellites']:.1f}")
                    print(f"  • 最大可見衛星數: {stats['max_visible_satellites']}")
                    print(f"  • 最小可見衛星數: {stats['min_visible_satellites']}")
                    print(f"  • 覆蓋率: {stats['coverage_percentage']:.1f}%")
                    print(f"  • 平均仰角: {stats.get('avg_elevation', 0):.1f}°")
            except Exception as e:
                log_warning(f"無法載入統計結果: {str(e)}")


@handle_errors()
def run_shiny(args):
    """啟動 Shiny 應用"""
    with ErrorContext("shiny_app", port=args.port, simple=args.simple):

        # 選擇應用檔案
        if args.simple:
            app_file = "app_simple.R"
            log_info("啟動簡化版 Shiny 界面")
        else:
            app_file = "app.R"
            log_info("啟動完整版 Shiny 界面")

        # 檢查檔案是否存在
        if not Path(app_file).exists():
            raise ConfigurationError(
                f"找不到 Shiny 應用檔案: {app_file}", details={"file": app_file}
            )

        print(f"\n🌐 啟動 Shiny 網頁應用...")
        print(f"📄 應用檔案: {app_file}")
        print(f"🔗 訪問地址: http://localhost:{args.port}")
        print(f"📡 監聽地址: {args.host}:{args.port}")
        print(f"\n💡 提示: 按 Ctrl+C 停止應用\n")

        # 構建 R 命令
        r_cmd = f"""
        library(shiny)
        runApp('{app_file}', host='{args.host}', port={args.port})
        """

        # 執行 Shiny 應用
        cmd = ["R", "--slave", "--no-save", "--no-restore", "-e", r_cmd]

        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            log_error(f"Shiny 應用啟動失敗: {str(e)}")
            print("\n❌ Shiny 應用啟動失敗!")
            print("請確保已安裝所需的 R 套件:")
            print("  - shiny")
            print("  - shinydashboard")
            print("  - plotly")
            print("  - DT")
            print("  - ggplot2")
            sys.exit(1)
        except KeyboardInterrupt:
            log_info("Shiny 應用被用戶中斷")
            print("\n\n✅ Shiny 應用已停止")


@handle_errors()
def run_update():
    """更新衛星軌道數據"""
    with ErrorContext("tle_update"):
        print("\n🔄 更新 Starlink 衛星軌道數據...")

        # 確保數據目錄存在
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)

        # 下載最新 TLE 數據
        url = "https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink&FORMAT=tle"

        try:
            import requests

            response = requests.get(url, timeout=30)
            response.raise_for_status()

            # 保存數據
            tle_file = data_dir / "starlink_tle.txt"
            with open(tle_file, "w") as f:
                f.write(response.text)

            # 計算衛星數量
            lines = response.text.strip().split("\n")
            satellite_count = len(lines) // 3

            log_info(f"TLE 數據更新成功", satellite_count=satellite_count)
            print(f"✅ 成功下載 {satellite_count} 顆衛星的軌道數據")
            print(f"📁 數據已保存到: {tle_file}")

        except Exception as e:
            log_error(f"TLE 數據更新失敗: {str(e)}")
            print(f"❌ 更新失敗: {str(e)}")
            sys.exit(1)


@handle_errors()
def run_health_check():
    """執行系統健康檢查"""
    with ErrorContext("health_check"):
        print("\n🏥 執行系統健康檢查...\n")

        health_status = {
            "python_packages": {},
            "r_packages": {},
            "files": {},
            "system": {},
        }

        # 檢查 Python 套件
        print("📦 檢查 Python 依賴套件:")
        python_packages = [
            "numpy",
            "pandas",
            "matplotlib",
            "skyfield",
            "requests",
            "tqdm",
            "plotly",
            "scipy",
        ]

        for package in python_packages:
            try:
                __import__(package)
                health_status["python_packages"][package] = True
                print(f"  ✅ {package}")
            except ImportError:
                health_status["python_packages"][package] = False
                print(f"  ❌ {package} (未安裝)")

        # 檢查 R 環境
        print("\n🔧 檢查 R 環境:")
        try:
            result = subprocess.run(["R", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                health_status["system"]["r_installed"] = True
                print("  ✅ R 環境可用")
            else:
                health_status["system"]["r_installed"] = False
                print("  ❌ R 環境不可用")
        except FileNotFoundError:
            health_status["system"]["r_installed"] = False
            print("  ❌ 找不到 R")

        # 檢查關鍵檔案
        print("\n📁 檢查關鍵檔案:")
        critical_files = [
            "satellite_analysis.py",
            "app.R",
            "ui.R",
            "server.R",
            "R/analysis.R",
            "R/plots.R",
        ]

        for file in critical_files:
            if Path(file).exists():
                health_status["files"][file] = True
                print(f"  ✅ {file}")
            else:
                health_status["files"][file] = False
                print(f"  ❌ {file} (缺失)")

        # 檢查目錄
        print("\n📂 檢查目錄:")
        directories = ["output", "data", "logs"]
        for directory in directories:
            path = Path(directory)
            if path.exists():
                file_count = len(list(path.iterdir()))
                print(f"  ✅ {directory}/ 目錄存在")
                print(f"     包含 {file_count} 個檔案")
            else:
                print(f"  ❌ {directory}/ 目錄不存在")
                path.mkdir(exist_ok=True)
                print(f"     已自動創建")

        # 總結健康狀態
        python_ok = all(health_status["python_packages"].values())
        files_ok = all(health_status["files"].values())
        r_ok = health_status["system"].get("r_installed", False)

        print("\n📊 健康檢查總結:")
        if python_ok and files_ok and r_ok:
            print("  ✅ 系統健康狀態: 良好")
            log_info("健康檢查通過")
        else:
            print("  ⚠️  系統健康狀態: 需要修復")
            log_warning("健康檢查發現問題", health_status=health_status)

            if not python_ok:
                print("\n  請安裝缺失的 Python 套件:")
                print("  pip install -r requirements.txt")

            if not r_ok:
                print("\n  請安裝 R 環境")

            if not files_ok:
                print("\n  請檢查缺失的檔案")


if __name__ == "__main__":
    main()
