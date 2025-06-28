#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# MIT License
# Copyright (c) 2025 Starlink Taipei Analysis Team
#
# This file is part of the Starlink Taipei Satellite Analysis System.

"""
🛰️ Starlink 台北衛星分析系統 - 主命令行工具
"""

import argparse
import sys
import os
import subprocess
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(
        description='🛰️ Starlink 台北衛星分析系統',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用範例:
  %(prog)s analyze --duration 30     # 執行30分鐘分析
  %(prog)s analyze --quick           # 快速10分鐘分析
  %(prog)s shiny                     # 啟動 Shiny 網頁介面
  %(prog)s health                    # 健康檢查
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用指令', required=True)
    
    # 分析指令
    analyze_parser = subparsers.add_parser('analyze', help='執行衛星覆蓋分析')
    analyze_parser.add_argument('--duration', type=int, default=30, 
                               help='分析時間長度（分鐘），預設30分鐘')
    analyze_parser.add_argument('--quick', action='store_true',
                               help='快速分析（10分鐘）')
    analyze_parser.add_argument('--interval', type=float, default=1.0,
                               help='時間間隔（分鐘），預設1.0分鐘')
    analyze_parser.add_argument('--min_elevation', type=float, default=25.0, 
                                help='最小衛星仰角閾值（度），預設25.0度')
    analyze_parser.add_argument('--cpu', type=int, default=None, 
                               help='用於並行處理的 CPU 核心數 (預設使用所有可用核心)')
    analyze_parser.add_argument('--lat', type=float, default=25.0330,
                               help='觀察者緯度，預設台北')
    analyze_parser.add_argument('--lon', type=float, default=121.5654,
                               help='觀察者經度，預設台北')
    
    # 健康檢查指令
    subparsers.add_parser('health', help='系統健康檢查')
    
    # Shiny 網頁介面指令
    shiny_parser = subparsers.add_parser('shiny', help='啟動 Shiny 網頁介面')
    shiny_parser.add_argument('--port', type=int, default=8080,
                             help='Shiny 應用端口，預設8080')
    shiny_parser.add_argument('--host', type=str, default='0.0.0.0',
                             help='監聽地址，預設0.0.0.0')
    
    args = parser.parse_args()
        
    try:
        if args.command == 'analyze':
            duration = 10 if args.quick else args.duration
            print(f"🛰️  執行 {duration} 分鐘分析...")
            
            cmd_parts = [
                sys.executable, "satellite_analysis.py", 
                "--duration", str(duration), 
                "--interval", str(args.interval),
                "--min_elevation", str(args.min_elevation),
                "--lat", str(args.lat),
                "--lon", str(args.lon)
            ]
            if args.cpu is not None:
                cmd_parts.extend(["--cpu", str(args.cpu)])
            
            process = subprocess.run(cmd_parts, capture_output=True, text=True, check=False)
            if process.returncode == 0:
                print("✅ 分析腳本執行完成。")
                if process.stdout:
                    print("輸出:")
                    print(process.stdout)
            else:
                print("❌ 分析腳本執行失敗。")
                if process.stderr:
                    print("錯誤:")
                    print(process.stderr)
            
        elif args.command == 'health':
            print("🏥 執行系統健康檢查...")
            
            # 檢查 Python 依賴
            python_deps = [
                'numpy', 'pandas', 'matplotlib', 'skyfield', 
                'requests', 'tqdm', 'plotly', 'scipy'
            ]
            
            print("\n📦 檢查 Python 依賴套件:")
            for dep in python_deps:
                try:
                    __import__(dep)
                    print(f"  ✅ {dep}")
                except ImportError:
                    print(f"  ❌ {dep} (未安裝)")
            
            # 檢查 R 是否可用
            print("\n🔧 檢查 R 環境:")
            try:
                r_result = subprocess.run(['R', '--version'], 
                                        capture_output=True, text=True, timeout=10)
                if r_result.returncode == 0:
                    print("  ✅ R 環境可用")
                else:
                    print("  ❌ R 環境不可用")
            except (subprocess.TimeoutExpired, FileNotFoundError):
                print("  ❌ 找不到 R 或執行超時")
            
            # 檢查關鍵檔案
            print("\n📁 檢查關鍵檔案:")
            key_files = [
                'satellite_analysis.py',
                'app.R',
                'ui.R', 
                'server.R',
                'R/analysis.R',
                'R/plots.R'
            ]
            
            for file_path in key_files:
                if os.path.exists(file_path):
                    print(f"  ✅ {file_path}")
                else:
                    print(f"  ❌ {file_path} (找不到)")
            
            # 檢查輸出目錄
            print("\n📂 檢查目錄:")
            output_dir = "output"
            if os.path.exists(output_dir):
                print(f"  ✅ {output_dir}/ 目錄存在")
                files = os.listdir(output_dir)
                if files:
                    print(f"     包含 {len(files)} 個檔案")
            else:
                print(f"  ⚠️  {output_dir}/ 目錄不存在，將在首次運行時創建")
            
        elif args.command == 'shiny':
            print(f"🌐 啟動 Shiny 網頁應用於 http://{args.host}:{args.port}")
            print("   請在瀏覽器中打開上述網址。按 Ctrl+C 停止應用。")
            
            try:
                # 檢查 app.R 是否存在
                app_r_path = "app.R"
                if not os.path.exists(app_r_path):
                    print(f"❌ 錯誤: 找不到 Shiny 應用檔案 {app_r_path}")
                    sys.exit(1)

                # 啟動 Shiny 應用
                env = os.environ.copy()
                env["R_SHINY_PORT"] = str(args.port)
                env["R_SHINY_HOST"] = args.host
                env["LANG"] = "en_US.UTF-8"
                env["LC_ALL"] = "en_US.UTF-8"
                env["LC_CTYPE"] = "en_US.UTF-8"
                
                # 使用 R 命令啟動 Shiny 應用
                r_command = f"""
Sys.setlocale("LC_ALL", "en_US.UTF-8")
options(encoding = "UTF-8")
library(shiny)
runApp(appDir=".", port={args.port}, host="{args.host}", launch.browser=FALSE)
"""
                
                process = subprocess.Popen(
                    ['R', '--slave', '-e', r_command], 
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    bufsize=1
                )
                
                # 即時輸出 R 的回應
                try:
                    for line in process.stdout:
                        print(line, end='')
                        if "Listening on" in line:
                            print(f"\n🎉 Shiny 應用已啟動！")
                            print(f"   瀏覽器地址: http://{args.host}:{args.port}")
                            
                    process.wait()
                except KeyboardInterrupt:
                    print("\n⏹️  收到中斷信號，正在停止 Shiny 應用...")
                    process.terminate()
                    process.wait()
                    print("✅ Shiny 應用已停止。")
                    
            except FileNotFoundError:
                print("❌ 錯誤: 找不到 R 命令。請確保 R 已安裝並在 PATH 中。")
                sys.exit(1)
            except Exception as e:
                print(f"❌ 啟動 Shiny 應用時發生錯誤: {e}")
                sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  用戶中斷操作")
    except Exception as e:
        print(f"❌ 執行錯誤: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 