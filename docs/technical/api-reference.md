# API 參考文件

## 概述

本文件描述 Starlink 台北衛星分析系統的內部 API 和函數接口。

## Python API

### SatelliteAnalyzer 類

主要的衛星分析類，提供完整的軌道計算和覆蓋分析功能。

#### 初始化

```python
from satellite_analysis import SatelliteAnalyzer

analyzer = SatelliteAnalyzer(
    tle_file="starlink_latest.tle",
    location=(25.033, 121.565, 0),  # 台北經緯度和海拔
    enable_ml=True,  # 啟用機器學習增強
    cache_enabled=True  # 啟用快取
)
```

#### 主要方法

##### analyze_coverage()

分析指定時間範圍內的衛星覆蓋情況。

```python
results = analyzer.analyze_coverage(
    start_time="2024-06-09 12:00:00",
    duration_minutes=60,
    min_elevation=25.0,
    time_step_seconds=60,
    enable_parallel=True
)
```

**參數：**
- `start_time` (str/datetime): 開始時間
- `duration_minutes` (int): 分析持續時間（分鐘）
- `min_elevation` (float): 最小仰角（度）
- `time_step_seconds` (int): 時間步長（秒）
- `enable_parallel` (bool): 是否啟用並行處理

**返回：**
```python
{
    "summary": {
        "total_satellites": 7500,
        "average_visible": 32.7,
        "coverage_percentage": 100.0,
        "analysis_time": 1.23
    },
    "time_series": [...],
    "satellites": {...},
    "optimal_windows": [...]
}
```

##### download_tle_data()

下載最新的 TLE 數據。

```python
success = analyzer.download_tle_data(
    sources=["celestrak", "space-track"],
    retry_times=3,
    timeout=30
)
```

##### calculate_visibility()

計算特定時間點的衛星可見性。

```python
visible_sats = analyzer.calculate_visibility(
    time_point="2024-06-09 12:00:00",
    min_elevation=25.0,
    max_range_km=1500
)
```

### OrbitPredictionEnhancer 類

深度學習軌道預測增強器。

#### 初始化

```python
from app.services.ml_enhanced_orbit import OrbitPredictionEnhancer

enhancer = OrbitPredictionEnhancer(
    model_type="scinet-sa",
    device="cuda",  # 或 "cpu"
    batch_size=32
)
```

#### 主要方法

##### enhance_predictions()

使用深度學習增強軌道預測。

```python
enhanced_orbits = enhancer.enhance_predictions(
    satellite_data=satellite_data,
    prediction_horizon_hours=24,
    confidence_level=0.95
)
```

### OptimalWindowDetector 類

最佳觀測窗口檢測器。

```python
detector = OptimalWindowDetector(
    min_satellites=30,
    min_duration_minutes=10,
    quality_threshold=0.8
)

windows = detector.detect_windows(
    visibility_data=visibility_data,
    time_range=(start_time, end_time)
)
```

## R API

### 主要函數

#### start_analysis()

啟動衛星分析。

```r
results <- start_analysis(
  latitude = 25.033,
  longitude = 121.565,
  duration = 60,
  elevation = 25
)
```

#### generate_plots()

生成分析圖表。

```r
plots <- generate_plots(
  analysis_results,
  plot_types = c("timeline", "skyplot", "coverage")
)
```

#### export_results()

匯出分析結果。

```r
export_results(
  results,
  format = "json",  # 或 "csv", "xlsx"
  filename = "analysis_results"
)
```

## 數據格式

### 輸入格式

#### TLE 格式
```
STARLINK-1234
1 44235U 19029A   24161.50000000  .00001234  00000-0  12345-4 0  9991
2 44235  53.0540 123.4567 0001234  90.1234 270.1234 15.06391234123456
```

#### 配置 JSON
```json
{
  "location": {
    "latitude": 25.033,
    "longitude": 121.565,
    "altitude": 0
  },
  "analysis": {
    "start_time": "2024-06-09T12:00:00Z",
    "duration_minutes": 60,
    "min_elevation": 25.0
  },
  "output": {
    "formats": ["json", "csv", "png"],
    "include_predictions": true
  }
}
```

### 輸出格式

#### 分析結果 JSON
```json
{
  "metadata": {
    "version": "2.0",
    "timestamp": "2024-06-09T12:00:00Z",
    "location": {...}
  },
  "summary": {
    "total_satellites": 7500,
    "average_visible": 32.7,
    "max_visible": 45,
    "min_visible": 25,
    "coverage_percentage": 100.0
  },
  "time_series": [
    {
      "time": "2024-06-09T12:00:00Z",
      "visible_count": 32,
      "satellites": [...]
    }
  ],
  "optimal_windows": [...],
  "predictions": {...}
}
```

#### CSV 格式
```csv
time,visible_count,average_elevation,coverage_quality
2024-06-09 12:00:00,32,73.5,0.95
2024-06-09 12:01:00,33,74.2,0.96
...
```

## 錯誤代碼

| 代碼 | 描述 | 解決方案 |
|------|------|----------|
| E001 | TLE 數據下載失敗 | 檢查網路連接 |
| E002 | 無效的位置參數 | 確認經緯度範圍 |
| E003 | 記憶體不足 | 減少分析時間範圍 |
| E004 | 模型載入失敗 | 檢查模型文件 |
| E005 | 並行處理錯誤 | 使用單核心模式 |

## 性能優化建議

### 批量處理
```python
# 不推薦：逐個處理
for time in time_points:
    result = analyzer.calculate_visibility(time)

# 推薦：批量處理
results = analyzer.analyze_coverage_batch(time_points)
```

### 快取使用
```python
# 啟用快取
analyzer = SatelliteAnalyzer(cache_enabled=True)

# 手動管理快取
analyzer.clear_cache()
analyzer.preload_cache(time_range)
```

### 並行處理
```python
# 自動選擇核心數
analyzer.analyze_coverage(enable_parallel=True)

# 指定核心數
analyzer.set_parallel_workers(8)
```

## 範例程式碼

### 完整分析流程

```python
# Python 範例
from satellite_analysis import SatelliteAnalyzer
import json

# 初始化分析器
analyzer = SatelliteAnalyzer(
    location=(25.033, 121.565, 0),
    enable_ml=True
)

# 下載最新 TLE 數據
analyzer.download_tle_data()

# 執行分析
results = analyzer.analyze_coverage(
    duration_minutes=120,
    min_elevation=30.0
)

# 保存結果
with open("results.json", "w") as f:
    json.dump(results, f, indent=2)

# 生成圖表
analyzer.generate_plots(results, output_dir="plots/")
```

### R Shiny 整合

```r
# R 範例
library(shiny)
library(reticulate)

# 載入 Python 模組
satellite <- import("satellite_analysis")

# Shiny 服務器邏輯
server <- function(input, output, session) {
  
  # 響應分析按鈕
  observeEvent(input$analyze, {
    
    # 創建分析器
    analyzer <- satellite$SatelliteAnalyzer(
      location = c(input$lat, input$lon, 0)
    )
    
    # 執行分析
    results <- analyzer$analyze_coverage(
      duration_minutes = input$duration,
      min_elevation = input$elevation
    )
    
    # 更新 UI
    output$results <- renderPlot({
      plot_satellite_coverage(results)
    })
  })
}
```

## 版本歷史

- **v2.0** (2024-06): 加入深度學習預測
- **v1.5** (2024-05): 性能優化和並行處理
- **v1.0** (2024-04): 初始版本

## 相關文件

- [系統架構](./architecture.md)
- [安裝指南](../user-guide/installation.md)
- [預測功能](./prediction-features.md)