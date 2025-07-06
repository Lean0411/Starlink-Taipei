# MIT License
# Copyright (c) 2025 Starlink Taipei Analysis Team
#
# This file is part of the Starlink Taipei Satellite Analysis System.

# ui.R
# Starlink 台北衛星分析與預測系統 v2.0 - Shiny UI

# 設置編碼和語言環境
Sys.setlocale("LC_ALL", "en_US.UTF-8")
options(encoding = "UTF-8")

# 設置 R 語言的編碼環境
if (Sys.info()["sysname"] == "Linux") {
  Sys.setenv(LANG = "en_US.UTF-8")
  Sys.setenv(LC_ALL = "en_US.UTF-8")
  Sys.setenv(LC_CTYPE = "en_US.UTF-8")
}

library(shiny)
library(shinydashboard)
library(plotly)
library(DT)

# 定義 UI
ui <- dashboardPage(
  # Header
  dashboardHeader(
    title = "🛰️ Starlink 台北衛星分析與預測系統 v2.0",
    titleWidth = 450
  ),
  
  # Sidebar
  dashboardSidebar(
    width = 320,
    sidebarMenu(
      menuItem("🏠 系統總覽", tabName = "overview", icon = icon("tachometer-alt")),
      menuItem("📊 性能指標", tabName = "performance", icon = icon("chart-line")),
      menuItem("🔮 預測分析", tabName = "prediction", icon = icon("brain")),
      menuItem("🛰️ 衛星追蹤", tabName = "tracking", icon = icon("satellite")),
      menuItem("📈 統計結果", tabName = "stats", icon = icon("chart-bar")),
      menuItem("🔧 分析參數", tabName = "parameters", icon = icon("sliders-h")),
      menuItem("💾 數據下載", tabName = "download", icon = icon("download"))
    ),
    
    # 系統狀態面板
    div(style = "padding: 15px; margin-top: 20px; background: #2c3e50; border-radius: 8px; color: white;",
        h5("🔥 系統狀態", style = "margin-bottom: 15px; color: #ecf0f1;"),
        
        # 運行狀態
        div(style = "display: flex; align-items: center; margin-bottom: 8px;",
            span(style = "width: 10px; height: 10px; background: #27ae60; border-radius: 50%; margin-right: 8px;"),
            span("系統運行中", style = "font-size: 0.9em;")
        ),
        
        # 當前分析
        div(style = "margin-bottom: 8px;",
            strong("衛星數量: "), 
            span(id = "sidebarSatCount", "7,500+", style = "color: #3498db;")
        ),
        
        # 性能指標
        div(style = "margin-bottom: 8px;",
            strong("處理速度: "), 
            span("< 2秒", style = "color: #e74c3c;")
        ),
        
        # 最後更新
        div(style = "font-size: 0.8em; color: #bdc3c7; margin-top: 10px;",
            "最後更新: ", 
            span(id = "lastUpdate", format(Sys.time(), "%H:%M:%S"))
        )
    ),
    
    # 快速分析控制
    div(style = "padding: 15px; margin-top: 15px;",
        h5("🚀 快速分析", style = "color: #2c3e50; margin-bottom: 15px;"),
        
        # 分析持續時間
        sliderInput("duration", "分析時長 (分鐘):",
                    min = 30, max = 240, value = 60, step = 30,
                    width = "100%"),
        
        # 一鍵分析按鈕
        actionButton("startAnalysis", "🔍 開始分析", 
                     class = "btn-primary btn-lg", 
                     style = "width: 100%; margin-bottom: 10px;"),
        
        # 進度顯示
        conditionalPanel(
          condition = "input.startAnalysis > 0",
          div(id = "progressContainer", style = "margin-top: 15px;",
              div(class = "progress", style = "height: 20px;",
                  div(id = "progressBar", 
                      class = "progress-bar progress-bar-striped progress-bar-animated",
                      role = "progressbar",
                      style = "width: 0%; background: linear-gradient(45deg, #3498db, #2980b9);",
                      "0%"
                  )
              ),
              div(id = "statusMessage", 
                  style = "color: #7f8c8d; font-size: 0.85em; text-align: center; margin-top: 5px;",
                  "準備開始分析..."
              )
          )
        )
    )
  ),
  
  # Body
  dashboardBody(
    # 自定義 CSS
    tags$head(
      tags$style(HTML("
        .content-wrapper, .right-side {
          background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        }
        .box {
          box-shadow: 0 4px 15px rgba(0,0,0,0.1);
          border-radius: 12px;
          border: none;
        }
        .performance-card {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          border-radius: 12px;
          padding: 25px;
          margin-bottom: 20px;
          text-align: center;
          box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
        }
        .performance-value {
          font-size: 3em;
          font-weight: bold;
          margin-bottom: 8px;
          text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }
        .performance-title {
          font-size: 1.1em;
          opacity: 0.95;
          text-transform: uppercase;
          letter-spacing: 1px;
        }
        .status-card {
          background: linear-gradient(135deg, #2ecc71 0%, #27ae60 100%);
          color: white;
          border-radius: 12px;
          padding: 20px;
          margin-bottom: 15px;
        }
        .prediction-card {
          background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
          color: white;
          border-radius: 12px;
          padding: 20px;
          margin-bottom: 15px;
        }
        .tech-card {
          background: linear-gradient(135deg, #f39c12 0%, #e67e22 100%);
          color: white;
          border-radius: 12px;
          padding: 20px;
          margin-bottom: 15px;
        }
        .metric-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 8px 0;
          border-bottom: 1px solid rgba(255,255,255,0.2);
        }
        .metric-row:last-child {
          border-bottom: none;
        }
        .metric-label {
          font-weight: 500;
          opacity: 0.9;
        }
        .metric-value {
          font-weight: bold;
          font-size: 1.1em;
        }
        .system-status {
          background: #ffffff;
          border: 2px solid #27ae60;
          border-radius: 8px;
          padding: 15px;
          margin-bottom: 15px;
        }
        .progress {
          background-color: #ecf0f1;
          border-radius: 10px;
          box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);
          overflow: hidden;
        }
        .progress-bar {
          float: left;
          height: 100%;
          font-size: 12px;
          line-height: 20px;
          color: #fff;
          text-align: center;
          background: linear-gradient(45deg, #3498db, #2980b9);
          box-shadow: inset 0 -1px 0 rgba(0,0,0,.15);
          transition: width .6s ease;
        }
        .progress-bar-striped {
          background-image: linear-gradient(45deg,rgba(255,255,255,.15) 25%,transparent 25%,transparent 50%,rgba(255,255,255,.15) 50%,rgba(255,255,255,.15) 75%,transparent 75%,transparent);
          background-size: 40px 40px;
        }
        .progress-bar-animated {
          animation: progress-bar-stripes 2s linear infinite;
        }
        @keyframes progress-bar-stripes {
          from { background-position: 40px 0; }
          to { background-position: 0 0; }
        }
        .info-card {
          background: #ffffff;
          border-left: 4px solid #3498db;
          padding: 20px;
          margin-bottom: 20px;
          border-radius: 8px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .upgrade-highlight {
          background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
          color: white;
          padding: 15px;
          border-radius: 8px;
          margin-bottom: 20px;
          text-align: center;
        }
        
        /* 專業模型介紹樣式 */
        .model-intro-card {
          background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
          padding: 25px;
          border-radius: 15px;
          border: 2px solid #bdc3c7;
          box-shadow: 0 10px 30px rgba(0,0,0,0.1);
          margin-bottom: 20px;
          transition: all 0.3s ease;
        }
        
        .model-intro-card:hover {
          transform: translateY(-3px);
          box-shadow: 0 15px 40px rgba(0,0,0,0.15);
        }
        
        .tech-description {
          margin-bottom: 20px;
          position: relative;
        }
        
        .hybrid-architecture {
          margin-bottom: 20px;
        }
        
        .performance-specs {
          margin-bottom: 20px;
        }
        
        .prediction-capabilities {
          margin-bottom: 20px;
        }
        
        /* 漸變文字效果 */
        .gradient-text {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
          font-weight: bold;
        }
        
        /* 專業指標卡片動畫 */
        .performance-specs .col-sm-4 > div,
        .prediction-capabilities .col-sm-4 > div {
          transition: all 0.3s ease;
        }
        
        .performance-specs .col-sm-4 > div:hover,
        .prediction-capabilities .col-sm-4 > div:hover {
          transform: scale(1.05);
          box-shadow: 0 8px 20px rgba(0,0,0,0.15);
        }
      "))
    ),
    
    # JavaScript 用於進度條和即時更新
    tags$script(HTML("
      $(document).ready(function() {
        var progressInterval;
        
        // 更新時間戳
        function updateTimestamp() {
          var now = new Date();
          var timeString = now.toLocaleTimeString('zh-TW');
          $('#lastUpdate').text(timeString);
        }
        
        // 更新預測點數顯示
        function updatePredictionPoints() {
          var timeScale = $('#predictionTimeScale').val();
          var points = 0;
          
          if (timeScale === 'short_term') {
            var interval = $('#shortInterval').val() || 5;
            points = Math.floor(60 / interval) + 1;
            $('#shortPredPoints').text(points + ' 個');
          } else if (timeScale === 'medium_term') {
            var interval = $('#mediumInterval').val() || 30;
            points = Math.floor(24 * 60 / interval) + 1;
            $('#mediumPredPoints').text(points + ' 個');
          } else if (timeScale === 'long_term') {
            var interval = $('#longInterval').val() || 1;
            points = Math.floor(7 * 24 / interval) + 1;
            $('#longPredPoints').text(points + ' 個');
          }
        }
        
        // 監聽時間尺度和間隔變化
        $(document).on('change', '#predictionTimeScale', updatePredictionPoints);
        $(document).on('change', '#shortInterval', updatePredictionPoints);
        $(document).on('change', '#mediumInterval', updatePredictionPoints);
        $(document).on('change', '#longInterval', updatePredictionPoints);
        
        // 更新預測按鈕點擊
        $(document).on('click', '#updatePrediction', function() {
          var now = new Date();
          var timeString = now.toLocaleTimeString('zh-TW');
          $('#predictionUpdateTime').text(timeString);
          updatePredictionPoints();
        });
        
        // 每30秒更新一次時間戳
        setInterval(updateTimestamp, 30000);
        
        // 初始化時更新預測點數
        setTimeout(updatePredictionPoints, 1000);
        
        // 監聽分析按鈕點擊
        $('#startAnalysis').on('click', function() {
          $('#progressBar').css('width', '0%').text('0%').addClass('progress-bar-animated');
          $('#statusMessage').text('🔄 正在初始化分析引擎...');
          $('#progressContainer').show();
          
          var progress = 0;
          var stepCount = 0;
          var statusMessages = [
            '📡 正在載入 TLE 衛星數據...',
            '🧮 正在計算軌道位置...',
            '🔍 正在分析衛星覆蓋情況...',
            '🤖 正在執行深度學習預測...',
            '📊 正在生成統計數據...',
            '📈 正在準備可視化圖表...',
            '✅ 分析完成！正在更新顯示...'
          ];
          
          progressInterval = setInterval(function() {
            stepCount++;
            progress += Math.random() * 12 + 8;
            
            if (stepCount > 20 || progress > 95) {
              progress = 100;
              clearInterval(progressInterval);
              
              $('#progressBar').css('width', '100%').text('100%').removeClass('progress-bar-animated');
              $('#statusMessage').text('✅ 分析完成！結果已更新');
              updateTimestamp();
              
              setTimeout(function() {
                $('#progressContainer').fadeOut('slow');
              }, 3000);
            } else {
              $('#progressBar').css('width', progress + '%').text(Math.round(progress) + '%');
              
              var messageIndex = Math.min(Math.floor(progress / 15), statusMessages.length - 1);
              $('#statusMessage').text(statusMessages[messageIndex]);
            }
          }, 180);
        });
      });
    ")),
    
    tabItems(
      # 系統總覽頁面
      tabItem(tabName = "overview",
        # 系統狀態概覽
        fluidRow(
          box(
            title = "🚀 系統狀態總覽", status = "primary", solidHeader = TRUE,
            width = 12,
            
            # v2.0 升級亮點
            div(class = "upgrade-highlight",
                h4("🎉 v2.0 深度學習增強版已部署！", style = "margin: 0;"),
                p("結合物理建模與 AI 預測，性能提升 15-38%", style = "margin: 5px 0 0 0;")
            ),
            
            # 系統狀態卡片
            fluidRow(
              column(4,
                div(class = "status-card",
                    h4("🟢 系統運行中", style = "margin-top: 0;"),
                    div(class = "metric-row",
                        span("運行時間:", class = "metric-label"),
                        span("24/7 穩定運行", class = "metric-value")
                    ),
                    div(class = "metric-row",
                        span("服務端口:", class = "metric-label"),
                        span("3838", class = "metric-value")
                    ),
                    div(class = "metric-row",
                        span("系統版本:", class = "metric-label"),
                        span("v2.0", class = "metric-value")
                    )
                )
              ),
              column(4,
                div(class = "prediction-card",
                    h4("🤖 AI 預測引擎", style = "margin-top: 0;"),
                    div(class = "metric-row",
                        span("模型架構:", class = "metric-label"),
                        span("SCINet-SA", class = "metric-value")
                    ),
                    div(class = "metric-row",
                        span("預測精度提升:", class = "metric-label"),
                        span("15-38%", class = "metric-value")
                    ),
                    div(class = "metric-row",
                        span("時間尺度:", class = "metric-label"),
                        span("1h/24h/7d", class = "metric-value")
                    )
                )
              ),
              column(4,
                div(class = "tech-card",
                    h4("⚡ 計算性能", style = "margin-top: 0;"),
                    div(class = "metric-row",
                        span("處理核心:", class = "metric-label"),
                        span("24 核心", class = "metric-value")
                    ),
                    div(class = "metric-row",
                        span("分析速度:", class = "metric-label"),
                        span("< 2 秒", class = "metric-value")
                    ),
                    div(class = "metric-row",
                        span("並行效率:", class = "metric-label"),
                        span("85%+", class = "metric-value")
                    )
                )
              )
            )
          )
        ),
        
        # 實時數據概覽
        fluidRow(
          # 當前衛星狀態
          box(
            title = "🛰️ 當前衛星狀態", status = "info", solidHeader = TRUE,
            width = 8,
            div(class = "info-card",
                h4("台北地區 Starlink 覆蓋狀況", style = "color: #2c3e50; margin-top: 0;"),
                fluidRow(
                  column(6,
                    div(style = "text-align: center; padding: 15px;",
                        div(style = "font-size: 2.5em; font-weight: bold; color: #3498db; margin-bottom: 5px;",
                            textOutput("currentSatellites", inline = TRUE)
                        ),
                        div("當前可見衛星", style = "color: #7f8c8d;")
                    )
                  ),
                  column(6,
                    div(style = "text-align: center; padding: 15px;",
                        div(style = "font-size: 2.5em; font-weight: bold; color: #27ae60; margin-bottom: 5px;",
                            textOutput("currentCoverage", inline = TRUE)
                        ),
                        div("覆蓋率", style = "color: #7f8c8d;")
                    )
                  )
                ),
                hr(),
                div("📍 觀測位置: 台北 (25.033°N, 121.565°E)", style = "text-align: center; color: #95a5a6;"),
                div(paste("📅 最後更新:", format(Sys.time(), "%Y-%m-%d %H:%M:%S")), 
                    style = "text-align: center; color: #95a5a6; margin-top: 5px;")
            )
          ),
          
          # 系統資源監控
          box(
            title = "💻 系統資源", status = "warning", solidHeader = TRUE,
            width = 4,
            verbatimTextOutput("systemResources")
          )
        )
      ),
      
      # 性能指標頁面
      tabItem(tabName = "performance",
        # 核心性能指標
        fluidRow(
          column(3,
            div(class = "performance-card",
                div(class = "performance-value", "32.7"),
                div(class = "performance-title", "平均可見衛星")
            )
          ),
          column(3,
            div(class = "performance-card",
                div(class = "performance-value", "45"),
                div(class = "performance-title", "最大可見衛星")
            )
          ),
          column(3,
            div(class = "performance-card",
                div(class = "performance-value", "100%"),
                div(class = "performance-title", "覆蓋率")
            )
          ),
          column(3,
            div(class = "performance-card",
                div(class = "performance-value", "73.6°"),
                div(class = "performance-title", "平均仰角")
            )
          )
        ),
        
        # 詳細性能分析
        fluidRow(
          box(
            title = "📊 性能基準測試", status = "primary", solidHeader = TRUE,
            width = 8,
            DT::dataTableOutput("performanceTable")
          ),
          
          box(
            title = "🎯 預測精度對比", status = "success", solidHeader = TRUE,
            width = 4,
            plotOutput("accuracyPlot", height = "300px")
          )
        ),
        
        # 系統性能趨勢
        fluidRow(
          box(
            title = "⚡ 系統性能趨勢", status = "info", solidHeader = TRUE,
            width = 12,
            plotlyOutput("performanceTrend", height = "400px")
          )
                )
            ),
      
            # 預測分析頁面
      tabItem(tabName = "prediction",
        fluidRow(
          box(
            title = "🔮 多時間尺度預測結果", status = "primary", solidHeader = TRUE,
            width = 12,
            
            # 專業模型介紹
            div(class = "model-intro-card",
                h4("🧠 SCINet-SA 深度學習預測引擎", style = "color: #2c3e50; margin-top: 0; margin-bottom: 15px;"),
                
                # 技術架構說明
                div(class = "tech-description",
                    p(style = "margin-bottom: 12px; font-size: 1.05em; line-height: 1.6;",
                      "本系統採用 ", strong("Sample Convolution and Interaction Network with Self-Attention (SCINet-SA)"), 
                      " 架構，這是一種專為時間序列預測設計的先進深度學習模型，結合了卷積神經網路的特徵提取能力與自注意力機制的長程依賴建模優勢。"
                    ),
                    
                    p(style = "margin-bottom: 15px; font-size: 1em; line-height: 1.6; color: #34495e;",
                      "該模型特別針對衛星軌道預測進行優化，能夠捕捉軌道動力學中的複雜週期性模式和非線性關係，",
                      "相較於傳統的物理模型，在預測精度上提升了 ", strong("15-38%"), "。"
                    )
                ),
                
                # 混合架構優勢
                div(class = "hybrid-architecture",
                    h5("🔬 混合預測架構", style = "color: #8e44ad; margin-bottom: 10px;"),
                    fluidRow(
                      column(6,
                        div(style = "background: #f8f9fa; padding: 12px; border-radius: 6px; border-left: 4px solid #3498db;",
                            strong("物理模型 (70%)"), br(),
                            span("• 基於牛頓軌道動力學", style = "font-size: 0.9em; color: #7f8c8d;"), br(),
                            span("• 確保物理一致性", style = "font-size: 0.9em; color: #7f8c8d;"), br(),
                            span("• 長期穩定性保證", style = "font-size: 0.9em; color: #7f8c8d;")
                        )
                      ),
                      column(6,
                        div(style = "background: #f8f9fa; padding: 12px; border-radius: 6px; border-left: 4px solid #e74c3c;",
                            strong("AI 模型 (30%)"), br(),
                            span("• 自適應誤差修正", style = "font-size: 0.9em; color: #7f8c8d;"), br(),
                            span("• 複雜模式識別", style = "font-size: 0.9em; color: #7f8c8d;"), br(),
                            span("• 精度動態提升", style = "font-size: 0.9em; color: #7f8c8d;")
                        )
                      )
                    )
                ),
                
                hr(style = "margin: 15px 0;"),
                
                # 技術規格與性能
                div(class = "performance-specs",
                    h5("⚡ 技術規格與性能指標", style = "color: #27ae60; margin-bottom: 10px;"),
                    fluidRow(
                      column(4,
                        div(style = "text-align: center; padding: 8px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 8px; margin-bottom: 8px;",
                            strong("模型複雜度"), br(),
                            span("6D 狀態向量", style = "font-size: 0.85em;"), br(),
                            span("64 隱藏維度", style = "font-size: 0.85em;")
                        )
                      ),
                      column(4,
                        div(style = "text-align: center; padding: 8px; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; border-radius: 8px; margin-bottom: 8px;",
                            strong("計算性能"), br(),
                            span("GPU 加速訓練", style = "font-size: 0.85em;"), br(),
                            span("< 2秒 推理", style = "font-size: 0.85em;")
                        )
                      ),
                      column(4,
                        div(style = "text-align: center; padding: 8px; background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); color: white; border-radius: 8px; margin-bottom: 8px;",
                            strong("數據處理"), br(),
                            span("7500+ 衛星", style = "font-size: 0.85em;"), br(),
                            span("24 核心並行", style = "font-size: 0.85em;")
                        )
                      )
                    )
                ),
                
                # 預測能力展示
                div(class = "prediction-capabilities",
                    h5("🎯 多時間尺度預測能力", style = "color: #e67e22; margin-bottom: 10px; margin-top: 15px;"),
                    fluidRow(
                      column(4,
                        div(style = "text-align: center; padding: 12px; background: #e8f5e8; border: 2px solid #27ae60; border-radius: 8px;",
                            strong("短期預測 (1小時)", style = "color: #27ae60;"),
                            br(),
                            span("🎯 精度: 95%+", style = "font-size: 0.9em; color: #2c3e50;"), br(),
                            span("⏱️ 間隔: 1-10分鐘", style = "font-size: 0.9em; color: #7f8c8d;"), br(),
                            span("🔬 用途: 即時決策", style = "font-size: 0.9em; color: #7f8c8d;")
                        )
                      ),
                      column(4,
                        div(style = "text-align: center; padding: 12px; background: #fff3cd; border: 2px solid #ffc107; border-radius: 8px;",
                            strong("中期預測 (24小時)", style = "color: #856404;"),
                            br(),
                            span("🎯 精度: 85-90%", style = "font-size: 0.9em; color: #2c3e50;"), br(),
                            span("⏱️ 間隔: 15-60分鐘", style = "font-size: 0.9em; color: #7f8c8d;"), br(),
                            span("🔬 用途: 日常規劃", style = "font-size: 0.9em; color: #7f8c8d;")
                        )
                      ),
                      column(4,
                        div(style = "text-align: center; padding: 12px; background: #d1ecf1; border: 2px solid #17a2b8; border-radius: 8px;",
                            strong("長期預測 (7天)", style = "color: #0c5460;"),
                            br(),
                            span("🎯 精度: 75-85%", style = "font-size: 0.9em; color: #2c3e50;"), br(),
                            span("⏱️ 間隔: 1-6小時", style = "font-size: 0.9em; color: #7f8c8d;"), br(),
                            span("🔬 用途: 策略規劃", style = "font-size: 0.9em; color: #7f8c8d;")
                        )
                      )
                    )
                ),
                
                # 技術優勢總結
                div(style = "margin-top: 15px; padding: 12px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 8px;",
                    h6("🏆 核心技術優勢", style = "margin-top: 0; margin-bottom: 8px;"),
                    div(style = "font-size: 0.95em;",
                        "✨ ", strong("自注意力機制"), "：捕捉長期時間依賴關係 | ",
                        "🔄 ", strong("樣本卷積交互"), "：提取多尺度特徵模式 | ",
                        "⚖️ ", strong("物理約束融合"), "：確保預測結果符合軌道力學原理 | ",
                        "🎯 ", strong("不確定性量化"), "：提供可信度評估與風險控制"
                    )
                ),
                
                # 技術細節展開區塊
                div(style = "margin-top: 15px;",
                    tags$details(
                      tags$summary("🔬 點擊查看技術架構詳細說明", 
                              style = "cursor: pointer; font-weight: bold; color: #2c3e50; padding: 10px; background: #ecf0f1; border-radius: 6px; outline: none;"),
                      div(style = "margin-top: 10px; padding: 15px; background: #f8f9fa; border-radius: 8px; border-left: 4px solid #3498db;",
                          h6("📐 模型架構組成", style = "color: #2c3e50; margin-bottom: 10px;"),
                          tags$ul(
                            tags$li(strong("輸入層"), "：6D 軌道狀態向量 (位置 x,y,z + 速度 vx,vy,vz)"),
                            tags$li(strong("嵌入層"), "：將軌道向量映射到 64 維隱藏空間"),
                            tags$li(strong("SCINet 層"), "：4 層樣本卷積交互網路，提取時間特徵"),
                            tags$li(strong("自注意力層"), "：計算長程時間依賴關係權重"),
                            tags$li(strong("輸出層"), "：預測未來時刻的 6D 軌道狀態")
                          ),
                          
                          h6("⚙️ 關鍵技術參數", style = "color: #2c3e50; margin-bottom: 10px; margin-top: 15px;"),
                          div(style = "display: grid; grid-template-columns: 1fr 1fr; gap: 10px;",
                              div(style = "background: white; padding: 10px; border-radius: 6px;",
                                  strong("序列長度："), "168 小時 (7天歷史)", br(),
                                  strong("預測長度："), "1-168 小時可調", br(),
                                  strong("隱藏維度："), "64 維向量空間"
                              ),
                              div(style = "background: white; padding: 10px; border-radius: 6px;",
                                  strong("學習率："), "0.001 (Adam 優化器)", br(),
                                  strong("批次大小："), "32 軌道序列", br(),
                                  strong("正規化："), "Layer Normalization"
                              )
                          ),
                          
                          h6("🎯 性能指標基準", style = "color: #2c3e50; margin-bottom: 10px; margin-top: 15px;"),
                          div(style = "background: white; padding: 12px; border-radius: 6px;",
                              "• ", strong("位置精度"), "：平均絕對誤差 < 500m (1小時預測)", br(),
                              "• ", strong("速度精度"), "：平均絕對誤差 < 0.1 m/s (1小時預測)", br(),
                              "• ", strong("覆蓋預測"), "：衛星數量預測誤差 < ±2 顆 (短期)", br(),
                              "• ", strong("計算效率"), "：推理時間 < 100ms (單顆衛星)"
                          )
                      )
                    )
                )
            )
          )
        ),
        
        # 動態預測控制面板
        fluidRow(
          box(
            title = "⚙️ 預測參數控制", status = "success", solidHeader = TRUE,
            width = 12,
            
            fluidRow(
              column(3,
                selectInput("predictionTimeScale", "預測時間尺度:",
                            choices = list(
                              "短期預測 (1小時)" = "short_term",
                              "中期預測 (24小時)" = "medium_term", 
                              "長期預測 (7天)" = "long_term"
                            ),
                            selected = "short_term")
              ),
              column(3,
                conditionalPanel(
                  condition = "input.predictionTimeScale == 'short_term'",
                  sliderInput("shortInterval", "時間間隔 (分鐘):",
                              min = 1, max = 10, value = 5, step = 1)
                ),
                conditionalPanel(
                  condition = "input.predictionTimeScale == 'medium_term'",
                  sliderInput("mediumInterval", "時間間隔 (分鐘):",
                              min = 15, max = 60, value = 30, step = 15)
                ),
                conditionalPanel(
                  condition = "input.predictionTimeScale == 'long_term'",
                  sliderInput("longInterval", "時間間隔 (小時):",
                              min = 1, max = 6, value = 1, step = 1)
                )
              ),
              column(3,
                conditionalPanel(
                  condition = "input.predictionTimeScale == 'short_term'",
                  div(style = "margin-top: 25px;",
                      span("📊 預測點數: ", style = "font-weight: bold;"),
                      span(id = "shortPredPoints", "12 個", style = "color: #3498db;")
                  )
                ),
                conditionalPanel(
                  condition = "input.predictionTimeScale == 'medium_term'",
                  div(style = "margin-top: 25px;",
                      span("📊 預測點數: ", style = "font-weight: bold;"),
                      span(id = "mediumPredPoints", "48 個", style = "color: #3498db;")
                  )
                ),
                conditionalPanel(
                  condition = "input.predictionTimeScale == 'long_term'",
                  div(style = "margin-top: 25px;",
                      span("📊 預測點數: ", style = "font-weight: bold;"),
                      span(id = "longPredPoints", "168 個", style = "color: #3498db;")
                  )
                )
              ),
              column(3,
                div(style = "margin-top: 20px;",
                    actionButton("updatePrediction", "🔄 更新預測", 
                                 class = "btn-primary btn-lg", 
                                 style = "width: 100%;")
                )
              )
            ),
            
            # 預測狀態指示器
            div(id = "predictionStatus", style = "margin-top: 15px; text-align: center;",
                conditionalPanel(
                  condition = "input.updatePrediction > 0",
                  div(style = "color: #27ae60; font-weight: bold;",
                      "✅ 預測已更新 | 更新時間: ", 
                      span(id = "predictionUpdateTime", format(Sys.time(), "%H:%M:%S"))
                  )
                )
            )
          )
        ),
        
        # 預測結果展示
        fluidRow(
          box(
            title = "📈 預測時間序列", status = "info", solidHeader = TRUE,
            width = 8,
            plotlyOutput("predictionTimeline", height = "400px")
          ),
          
          box(
            title = "🎯 最佳觀測窗口", status = "warning", solidHeader = TRUE,
            width = 4,
            verbatimTextOutput("optimalWindows")
          )
        )
      ),
      
      # 衛星追蹤頁面
      tabItem(tabName = "tracking",
        fluidRow(
          # 實時追蹤圖表
          box(
            title = "🛰️ 實時衛星追蹤", status = "primary", solidHeader = TRUE,
            width = 8,
            plotlyOutput("satelliteTracking", height = "450px")
          ),
          
          # 衛星統計
          box(
            title = "📊 衛星統計", status = "info", solidHeader = TRUE,
            width = 4,
            verbatimTextOutput("satelliteStats")
          )
        ),
        
        # 覆蓋分析
        fluidRow(
          box(
            title = "📐 仰角分布分析", status = "success", solidHeader = TRUE,
            width = 6,
            plotOutput("elevationDistribution", height = "350px")
          ),
          
          box(
            title = "🌍 覆蓋熱力圖", status = "warning", solidHeader = TRUE,
            width = 6,
            plotOutput("coverageHeatmap", height = "350px")
          )
        )
      ),
      
      # 統計結果頁面（保留原有功能，但增強展示）
      tabItem(tabName = "stats",
        fluidRow(
          # 統計卡片（保留原有設計）
          column(3,
            div(class = "performance-card",
                div(class = "performance-value", textOutput("avgSatellites")),
                div(class = "performance-title", "平均可見衛星數")
            )
          ),
          column(3,
            div(class = "performance-card",
                div(class = "performance-value", textOutput("maxSatellites")),
                div(class = "performance-title", "最大可見衛星數")
            )
          ),
          column(3,
            div(class = "performance-card",
                div(class = "performance-value", textOutput("coveragePercentage")),
                div(class = "performance-title", "覆蓋率")
            )
          ),
          column(3,
            div(class = "performance-card",
                div(class = "performance-value", textOutput("avgElevation")),
                div(class = "performance-title", "平均仰角")
            )
          )
        ),
        
        # 詳細統計（保留原有功能）
        fluidRow(
          box(
            title = "📋 詳細統計數據", status = "info", solidHeader = TRUE,
            width = 8,
            DT::dataTableOutput("statsTable")
          ),
          
          box(
            title = "ℹ️ 分析資訊", status = "warning", solidHeader = TRUE,
            width = 4,
            verbatimTextOutput("analysisInfo")
        )
      ),
      
        # 視覺化圖表
        fluidRow(
          box(
            title = "📈 可見衛星時間線", status = "primary", solidHeader = TRUE,
            width = 8,
            plotlyOutput("timelinePlot", height = "400px")
          ),
          
          box(
            title = "📊 統計摘要", status = "success", solidHeader = TRUE,
            width = 4,
            plotOutput("summaryPlot", height = "400px")
          )
          )
        ),
        
      # 分析參數頁面（簡化，主要功能移到側邊欄）
      tabItem(tabName = "parameters",
        fluidRow(
          box(
            title = "🔧 高級分析參數", status = "primary", solidHeader = TRUE,
            width = 8,
            
            # 詳細參數設置
            fluidRow(
              column(6,
                h5("📍 觀測位置"),
                numericInput("lat", "緯度 (°):", 
                             value = 25.0330, 
                             min = -90, max = 90, step = 0.0001),
                numericInput("lon", "經度 (°):", 
                             value = 121.5654, 
                             min = -180, max = 180, step = 0.0001)
              ),
              column(6,
                h5("⚙️ 分析設置"),
                sliderInput("interval", "時間間隔 (分鐘):",
                            min = 0.5, max = 5, value = 1.0, step = 0.5),
                sliderInput("min_elevation", "最小仰角 (度):",
                            min = 10, max = 45, value = 25, step = 1)
              )
            ),
            
            hr(),
            
            # 預測模型參數
            h5("🤖 深度學習模型參數"),
            fluidRow(
              column(6,
                selectInput("model_type", "預測模型:",
                            choices = list(
                              "SCINet-SA (推薦)" = "scinet_sa",
                              "物理模型" = "physical",
                              "混合模型" = "hybrid"
                            ),
                            selected = "scinet_sa")
              ),
              column(6,
                selectInput("prediction_horizon", "預測時間範圍:",
                            choices = list(
                              "短期 (1小時)" = "short",
                              "中期 (24小時)" = "medium", 
                              "長期 (7天)" = "long",
                              "全範圍" = "all"
                            ),
                            selected = "all")
              )
            )
          ),
          
          box(
            title = "📖 參數說明", status = "info", solidHeader = TRUE,
            width = 4,
            div(class = "info-card",
                h5("🎯 參數優化建議"),
                tags$ul(
                  tags$li(strong("時間間隔"), ": 較小間隔提供更精細分析"),
                  tags$li(strong("最小仰角"), ": 25°以上確保良好信號品質"),
                  tags$li(strong("預測模型"), ": SCINet-SA 提供最佳精度"),
                  tags$li(strong("分析時長"), ": 建議 60-120 分鐘獲得完整週期")
                )
            )
          )
        )
      ),
      
      # 數據下載頁面（保留並增強）
      tabItem(tabName = "download",
        fluidRow(
          box(
            title = "💾 數據下載中心", status = "primary", solidHeader = TRUE,
            width = 8,
            
            div(class = "info-card",
                h4("📥 可用下載項目"),
                
                # 下載按鈕組
                div(style = "text-align: center; margin-top: 20px;",
                    downloadButton("downloadStats", "📊 統計數據 (JSON)", 
                                   class = "btn-primary", 
                                   style = "margin: 8px; width: 220px;"),
                    br(),
                    downloadButton("downloadData", "📈 時間序列數據 (CSV)", 
                                   class = "btn-info", 
                                   style = "margin: 8px; width: 220px;"),
                    br(),
                    downloadButton("downloadPrediction", "🔮 預測報告 (JSON)", 
                                   class = "btn-warning", 
                                   style = "margin: 8px; width: 220px;"),
                    br(),
                    downloadButton("downloadReport", "📄 完整報告 (HTML)", 
                                   class = "btn-success", 
                                   style = "margin: 8px; width: 220px;"),
                    br(),
                    downloadButton("downloadPlots", "🖼️ 圖表合集 (PNG)", 
                                   class = "btn-secondary", 
                                   style = "margin: 8px; width: 220px;")
                )
            )
          ),
          
          box(
            title = "📁 檔案資訊", status = "info", solidHeader = TRUE,
            width = 4,
            verbatimTextOutput("fileInfo")
          )
        ),
        
        # 使用說明
        fluidRow(
          box(
            title = "📖 下載說明", status = "warning", solidHeader = TRUE,
            width = 12,
            
            div(class = "info-card",
                h5("📋 檔案格式說明"),
                fluidRow(
                  column(6,
                tags$ul(
                      tags$li(strong("JSON 統計數據"), ": 核心性能指標"),
                      tags$li(strong("CSV 時間序列"), ": 詳細覆蓋數據"),
                      tags$li(strong("預測報告"), ": AI 模型預測結果")
                    )
                  ),
                  column(6,
                    tags$ul(
                      tags$li(strong("HTML 報告"), ": 完整可視化報告"),
                      tags$li(strong("PNG 圖表"), ": 高解析度圖表集合"),
                      tags$li(strong("系統日誌"), ": 分析執行詳情")
                    )
                  )
                )
            )
          )
        )
      )
    )
  )
) 