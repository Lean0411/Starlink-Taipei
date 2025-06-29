#!/usr/bin/env Rscript
# run_app.R - 啟動 Shiny 應用的腳本

# 檢查必要套件
required_packages <- c("shiny", "shinydashboard", "plotly", "DT", "httr", "jsonlite", "R6")

missing_packages <- required_packages[!(required_packages %in% installed.packages()[,"Package"])]

if(length(missing_packages) > 0) {
  cat("缺少以下套件：", paste(missing_packages, collapse = ", "), "\n")
  cat("正在安裝...\n")
  install.packages(missing_packages, repos = "https://cloud.r-project.org/")
}

# 載入 shiny
library(shiny)

# 設定端口（可通過環境變數覆蓋）
port <- as.numeric(Sys.getenv("SHINY_PORT", "3838"))

# 設定主機（可通過環境變數覆蓋）
host <- Sys.getenv("SHINY_HOST", "127.0.0.1")

# API URL（可通過環境變數覆蓋）
api_url <- Sys.getenv("API_URL", "http://localhost:8000")

cat("啟動 Starlink Taipei Shiny UI...\n")
cat("主機:", host, "\n")
cat("端口:", port, "\n")
cat("API URL:", api_url, "\n")

# 執行應用
runApp("app.R", host = host, port = port, launch.browser = TRUE)