# MIT License
# Copyright (c) 2025 Starlink Taipei Analysis Team
#
# This file is part of the Starlink Taipei Satellite Analysis System.

# Starlink 台北衛星分析系統啟動腳本
cat("正在啟動 Starlink 台北衛星分析系統...\n")

# 檢查並安裝必要的套件
required_packages <- c("shiny", "shinydashboard", "plotly", "DT", "ggplot2", "dplyr", "scales", "jsonlite")

for (pkg in required_packages) {
  if (!require(pkg, character.only = TRUE, quietly = TRUE)) {
    cat(paste("正在安裝套件:", pkg, "\n"))
    install.packages(pkg, repos = "https://cran.rstudio.com/", dependencies = TRUE)
    library(pkg, character.only = TRUE)
  }
}

# 檢查 reticulate (Python 介面，可選)
if (!require("reticulate", quietly = TRUE)) {
  cat("注意: reticulate 套件未安裝，部分 Python 功能可能無法使用\n")
}

# 確保輸出目錄存在
if (!dir.exists("output")) {
  dir.create("output", recursive = TRUE)
  cat("已創建 output 目錄\n")
}

# 載入應用程式文件
if (file.exists("app.R")) {
  cat("載入 app.R...\n")
  source("app.R")
} else if (file.exists("ui.R") && file.exists("server.R")) {
  cat("載入 ui.R 和 server.R...\n")
  source("ui.R")
  source("server.R")
  
  # 啟動應用程式
  cat("🚀 正在啟動 Starlink 台北衛星分析系統...\n")
  cat("📱 應用程式將在以下位址運行:\n")
  cat("   • 本機存取: http://localhost:3838\n")
  cat("   • 網路存取: http://0.0.0.0:3838\n")
  cat("💡 按 Ctrl+C 停止服務\n")
  
  shinyApp(ui = ui, server = server, options = list(host = "0.0.0.0", port = 3838))
} else {
  cat("錯誤: 找不到 app.R 或 ui.R/server.R 文件\n")
} 