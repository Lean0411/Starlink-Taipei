#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# MIT License
# Copyright (c) 2025 Starlink Taipei Analysis Team
#
# This file is part of the Starlink Taipei Satellite Analysis System.

"""
Starlink 台北衛星分析模組
提供衛星可見性和覆蓋率分析功能，整合統一錯誤處理和日誌系統
"""

import os
import sys
import json
import time
import argparse
import warnings
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # 使用非互動式後端
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta, timezone
from pathlib import Path
import requests
import concurrent.futures
from tqdm import tqdm
from skyfield.api import load, wgs84, EarthSatellite, Loader
from skyfield.timelib import Time
from multiprocessing import cpu_count
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.preprocessing import StandardScaler
from collections import deque

# 導入錯誤處理和日誌系統
from app.utils import (
    get_logger, log_info, log_error, log_warning, log_debug,
    handle_errors, validate_input, ErrorContext,
    SatelliteCalculationError, TLEDataError, NetworkError,
    DataValidationError
)

# 初始化日誌器
logger = get_logger('satellite_analysis')

# 忽略一些常見的警告
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', category=FutureWarning)

# 台北地區常數
TAIPEI_LAT = 25.0330
TAIPEI_LON = 121.5654
ELEVATION = 10.0
utc = timezone.utc


def process_time_point_worker(time_data_tuple, worker_tle_list_of_tuples, worker_observer_lat, worker_observer_lon, worker_observer_elev, worker_ts_init_args, min_elevation_threshold=25):
    """
    處理單一時間點的衛星可見性計算（工作進程版本）
    
    在工作進程中重新創建必要的 Skyfield 物件，因為它們不能被序列化
    """
    try:
        idx, t_dt = time_data_tuple
        
        # 在工作進程中重新初始化 Skyfield
        ts_local = load.timescale(**worker_ts_init_args)
        
        # 創建觀測者位置
        observer = wgs84.latlon(worker_observer_lat, worker_observer_lon, worker_observer_elev)
        
        # 轉換時間
        t = ts_local.from_datetime(t_dt)
        
        visible_satellites = []
        
        for tle_line1, tle_line2 in worker_tle_list_of_tuples:
            try:
                satellite = EarthSatellite(tle_line1, tle_line2, 'STARLINK', ts_local)
                
                # 計算相對位置
                difference = satellite - observer
                topocentric = difference.at(t)
                alt, az, distance = topocentric.altaz()
                
                elevation_deg = alt.degrees
                
                if elevation_deg >= min_elevation_threshold:
                    visible_satellites.append({
                        'elevation': elevation_deg,
                        'azimuth': az.degrees,
                        'distance': distance.km
                    })
            except Exception:
                # 忽略單個衛星的錯誤
                continue
        
        return idx, len(visible_satellites), visible_satellites
        
    except Exception as e:
        log_error(f"處理時間點時發生錯誤: {str(e)}", exc_info=True)
        return idx, 0, []


@handle_errors(retry_count=3, retry_delay=2.0)
@validate_input(
    observer_lat=(-90, 90),
    observer_lon=(-180, 180),
    duration_minutes=(1, 1440),
    time_interval_minutes=(0.1, 60)
)
def analyze_satellite_coverage(
    observer_lat=TAIPEI_LAT,
    observer_lon=TAIPEI_LON,
    observer_elev=ELEVATION,
    start_time=None,
    duration_minutes=60,
    time_interval_minutes=1,
    min_elevation=25,
    max_workers=None,
    tle_file=None,
    output_dir='output',
    include_prediction=True
):
    """
    分析 Starlink 衛星覆蓋情況
    
    Args:
        observer_lat: 觀測者緯度
        observer_lon: 觀測者經度
        observer_elev: 觀測者海拔（米）
        start_time: 開始時間（默認為當前時間）
        duration_minutes: 分析持續時間（分鐘）
        time_interval_minutes: 時間間隔（分鐘）
        min_elevation: 最小仰角（度）
        max_workers: 最大工作進程數
        tle_file: TLE 文件路徑
        output_dir: 輸出目錄
        include_prediction: 是否包含預測
        
    Returns:
        dict: 分析結果
    """
    
    with ErrorContext(
        "satellite_coverage_analysis",
        observer_lat=observer_lat,
        observer_lon=observer_lon,
        duration_minutes=duration_minutes
    ):
        log_info(
            "開始衛星覆蓋分析",
            user_id="system",
            satellite_count=0,
            duration=duration_minutes
        )
        
        # 確保輸出目錄存在
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # 設置開始時間
        if start_time is None:
            start_time = datetime.now(utc)
        
        # 載入 TLE 數據
        satellites = load_starlink_tle_data(tle_file)
        log_info(f"載入了 {len(satellites)} 顆衛星數據")
        
        # 初始化 Skyfield
        ts = load.timescale()
        
        # 準備用於多進程的 TLE 數據
        tle_list_of_tuples = [(sat['tle_line1'], sat['tle_line2']) for sat in satellites]
        
        # 設置工作進程數
        if max_workers is None:
            max_workers = max(1, min(cpu_count() - 1, 16))
        
        # 生成時間序列
        time_steps = int(duration_minutes / time_interval_minutes)
        time_points = []
        for i in range(time_steps):
            t = start_time + timedelta(minutes=i * time_interval_minutes)
            time_points.append(t)
        
        # 準備工作進程參數
        time_data = list(enumerate(time_points))
        ts_init_args = {'builtin': True}
        
        # 並行處理
        results = []
        log_info(f"使用 {max_workers} 個工作進程進行並行處理")
        
        with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for time_tuple in time_data:
                future = executor.submit(
                    process_time_point_worker,
                    time_tuple,
                    tle_list_of_tuples,
                    observer_lat,
                    observer_lon,
                    observer_elev,
                    ts_init_args,
                    min_elevation
                )
                futures.append(future)
            
            # 收集結果
            for future in tqdm(concurrent.futures.as_completed(futures), 
                             total=len(futures), 
                             desc="分析進度"):
                idx, count, visible_sats = future.result()
                results.append((idx, time_points[idx], count, visible_sats))
        
        # 按時間排序結果
        results.sort(key=lambda x: x[0])
        
        # 準備分析數據
        analysis_data = {
            'timestamps': [r[1] for r in results],
            'visible_counts': [r[2] for r in results],
            'visible_satellites': [r[3] for r in results]
        }
        
        # 計算統計資料
        stats = calculate_statistics(analysis_data, observer_lat, observer_lon, min_elevation)
        
        # 生成視覺化
        generate_visualizations(analysis_data, stats, output_dir)
        
        # 如果需要，執行預測
        predictions = None
        if include_prediction:
            try:
                predictions = perform_prediction(analysis_data)
                log_info("預測分析完成")
            except Exception as e:
                log_warning(f"預測分析失敗: {str(e)}")
        
        # 準備返回結果
        result = {
            'stats': stats,
            'data': analysis_data,
            'predictions': predictions,
            'metadata': {
                'analysis_time': datetime.now(utc).isoformat(),
                'satellite_count': len(satellites),
                'duration_minutes': duration_minutes,
                'time_interval_minutes': time_interval_minutes,
                'observer_location': {
                    'latitude': observer_lat,
                    'longitude': observer_lon,
                    'elevation': observer_elev
                },
                'min_elevation_threshold': min_elevation
            }
        }
        
        # 保存結果
        save_results(result, output_dir)
        
        log_info(
            "衛星覆蓋分析完成",
            duration=time.time() - start_time.timestamp(),
            satellite_count=len(satellites)
        )
        
        return result


@handle_errors(retry_count=3, retry_delay=5.0)
def load_starlink_tle_data(tle_file=None):
    """
    載入 Starlink 衛星的 TLE 數據
    
    Args:
        tle_file: TLE 文件路徑（可選）
        
    Returns:
        list: 衛星數據列表
    """
    
    satellites = []
    
    if tle_file and Path(tle_file).exists():
        # 從文件載入
        log_info(f"從文件載入 TLE 數據: {tle_file}")
        with open(tle_file, 'r') as f:
            lines = f.readlines()
    else:
        # 從網路下載
        log_info("從 CelesTrak 下載最新 TLE 數據")
        url = "https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink&FORMAT=tle"
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            lines = response.text.strip().split('\n')
            
            # 保存到本地緩存
            cache_file = Path('data/starlink_tle_cache.txt')
            cache_file.parent.mkdir(exist_ok=True)
            with open(cache_file, 'w') as f:
                f.write(response.text)
            log_info(f"TLE 數據已緩存到: {cache_file}")
            
        except requests.RequestException as e:
            raise NetworkError(
                "無法下載 TLE 數據",
                details={'url': url, 'error': str(e)}
            )
    
    # 解析 TLE 數據
    i = 0
    while i + 2 < len(lines):
        name = lines[i].strip()
        tle_line1 = lines[i + 1].strip()
        tle_line2 = lines[i + 2].strip()
        
        if name.startswith('STARLINK') and len(tle_line1) == 69 and len(tle_line2) == 69:
            satellites.append({
                'name': name,
                'tle_line1': tle_line1,
                'tle_line2': tle_line2
            })
        
        i += 3
    
    if not satellites:
        raise TLEDataError("未找到有效的 Starlink 衛星數據")
    
    log_info(f"成功載入 {len(satellites)} 顆 Starlink 衛星數據")
    return satellites


def calculate_statistics(analysis_data, observer_lat, observer_lon, min_elevation):
    """計算統計資料"""
    visible_counts = analysis_data['visible_counts']
    
    stats = {
        'avg_visible_satellites': np.mean(visible_counts),
        'max_visible_satellites': np.max(visible_counts),
        'min_visible_satellites': np.min(visible_counts),
        'std_visible_satellites': np.std(visible_counts),
        'coverage_percentage': (np.sum(np.array(visible_counts) > 0) / len(visible_counts)) * 100,
        'observer_lat': observer_lat,
        'observer_lon': observer_lon,
        'min_elevation_threshold': min_elevation,
        'total_observations': len(visible_counts)
    }
    
    # 計算平均仰角
    all_elevations = []
    for visible_sats in analysis_data['visible_satellites']:
        for sat in visible_sats:
            all_elevations.append(sat['elevation'])
    
    if all_elevations:
        stats['avg_elevation'] = np.mean(all_elevations)
        stats['max_elevation'] = np.max(all_elevations)
    else:
        stats['avg_elevation'] = 0
        stats['max_elevation'] = 0
    
    return stats


def generate_visualizations(analysis_data, stats, output_dir):
    """生成視覺化圖表"""
    try:
        output_path = Path(output_dir)
        
        # 設置中文字體
        plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 時間序列圖
        fig, ax = plt.subplots(figsize=(12, 6))
        timestamps = analysis_data['timestamps']
        visible_counts = analysis_data['visible_counts']
        
        ax.plot(timestamps, visible_counts, 'b-', linewidth=2)
        ax.fill_between(timestamps, visible_counts, alpha=0.3)
        ax.set_xlabel('Time (UTC)')
        ax.set_ylabel('Number of Visible Satellites')
        ax.set_title(f'Starlink Satellite Visibility Over Time\nLocation: ({stats["observer_lat"]:.4f}, {stats["observer_lon"]:.4f})')
        ax.grid(True, alpha=0.3)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(output_path / 'satellite_visibility_timeline.png', dpi=300)
        plt.close()
        
        log_info("視覺化圖表生成完成")
        
    except Exception as e:
        log_error(f"生成視覺化時發生錯誤: {str(e)}", exc_info=True)


def save_results(result, output_dir):
    """保存分析結果"""
    output_path = Path(output_dir)
    
    # 保存統計資料
    with open(output_path / 'coverage_stats.json', 'w', encoding='utf-8') as f:
        json.dump(result['stats'], f, indent=2, ensure_ascii=False)
    
    # 保存詳細數據
    df = pd.DataFrame({
        'timestamp': result['data']['timestamps'],
        'visible_count': result['data']['visible_counts']
    })
    df.to_csv(output_path / 'coverage_data.csv', index=False)
    
    # 保存完整結果
    with open(output_path / 'full_analysis_result.json', 'w', encoding='utf-8') as f:
        # 轉換 datetime 物件為字串
        result_copy = result.copy()
        result_copy['data']['timestamps'] = [
            t.isoformat() for t in result['data']['timestamps']
        ]
        # 移除大型的衛星詳細數據以減少文件大小
        result_copy['data'].pop('visible_satellites', None)
        json.dump(result_copy, f, indent=2, ensure_ascii=False)
    
    log_info(f"分析結果已保存到: {output_path}")


def perform_prediction(analysis_data):
    """執行簡單的預測分析"""
    # 這裡可以整合更複雜的預測模型
    # 目前只做簡單的統計預測
    visible_counts = analysis_data['visible_counts']
    
    predictions = {
        'next_hour_avg': np.mean(visible_counts),
        'next_hour_std': np.std(visible_counts),
        'trend': 'stable',
        'confidence': 0.85
    }
    
    # 簡單的趨勢分析
    if len(visible_counts) > 10:
        recent = visible_counts[-10:]
        earlier = visible_counts[:10]
        if np.mean(recent) > np.mean(earlier) * 1.1:
            predictions['trend'] = 'increasing'
        elif np.mean(recent) < np.mean(earlier) * 0.9:
            predictions['trend'] = 'decreasing'
    
    return predictions


def main():
    """主程式入口"""
    parser = argparse.ArgumentParser(
        description='Starlink 衛星覆蓋分析工具',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--lat', type=float, default=TAIPEI_LAT,
                       help='觀測者緯度')
    parser.add_argument('--lon', type=float, default=TAIPEI_LON,
                       help='觀測者經度')
    parser.add_argument('--elevation', type=float, default=ELEVATION,
                       help='觀測者海拔（米）')
    parser.add_argument('--duration', type=int, default=60,
                       help='分析持續時間（分鐘）')
    parser.add_argument('--interval', type=float, default=1,
                       help='時間間隔（分鐘）')
    parser.add_argument('--min-elevation', type=float, default=25,
                       help='最小仰角（度）')
    parser.add_argument('--workers', type=int,
                       help='工作進程數')
    parser.add_argument('--tle-file', type=str,
                       help='TLE 文件路徑')
    parser.add_argument('--output-dir', type=str, default='output',
                       help='輸出目錄')
    parser.add_argument('--no-prediction', action='store_true',
                       help='禁用預測分析')
    
    args = parser.parse_args()
    
    try:
        result = analyze_satellite_coverage(
            observer_lat=args.lat,
            observer_lon=args.lon,
            observer_elev=args.elevation,
            duration_minutes=args.duration,
            time_interval_minutes=args.interval,
            min_elevation=args.min_elevation,
            max_workers=args.workers,
            tle_file=args.tle_file,
            output_dir=args.output_dir,
            include_prediction=not args.no_prediction
        )
        
        # 顯示摘要
        print("\n分析完成！")
        print(f"平均可見衛星數: {result['stats']['avg_visible_satellites']:.1f}")
        print(f"最大可見衛星數: {result['stats']['max_visible_satellites']}")
        print(f"覆蓋率: {result['stats']['coverage_percentage']:.1f}%")
        print(f"\n結果已保存到: {args.output_dir}/")
        
    except Exception as e:
        log_error(f"分析失敗: {str(e)}", exc_info=True)
        print(f"\n錯誤: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()