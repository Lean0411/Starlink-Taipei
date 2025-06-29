# MIT License
# Copyright (c) 2025 Starlink Taipei Analysis Team

# app.R - Clean Architecture Shiny UI Layer
# 這是一個純粹的展示層，通過 REST API 與應用層通信

library(shiny)
library(shinydashboard)
library(plotly)
library(DT)
library(httr)
library(jsonlite)

# 載入 UI 模組
source("ui_modules.R")
source("api_client.R")

# 定義 UI
ui <- dashboardPage(
  dashboardHeader(
    title = "Starlink 台北衛星分析系統",
    titleWidth = 350
  ),
  
  dashboardSidebar(
    sidebarMenu(
      menuItem("覆蓋分析", tabName = "coverage", icon = icon("satellite")),
      menuItem("即時追蹤", tabName = "tracking", icon = icon("map")),
      menuItem("統計報告", tabName = "stats", icon = icon("chart-bar")),
      menuItem("API 狀態", tabName = "api", icon = icon("server"))
    )
  ),
  
  dashboardBody(
    tags$head(
      tags$style(HTML("
        .content-wrapper, .right-side {
          background-color: #f4f4f4;
        }
      "))
    ),
    
    tabItems(
      # 覆蓋分析頁面
      tabItem(
        tabName = "coverage",
        coverage_analysis_ui("coverage")
      ),
      
      # 即時追蹤頁面
      tabItem(
        tabName = "tracking",
        real_time_tracking_ui("tracking")
      ),
      
      # 統計報告頁面
      tabItem(
        tabName = "stats",
        statistics_ui("stats")
      ),
      
      # API 狀態頁面
      tabItem(
        tabName = "api",
        api_status_ui("api")
      )
    )
  )
)

# 定義 Server
server <- function(input, output, session) {
  # 初始化 API 客戶端
  api_client <- ApiClient$new()
  
  # 載入各模組的 server 邏輯
  coverage_analysis_server("coverage", api_client)
  real_time_tracking_server("tracking", api_client)
  statistics_server("stats", api_client)
  api_status_server("api", api_client)
}

# 執行應用程式
shinyApp(ui = ui, server = server)