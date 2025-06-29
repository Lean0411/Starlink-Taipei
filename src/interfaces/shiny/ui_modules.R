# ui_modules.R - Shiny UI 模組
# 包含各個功能模組的 UI 定義

# 覆蓋分析 UI 模組
coverage_analysis_ui <- function(id) {
  ns <- NS(id)
  
  fluidRow(
    # 參數設定面板
    box(
      width = 4,
      title = "分析參數",
      status = "primary",
      solidHeader = TRUE,
      
      dateRangeInput(
        ns("date_range"),
        "分析時間範圍",
        start = Sys.Date(),
        end = Sys.Date() + 1,
        format = "yyyy-mm-dd"
      ),
      
      sliderInput(
        ns("time_step"),
        "時間步長（分鐘）",
        min = 10,
        max = 120,
        value = 60,
        step = 10
      ),
      
      sliderInput(
        ns("elevation_mask"),
        "最小仰角（度）",
        min = 0,
        max = 90,
        value = 25,
        step = 5
      ),
      
      h4("觀察者位置"),
      numericInput(ns("latitude"), "緯度", value = 25.0330, step = 0.001),
      numericInput(ns("longitude"), "經度", value = 121.5654, step = 0.001),
      numericInput(ns("altitude"), "高度（公尺）", value = 0, step = 10),
      
      actionButton(
        ns("analyze"),
        "開始分析",
        class = "btn-primary",
        style = "width: 100%;"
      )
    ),
    
    # 結果顯示面板
    box(
      width = 8,
      title = "分析結果",
      status = "info",
      solidHeader = TRUE,
      
      tabsetPanel(
        tabPanel(
          "覆蓋統計",
          br(),
          valueBoxOutput(ns("total_satellites")),
          valueBoxOutput(ns("avg_coverage")),
          valueBoxOutput(ns("max_coverage")),
          br(),
          plotlyOutput(ns("coverage_timeline"), height = "400px")
        ),
        
        tabPanel(
          "衛星分布",
          br(),
          plotlyOutput(ns("satellite_distribution"), height = "500px")
        ),
        
        tabPanel(
          "詳細數據",
          br(),
          DTOutput(ns("coverage_data"))
        )
      )
    )
  )
}

# 即時追蹤 UI 模組
real_time_tracking_ui <- function(id) {
  ns <- NS(id)
  
  fluidRow(
    box(
      width = 12,
      title = "即時衛星追蹤",
      status = "success",
      solidHeader = TRUE,
      
      fluidRow(
        column(
          width = 3,
          selectInput(
            ns("satellite_select"),
            "選擇衛星",
            choices = c("載入中..."),
            multiple = TRUE
          ),
          
          actionButton(
            ns("refresh"),
            "更新位置",
            icon = icon("sync"),
            class = "btn-success"
          )
        ),
        
        column(
          width = 9,
          plotlyOutput(ns("tracking_map"), height = "500px")
        )
      ),
      
      hr(),
      
      DTOutput(ns("tracking_data"))
    )
  )
}

# 統計報告 UI 模組
statistics_ui <- function(id) {
  ns <- NS(id)
  
  fluidRow(
    box(
      width = 12,
      title = "統計報告",
      status = "warning",
      solidHeader = TRUE,
      
      dateRangeInput(
        ns("stats_date_range"),
        "統計時間範圍",
        start = Sys.Date() - 7,
        end = Sys.Date(),
        format = "yyyy-mm-dd"
      ),
      
      actionButton(
        ns("generate_stats"),
        "生成報告",
        icon = icon("chart-bar"),
        class = "btn-warning"
      ),
      
      hr(),
      
      fluidRow(
        column(
          width = 6,
          plotlyOutput(ns("coverage_histogram"), height = "300px")
        ),
        column(
          width = 6,
          plotlyOutput(ns("satellite_activity"), height = "300px")
        )
      ),
      
      hr(),
      
      DTOutput(ns("statistics_table"))
    )
  )
}

# API 狀態 UI 模組
api_status_ui <- function(id) {
  ns <- NS(id)
  
  fluidRow(
    box(
      width = 12,
      title = "API 狀態",
      status = "danger",
      solidHeader = TRUE,
      
      fluidRow(
        column(
          width = 6,
          h4("連接狀態"),
          verbatimTextOutput(ns("api_status")),
          br(),
          actionButton(
            ns("check_status"),
            "檢查連接",
            icon = icon("plug"),
            class = "btn-danger"
          )
        ),
        
        column(
          width = 6,
          h4("API 端點"),
          tableOutput(ns("api_endpoints"))
        )
      )
    )
  )
}

# Server 邏輯函數
coverage_analysis_server <- function(id, api_client) {
  moduleServer(id, function(input, output, session) {
    # 分析結果
    analysis_results <- reactiveVal()
    
    observeEvent(input$analyze, {
      withProgress(message = '執行覆蓋分析...', {
        results <- api_client$analyze_coverage(
          start_time = paste0(input$date_range[1], "T00:00:00Z"),
          end_time = paste0(input$date_range[2], "T00:00:00Z"),
          time_step_minutes = input$time_step,
          elevation_mask = input$elevation_mask,
          observer_lat = input$latitude,
          observer_lon = input$longitude,
          observer_alt = input$altitude
        )
        
        if (!is.null(results$error)) {
          showNotification(results$error, type = "error")
        } else {
          analysis_results(results)
          showNotification("分析完成", type = "success")
        }
      })
    })
    
    # 渲染輸出
    output$total_satellites <- renderValueBox({
      results <- analysis_results()
      if (is.null(results)) {
        valueBox(0, "總衛星數", icon = icon("satellite"))
      } else {
        valueBox(
          length(unique(results$satellites)),
          "總衛星數",
          icon = icon("satellite"),
          color = "blue"
        )
      }
    })
    
    output$avg_coverage <- renderValueBox({
      results <- analysis_results()
      if (is.null(results)) {
        valueBox(0, "平均覆蓋", icon = icon("signal"))
      } else {
        valueBox(
          round(mean(results$coverage_percentage), 2),
          "平均覆蓋率 %",
          icon = icon("signal"),
          color = "green"
        )
      }
    })
    
    output$max_coverage <- renderValueBox({
      results <- analysis_results()
      if (is.null(results)) {
        valueBox(0, "最大覆蓋", icon = icon("chart-line"))
      } else {
        valueBox(
          round(max(results$coverage_percentage), 2),
          "最大覆蓋率 %",
          icon = icon("chart-line"),
          color = "yellow"
        )
      }
    })
  })
}

real_time_tracking_server <- function(id, api_client) {
  moduleServer(id, function(input, output, session) {
    # 載入衛星列表
    satellites <- reactive({
      api_client$get_satellites()
    })
    
    observe({
      sat_list <- satellites()
      if (!is.null(sat_list) && !is.null(sat_list$satellites)) {
        updateSelectInput(
          session,
          "satellite_select",
          choices = sat_list$satellites
        )
      }
    })
    
    # 更新位置
    observeEvent(input$refresh, {
      showNotification("更新衛星位置...", type = "info")
    })
  })
}

statistics_server <- function(id, api_client) {
  moduleServer(id, function(input, output, session) {
    observeEvent(input$generate_stats, {
      showNotification("生成統計報告...", type = "info")
    })
  })
}

api_status_server <- function(id, api_client) {
  moduleServer(id, function(input, output, session) {
    observeEvent(input$check_status, {
      status <- api_client$check_health()
      
      output$api_status <- renderPrint({
        status
      })
      
      if (status$status == "healthy") {
        showNotification("API 連接正常", type = "success")
      } else {
        showNotification("API 連接失敗", type = "error")
      }
    })
    
    output$api_endpoints <- renderTable({
      data.frame(
        端點 = c("/health", "/coverage/analyze", "/satellites", "/statistics"),
        方法 = c("GET", "POST", "GET", "GET"),
        描述 = c("健康檢查", "覆蓋分析", "衛星列表", "統計資訊")
      )
    })
  })
}