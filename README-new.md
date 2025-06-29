# Starlink Taipei Satellite Analysis System v2.0

🛰️ 基於清晰架構的 Starlink 衛星覆蓋率分析系統

## 🏗️ 架構概述

本專案採用清晰架構（Clean Architecture）設計，確保高內聚、低耦合的程式碼結構：

```
src/
├── domain/         # 領域層：核心業務邏輯
├── application/    # 應用層：用例和協調
├── infrastructure/ # 基礎設施層：技術實作
└── interfaces/     # 介面層：API、CLI、UI
```

## 🚀 快速開始

### 安裝

```bash
# 安裝依賴
pip install -r requirements-new.txt

# 執行 CLI 分析
python run.py --lat 25.0330 --lon 121.5654 --duration 60

# 啟動 API 伺服器
python run.py api
```

### API 使用範例

```bash
# 分析衛星覆蓋率
curl -X POST http://localhost:8000/api/v1/coverage/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "observer_latitude": 25.0330,
    "observer_longitude": 121.5654,
    "duration_minutes": 60,
    "min_elevation": 25.0
  }'
```

## 📁 專案結構

### 領域層（Domain Layer）
- `entities/`: 核心實體（Satellite, Observer, Coverage）
- `value_objects/`: 值物件（Position, OrbitalElements）
- `services/`: 領域服務（OrbitCalculator, CoverageAnalyzer）
- `repositories/`: Repository 介面

### 應用層（Application Layer）
- `use_cases/`: 應用用例（AnalyzeCoverageUseCase）
- `dto/`: 資料傳輸物件
- `services/`: 應用服務

### 基礎設施層（Infrastructure Layer）
- `repositories/`: Repository 實作（CelestrakSatelliteRepository）
- `external_services/`: 外部服務（SkyfieldOrbitCalculator）
- `container/`: 依賴注入容器

### 介面層（Interface Layer）
- `api/`: REST API（FastAPI）
- `cli/`: 命令列介面
- `web/`: Web UI（開發中）

## 🧪 測試

```bash
# 執行所有測試
pytest

# 執行單元測試
pytest tests/unit/

# 執行整合測試
pytest tests/integration/

# 產生覆蓋率報告
pytest --cov=src --cov-report=html
```

## 📊 主要功能

1. **衛星覆蓋率分析**
   - 即時計算可見衛星數量
   - 分析最佳觀測時段
   - 統計覆蓋率指標

2. **多種介面支援**
   - REST API
   - 命令列工具
   - Web UI（開發中）

3. **可擴展架構**
   - 易於添加新的資料來源
   - 支援不同的軌道計算器
   - 模組化的分析功能

## 🔧 配置

配置檔案位於 `config/` 目錄：
- `base.yaml`: 基礎配置
- `development.yaml`: 開發環境
- `production.yaml`: 生產環境

## 📚 API 文件

啟動 API 後，訪問 http://localhost:8000/docs 查看互動式 API 文件。

## 🤝 貢獻

歡迎提交 Pull Request！請確保：
1. 遵循清晰架構原則
2. 添加適當的測試
3. 更新相關文件

## 📄 授權

MIT License