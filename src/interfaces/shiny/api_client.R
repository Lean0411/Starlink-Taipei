# api_client.R - REST API 客戶端
# 負責與後端 API 通信

library(R6)
library(httr)
library(jsonlite)

ApiClient <- R6Class("ApiClient",
  public = list(
    base_url = NULL,
    
    initialize = function(base_url = "http://localhost:8000") {
      self$base_url <- base_url
    },
    
    # 檢查 API 健康狀態
    check_health = function() {
      tryCatch({
        response <- GET(paste0(self$base_url, "/health"))
        if (status_code(response) == 200) {
          return(content(response, "parsed"))
        } else {
          return(list(status = "error", message = "API not available"))
        }
      }, error = function(e) {
        return(list(status = "error", message = toString(e)))
      })
    },
    
    # 分析衛星覆蓋
    analyze_coverage = function(start_time, end_time, time_step_minutes = 60,
                              elevation_mask = 25.0, observer_lat = 25.0330,
                              observer_lon = 121.5654, observer_alt = 0.0) {
      tryCatch({
        body <- list(
          start_time = start_time,
          end_time = end_time,
          time_step_minutes = time_step_minutes,
          elevation_mask = elevation_mask,
          observer = list(
            latitude = observer_lat,
            longitude = observer_lon,
            altitude = observer_alt
          )
        )
        
        response <- POST(
          paste0(self$base_url, "/coverage/analyze"),
          body = toJSON(body, auto_unbox = TRUE),
          content_type_json(),
          encode = "json"
        )
        
        if (status_code(response) == 200) {
          return(content(response, "parsed"))
        } else {
          return(list(error = paste("API error:", status_code(response))))
        }
      }, error = function(e) {
        return(list(error = toString(e)))
      })
    },
    
    # 獲取衛星列表
    get_satellites = function() {
      tryCatch({
        response <- GET(paste0(self$base_url, "/satellites"))
        if (status_code(response) == 200) {
          return(content(response, "parsed"))
        } else {
          return(list(error = "Failed to fetch satellites"))
        }
      }, error = function(e) {
        return(list(error = toString(e)))
      })
    },
    
    # 獲取特定衛星的位置
    get_satellite_position = function(satellite_id, time) {
      tryCatch({
        response <- GET(
          paste0(self$base_url, "/satellites/", satellite_id, "/position"),
          query = list(time = time)
        )
        if (status_code(response) == 200) {
          return(content(response, "parsed"))
        } else {
          return(list(error = "Failed to fetch position"))
        }
      }, error = function(e) {
        return(list(error = toString(e)))
      })
    },
    
    # 獲取統計資訊
    get_statistics = function(start_time, end_time) {
      tryCatch({
        response <- GET(
          paste0(self$base_url, "/statistics"),
          query = list(
            start_time = start_time,
            end_time = end_time
          )
        )
        if (status_code(response) == 200) {
          return(content(response, "parsed"))
        } else {
          return(list(error = "Failed to fetch statistics"))
        }
      }, error = function(e) {
        return(list(error = toString(e)))
      })
    }
  )
)