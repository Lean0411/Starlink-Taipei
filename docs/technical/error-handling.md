# 錯誤處理和日誌系統文檔

## 概述

Starlink 台北衛星分析系統實作了統一的錯誤處理和結構化日誌系統，提供：

- 🔍 結構化 JSON 日誌格式
- 🔄 自動重試機制
- 📝 自定義異常層次結構
- 🛡️ 輸入驗證裝飾器
- 📊 性能追踪
- 🔐 敏感資訊過濾

## 快速開始

### 基本使用

```python
from app.utils import get_logger, log_info, log_error

# 獲取日誌器
logger = get_logger('module_name')

# 記錄日誌
log_info("操作開始", user_id="user123", operation="satellite_analysis")
log_error("操作失敗", exc_info=True, error_code="SAT001")
```

### 錯誤處理裝飾器

```python
from app.utils import handle_errors, validate_input

@handle_errors(retry_count=3, retry_delay=2.0)
@validate_input(lat=(-90, 90), lon=(-180, 180))
def analyze_location(lat, lon):
    # 函數會自動重試並驗證輸入
    return perform_analysis(lat, lon)
```

## 自定義異常類別

### 異常層次結構

```
BaseStarlinkException
├── DataValidationError      # 數據驗證錯誤
├── SatelliteCalculationError # 衛星計算錯誤  
├── NetworkError             # 網路連接錯誤
├── ConfigurationError       # 配置錯誤
├── TLEDataError            # TLE 數據錯誤
├── ResourceNotFoundError    # 資源未找到
├── PermissionDeniedError    # 權限拒絕
└── RateLimitError          # 速率限制
```

### 使用範例

```python
from app.utils import SatelliteCalculationError

def calculate_visibility():
    try:
        # 計算邏輯
        pass
    except Exception as e:
        raise SatelliteCalculationError(
            "衛星可見性計算失敗",
            details={
                'satellite_id': 'STARLINK-1234',
                'error_type': 'orbital_calculation',
                'original_error': str(e)
            }
        )
```

## 日誌系統功能

### JSON 格式日誌

所有日誌自動格式化為 JSON，便於分析和監控：

```json
{
    "timestamp": "2025-06-24T12:00:00.000Z",
    "level": "INFO",
    "logger": "starlink.satellite_analysis",
    "message": "分析完成",
    "module": "satellite_analysis",
    "function": "analyze_coverage",
    "line": 125,
    "user_id": "user123",
    "trace_id": "abc-123-def",
    "duration": 45.3,
    "satellite_count": 7500
}
```

### 日誌輪轉

- 主日誌文件：最大 10MB，保留 5 個備份
- 錯誤日誌文件：最大 5MB，保留 3 個備份

### 敏感資訊過濾

自動過濾包含以下關鍵字的欄位：
- password
- token
- api_key
- secret
- credential

## 錯誤上下文管理

使用 `ErrorContext` 提供更好的錯誤追踪：

```python
from app.utils import ErrorContext

with ErrorContext("satellite_download", 
                  satellite_group="starlink",
                  source="celestrak"):
    # 執行可能出錯的操作
    download_tle_data()
    process_tle_data()
    # 如果發生錯誤，上下文信息會自動記錄
```

## 性能監控

錯誤處理裝飾器自動記錄函數執行時間：

```python
@handle_errors(log_performance=True)
def expensive_operation():
    # 執行時間會自動記錄到日誌
    perform_calculation()
```

## 配置選項

### 環境變數

- `LOG_LEVEL`: 設置日誌級別 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `LOG_DIR`: 日誌目錄路徑（預設: `logs/`）

### 配置文件

參見 `config/logging.yaml` 進行詳細配置。

## 最佳實踐

### 1. 使用適當的日誌級別

```python
log_debug("詳細的除錯信息")      # 開發時使用
log_info("重要的操作信息")        # 正常流程
log_warning("需要注意的情況")     # 潛在問題
log_error("錯誤但可恢復")        # 錯誤處理
log_critical("系統級嚴重錯誤")   # 嚴重問題
```

### 2. 提供豐富的上下文

```python
log_info(
    "衛星分析完成",
    user_id=user.id,
    location=(lat, lon),
    satellite_count=len(satellites),
    duration=time.time() - start_time,
    cache_hit=True
)
```

### 3. 使用自定義異常

不要使用通用的 `Exception`，而是使用特定的異常類別：

```python
# ❌ 不好
raise Exception("找不到衛星數據")

# ✅ 好
raise TLEDataError(
    "找不到指定的衛星數據",
    details={'satellite_id': sat_id, 'search_time': datetime.now()}
)
```

### 4. 合理設置重試

```python
# 網路請求：較多重試
@handle_errors(retry_count=3, retry_delay=5.0)
def download_data():
    pass

# 計算操作：較少重試
@handle_errors(retry_count=1, retry_delay=1.0)
def calculate_result():
    pass
```

## 故障排除

### 日誌文件位置

- 主日誌：`logs/starlink.log`
- 錯誤日誌：`logs/error.log`
- 控制台輸出：INFO 級別以上

### 常見問題

1. **日誌文件過大**
   - 檢查日誌輪轉設置
   - 調整日誌級別

2. **性能影響**
   - 在生產環境設置 `LOG_LEVEL=INFO`
   - 避免在循環中記錄過多日誌

3. **日誌格式問題**
   - 確保 JSON 格式化器正確配置
   - 檢查自定義欄位是否可序列化

## 範例應用

完整的使用範例請參考：
- `test_error_handling.py` - 測試腳本
- `satellite_analysis_updated.py` - 實際應用範例
- `starlink_updated.py` - CLI 整合範例