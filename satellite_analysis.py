#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import matplotlib # Import matplotlib
# Suppress Matplotlib font warnings early
import logging
logging.getLogger('matplotlib.font_manager').setLevel(logging.ERROR)
import matplotlib.pyplot as plt
import argparse
import requests
from skyfield.api import load, wgs84, EarthSatellite, utc
from tqdm import tqdm
import plotly.express as px
import plotly.graph_objects as go
import concurrent.futures
import matplotlib.font_manager as fm

# 定義台北市的經緯度常數
TAIPEI_LAT = 25.0330  # 台北市緯度
TAIPEI_LON = 121.5654  # 台北市經度
ELEVATION = 10.0  # 假設高度(公尺)

# 設定中文字體，嘗試使用文泉驛微米黑，如果沒有，matplotlib會回退到預設字體
# 指定中文字體路徑
chinese_font_path = '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc'  # 文泉驛微米黑字體路徑
chinese_font_prop = fm.FontProperties(fname=chinese_font_path)

# 更新字體設定
plt.rcParams['font.sans-serif'] = ['Noto Sans CJK TC', 'WenQuanYi Micro Hei', 'WenQuanYi Zen Hei']
plt.rcParams['axes.unicode_minus'] = False  # 解決負號顯示問題

# 定義中文文字繪製函數，將在需要中文文字的地方使用
def plot_with_chinese_font(title, xlabel, ylabel):
    plt.title(title, fontproperties=chinese_font_prop)
    plt.xlabel(xlabel, fontproperties=chinese_font_prop)
    plt.ylabel(ylabel, fontproperties=chinese_font_prop)

# 將 process_time_point_worker 移至頂層
def process_time_point_worker(time_data_tuple, worker_sats_list, worker_observer_lat, worker_observer_lon, worker_observer_elev, worker_ts):
    t_skyfield, time_point_datetime = time_data_tuple # 解包時間元組
    visible_satellites = []
    
    # 從傳入的經緯度和高度重新創建觀測者位置
    observer_pos = wgs84.latlon(worker_observer_lat, worker_observer_lon, elevation_m=worker_observer_elev)

    if not isinstance(worker_sats_list, list):
        print(f"警告: 預期 worker_sats_list 為列表，但收到 {type(worker_sats_list)}。跳過此時間點的衛星處理。")
    else:
        for sat_obj in worker_sats_list:
            try:
                # 修正衛星位置計算方法
                geocentric = sat_obj.at(t_skyfield)
                subpoint = wgs84.subpoint(geocentric)
                difference = sat_obj - observer_pos
                topocentric = difference.at(t_skyfield)
                alt, az, distance = topocentric.altaz()
                
                if alt.degrees > 25: # 仰角閾值
                    sat_name = getattr(sat_obj, 'name', f"UnknownSatellite-{id(sat_obj)}")
                    visible_satellites.append({
                        'name': sat_name,
                        'distance_km': distance.km,
                        'elevation': alt.degrees,
                        'azimuth': az.degrees,
                        'timestamp': time_point_datetime.strftime('%Y-%m-%d %H:%M:%S')
                    })
            except Exception as e:
                sat_name = getattr(sat_obj, 'name', f"UnknownSatellite-{id(sat_obj)}")
                print(f"處理衛星 {sat_name} 在時間點 {time_point_datetime} 時發生錯誤: {e}")
                continue
    
    best_satellite_info = None
    max_elevation = -90
    
    if visible_satellites:
        for sat_info in visible_satellites:
            if sat_info['elevation'] > max_elevation:
                max_elevation = sat_info['elevation']
                best_satellite_info = sat_info
    
    result = {
        'timestamp': time_point_datetime.strftime('%Y-%m-%d %H:%M:%S'),
        'visible_count': len(visible_satellites),
        'visible_satellites': visible_satellites
    }
    
    if best_satellite_info:
        result['elevation'] = best_satellite_info['elevation']
        result['best_satellite'] = best_satellite_info['name']
        result['distance_km'] = best_satellite_info['distance_km']
    else:
        result['elevation'] = 0
        result['best_satellite'] = None
        result['distance_km'] = 0
            
    return result

class StarlinkAnalysis:
    def __init__(self, output_dir="output"):
        """初始化分析類別並下載最新的 TLE 數據"""
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # 初始化 skyfield 的時間尺度
        self.ts = load.timescale()
        
        # 設置觀察者位置（預設為台北市）
        self.observer = wgs84.latlon(TAIPEI_LAT, TAIPEI_LON, elevation_m=ELEVATION)
        
        # 初始化衛星列表並下載 TLE 數據
        self.satellites = []
        self.download_tle_data()
        
    def set_observer_location(self, lat, lon, elevation_m=10.0):
        """設置觀察者位置"""
        self.observer = wgs84.latlon(lat, lon, elevation_m=elevation_m)
    
    def download_tle_data(self):
        """下載最新的 Starlink TLE 數據"""
        print("正在下載 Starlink TLE 數據...")
        try:
            response = requests.get('https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink&FORMAT=tle')
            if response.status_code != 200:
                raise Exception(f"下載失敗，狀態碼：{response.status_code}")
                
            tle_data = response.text.strip().split('\n')
            if len(tle_data) < 3:
                raise Exception("TLE 數據格式錯誤")
            
            # 解析 TLE 數據
            self.satellites = []
            for i in range(0, len(tle_data), 3):
                if i + 2 < len(tle_data):
                    name = tle_data[i].strip()
                    line1 = tle_data[i + 1]
                    line2 = tle_data[i + 2]
                    try:
                        satellite = EarthSatellite(line1, line2, name, self.ts)
                        self.satellites.append(satellite)
                    except Exception as e:
                        print(f"無法解析衛星 {name}: {str(e)}")
            
            print(f"成功下載並解析 {len(self.satellites)} 顆 Starlink 衛星的 TLE 數據")
            
            # 保存 TLE 數據到文件
            tle_file = os.path.join(self.output_dir, 'starlink.tle')
            with open(tle_file, 'w') as f:
                for i in range(0, len(tle_data), 3):
                    if i + 2 < len(tle_data):
                        f.write(f"{tle_data[i]}\n{tle_data[i+1]}\n{tle_data[i+2]}\n")
            print(f"TLE 數據已保存到 {tle_file}")
            
        except Exception as e:
            print(f"下載 TLE 數據時發生錯誤: {str(e)}")
            # 嘗試從本地文件載入
            tle_file = os.path.join(self.output_dir, 'starlink.tle')
            if os.path.exists(tle_file):
                print("嘗試從本地文件載入 TLE 數據...")
                with open(tle_file, 'r') as f:
                    tle_data = f.read().strip().split('\n')
                for i in range(0, len(tle_data), 3):
                    if i + 2 < len(tle_data):
                        name = tle_data[i].strip()
                        line1 = tle_data[i + 1]
                        line2 = tle_data[i + 2]
                        try:
                            satellite = EarthSatellite(line1, line2, name, self.ts)
                            self.satellites.append(satellite)
                        except Exception as e:
                            print(f"無法解析衛星 {name}: {str(e)}")
                print(f"從本地文件載入了 {len(self.satellites)} 顆衛星的 TLE 數據")
            else:
                raise Exception("無法下載或載入 TLE 數據")
    
    def analyze_24h_coverage(self, interval_minutes=1, analysis_duration_minutes=60):
        """分析衛星覆蓋情況
        
        Args:
            interval_minutes (int): 分析間隔（分鐘）
            analysis_duration_minutes (int): 分析持續時間（分鐘），預設為60分鐘
        """
        if not self.satellites:
            raise ValueError("沒有衛星數據可供分析")
            
        # 創建時間序列
        now = datetime.now(utc)
        times = []
        # 確保 interval_minutes 是整數
        interval_minutes = int(interval_minutes)
        if interval_minutes < 1:
            interval_minutes = 1
            
        # 限制分析時間範圍
        max_minutes = min(24 * 60, analysis_duration_minutes)
        print(f"分析時間範圍設定為 {max_minutes} 分鐘")
            
        for minutes in range(0, max_minutes, interval_minutes):
            times.append(now + timedelta(minutes=minutes))
            
        # 轉換為 skyfield 時間
        t = self.ts.from_datetimes(times)
        
        # 初始化結果列表
        results = []
        
        # 對每個時間點進行分析
        for time_point in tqdm(t, desc="分析衛星覆蓋"):
            visible_sats = []
            for sat in self.satellites:
                try:
                    difference = sat - self.observer
                    topocentric = difference.at(time_point)
                    alt, az, distance = topocentric.altaz()
                    
                    if alt.degrees > 25:  # 僅考慮仰角大於25度的衛星
                        visible_sats.append({
                            'name': sat.name,
                            'alt': float(alt.degrees),  # 轉換為 Python float
                            'az': float(az.degrees),    # 轉換為 Python float
                            'distance': float(distance.km)  # 轉換為 Python float
                        })
                except Exception as e:
                    print(f"計算衛星 {sat.name} 位置時出錯: {str(e)}")
                    continue
            
            # 找出最佳衛星（仰角最高的）
            best_sat = max(visible_sats, key=lambda x: x['alt']) if visible_sats else None
            
            results.append({
                'time': time_point.utc_datetime().strftime('%Y-%m-%d %H:%M:%S'),  # 轉換為字符串
                'visible_satellites': len(visible_sats),
                'best_satellite': best_sat['name'] if best_sat else None,
                'best_alt': float(best_sat['alt']) if best_sat else None,  # 轉換為 Python float
                'best_az': float(best_sat['az']) if best_sat else None,    # 轉換為 Python float
                'best_distance': float(best_sat['distance']) if best_sat else None  # 轉換為 Python float
            })
        
        # 轉換為 DataFrame
        coverage_df = pd.DataFrame(results)
        
        # 計算統計數據（確保使用 Python 原生類型）
        stats = {
            'avg_visible_satellites': float(coverage_df['visible_satellites'].mean()),
            'max_visible_satellites': int(coverage_df['visible_satellites'].max()),
            'min_visible_satellites': int(coverage_df['visible_satellites'].min()),
            'coverage_percentage': float((coverage_df['visible_satellites'] > 0).mean() * 100),
            'analysis_duration_minutes': analysis_duration_minutes
        }
        
        # 保存結果
        self.save_results(coverage_df, stats)
        
        return stats
    
    def save_results(self, coverage_df=None, stats=None):
        """保存分析結果"""
        # 保存覆蓋率數據
        if coverage_df is not None:
            coverage_df.to_csv(os.path.join(self.output_dir, 'coverage_data.csv'), index=False)
        
        # 保存統計數據
        if stats is not None:
            with open(os.path.join(self.output_dir, 'coverage_stats.json'), 'w') as f:
                json.dump(stats, f)
    
    def generate_visualizations(self):
        """生成可視化結果"""
        # 嘗試從文件載入覆蓋率數據
        coverage_file = os.path.join(self.output_dir, 'coverage_data.csv')
        if os.path.exists(coverage_file):
            coverage_df = pd.read_csv(coverage_file)
        else:
            # 檢查是否已執行分析
            if not hasattr(self, 'coverage_df'):
                print("請先執行分析或確保 coverage_data.csv 文件存在")
                return
            coverage_df = self.coverage_df
            
        # 檢查資料是否為空
        if coverage_df.empty:
            print("警告：資料為空，無法生成視覺化")
            # 生成空的圖片文件以確保R應用程式不會出錯
            for filename in ["elevation_timeline.png", "visible_satellites_timeline.png"]:
                plt.figure(figsize=(12, 6))
                plt.title('無數據可顯示')
                plt.text(0.5, 0.5, '沒有可用的衛星數據', horizontalalignment='center', verticalalignment='center', transform=plt.gca().transAxes)
                plt.tight_layout()
                plt.savefig(f"{self.output_dir}/{filename}", dpi=300)
                plt.close()
            return

        # 生成可見衛星數量時間線圖
        if 'visible_satellites' in coverage_df.columns and not coverage_df['visible_satellites'].isnull().all():
            plt.figure(figsize=(12, 6))
            # 創建時間索引
            time_indices = range(len(coverage_df))
            plt.plot(time_indices, coverage_df['visible_satellites'])
            # 使用中文字體函數
            plot_with_chinese_font('台北市區可見 Starlink 衛星數量變化', '時間 (分鐘)', '可見衛星數量 (個)')
            plt.grid(True, linestyle='--', alpha=0.7)
            
            # 設置X軸刻度，每5分鐘一個刻度
            if len(coverage_df) > 20:
                step = max(1, len(coverage_df) // 10)  # 不超過10個刻度
                plt.xticks(time_indices[::step])
            
            plt.tight_layout()
            plt.savefig(f"{self.output_dir}/visible_satellites_timeline.png", dpi=300)
            plt.close()
        else:
            print("警告：缺少 visible_satellites 數據或數據全為 NaN，無法生成可見衛星數量圖")
            plt.figure(figsize=(12, 6))
            # 使用中文字體函數
            plot_with_chinese_font('台北市區可見 Starlink 衛星數量變化 (無數據)', '時間點', '可見衛星數量 (個)')
            plt.text(0.5, 0.5, '缺少可見衛星數量數據', horizontalalignment='center', verticalalignment='center', transform=plt.gca().transAxes)
            plt.tight_layout()
            plt.savefig(f"{self.output_dir}/visible_satellites_timeline.png", dpi=300)
            plt.close()

        # 生成最大仰角時間線圖
        if 'best_alt' in coverage_df.columns and not coverage_df['best_alt'].isnull().all():
            plt.figure(figsize=(12, 6))
            # 創建時間索引
            time_indices = range(len(coverage_df))
            plt.plot(time_indices, coverage_df['best_alt'])
            # 使用中文字體函數
            plot_with_chinese_font('衛星最大仰角隨時間變化', '時間 (分鐘)', '最大仰角 (度)')
            plt.grid(True, linestyle='--', alpha=0.7)
            
            # 設置X軸刻度，每5分鐘一個刻度
            if len(coverage_df) > 20:
                step = max(1, len(coverage_df) // 10)  # 不超過10個刻度
                plt.xticks(time_indices[::step])
            
            plt.tight_layout()
            plt.savefig(f"{self.output_dir}/elevation_timeline.png", dpi=300)
            plt.close()
        else:
            print("警告：缺少 best_alt 數據或數據全為 NaN，無法生成仰角圖")
            plt.figure(figsize=(12, 6))
            # 使用中文字體函數
            plot_with_chinese_font('衛星最大仰角隨時間變化 (無數據)', '時間', '最大仰角 (度)')
            plt.text(0.5, 0.5, '缺少仰角數據', horizontalalignment='center', verticalalignment='center', transform=plt.gca().transAxes)
            plt.tight_layout()
            plt.savefig(f"{self.output_dir}/elevation_timeline.png", dpi=300)
            plt.close()

        # 生成熱力圖
        self._generate_heatmap(coverage_df)

        print("視覺化生成完成")
        
    def _generate_heatmap(self, coverage_df):
        """生成互動式熱力圖"""
        try:
            # 獲取分析持續時間（分鐘）
            duration_minutes = len(coverage_df)
            
            # 計算小時和分鐘
            hours = duration_minutes // 60
            minutes = duration_minutes % 60
            
            if hours == 0:
                # 如果分析時間少於一小時，只顯示分鐘
                # 創建熱力圖的基本數據
                data = np.zeros((1, minutes))
                
                # 遍歷每個時間點，填充數據
                for i, row in coverage_df.iterrows():
                    if i >= minutes:
                        break
                    data[0, i] = row['visible_satellites']
                
                # 創建時間標籤
                hour_labels = ["00:00"]
                
                # 創建熱力圖
                fig = px.imshow(data,
                            labels=dict(x="分鐘", y="", color="可見衛星數"),
                            x=[f"{m:02d}" for m in range(minutes)],
                            y=hour_labels,
                            title=f"衛星覆蓋熱力圖 ({minutes}分鐘分析)",
                            color_continuous_scale="Viridis",
                            aspect="auto")
                
            else:
                # 創建熱力圖的基本數據
                data = np.zeros((hours+1, 60))
                
                # 遍歷每個時間點，填充數據
                for i, row in coverage_df.iterrows():
                    if i >= duration_minutes:
                        break
                        
                    hour = i // 60
                    minute = i % 60
                    data[hour, minute] = row['visible_satellites']
                
                # 創建時間標籤
                hour_labels = [f"{h:02d}:00" for h in range(hours+1)]
                
                # 創建熱力圖
                fig = px.imshow(data,
                            labels=dict(x="分鐘", y="小時", color="可見衛星數"),
                            x=[f"{m:02d}" for m in range(60)],
                            y=hour_labels,
                            title=f"衛星覆蓋熱力圖 ({hours}小時{minutes}分鐘分析)",
                            color_continuous_scale="Viridis",
                            aspect="auto")
            
            # 增加交互元素
            fig.update_traces(
                hovertemplate="時間: %{y}:%{x}<br>可見衛星數: %{z}<extra></extra>"
            )
            
            # 調整布局
            fig.update_layout(
                autosize=True,
                height=800,
                margin=dict(t=50, l=50, b=50, r=50),
                font=dict(family="Arial", size=12),
            )
            
            # 保存為HTML文件
            fig.write_html(f"{self.output_dir}/coverage_heatmap.html")
            print(f"熱力圖已保存至 {self.output_dir}/coverage_heatmap.html")
            
        except Exception as e:
            print(f"生成熱力圖時出錯: {e}")
            # 創建一個簡單的錯誤頁面
            with open(f"{self.output_dir}/coverage_heatmap.html", 'w') as f:
                f.write("""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>覆蓋率熱力圖</title>
                    <style>
                        body { 
                            font-family: 'Noto Sans TC', Arial, sans-serif; 
                            text-align: center; 
                            margin-top: 50px;
                            background-color: #f8f9fa;
                        }
                        .error-box {
                            max-width: 600px;
                            margin: 0 auto;
                            background: white;
                            border-radius: 8px;
                            padding: 30px;
                            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                        }
                        h2 {
                            color: #e74c3c;
                        }
                    </style>
                </head>
                <body>
                    <div class="error-box">
                        <h2>覆蓋率熱力圖</h2>
                        <p>生成熱力圖時發生錯誤。請檢查日誌了解詳情。</p>
                        <p>錯誤信息: """ + str(e) + """</p>
                    </div>
                </body>
                </html>
                """)
    
    def export_html_report(self):
        """生成HTML報告"""
        # 嘗試從文件載入覆蓋率數據
        coverage_file = os.path.join(self.output_dir, 'coverage_data.csv')
        stats_file = os.path.join(self.output_dir, 'coverage_stats.json')
        
        if os.path.exists(coverage_file):
            coverage_df = pd.read_csv(coverage_file)
        else:
            # 檢查是否已執行分析
            if not hasattr(self, 'coverage_df'):
                print("請先執行分析或確保 coverage_data.csv 文件存在")
                report_path = os.path.join(self.output_dir, 'report.html')
                self._generate_empty_report(report_path)
                return report_path
            coverage_df = self.coverage_df
            
        # 載入統計數據
        if os.path.exists(stats_file):
            with open(stats_file, 'r') as f:
                stats = json.load(f)
        else:
            # 計算統計數據
            stats = self._calculate_stats(coverage_df)
            
        # 檢查資料是否為空
        if coverage_df.empty:
            print("警告：資料為空，無法生成 HTML 報告")
            report_path = os.path.join(self.output_dir, 'report.html')
            self._generate_empty_report(report_path)
            return report_path
            
        # 生成HTML報告
        report_path = os.path.join(self.output_dir, 'report.html')
        self._generate_html_report(report_path, coverage_df, stats)
        print(f"HTML報告已保存至 {report_path}")
        return report_path
        
    def _generate_empty_report(self, report_path):
        """生成空報告"""
        empty_html = """
        <!DOCTYPE html>
        <html lang="zh-TW">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>台北市 Starlink 衛星覆蓋分析報告</title>
            <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@300;400;500;700&display=swap" rel="stylesheet">
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css">
            <style>
                body {
                    font-family: 'Noto Sans TC', sans-serif;
                    line-height: 1.6;
                    margin: 0;
                    padding: 0;
                    color: #333;
                    background-color: #f5f7fa;
                }
                .container {
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                }
                header {
                    background-color: #e74c3c;
                    color: white;
                    padding: 20px 0;
                    margin-bottom: 30px;
                    border-radius: 8px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                    text-align: center;
                }
                h1 {
                    margin: 0;
                    font-size: 2.5em;
                    font-weight: 700;
                }
                .warning-box {
                    background-color: white;
                    border-radius: 8px;
                    padding: 30px;
                    margin: 40px auto;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.05);
                    text-align: center;
                    max-width: 600px;
                }
                .warning-icon {
                    font-size: 60px;
                    color: #e74c3c;
                    margin-bottom: 20px;
                }
                .warning {
                    color: #e74c3c;
                    font-size: 1.5em;
                    font-weight: 700;
                    margin-bottom: 20px;
                }
                .message {
                    font-size: 1.1em;
                    color: #7f8c8d;
                }
                footer {
                    text-align: center;
                    margin-top: 50px;
                    padding: 20px;
                    color: #7f8c8d;
                    font-size: 0.9em;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <header>
                    <h1>台北市 Starlink 衛星覆蓋分析報告</h1>
                </header>

                <div class="warning-box">
                    <div class="warning-icon">
                        <i class="fas fa-exclamation-triangle"></i>
                    </div>
                    <div class="warning">無法生成報告</div>
                    <div class="message">分析結果為空，請檢查日誌以獲取更多信息</div>
                </div>

                <footer>
                    生成於 """ + datetime.now(utc).strftime('%Y-%m-%d %H:%M:%S') + """ · 台北市 Starlink 衛星分析系統
                </footer>
            </div>
        </body>
        </html>
        """
        with open(report_path, "w") as f:
            f.write(empty_html)
        print(f"空報告已生成至 {report_path}")
        
    def _calculate_stats(self, coverage_df):
        """從覆蓋率數據計算統計數據"""
        try:
            stats = {
                'avg_visible_satellites': float(coverage_df['visible_satellites'].mean()),
                'max_visible_satellites': int(coverage_df['visible_satellites'].max()),
                'min_visible_satellites': int(coverage_df['visible_satellites'].min()),
                'coverage_percentage': float((coverage_df['visible_satellites'] > 0).mean() * 100)
            }
            
            # 如果有最佳仰角數據
            if 'best_alt' in coverage_df.columns and not coverage_df['best_alt'].isnull().all():
                stats['avg_elevation'] = float(coverage_df['best_alt'].mean())
                stats['max_elevation'] = float(coverage_df['best_alt'].max())
            else:
                stats['avg_elevation'] = 0
                stats['max_elevation'] = 0
                
            return stats
        except Exception as e:
            print(f"計算統計數據時出錯: {e}")
            return {
                'avg_visible_satellites': 0,
                'max_visible_satellites': 0,
                'min_visible_satellites': 0,
                'coverage_percentage': 0,
                'avg_elevation': 0,
                'max_elevation': 0
            }
            
    def _generate_html_report(self, report_path, coverage_df, stats):
        """生成HTML報告"""
        # 獲取輸出目錄的絕對路徑
        abs_output_dir = os.path.abspath(self.output_dir)
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="zh-TW">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>台北市 Starlink 衛星覆蓋分析報告</title>
            <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@300;400;500;700&display=swap" rel="stylesheet">
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css">
            <style>
                body {{
                    font-family: 'Noto Sans TC', sans-serif;
                    line-height: 1.6;
                    margin: 0;
                    padding: 0;
                    color: #333;
                    background-color: #f5f7fa;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                header {{
                    background-color: #3498db;
                    color: white;
                    padding: 20px 0;
                    margin-bottom: 30px;
                    border-radius: 8px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                    text-align: center;
                }}
                h1 {{
                    margin: 0;
                    font-size: 2.5em;
                    font-weight: 700;
                }}
                .analysis-time {{
                    margin-top: 10px;
                    font-style: italic;
                    opacity: 0.8;
                }}
                h2 {{
                    color: #2980b9;
                    padding-bottom: 10px;
                    border-bottom: 2px solid #eee;
                    margin-top: 40px;
                    margin-bottom: 30px;
                }}
                h3 {{
                    color: #3498db;
                    margin-top: 30px;
                }}
                .stats-container {{
                    display: flex;
                    flex-wrap: wrap;
                    gap: 20px;
                    margin-bottom: 40px;
                }}
                .stat-card {{
                    background-color: white;
                    border-radius: 8px;
                    padding: 20px;
                    flex: 1 1 220px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.05);
                    transition: transform 0.3s, box-shadow 0.3s;
                }}
                .stat-card:hover {{
                    transform: translateY(-5px);
                    box-shadow: 0 5px 15px rgba(0,0,0,0.1);
                }}
                .stat-title {{
                    font-size: 1em;
                    color: #7f8c8d;
                    margin-bottom: 10px;
                    display: flex;
                    align-items: center;
                }}
                .stat-title i {{
                    margin-right: 8px;
                    color: #3498db;
                }}
                .stat-value {{
                    font-size: 2.2em;
                    font-weight: 700;
                    color: #2980b9;
                }}
                .visualization-container {{
                    background-color: white;
                    border-radius: 8px;
                    padding: 20px;
                    margin-bottom: 30px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.05);
                }}
                img {{
                    max-width: 100%;
                    height: auto;
                    border-radius: 8px;
                    display: block;
                    margin: 20px auto;
                    border: 1px solid #eee;
                }}
                iframe {{
                    width: 100%;
                    border: none;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.05);
                }}
                .analysis-params {{
                    background-color: #eef2f5;
                    border-radius: 8px;
                    padding: 15px;
                    margin-top: 20px;
                    margin-bottom: 30px;
                }}
                .param-title {{
                    font-weight: 700;
                    color: #34495e;
                    display: inline-block;
                    width: 180px;
                }}
                footer {{
                    text-align: center;
                    margin-top: 50px;
                    padding: 20px;
                    color: #7f8c8d;
                    font-size: 0.9em;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <header>
                    <h1>台北市 Starlink 衛星覆蓋分析報告</h1>
                    <div class="analysis-time">分析時間: {datetime.now(utc).strftime('%Y-%m-%d %H:%M:%S')} UTC</div>
                </header>
                
                <div class="analysis-params">
                    <div><span class="param-title">分析持續時間:</span> {stats.get('analysis_duration_minutes', 60)} 分鐘</div>
                    <div><span class="param-title">觀測位置:</span> 緯度 {self.observer.latitude.degrees:.4f}°, 經度 {self.observer.longitude.degrees:.4f}°</div>
                </div>
                
                <h2><i class="fas fa-chart-bar"></i> 主要統計數據</h2>
                <div class="stats-container">
                    <div class="stat-card">
                        <div class="stat-title"><i class="fas fa-satellite"></i> 平均可見衛星數</div>
                        <div class="stat-value">{stats.get('avg_visible_satellites', 0):.1f}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-title"><i class="fas fa-satellite-dish"></i> 最大可見衛星數</div>
                        <div class="stat-value">{stats.get('max_visible_satellites', 0)}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-title"><i class="fas fa-satellite"></i> 最小可見衛星數</div>
                        <div class="stat-value">{stats.get('min_visible_satellites', 0)}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-title"><i class="fas fa-angle-up"></i> 平均最佳仰角</div>
                        <div class="stat-value">{stats.get('avg_elevation', 0):.1f}°</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-title"><i class="fas fa-angle-double-up"></i> 最大仰角</div>
                        <div class="stat-value">{stats.get('max_elevation', 0):.1f}°</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-title"><i class="fas fa-signal"></i> 衛星覆蓋率</div>
                        <div class="stat-value">{stats.get('coverage_percentage', 0):.1f}%</div>
                    </div>
                </div>
                
                <h2><i class="fas fa-chart-line"></i> 視覺化結果</h2>
                
                <div class="visualization-container">
                    <h3><i class="fas fa-satellite"></i> 可見衛星數量時間線</h3>
                    <img src="./visible_satellites_timeline.png" alt="可見衛星數量時間線">
                </div>
                
                <div class="visualization-container">
                    <h3><i class="fas fa-angle-up"></i> 最佳衛星仰角時間線</h3>
                    <img src="./elevation_timeline.png" alt="最佳衛星仰角時間線">
                </div>
                
                <div class="visualization-container">
                    <h3><i class="fas fa-fire"></i> 衛星覆蓋熱力圖</h3>
                    <iframe src="./coverage_heatmap.html" width="100%" height="600px"></iframe>
                </div>
                
                <footer>
                    生成於 {datetime.now(utc).strftime('%Y-%m-%d %H:%M:%S')} · 台北市 Starlink 衛星分析系統
                </footer>
            </div>
        </body>
        </html>
        """
        
        with open(report_path, "w") as f:
            f.write(html_content)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Starlink衛星覆蓋分析工具')
    parser.add_argument('--tle', help='TLE文件路徑 (如未指定則下載最新數據)')
    parser.add_argument('--output', default='output', help='輸出目錄')
    parser.add_argument('--cpu', type=int, default=0, help='使用的CPU數量 (0表示使用所有可用CPU)')
    parser.add_argument('--interval', type=float, default=1.0, help='分析間隔 (分鐘)')
    parser.add_argument('--duration', type=int, default=60, help='分析持續時間 (分鐘), 預設為60分鐘')
    args = parser.parse_args()
    
    # 創建分析器物件
    analyzer = StarlinkAnalysis(output_dir=args.output)
    
    # 執行分析
    analyzer.analyze_24h_coverage(interval_minutes=args.interval, analysis_duration_minutes=args.duration)
    
    # 生成視覺化和報告
    analyzer.generate_visualizations()
    analyzer.export_html_report()
    
    # 打印分析結果
    if hasattr(analyzer, 'coverage_df') and not analyzer.coverage_df.empty:
        visible_count_mean = analyzer.coverage_df['visible_satellites'].mean()
        visible_count_max = analyzer.coverage_df['visible_satellites'].max()
        visible_count_min = analyzer.coverage_df['visible_satellites'].min()
        
        # 檢查值是否為 NaN，若是則替換為 0
        if pd.isna(visible_count_mean):
            visible_count_mean = 0
        if pd.isna(visible_count_max):
            visible_count_max = 0
        if pd.isna(visible_count_min):
            visible_count_min = 0
            
        print(f"\n==== 分析結果摘要 ====")
        print(f"分析持續時間: {args.duration} 分鐘")
        print(f"平均可見衛星數量: {visible_count_mean:.2f}")
        print(f"最大可見衛星數量: {visible_count_max}")
        print(f"最小可見衛星數量: {visible_count_min}")
        print("============================\n")
    else:
        print(f"\n==== 分析結果摘要 ====")
        print(f"未成功生成分析結果。請檢查日誌了解詳情。")
        print("============================\n") 