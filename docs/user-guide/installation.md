# 安裝指南

本指南將協助你安裝和設置 Starlink 台北衛星分析系統。

## 系統要求

### 最低要求
- **作業系統**: Windows 10+, macOS 10.14+, Ubuntu 20.04+
- **R 語言**: 4.0.0 或更新版本
- **Python**: 3.8 或更新版本
- **記憶體**: 至少 8GB RAM
- **硬碟空間**: 至少 2GB 可用空間
- **網路連接**: 用於下載套件和衛星數據

### 建議配置
- **CPU**: 多核心處理器（支援並行計算）
- **記憶體**: 16GB RAM 或以上
- **顯示卡**: 支援 CUDA 的 NVIDIA GPU（可選，用於深度學習加速）

## 安裝步驟

### 1. 安裝 R 語言

#### Windows
1. 訪問 [R 官方網站](https://cran.r-project.org/)
2. 下載最新版本的 R for Windows
3. 執行安裝程式，使用預設設置

#### macOS
```bash
# 使用 Homebrew
brew install r
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install r-base r-base-dev
```

### 2. 安裝 Python

#### 使用 Anaconda（推薦）
1. 下載 [Anaconda](https://www.anaconda.com/products/distribution)
2. 安裝 Anaconda
3. 創建虛擬環境：
```bash
conda env create -f environment.yml
conda activate starlink-taipei
```

#### 使用 pip
```bash
# 安裝 Python（如果尚未安裝）
sudo apt install python3 python3-pip  # Linux
brew install python3  # macOS

# 安裝依賴
pip install -r requirements.txt
```

### 3. 安裝 R 套件

#### 自動安裝（推薦）
執行快速啟動腳本，它會自動安裝所有必要的 R 套件：
```bash
Rscript quick_start.R
```

#### 手動安裝
如果自動安裝失敗，可以手動安裝：
```r
# 在 R 控制台中執行
install.packages(c(
  "shiny",
  "shinydashboard",
  "shinycssloaders",
  "DT",
  "plotly",
  "leaflet",
  "jsonlite",
  "tidyverse",
  "viridis"
))
```

### 4. 驗證安裝

執行以下命令驗證安裝是否成功：

#### 檢查 R 版本
```bash
R --version
```

#### 檢查 Python 版本
```bash
python --version
```

#### 測試應用
```bash
# 簡化版界面
Rscript app_simple.R

# 完整版界面
Rscript app.R
```

## 常見問題

### Q: R 套件安裝失敗
A: 嘗試以下解決方案：
1. 更新 R 到最新版本
2. 安裝系統依賴：
   ```bash
   # Ubuntu/Debian
   sudo apt install libcurl4-openssl-dev libssl-dev libxml2-dev
   
   # macOS
   brew install openssl libxml2
   ```

### Q: Python 模組找不到
A: 確保已激活正確的虛擬環境：
```bash
conda activate starlink-taipei
# 或
source venv/bin/activate
```

### Q: 記憶體不足錯誤
A: 減少分析的時間範圍或衛星數量，或升級系統記憶體。

### Q: 網頁應用無法啟動
A: 檢查端口 3838 是否被占用：
```bash
lsof -i :3838  # macOS/Linux
netstat -ano | findstr :3838  # Windows
```

## 下一步

安裝完成後，請參考[快速開始指南](./quick-start.md)來開始使用系統。

如需更多技術細節，請查看[系統架構文件](../technical/architecture.md)。