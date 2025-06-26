# MIT License
# Copyright (c) 2025 Starlink Taipei Analysis Team
#
# This file is part of the Starlink Taipei Satellite Analysis System.

# quick_start.R
# Starlink 台北衛星分析系統 - 統一簡化啟動腳本

cat("=== Starlink 台北衛星分析系統 ===\n")
cat("正在啟動簡化版用戶界面...\n\n")

# 設置編碼環境
Sys.setlocale("LC_ALL", "en_US.UTF-8")
options(encoding = "UTF-8")

if (Sys.info()["sysname"] == "Linux") {
  Sys.setenv(LANG = "en_US.UTF-8")
  Sys.setenv(LC_ALL = "en_US.UTF-8")
  Sys.setenv(LC_CTYPE = "en_US.UTF-8")
}

# 檢查並安裝必要套件
cat("正在檢查必要套件...\n")
required_packages <- c("shiny", "shinydashboard", "plotly", "DT", "ggplot2")

install_if_missing <- function(packages) {
  for (pkg in packages) {
    if (!require(pkg, character.only = TRUE, quietly = TRUE)) {
      cat(paste("正在安裝:", pkg, "\n"))
      install.packages(pkg, repos = "https://cran.rstudio.com/", 
                      dependencies = TRUE, quiet = TRUE)
      
      if (require(pkg, character.only = TRUE, quietly = TRUE)) {
        cat(paste("已成功安裝:", pkg, "\n"))
      } else {
        cat(paste("安裝失敗:", pkg, "\n"))
        return(FALSE)
      }
    } else {
      cat(paste("已載入:", pkg, "\n"))
    }
  }
  return(TRUE)
}

# 安裝套件
if (!install_if_missing(required_packages)) {
  cat("套件安裝失敗，嘗試使用基本功能...\n")
}

cat("\n正在載入應用程式...\n")

# 檢查並載入簡化版界面
if (file.exists("ui_simple.R") && file.exists("server_simple.R")) {
  cat("載入簡化版界面...\n")
  
  tryCatch({
    source("ui_simple.R")
    source("server_simple.R")
    
    cat("\n=== 啟動成功 ===\n")
    cat("功能特色:\n")
    cat("• 一鍵快速分析\n")
    cat("• 簡化的參數設置\n")
    cat("• 清晰的結果展示\n")
    cat("• 友好的用戶界面\n")
    
    cat("\n應用程式將在以下位址運行:\n")
    cat("• 本機訪問: http://localhost:3838\n")
    cat("• 網路訪問: http://0.0.0.0:3838\n")
    cat("\n按 Ctrl+C 停止服務\n")
    cat("========================\n\n")
    
    # 啟動應用
    shinyApp(ui = ui, server = server, options = list(
      host = "0.0.0.0",
      port = 3838,
      launch.browser = FALSE
    ))
    
  }, error = function(e) {
    cat(paste("載入簡化版界面失敗:", e$message, "\n"))
    cat("嘗試載入完整版界面...\n")
    
    # 回退到完整版
    if (file.exists("ui.R") && file.exists("server.R")) {
      source("ui.R")
      source("server.R")
      
      cat("已載入完整版界面\n")
      shinyApp(ui = ui, server = server, options = list(
        host = "0.0.0.0",
        port = 3838,
        launch.browser = FALSE
      ))
    } else {
      cat("錯誤: 找不到可用的界面文件\n")
      stop("No UI files found")
    }
  })
  
} else if (file.exists("ui.R") && file.exists("server.R")) {
  cat("簡化版不可用，載入完整版界面...\n")
  
  source("ui.R")
  source("server.R")
  
  cat("\n已載入完整版界面\n")
  cat("應用程式將在以下位址運行:\n")
  cat("• 本機訪問: http://localhost:3838\n")
  cat("• 網路訪問: http://0.0.0.0:3838\n")
  cat("\n按 Ctrl+C 停止服務\n\n")
  
  shinyApp(ui = ui, server = server, options = list(
    host = "0.0.0.0",
    port = 3838,
    launch.browser = FALSE
  ))
  
} else if (file.exists("app.R")) {
  cat("載入 app.R...\n")
  source("app.R")
  
} else {
  cat("錯誤: 找不到任何可用的應用文件\n")
  cat("請確保以下文件之一存在:\n")
  cat("• ui_simple.R + server_simple.R (推薦)\n")
  cat("• ui.R + server.R\n")
  cat("• app.R\n")
  stop("No application files found")
}