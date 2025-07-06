# Legacy Code

此目錄包含專案的舊版本程式碼，這些檔案正在被新的 Clean Architecture 實作所取代。

## 目錄結構

- `python/` - 舊版 Python 腳本
  - `starlink.py` - 原始的衛星追蹤腳本
  - `satellite_analysis.py` - 衛星分析功能
  - `simple_analysis.py` - 簡化版分析腳本

- `r/` - 舊版 R Shiny 應用程式
  - `app.R`, `app_simple.R` - Shiny 應用程式主檔案
  - `server.R`, `server_simple.R` - 伺服器邏輯
  - `ui.R`, `ui_simple.R` - 使用者介面
  - `R/` - R 分析腳本

## 注意事項

這些檔案保留作為參考，但不再是主要開發的一部分。新功能應該在 `src/` 目錄下的 Clean Architecture 結構中實作。