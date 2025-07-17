# Starlink Taipei - Shiny UI Layer

這是 Starlink Taipei 專案的 Shiny UI 層，遵循清晰架構原則設計。

## 架構概述

這個 Shiny 應用是一個純粹的展示層，通過 REST API 與後端應用層通信：

```
Shiny UI (展示層)
    ↓
REST API Client
    ↓
FastAPI Backend (應用層)
    ↓
Domain Services (領域層)
```

## 功能模組

1. **覆蓋分析** - 分析衛星覆蓋範圍
2. **即時追蹤** - 追蹤衛星即時位置
3. **統計報告** - 生成統計分析報告
4. **API 狀態** - 監控後端 API 健康狀態

## 安裝與執行

### 前置需求

```R
# 安裝必要的 R 套件
install.packages(c(
  "shiny",
  "shinydashboard",
  "plotly",
  "DT",
  "httr",
  "jsonlite",
  "R6"
))
```

### 執行步驟

1. 確保後端 API 正在運行：
```bash
# 在專案根目錄執行
cd ../../../
python -m uvicorn src.interfaces.api.app:app --reload
```

2. 啟動 Shiny 應用：
```R
# 在 R 中執行
setwd("src/interfaces/shiny")
shiny::runApp("app.R", port = 3838)
```

## 配置

預設 API 端點為 `http://localhost:8000`。如需修改，請編輯 `api_client.R` 中的 `base_url` 參數。

## 開發指南

### 新增功能模組

1. 在 `ui_modules.R` 中新增 UI 函數：
```R
new_feature_ui <- function(id) {
  ns <- NS(id)
  # UI 定義
}
```

2. 在 `ui_modules.R` 中新增 Server 函數：
```R
new_feature_server <- function(id, api_client) {
  moduleServer(id, function(input, output, session) {
    # Server 邏輯
  })
}
```

3. 在 `app.R` 中註冊模組：
```R
# UI 部分
tabItem(
  tabName = "new_feature",
  new_feature_ui("new_feature")
)

# Server 部分
new_feature_server("new_feature", api_client)
```

### API 客戶端擴展

在 `api_client.R` 中新增方法來呼叫新的 API 端點：

```R
new_api_method = function(params) {
  tryCatch({
    response <- GET/POST(
      paste0(self$base_url, "/new/endpoint"),
      # 參數設定
    )
    # 處理回應
  }, error = function(e) {
    return(list(error = toString(e)))
  })
}
```

## 注意事項

1. 此 UI 層不包含任何業務邏輯
2. 所有計算和處理都在後端進行
3. UI 只負責展示和用戶交互
4. 錯誤處理應該優雅地顯示給用戶