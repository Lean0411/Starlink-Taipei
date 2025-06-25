# Docker 部署指南

## 概述

本指南說明如何使用 Docker 部署 Starlink 台北衛星分析系統。Docker 提供了一致的運行環境，簡化了部署流程。

## 前置要求

- Docker 20.10 或更新版本
- Docker Compose 2.0 或更新版本
- 至少 4GB 可用記憶體
- 10GB 可用硬碟空間

## 快速開始

### 1. 使用 Docker Compose（推薦）

```bash
# 克隆專案
git clone https://github.com/yourusername/Starlink-Taipei.git
cd Starlink-Taipei

# 啟動服務
docker-compose up -d

# 查看日誌
docker-compose logs -f

# 停止服務
docker-compose down
```

服務啟動後，訪問 http://localhost:3838 即可使用。

### 2. 使用單一 Docker 容器

```bash
# 構建映像
docker build -t starlink-taipei:latest .

# 運行容器
docker run -d \
  --name starlink-taipei \
  -p 3838:3838 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/output:/app/output \
  starlink-taipei:latest
```

## Docker Compose 配置

### docker-compose.yml 詳解

```yaml
version: '3.8'

services:
  # 主應用服務
  starlink-app:
    build: 
      context: .
      dockerfile: Dockerfile
    container_name: starlink-taipei
    ports:
      - "3838:3838"  # Shiny 應用端口
    volumes:
      - ./data:/app/data  # 數據目錄
      - ./output:/app/output  # 輸出目錄
      - ./logs:/app/logs  # 日誌目錄
    environment:
      - TZ=Asia/Taipei  # 時區設置
      - SHINY_PORT=3838
      - ENABLE_ML=true  # 啟用機器學習
      - MAX_WORKERS=4  # 最大工作進程數
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3838"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Redis 快取服務（可選）
  redis:
    image: redis:7-alpine
    container_name: starlink-redis
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    restart: unless-stopped

  # Nginx 反向代理（生產環境）
  nginx:
    image: nginx:alpine
    container_name: starlink-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - starlink-app
    restart: unless-stopped

volumes:
  redis-data:
```

## Dockerfile 詳解

### 多階段構建 Dockerfile

```dockerfile
# 第一階段：Python 依賴安裝
FROM python:3.9-slim as python-deps

WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 複製並安裝 Python 依賴
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 第二階段：R 環境設置
FROM rocker/shiny:4.3.0

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 設置工作目錄
WORKDIR /app

# 複製 Python 環境
COPY --from=python-deps /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages

# 安裝 R 套件
RUN R -e "install.packages(c('shinydashboard', 'shinycssloaders', 'DT', 'plotly', 'leaflet', 'jsonlite', 'tidyverse', 'viridis', 'reticulate'), repos='https://cloud.r-project.org/')"

# 複製應用程式碼
COPY . /app

# 設置權限
RUN chown -R shiny:shiny /app

# 暴露端口
EXPOSE 3838

# 啟動命令
CMD ["R", "-e", "shiny::runApp('/app/app.R', host='0.0.0.0', port=3838)"]
```

## 環境變數配置

### 應用配置

創建 `.env` 文件：

```env
# 應用設置
SHINY_PORT=3838
ENABLE_ML=true
LOG_LEVEL=INFO

# 性能設置
MAX_WORKERS=4
CACHE_TTL=900
MEMORY_LIMIT=4G

# 數據源設置
TLE_UPDATE_INTERVAL=3600
TLE_SOURCES=celestrak,space-track

# 安全設置
ENABLE_AUTH=false
SESSION_TIMEOUT=3600
```

### 在 docker-compose.yml 中使用

```yaml
services:
  starlink-app:
    env_file:
      - .env
```

## 生產環境部署

### 1. 優化配置

#### 生產環境 Dockerfile

```dockerfile
# 使用更小的基礎映像
FROM rocker/shiny:4.3.0-slim

# 優化層快取
COPY requirements.txt package.json* ./
RUN pip install --no-cache-dir -r requirements.txt && \
    R -e "install.packages(...)"

# 使用非 root 用戶
USER shiny

# 健康檢查
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:3838/ || exit 1
```

### 2. Nginx 配置

創建 `nginx.conf`：

```nginx
events {
    worker_connections 1024;
}

http {
    upstream shiny {
        server starlink-app:3838;
    }

    server {
        listen 80;
        server_name your-domain.com;

        # 重定向到 HTTPS
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name your-domain.com;

        # SSL 設置
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;

        # 安全標頭
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;

        location / {
            proxy_pass http://shiny;
            proxy_redirect off;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_read_timeout 86400;
        }
    }
}
```

### 3. 資源限制

在 docker-compose.yml 中設置資源限制：

```yaml
services:
  starlink-app:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

## 監控和日誌

### 1. 日誌管理

```yaml
services:
  starlink-app:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### 2. 查看日誌

```bash
# 查看所有服務日誌
docker-compose logs

# 查看特定服務日誌
docker-compose logs starlink-app

# 實時查看日誌
docker-compose logs -f --tail=100
```

### 3. 監控整合

添加 Prometheus 監控：

```yaml
services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"
```

## 備份和還原

### 1. 備份數據

```bash
# 備份數據卷
docker run --rm \
  -v starlink-taipei_data:/data \
  -v $(pwd)/backup:/backup \
  alpine tar czf /backup/data-$(date +%Y%m%d).tar.gz -C /data .

# 備份資料庫（如果使用）
docker-compose exec -T postgres pg_dump -U user dbname > backup.sql
```

### 2. 還原數據

```bash
# 還原數據卷
docker run --rm \
  -v starlink-taipei_data:/data \
  -v $(pwd)/backup:/backup \
  alpine tar xzf /backup/data-20240609.tar.gz -C /data
```

## 故障排除

### 常見問題

#### 1. 容器無法啟動

```bash
# 檢查日誌
docker-compose logs starlink-app

# 檢查容器狀態
docker-compose ps

# 進入容器調試
docker-compose exec starlink-app bash
```

#### 2. 記憶體不足

```bash
# 增加 Docker 記憶體限制
# Docker Desktop: Preferences > Resources > Memory

# 或調整 docker-compose.yml 中的限制
```

#### 3. 端口衝突

```bash
# 檢查端口占用
netstat -tulpn | grep 3838

# 修改 docker-compose.yml 中的端口映射
ports:
  - "3839:3838"  # 改用其他端口
```

## 安全建議

1. **定期更新映像**
   ```bash
   docker-compose pull
   docker-compose up -d
   ```

2. **使用密鑰管理**
   - 不要在映像中硬編碼密鑰
   - 使用 Docker secrets 或環境變數

3. **網路隔離**
   ```yaml
   networks:
     frontend:
     backend:
       internal: true
   ```

4. **掃描漏洞**
   ```bash
   docker scan starlink-taipei:latest
   ```

## 性能優化

1. **使用 BuildKit**
   ```bash
   DOCKER_BUILDKIT=1 docker build .
   ```

2. **優化層快取**
   - 將不常變動的指令放在前面
   - 合併 RUN 指令減少層數

3. **使用 .dockerignore**
   ```
   .git
   *.log
   output/
   __pycache__/
   .pytest_cache/
   ```

## 相關資源

- [Docker 官方文檔](https://docs.docker.com/)
- [Docker Compose 文檔](https://docs.docker.com/compose/)
- [Rocker 專案](https://www.rocker-project.org/)
- [Shiny Server 文檔](https://docs.rstudio.com/shiny-server/)