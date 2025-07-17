# 專案結構遷移指南

## 已完成的變更

### 1. 移除的檔案
- `run.py` - 請使用 `python src/interfaces/cli/main.py` 或 `starlink.py`
- `start_full_app.R`, `start_service.R`, `quick_start.R` - 請使用 `app.R` 或 `app_simple.R`
- `README-new.md` - 內容已整合到主 `README.md`
- `app/services/` - 功能已遷移到 `src/` 清晰架構

### 2. 移動的檔案
- `test_integration.py` → `tests/integration/test_integration.py`
- `test_core_functionality.py` → `tests/integration/test_core_functionality.py`
- `test_app.R` → `tests/r/test_app.R`

### 3. 主要入口點
- **Python CLI**: `python starlink.py` (主要推薦)
- **清晰架構 CLI**: `python src/interfaces/cli/main.py`
- **Shiny 網頁介面**: `python starlink.py shiny` 或直接執行 `Rscript app.R`

### 4. 清晰架構說明
專案現在採用清晰架構設計：
```
src/
├── domain/         # 核心業務邏輯（實體、值物件、領域服務）
├── application/    # 應用層（用例、DTO）
├── infrastructure/ # 技術實作（外部服務、資料庫）
└── interfaces/     # 介面層（API、CLI、Shiny）
```

## 遷移建議

### 對於使用舊 API 的用戶
如果您的程式碼依賴 `app/services/`：
1. 檢查 `src/domain/services/` 和 `src/application/services/` 尋找對應功能
2. 更新 import 路徑
3. 參考 `tests/integration/` 下的測試案例了解新 API 用法

### 對於使用舊啟動腳本的用戶
- 將 `Rscript quick_start.R` 改為 `python starlink.py shiny`
- 將 `python run.py` 改為 `python starlink.py`

### 對於開發者
- 新功能請按照清晰架構原則添加到對應層級
- 測試檔案統一放在 `tests/` 目錄下
- 文檔更新請直接修改主 `README.md`