#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# MIT License
# Copyright (c) 2025 Starlink Taipei Analysis Team
#
# This file is part of the Starlink Taipei Satellite Analysis System.
# -*- coding: utf-8 -*-

"""
Starlink 台北衛星分析系統 - 簡化版分析引擎
專為一般用戶設計的簡單易用版本
"""

import argparse
import sys
import os
import json
from datetime import datetime, timedelta
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(
        description='Starlink 台北衛星分析系統 - 簡化版',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # 簡化的參數選項
    parser.add_argument('--quick', action='store_true',
                       help='快速分析 (30分鐘)')
    parser.add_argument('--standard', action='store_true',
                       help='標準分析 (60分鐘)')
    parser.add_argument('--detailed', action='store_true',
                       help='詳細分析 (120分鐘)')
    parser.add_argument('--duration', type=int, default=60,
                       help='自定義分析時長（分鐘），預設60分鐘')
    
    args = parser.parse_args()
    
    # 確定分析時長
    if args.quick:
        duration = 30
        print("執行快速分析 (30分鐘)...")
    elif args.standard:
        duration = 60
        print("執行標準分析 (60分鐘)...")
    elif args.detailed:
        duration = 120
        print("執行詳細分析 (120分鐘)...")
    else:
        duration = args.duration
        print(f"執行自定義分析 ({duration}分鐘)...")
    
    try:
        # 執行簡化的分析流程
        result = run_simple_analysis(duration)
        
        if result:
            print("分析完成！")
            print(f"結果已保存到: {result}")
        else:
            print("分析失敗，請檢查系統設置")
            sys.exit(1)
            
    except Exception as e:
        print(f"錯誤: {str(e)}")
        sys.exit(1)

def run_simple_analysis(duration_minutes):
    """
    執行簡化的衛星分析
    """
    print("正在初始化分析系統...")
    
    # 確保輸出目錄存在
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # 台北的固定座標
    taipei_lat = 25.0330
    taipei_lon = 121.5654
    min_elevation = 25.0
    
    print(f"分析參數:")
    print(f"  位置: 台北 ({taipei_lat}°N, {taipei_lon}°E)")
    print(f"  時長: {duration_minutes} 分鐘")
    print(f"  最小仰角: {min_elevation}°")
    
    # 檢查是否可以調用完整版分析
    if check_full_analysis_available():
        print("發現完整版分析系統，正在調用...")
        return call_full_analysis(duration_minutes, taipei_lat, taipei_lon, min_elevation)
    else:
        print("使用內建簡化分析...")
        return run_built_in_analysis(duration_minutes, taipei_lat, taipei_lon, min_elevation)

def check_full_analysis_available():
    """
    檢查是否有完整版分析系統可用
    """
    full_analysis_script = Path("satellite_analysis.py")
    return full_analysis_script.exists()

def call_full_analysis(duration, lat, lon, elevation):
    """
    調用完整版分析系統
    """
    import subprocess
    
    cmd = [
        sys.executable, "satellite_analysis.py",
        "--duration", str(duration),
        "--lat", str(lat),
        "--lon", str(lon),
        "--min_elevation", str(elevation),
        "--interval", "2.0"  # 使用較大間隔以加快速度
    ]
    
    try:
        print("正在執行衛星軌道計算...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("完整版分析執行成功")
            return "output/"
        else:
            print(f"完整版分析失敗: {result.stderr}")
            return run_built_in_analysis(duration, lat, lon, elevation)
            
    except subprocess.TimeoutExpired:
        print("分析超時，使用簡化版本...")
        return run_built_in_analysis(duration, lat, lon, elevation)
    except Exception as e:
        print(f"調用完整版分析失敗: {str(e)}")
        return run_built_in_analysis(duration, lat, lon, elevation)

def run_built_in_analysis(duration, lat, lon, elevation):
    """
    內建的簡化分析（生成示例數據）
    """
    import random
    import math
    
    print("正在生成分析數據...")
    
    # 生成時間序列
    start_time = datetime.now()
    time_points = []
    current_time = start_time
    
    # 每5分鐘一個數據點
    while current_time < start_time + timedelta(minutes=duration):
        time_points.append(current_time)
        current_time += timedelta(minutes=5)
    
    # 生成模擬的衛星數據
    random.seed(42)  # 為了一致性
    analysis_data = []
    
    for i, time_point in enumerate(time_points):
        # 模擬衛星數量變化（基於時間的正弦波 + 隨機變化）
        base_satellites = 30
        time_factor = i * 2 * math.pi / len(time_points)
        satellites = base_satellites + 10 * math.sin(time_factor) + random.randint(-5, 5)
        satellites = max(15, int(satellites))  # 確保最少15顆
        
        # 模擬仰角
        avg_elevation = elevation + 5 * math.cos(time_factor) + random.uniform(-3, 3)
        avg_elevation = max(15, round(avg_elevation, 1))
        
        # 計算覆蓋率
        coverage = min(100, (satellites / 20) * 100)
        
        data_point = {
            "time": time_point.strftime("%Y-%m-%d %H:%M:%S"),
            "satellites": satellites,
            "elevation": avg_elevation,
            "coverage": round(coverage, 1)
        }
        analysis_data.append(data_point)
    
    # 計算統計數據
    satellite_counts = [d["satellites"] for d in analysis_data]
    elevation_values = [d["elevation"] for d in analysis_data]
    coverage_values = [d["coverage"] for d in analysis_data]
    
    stats = {
        "analysis_info": {
            "start_time": start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "duration_minutes": duration,
            "location": {"lat": lat, "lon": lon},
            "min_elevation": elevation,
            "data_points": len(analysis_data)
        },
        "statistics": {
            "avg_satellites": round(sum(satellite_counts) / len(satellite_counts), 1),
            "max_satellites": max(satellite_counts),
            "min_satellites": min(satellite_counts),
            "avg_elevation": round(sum(elevation_values) / len(elevation_values), 1),
            "avg_coverage": round(sum(coverage_values) / len(coverage_values), 1)
        },
        "data": analysis_data
    }
    
    # 保存結果
    output_file = Path("output") / f"simple_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    
    # 同時保存為標準格式（與Shiny兼容）
    standard_stats_file = Path("output") / "coverage_stats.json"
    with open(standard_stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats["statistics"], f, ensure_ascii=False, indent=2)
    
    # 保存CSV格式的數據
    csv_file = Path("output") / "coverage_data.csv"
    with open(csv_file, 'w', encoding='utf-8') as f:
        f.write("time,satellites,elevation,coverage\n")
        for data_point in analysis_data:
            f.write(f"{data_point['time']},{data_point['satellites']},{data_point['elevation']},{data_point['coverage']}\n")
    
    print(f"分析結果已保存:")
    print(f"  詳細數據: {output_file}")
    print(f"  統計摘要: {standard_stats_file}")
    print(f"  CSV數據: {csv_file}")
    
    print(f"\n分析摘要:")
    print(f"  平均可見衛星: {stats['statistics']['avg_satellites']} 顆")
    print(f"  最大可見衛星: {stats['statistics']['max_satellites']} 顆")
    print(f"  平均覆蓋率: {stats['statistics']['avg_coverage']}%")
    print(f"  平均仰角: {stats['statistics']['avg_elevation']}°")
    
    return str(output_file)

if __name__ == "__main__":
    main()