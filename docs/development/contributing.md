# 貢獻指南

感謝您對 Starlink 台北衛星分析與預測系統的關注！我們歡迎各種形式的貢獻，包括但不限於錯誤回報、功能建議、文檔改進和程式碼貢獻。

## 目錄
- [行為準則](#行為準則)
- [如何貢獻](#如何貢獻)
- [開發環境設置](#開發環境設置)
- [提交流程](#提交流程)
- [程式碼規範](#程式碼規範)
- [測試要求](#測試要求)
- [文檔貢獻](#文檔貢獻)
- [社群支援](#社群支援)

## 行為準則

我們致力於為所有人提供友善、包容的環境。參與此專案時，請：

- 使用友善和包容的語言
- 尊重不同的觀點和經驗
- 優雅地接受建設性批評
- 專注於對社群最有利的事情
- 對其他社群成員表現出同理心

## 如何貢獻

### 1. 回報問題

發現 bug 或有改進建議？請：

1. 檢查 [Issues](https://github.com/your-repo/issues) 確認問題尚未被回報
2. 創建新 Issue，包含：
   - 清晰的標題和描述
   - 重現步驟（針對 bug）
   - 預期行為 vs 實際行為
   - 系統環境資訊
   - 相關日誌或截圖

### 2. 提出功能建議

有新功能想法？請：

1. 創建 Feature Request Issue
2. 說明功能的用途和價值
3. 提供使用案例
4. 考慮實作複雜度

### 3. 提交程式碼

準備好貢獻程式碼了嗎？

1. Fork 專案到您的 GitHub 帳號
2. Clone 到本地：
   ```bash
   git clone https://github.com/your-username/Starlink-Taipei.git
   cd Starlink-Taipei
   ```
3. 創建功能分支：
   ```bash
   git checkout -b feature/your-feature-name
   ```
4. 進行修改並提交
5. Push 到您的 Fork
6. 創建 Pull Request

## 開發環境設置

### Python 環境

1. 安裝 Python 3.8+：
   ```bash
   python --version  # 確認版本
   ```

2. 創建虛擬環境：
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # 或
   venv\Scripts\activate  # Windows
   ```

3. 安裝依賴：
   ```bash
   pip install -r requirements.txt
   pip install -r requirements/development.txt  # 開發依賴
   ```

### R 環境

1. 安裝 R 4.0+：
   ```bash
   R --version
   ```

2. 安裝必要套件：
   ```r
   install.packages(c("shiny", "shinydashboard", "plotly", "DT", "ggplot2", "dplyr", "reticulate"))
   ```

### 開發工具

推薦使用：
- **VS Code** + Python/R 擴展
- **PyCharm** (Python 開發)
- **RStudio** (R 開發)
- **Git** 版本控制

## 提交流程

### 1. 程式碼風格

#### Python
- 遵循 PEP 8 規範
- 使用 4 個空格縮進
- 最大行長 88 字符（使用 Black 格式化）
- 函數和類別使用 docstring

```python
def calculate_visibility(satellite, observer, time):
    """
    計算衛星可見性。
    
    Args:
        satellite: 衛星物件
        observer: 觀測者位置
        time: 觀測時間
    
    Returns:
        bool: 是否可見
    """
    # 實作程式碼
```

#### R
- 使用 tidyverse 風格指南
- 變數名使用 snake_case
- 函數名使用動詞

```r
calculate_coverage <- function(data, min_elevation = 25) {
  # 計算覆蓋率
  data %>%
    filter(elevation > min_elevation) %>%
    summarize(coverage = n() / nrow(data))
}
```

### 2. Commit 訊息

使用清晰的 commit 訊息：

```
類型: 簡短描述 (最多 50 字)

詳細說明（可選）。解釋為什麼需要這個改變，
而不只是做了什麼改變。

Fixes #issue_number
```

類型包括：
- `feat`: 新功能
- `fix`: 修復 bug
- `docs`: 文檔更新
- `style`: 格式調整
- `refactor`: 重構
- `test`: 測試相關
- `chore`: 維護工作

### 3. Pull Request

創建 PR 時請：

1. 確保所有測試通過
2. 更新相關文檔
3. 填寫 PR 模板
4. 連結相關 Issue
5. 等待程式碼審查

## 測試要求

### Python 測試

1. 使用 pytest 編寫測試：
   ```python
   def test_satellite_visibility():
       # 測試程式碼
       assert result == expected
   ```

2. 執行測試：
   ```bash
   pytest tests/
   ```

3. 檢查覆蓋率：
   ```bash
   pytest --cov=app tests/
   ```

### R 測試

1. 使用 testthat 套件
2. 將測試放在 `tests/testthat/` 目錄
3. 執行測試：
   ```r
   devtools::test()
   ```

## 文檔貢獻

改進文檔同樣重要！

### 文檔規範

1. 使用 Markdown 格式
2. 保持簡潔清晰
3. 包含程式碼範例
4. 更新日期標記

### 文檔類型

- **使用者指南**：面向終端使用者
- **技術文檔**：API 和架構說明
- **教學文章**：步驟指南
- **範例程式**：實際使用案例

## 社群支援

### 獲得幫助

- 查看[文檔](../README.md)
- 搜尋既有 [Issues](https://github.com/your-repo/issues)
- 加入討論區

### 幫助他人

- 回答 Issues 中的問題
- 改進文檔
- 分享使用經驗
- 審查 Pull Request

## 版本發布

我們使用語義化版本號：

- **主版本**：不相容的 API 變更
- **次版本**：向後相容的功能新增
- **修訂版本**：向後相容的錯誤修正

## 授權

提交貢獻即表示您同意在 MIT 授權下發布您的貢獻。

## 致謝

感謝所有貢獻者！您的努力使這個專案變得更好。

特別感謝：
- 早期測試者和回饋者
- 文檔貢獻者
- 程式碼審查者
- 社群維護者

---
*最後更新：2025-06-24*