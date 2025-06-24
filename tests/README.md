# 測試套件說明

本目錄包含 Starlink 台北衛星分析系統的完整測試套件。

## 測試結構

```
tests/
├── __init__.py           # 測試套件初始化
├── conftest.py          # pytest 設定和共用 fixtures
├── unit/                # 單元測試
│   └── test_*.py       # 個別模組的單元測試
├── integration/         # 整合測試
│   └── test_*.py       # 系統整合測試
└── fixtures/           # 測試數據和資源
```

## 執行測試

### 執行所有測試
```bash
pytest
```

### 只執行單元測試
```bash
pytest tests/unit/ -m unit
```

### 只執行整合測試
```bash
pytest tests/integration/ -m integration
```

### 生成覆蓋率報告
```bash
pytest --cov=. --cov-report=html
# 報告會生成在 htmlcov/ 目錄
```

### 執行特定測試
```bash
pytest tests/unit/test_satellite_analysis.py::TestSatelliteAnalysis::test_process_time_point_worker_with_visible_satellite
```

## 測試標記

- `@pytest.mark.unit` - 單元測試
- `@pytest.mark.integration` - 整合測試
- `@pytest.mark.slow` - 執行時間較長的測試
- `@pytest.mark.requires_network` - 需要網路連接的測試

## 編寫測試指南

### 單元測試
- 測試單一函數或類別
- 使用 mock 隔離外部依賴
- 執行速度要快
- 覆蓋各種邊界情況

### 整合測試
- 測試多個組件的交互
- 可以使用真實的外部資源
- 測試完整的使用場景
- 確保系統整體運作正常

## 常用 Fixtures

- `temp_output_dir` - 臨時輸出目錄
- `sample_tle_data` - 範例 TLE 數據
- `mock_observer_location` - 測試用觀測者位置
- `analysis_params` - 預設分析參數
- `mock_datetime` - 固定時間 mock

## 持續整合

測試會在以下情況自動執行：
- 提交 Pull Request
- 推送到主分支
- 每日定時執行

覆蓋率目標：80% 以上