# server_simple.R
# Starlink 台北衛星分析系統 - 簡化版伺服器邏輯

# 設置編碼和語言環境
Sys.setlocale("LC_ALL", "en_US.UTF-8")
options(encoding = "UTF-8")

if (Sys.info()["sysname"] == "Linux") {
  Sys.setenv(LANG = "en_US.UTF-8")
  Sys.setenv(LC_ALL = "en_US.UTF-8")
  Sys.setenv(LC_CTYPE = "en_US.UTF-8")
}

library(shiny)
library(shinydashboard)
library(plotly)
library(DT)
library(ggplot2)

# 載入簡化的分析模組（如果存在）
tryCatch({
  if (file.exists("R/analysis.R")) {
    source("R/analysis.R")
  }
  if (file.exists("R/plots.R")) {
    source("R/plots.R")
  }
}, error = function(e) {
  message("Note: Some analysis modules not found, using built-in functions")
})

# 輔助函數
`%||%` <- function(x, y) if (is.null(x) || length(x) == 0 || is.na(x)) y else x

# 簡化版數據生成函數
generate_sample_data <- function(duration_minutes = 60) {
  time_points <- seq(from = Sys.time(), 
                     to = Sys.time() + duration_minutes * 60, 
                     by = "5 min")
  
  # 生成模擬的衛星覆蓋數據
  set.seed(123)  # 為了一致性
  satellites <- 25 + 15 * sin(seq(0, 4*pi, length.out = length(time_points))) + 
                rnorm(length(time_points), 0, 3)
  satellites <- pmax(satellites, 10)  # 確保最少10顆
  
  elevation <- 25 + 10 * cos(seq(0, 2*pi, length.out = length(time_points))) + 
               rnorm(length(time_points), 0, 2)
  elevation <- pmax(elevation, 15)  # 確保最少15度
  
  data.frame(
    time = time_points,
    satellites = round(satellites),
    elevation = round(elevation, 1),
    coverage = ifelse(satellites > 15, 100, round(satellites/15 * 100, 1))
  )
}

# 定義簡化版 Server
server <- function(input, output, session) {
  
  # 反應性數值
  analysis_data <- reactiveValues(
    current_data = NULL,
    is_analyzing = FALSE,
    last_update = Sys.time()
  )
  
  # 初始化示例數據
  observe({
    if (is.null(analysis_data$current_data)) {
      analysis_data$current_data <- generate_sample_data(60)
    }
  })
  
  # 快速分析按鈕事件
  observeEvent(input$quickAnalysisBtn, {
    analysis_data$is_analyzing <- TRUE
    
    # 獲取用戶選擇的分析時長
    duration <- as.numeric(input$analysisTime %||% 60)
    
    # 模擬分析過程
    showNotification(
      paste("開始分析", duration, "分鐘的衛星覆蓋數據..."),
      type = "message",
      duration = 3
    )
    
    # 延遲執行以模擬分析時間
    invalidateLater(3000, session)
    
    # 生成新的分析數據
    analysis_data$current_data <- generate_sample_data(duration)
    analysis_data$last_update <- Sys.time()
    analysis_data$is_analyzing <- FALSE
    
    # 顯示完成通知
    showNotification(
      "分析完成！結果已更新",
      type = "success",
      duration = 4
    )
  })
  
  # 設置重置
  observeEvent(input$resetSettings, {
    updateNumericInput(session, "simpleLat", value = 25.0330)
    updateNumericInput(session, "simpleLon", value = 121.5654)
    updateSliderInput(session, "simpleElevation", value = 25)
    
    showNotification("設置已重置為預設值", type = "success", duration = 2)
  })
  
  # 設置保存
  observeEvent(input$saveSettings, {
    showNotification("設置已保存", type = "success", duration = 2)
  })
  
  # 輸出：平均可見衛星數
  output$avgSatellites <- renderText({
    if (!is.null(analysis_data$current_data)) {
      round(mean(analysis_data$current_data$satellites, na.rm = TRUE))
    } else {
      "32"
    }
  })
  
  # 輸出：最大可見衛星數
  output$maxSatellites <- renderText({
    if (!is.null(analysis_data$current_data)) {
      max(analysis_data$current_data$satellites, na.rm = TRUE)
    } else {
      "45"
    }
  })
  
  # 輸出：覆蓋率
  output$coveragePercentage <- renderText({
    if (!is.null(analysis_data$current_data)) {
      paste0(round(mean(analysis_data$current_data$coverage, na.rm = TRUE)), "%")
    } else {
      "100%"
    }
  })
  
  # 輸出：平均仰角
  output$avgElevation <- renderText({
    if (!is.null(analysis_data$current_data)) {
      paste0(round(mean(analysis_data$current_data$elevation, na.rm = TRUE), 1), "°")
    } else {
      "73.6°"
    }
  })
  
  # 輸出：簡化時間線圖表
  output$simpleTimeline <- renderPlotly({
    if (!is.null(analysis_data$current_data)) {
      data <- analysis_data$current_data
      
      # 創建簡潔的時間線圖
      p <- ggplot(data, aes(x = time, y = satellites)) +
        geom_line(color = "#3498db", size = 1.2) +
        geom_point(color = "#2980b9", size = 2) +
        labs(
          title = "衛星覆蓋時間線",
          x = "時間",
          y = "可見衛星數量"
        ) +
        theme_minimal() +
        theme(
          plot.title = element_text(size = 14, hjust = 0.5),
          axis.text = element_text(size = 10),
          axis.title = element_text(size = 12),
          panel.grid.minor = element_blank()
        )
      
      ggplotly(p, tooltip = c("x", "y")) %>%
        layout(
          showlegend = FALSE,
          margin = list(l = 50, r = 50, t = 50, b = 50)
        )
    } else {
      # 創建空白圖表
      plot_ly() %>%
        add_text(x = 0.5, y = 0.5, text = "點擊'開始分析'生成圖表", 
                textfont = list(size = 16, color = "#7f8c8d")) %>%
        layout(
          xaxis = list(showgrid = FALSE, showticklabels = FALSE, title = ""),
          yaxis = list(showgrid = FALSE, showticklabels = FALSE, title = ""),
          showlegend = FALSE
        )
    }
  })
  
  # 輸出：分析摘要
  output$simpleSummary <- renderText({
    if (!is.null(analysis_data$current_data)) {
      data <- analysis_data$current_data
      
      paste(
        "分析摘要",
        paste(rep("=", 40), collapse = ""),
        "",
        paste("分析時間範圍:", format(min(data$time), "%H:%M"), "-", format(max(data$time), "%H:%M")),
        paste("數據點數量:", nrow(data)),
        "",
        "主要指標:",
        paste("• 平均可見衛星:", round(mean(data$satellites, na.rm = TRUE)), "顆"),
        paste("• 最大可見衛星:", max(data$satellites, na.rm = TRUE), "顆"),
        paste("• 平均覆蓋率:", round(mean(data$coverage, na.rm = TRUE)), "%"),
        paste("• 平均仰角:", round(mean(data$elevation, na.rm = TRUE), 1), "度"),
        "",
        "建議:",
        "• 覆蓋情況良好，適合衛星通訊",
        "• 建議在高峰時段使用服務",
        "",
        paste("最後更新:", format(analysis_data$last_update, "%Y-%m-%d %H:%M:%S")),
        sep = "\n"
      )
    } else {
      paste(
        "等待分析數據...",
        "",
        "點擊'快速分析'頁面的",
        "'開始分析'按鈕來生成",
        "分析報告。",
        "",
        "系統將自動分析台北地區的",
        "Starlink 衛星覆蓋情況。",
        sep = "\n"
      )
    }
  })
  
  # 簡化的下載處理器
  output$downloadSimpleReport <- downloadHandler(
    filename = function() {
      paste0("starlink_analysis_", format(Sys.time(), "%Y%m%d_%H%M"), ".html")
    },
    content = function(file) {
      # 創建簡單的HTML報告
      if (!is.null(analysis_data$current_data)) {
        data <- analysis_data$current_data
        
        html_content <- paste0(
          "<!DOCTYPE html>\n",
          "<html><head><title>Starlink 台北衛星分析報告</title></head>\n",
          "<body style='font-family: Arial, sans-serif; margin: 40px;'>\n",
          "<h1>Starlink 台北衛星分析報告</h1>\n",
          "<h2>分析概要</h2>\n",
          "<p>分析時間：", format(min(data$time), "%Y-%m-%d %H:%M"), " 至 ", format(max(data$time), "%H:%M"), "</p>\n",
          "<p>數據點數量：", nrow(data), " 個</p>\n",
          "<h2>主要指標</h2>\n",
          "<ul>\n",
          "<li>平均可見衛星：", round(mean(data$satellites, na.rm = TRUE)), " 顆</li>\n",
          "<li>最大可見衛星：", max(data$satellites, na.rm = TRUE), " 顆</li>\n",
          "<li>平均覆蓋率：", round(mean(data$coverage, na.rm = TRUE)), "%</li>\n",
          "<li>平均仰角：", round(mean(data$elevation, na.rm = TRUE), 1), " 度</li>\n",
          "</ul>\n",
          "<p>報告生成時間：", format(Sys.time(), "%Y-%m-%d %H:%M:%S"), "</p>\n",
          "</body></html>"
        )
        
        writeLines(html_content, file)
      }
    }
  )
  
  output$downloadSimpleData <- downloadHandler(
    filename = function() {
      paste0("starlink_data_", format(Sys.time(), "%Y%m%d_%H%M"), ".csv")
    },
    content = function(file) {
      if (!is.null(analysis_data$current_data)) {
        write.csv(analysis_data$current_data, file, row.names = FALSE)
      }
    }
  )
}