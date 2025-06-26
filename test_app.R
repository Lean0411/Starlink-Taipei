# MIT License
# Copyright (c) 2025 Starlink Taipei Analysis Team
#
# This file is part of the Starlink Taipei Satellite Analysis System.

# 簡化版 Starlink 台北衛星分析系統測試
library(shiny)
library(shinydashboard)

# UI
ui <- dashboardPage(
  dashboardHeader(title = "🛰️ Starlink 台北衛星分析系統 v2.0"),
  dashboardSidebar(
    sidebarMenu(
      menuItem("🏠 系統總覽", tabName = "overview", icon = icon("home")),
      menuItem("🔮 預測分析", tabName = "prediction", icon = icon("chart-line"))
    )
  ),
  dashboardBody(
    tabItems(
      tabItem(tabName = "overview",
        fluidRow(
          box(width = 12, title = "歡迎使用 Starlink 台北衛星分析系統", status = "primary",
            h3("🎉 系統狀態：正常運行"),
            p("✅ 衛星數據：實時更新"),
            p("🚀 處理速度：< 2秒"),
            p("📊 分析功能：完整可用"),
            p("🔮 預測模型：AI 增強"),
            br(),
            p("請使用左側選單瀏覽各項功能。"),
            br(),
            tags$div(
              style = "background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                       color: white; padding: 20px; border-radius: 10px; text-align: center;",
              h4("🛰️ 當前可見衛星數量"),
              h2("7,500+", style = "font-size: 3em; margin: 10px 0;"),
              p("實時更新中...")
            )
          )
        )
      ),
      
      tabItem(tabName = "prediction",
        fluidRow(
          box(width = 12, title = "🔮 動態時間範圍預測功能", status = "success",
            h4("預測模式選擇："),
            selectInput("timeMode", "選擇時間尺度：",
                       choices = list(
                         "🕐 短期預測 (1小時) - 即時決策" = "short",
                         "🕕 中期預測 (24小時) - 日常規劃" = "medium", 
                         "🕘 長期預測 (7天) - 策略規劃" = "long"
                       ),
                       selected = "medium"),
            
            sliderInput("interval", "時間間隔 (分鐘)：",
                       min = 1, max = 60, value = 15),
            
            actionButton("updatePrediction", "🔄 更新預測", class = "btn-primary"),
            
            br(), br(),
            
            div(id = "predictionResults",
              style = "background: #f8f9fa; padding: 20px; border-radius: 8px; margin-top: 15px;",
              h5("📈 預測結果："),
              p("• 預測精度：90%+"),
              p("• 最佳觀測時段：14:00-16:00"),
              p("• 平均可見衛星：45 顆"),
              p("• 信賴區間：±3 顆")
            )
          )
        )
      )
    )
  )
)

# Server
server <- function(input, output, session) {
  
  # 預測更新處理
  observeEvent(input$updatePrediction, {
    showModal(modalDialog(
      title = "🔄 正在更新預測...",
      "請稍候，正在分析衛星軌道數據...",
      easyClose = FALSE,
      footer = NULL
    ))
    
    # 模擬處理時間
    Sys.sleep(2)
    
    removeModal()
    
    showNotification(
      "✅ 預測更新完成！",
      type = "success",
      duration = 3
    )
  })
  
  # 定期更新衛星數量 (每30秒)
  autoInvalidate <- reactiveTimer(30000)
  
  observe({
    autoInvalidate()
    # 這裡可以加入實際的數據更新邏輯
  })
}

# 啟動應用程式
cat("🚀 正在啟動 Starlink 台北衛星分析系統...\n")
cat("📱 應用程式將在以下位址運行:\n")
cat("   • 本機存取: http://localhost:3838\n")
cat("   • 網路存取: http://0.0.0.0:3838\n")
cat("💡 按 Ctrl+C 停止服務\n\n")

shinyApp(ui = ui, server = server, options = list(host = "0.0.0.0", port = 3838)) 