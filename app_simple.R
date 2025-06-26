# MIT License
# Copyright (c) 2025 Starlink Taipei Analysis Team
#
# This file is part of the Starlink Taipei Satellite Analysis System.

# app_simple.R
# Starlink 台北衛星分析系統 - 簡化版主應用檔案

# 載入必要的庫
library(shiny)
library(shinydashboard)
library(plotly)
library(DT)
library(ggplot2)

# 設置編碼環境
Sys.setlocale("LC_ALL", "en_US.UTF-8")
options(encoding = "UTF-8")

if (Sys.info()["sysname"] == "Linux") {
  Sys.setenv(LANG = "en_US.UTF-8")
  Sys.setenv(LC_ALL = "en_US.UTF-8")
  Sys.setenv(LC_CTYPE = "en_US.UTF-8")
}

# 確保輸出目錄存在
if (!dir.exists("output")) {
  dir.create("output", recursive = TRUE)
}

# 載入簡化版 UI 和 Server
source("ui_simple.R")
source("server_simple.R")

# 執行應用程式
shinyApp(ui = ui, server = server)