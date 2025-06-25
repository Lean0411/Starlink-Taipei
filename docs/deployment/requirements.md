# 依賴和需求文件說明

## 概述

本文件詳細說明 Starlink 台北衛星分析系統的所有依賴項目和系統需求。

## Python 依賴

### 核心依賴 (requirements.txt)

```txt
# 天文計算
skyfield==1.48
sgp4==2.22
ephem==4.1.5

# 數據處理
numpy==1.24.3
pandas==2.0.3
scipy==1.11.1

# 深度學習
torch==2.0.1
scikit-learn==1.3.0

# 視覺化
matplotlib==3.7.2
plotly==5.15.0
seaborn==0.12.2

# 網路和 API
requests==2.31.0
urllib3==2.0.3
aiohttp==3.8.5

# 工具類
python-dateutil==2.8.2
pytz==2023.3
tqdm==4.65.0
colorama==0.4.6

# 並行處理
multiprocessing-logging==0.3.4
joblib==1.3.1

# 測試
pytest==7.4.0
pytest-cov==4.1.0
```

### 開發依賴 (requirements-dev.txt)

```txt
# 程式碼品質
pylint==2.17.4
black==23.7.0
flake8==6.0.0
mypy==1.4.1

# 測試工具
pytest-mock==3.11.1
pytest-asyncio==0.21.1
coverage==7.2.7

# 文檔生成
sphinx==7.0.1
sphinx-rtd-theme==1.3.0

# 調試工具
ipython==8.14.0
ipdb==0.13.13
```

### 生產環境依賴 (requirements/production.txt)

```txt
# 應用服務器
gunicorn==21.2.0
uvicorn==0.23.1

# 監控
prometheus-client==0.17.1
opentelemetry-api==1.19.0

# 快取
redis==4.6.0
pymemcache==4.0.0

# 資料庫（可選）
psycopg2-binary==2.9.7
sqlalchemy==2.0.19
```

## R 依賴

### 核心 R 套件

```r
# 在 R 中安裝
install.packages(c(
  # Shiny 框架
  "shiny",           # 1.7.5
  "shinydashboard",  # 0.7.2
  "shinycssloaders", # 1.0.0
  "shinyjs",         # 2.1.0
  
  # 數據處理
  "tidyverse",       # 2.0.0
  "data.table",      # 1.14.8
  "jsonlite",        # 1.8.7
  
  # 視覺化
  "plotly",          # 4.10.2
  "leaflet",         # 2.1.2
  "viridis",         # 0.6.4
  "DT",              # 0.28
  
  # Python 整合
  "reticulate",      # 1.31
  
  # 工具
  "lubridate",       # 1.9.2
  "stringr",         # 1.5.0
))
```

### 系統需求（R）

```r
# 檢查 R 版本
R.version.string  # 需要 R >= 4.0.0

# 檢查套件版本
packageVersion("shiny")  # >= 1.7.0
packageVersion("reticulate")  # >= 1.25
```

## 系統依賴

### Ubuntu/Debian

```bash
# 基礎工具
sudo apt-get update
sudo apt-get install -y \
    build-essential \
    curl \
    wget \
    git

# Python 開發
sudo apt-get install -y \
    python3-dev \
    python3-pip \
    python3-venv

# R 依賴
sudo apt-get install -y \
    r-base \
    r-base-dev \
    libcurl4-openssl-dev \
    libssl-dev \
    libxml2-dev \
    libfontconfig1-dev \
    libharfbuzz-dev \
    libfribidi-dev

# 圖形處理
sudo apt-get install -y \
    libpng-dev \
    libjpeg-dev \
    libtiff5-dev

# 地理空間（可選）
sudo apt-get install -y \
    libgdal-dev \
    libproj-dev \
    libgeos-dev
```

### macOS

```bash
# 使用 Homebrew
brew update
brew install \
    python@3.9 \
    r \
    gdal \
    proj \
    geos \
    libxml2 \
    openssl
```

### Windows

使用 Chocolatey 或手動安裝：

```powershell
# 使用 Chocolatey
choco install python r r.studio

# 或從官網下載
# Python: https://www.python.org/downloads/
# R: https://cran.r-project.org/bin/windows/
```

## 環境配置

### Conda 環境 (environment.yml)

```yaml
name: starlink-taipei
channels:
  - conda-forge
  - defaults
dependencies:
  # Python
  - python=3.9
  - pip
  - numpy
  - pandas
  - matplotlib
  - scikit-learn
  
  # R
  - r-base=4.3
  - r-shiny
  - r-tidyverse
  - r-reticulate
  
  # 系統工具
  - git
  - make
  - gcc
  
  # pip 依賴
  - pip:
    - skyfield
    - torch
    - plotly
```

### 虛擬環境設置

#### Python venv

```bash
# 創建虛擬環境
python -m venv venv

# 啟動虛擬環境
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# 安裝依賴
pip install -r requirements.txt
```

#### Conda

```bash
# 創建環境
conda env create -f environment.yml

# 啟動環境
conda activate starlink-taipei

# 更新環境
conda env update -f environment.yml
```

## 版本相容性

### Python 版本支援

- **推薦**: Python 3.9
- **最低**: Python 3.8
- **最高**: Python 3.11

### R 版本支援

- **推薦**: R 4.3.0
- **最低**: R 4.0.0
- **最高**: R 4.3.x

### 作業系統支援

- **Linux**: Ubuntu 20.04+, Debian 10+, CentOS 8+
- **macOS**: 10.14+ (Mojave)
- **Windows**: Windows 10 (版本 1909+)

## 依賴管理最佳實踐

### 1. 版本鎖定

```bash
# 生成精確版本
pip freeze > requirements.lock

# 使用鎖定版本
pip install -r requirements.lock
```

### 2. 依賴分層

```
requirements/
├── base.txt        # 核心依賴
├── dev.txt         # 開發依賴
├── test.txt        # 測試依賴
└── production.txt  # 生產環境
```

### 3. 定期更新

```bash
# 檢查過時套件
pip list --outdated

# 更新特定套件
pip install --upgrade package_name

# R 套件更新
update.packages(ask = FALSE)
```

## 故障排除

### Python 依賴問題

#### 1. NumPy/SciPy 安裝失敗

```bash
# 安裝系統依賴
sudo apt-get install python3-numpy python3-scipy

# 或使用預編譯版本
pip install --only-binary :all: numpy scipy
```

#### 2. PyTorch 安裝

```bash
# CPU 版本
pip install torch --index-url https://download.pytorch.org/whl/cpu

# CUDA 版本
pip install torch --index-url https://download.pytorch.org/whl/cu118
```

### R 套件問題

#### 1. 編譯錯誤

```r
# 使用二進制版本
options(pkgType = "binary")
install.packages("package_name")
```

#### 2. 依賴衝突

```r
# 清理並重新安裝
remove.packages("conflicting_package")
install.packages("conflicting_package")
```

## 性能優化依賴

### 1. 數值計算加速

```txt
# Intel MKL
mkl==2023.2.0
mkl-service==2.4.0

# OpenBLAS
scipy[openblas]
```

### 2. GPU 加速

```txt
# CUDA 支援
cuda-toolkit==11.8
cudnn==8.9.0

# GPU 版本 PyTorch
torch==2.0.1+cu118
```

### 3. 並行處理

```txt
# Dask 分散式計算
dask[complete]==2023.7.0

# Ray 並行框架
ray==2.6.0
```

## 安全性考慮

### 1. 依賴掃描

```bash
# 使用 pip-audit
pip install pip-audit
pip-audit

# 使用 safety
pip install safety
safety check
```

### 2. 最小化依賴

- 只安裝必要的套件
- 定期審查依賴列表
- 移除未使用的依賴

### 3. 私有套件源

```bash
# 使用私有 PyPI
pip install --index-url https://your-pypi.com/simple/ package_name

# 使用私有 CRAN
options(repos = c(CRAN = "https://your-cran-mirror.com/"))
```

## 相關文件

- [安裝指南](../user-guide/installation.md)
- [Docker 部署指南](./docker-guide.md)
- [系統架構](../technical/architecture.md)