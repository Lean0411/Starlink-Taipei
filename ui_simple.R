# ui_simple.R
# Starlink 台北衛星分析系統 - 簡化版用戶界面

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

# 定義簡化版 UI
ui <- dashboardPage(
  # Header - 簡化標題
  dashboardHeader(
    title = "Starlink 台北衛星分析系統",
    titleWidth = 350
  ),
  
  # Sidebar - 大幅簡化選單
  dashboardSidebar(
    width = 280,
    sidebarMenu(
      menuItem("快速分析", tabName = "quick_analysis", icon = icon("play-circle")),
      menuItem("結果查看", tabName = "results", icon = icon("chart-bar")),
      menuItem("簡單設置", tabName = "settings", icon = icon("cog"))
    ),
    
    # 系統狀態面板 - 移除過多 emoji
    div(style = "padding: 15px; margin-top: 20px; background: #34495e; border-radius: 8px; color: white;",
        h5("系統狀態", style = "margin-bottom: 15px; color: #ecf0f1;"),
        
        # 運行狀態
        div(style = "display: flex; align-items: center; margin-bottom: 8px;",
            span(style = "width: 10px; height: 10px; background: #27ae60; border-radius: 50%; margin-right: 8px;"),
            span("系統運行正常", style = "font-size: 0.9em;")
        ),
        
        # 當前分析
        div(style = "margin-bottom: 8px;",
            strong("衛星數量: "), 
            span(id = "sidebarSatCount", "7,500+", style = "color: #3498db;")
        ),
        
        # 最後更新
        div(style = "font-size: 0.8em; color: #bdc3c7; margin-top: 10px;",
            "最後更新: ", 
            span(id = "lastUpdate", format(Sys.time(), "%H:%M:%S"))
        )
    )
  ),
  
  # Body
  dashboardBody(
    # 自定義 CSS - 簡化樣式
    tags$head(
      tags$style(HTML("
        .content-wrapper, .right-side {
          background: #f4f6f9;
        }
        .box {
          box-shadow: 0 2px 8px rgba(0,0,0,0.1);
          border-radius: 8px;
          border: none;
        }
        .quick-action-card {
          background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
          color: white;
          border-radius: 12px;
          padding: 30px;
          margin-bottom: 20px;
          text-align: center;
          box-shadow: 0 4px 15px rgba(52, 152, 219, 0.3);
        }
        .result-card {
          background: white;
          border-radius: 8px;
          padding: 20px;
          margin-bottom: 15px;
          border-left: 4px solid #27ae60;
        }
        .metric-display {
          font-size: 2.5em;
          font-weight: bold;
          color: #2c3e50;
          margin-bottom: 5px;
        }
        .metric-label {
          color: #7f8c8d;
          font-size: 1.1em;
        }
        .start-button {
          background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%);
          border: none;
          color: white;
          padding: 15px 30px;
          font-size: 1.2em;
          border-radius: 8px;
          cursor: pointer;
          transition: all 0.3s ease;
        }
        .start-button:hover {
          transform: translateY(-2px);
          box-shadow: 0 4px 12px rgba(39, 174, 96, 0.3);
        }
        .simple-progress {
          background: #ecf0f1;
          border-radius: 10px;
          overflow: hidden;
          margin: 15px 0;
        }
        .simple-progress-bar {
          background: linear-gradient(90deg, #3498db, #2980b9);
          height: 20px;
          color: white;
          text-align: center;
          line-height: 20px;
          transition: width 0.3s ease;
        }
      "))
    ),
    
    # JavaScript 用於簡化的功能
    tags$script(HTML("
      $(document).ready(function() {
        // 更新時間戳
        function updateTimestamp() {
          var now = new Date();
          var timeString = now.toLocaleTimeString('zh-TW');
          $('#lastUpdate').text(timeString);
        }
        
        // 每30秒更新一次時間戳
        setInterval(updateTimestamp, 30000);
        
        // 快速分析按鈕處理
        $('#quickAnalysisBtn').on('click', function() {
          $('#analysisProgress').show();
          var progress = 0;
          var interval = setInterval(function() {
            progress += Math.random() * 15 + 5;
            if (progress >= 100) {
              progress = 100;
              clearInterval(interval);
              $('#progressText').text('分析完成！');
              setTimeout(function() {
                $('#analysisProgress').fadeOut();
                // 自動切換到結果頁面
                $('a[href=\"#shiny-tab-results\"]').click();
              }, 2000);
            }
            $('#progressBar').css('width', progress + '%').text(Math.round(progress) + '%');
          }, 200);
        });
      });
    ")),
    
    tabItems(
      # 快速分析頁面
      tabItem(tabName = "quick_analysis",
        fluidRow(
          column(12,
            div(class = "quick-action-card",
                h2("一鍵衛星分析", style = "margin-top: 0;"),
                p("點擊下方按鈕開始分析台北地區的 Starlink 衛星覆蓋情況", style = "font-size: 1.1em; margin-bottom: 25px;"),
                
                # 簡化的時間選擇
                div(style = "margin-bottom: 20px;",
                    h4("分析時長選擇："),
                    selectInput("analysisTime", "", 
                                choices = list(
                                  "快速分析 (30分鐘)" = 30,
                                  "標準分析 (60分鐘)" = 60,
                                  "詳細分析 (120分鐘)" = 120
                                ), 
                                selected = 60,
                                width = "300px")
                ),
                
                # 一鍵開始按鈕
                actionButton("quickAnalysisBtn", "開始分析", 
                             class = "start-button",
                             style = "width: 250px; height: 60px;")
            )
          )
        ),
        
        # 進度顯示
        fluidRow(
          column(12,
            div(id = "analysisProgress", style = "display: none; margin-top: 20px;",
                box(
                  title = "分析進度", status = "primary", solidHeader = TRUE, width = 12,
                  div(class = "simple-progress",
                      div(id = "progressBar", class = "simple-progress-bar", style = "width: 0%;", "0%")
                  ),
                  div(id = "progressText", style = "text-align: center; margin-top: 10px; color: #7f8c8d;", 
                      "正在分析衛星軌道數據...")
                )
            )
          )
        )
      ),
      
      # 結果查看頁面
      tabItem(tabName = "results",
        # 核心指標卡片
        fluidRow(
          column(3,
            div(class = "result-card",
                div(class = "metric-display", textOutput("avgSatellites")),
                div(class = "metric-label", "平均可見衛星")
            )
          ),
          column(3,
            div(class = "result-card",
                div(class = "metric-display", textOutput("maxSatellites")),
                div(class = "metric-label", "最大可見衛星")
            )
          ),
          column(3,
            div(class = "result-card", 
                div(class = "metric-display", textOutput("coveragePercentage")),
                div(class = "metric-label", "覆蓋率")
            )
          ),
          column(3,
            div(class = "result-card",
                div(class = "metric-display", textOutput("avgElevation")),
                div(class = "metric-label", "平均仰角")
            )
          )
        ),
        
        # 圖表展示
        fluidRow(
          box(
            title = "衛星覆蓋時間線", status = "primary", solidHeader = TRUE,
            width = 8,
            plotlyOutput("simpleTimeline", height = "400px")
          ),
          
          box(
            title = "分析摘要", status = "info", solidHeader = TRUE,
            width = 4,
            verbatimTextOutput("simpleSummary")
          )
        ),
        
        # 數據下載
        fluidRow(
          box(
            title = "下載結果", status = "success", solidHeader = TRUE,
            width = 12,
            div(style = "text-align: center; padding: 20px;",
                downloadButton("downloadSimpleReport", "下載分析報告", 
                               class = "btn-success", 
                               style = "margin: 10px; padding: 10px 20px;"),
                downloadButton("downloadSimpleData", "下載數據", 
                               class = "btn-info", 
                               style = "margin: 10px; padding: 10px 20px;")
            )
          )
        )
      ),
      
      # 簡單設置頁面
      tabItem(tabName = "settings",
        fluidRow(
          box(
            title = "基本設置", status = "primary", solidHeader = TRUE,
            width = 8,
            
            h4("觀測位置"),
            p("預設為台北市中心，一般用戶無需修改", style = "color: #7f8c8d;"),
            fluidRow(
              column(6,
                numericInput("simpleLat", "緯度：", 
                             value = 25.0330, 
                             min = 24, max = 26, step = 0.01)
              ),
              column(6,
                numericInput("simpleLon", "經度：", 
                             value = 121.5654, 
                             min = 120, max = 123, step = 0.01)
              )
            ),
            
            hr(),
            
            h4("分析參數"),
            p("建議使用預設值，除非有特殊需求", style = "color: #7f8c8d;"),
            sliderInput("simpleElevation", "最小衛星仰角 (度)：",
                        min = 10, max = 45, value = 25, step = 5),
            
            div(style = "margin-top: 20px;",
                actionButton("resetSettings", "重置為預設值", 
                             class = "btn-warning"),
                actionButton("saveSettings", "保存設置", 
                             class = "btn-primary", 
                             style = "margin-left: 10px;")
            )
          ),
          
          box(
            title = "設置說明", status = "info", solidHeader = TRUE,
            width = 4,
            div(style = "padding: 10px;",
                h5("參數說明："),
                tags$ul(
                  tags$li(strong("緯度/經度："), "觀測位置座標"),
                  tags$li(strong("最小仰角："), "衛星需要高於此角度才會被計算"),
                  tags$li(strong("建議值："), "25度以上確保良好信號品質")
                ),
                
                hr(),
                
                h5("預設位置："),
                p("台北市中心 (25.033°N, 121.565°E)", style = "font-family: monospace;"),
                p("涵蓋範圍：大台北地區", style = "color: #7f8c8d;")
            )
          )
        )
      )
    )
  )
)