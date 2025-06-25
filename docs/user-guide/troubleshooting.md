# 疑難排解指南

本指南幫助您解決使用 Starlink 台北衛星分析系統時可能遇到的常見問題。

## 目錄
- [安裝問題](#安裝問題)
- [執行時錯誤](#執行時錯誤)
- [網頁介面問題](#網頁介面問題)
- [數據分析問題](#數據分析問題)
- [性能問題](#性能問題)
- [網路連接問題](#網路連接問題)

## 安裝問題

### Python 依賴安裝失敗

**問題**：執行 `pip install -r requirements.txt` 時出現錯誤

**解決方案**：
1. 確保使用 Python 3.8 或更高版本：
   ```bash
   python --version
   ```

2. 更新 pip 到最新版本：
   ```bash
   python -m pip install --upgrade pip
   ```

3. 如果特定套件安裝失敗，嘗試單獨安裝：
   ```bash
   pip install numpy
   pip install pandas
   pip install skyfield
   ```

### R 套件安裝問題

**問題**：R 套件安裝失敗或找不到套件

**解決方案**：
1. 確保 R 版本為 4.0 或更高：
   ```r
   R.version.string
   ```

2. 設定 CRAN 鏡像站：
   ```r
   options(repos = c(CRAN = "https://cloud.r-project.org"))
   ```

3. 安裝系統依賴（Ubuntu/Debian）：
   ```bash
   sudo apt-get install libcurl4-openssl-dev libssl-dev libxml2-dev
   ```

## 執行時錯誤

### "找不到 Python" 錯誤

**問題**：執行 `python starlink.py` 時顯示找不到命令

**解決方案**：
1. 檢查 Python 是否已安裝：
   ```bash
   which python3
   ```

2. 使用 `python3` 替代 `python`：
   ```bash
   python3 starlink.py analyze
   ```

3. 創建 Python 別名：
   ```bash
   alias python=python3
   ```

### TLE 數據下載失敗

**問題**：無法從 CelesTrak 下載衛星數據

**解決方案**：
1. 檢查網路連接：
   ```bash
   ping celestrak.org
   ```

2. 檢查代理設定：
   ```bash
   export HTTP_PROXY=your_proxy
   export HTTPS_PROXY=your_proxy
   ```

3. 使用備用 TLE 來源或本地緩存文件

## 網頁介面問題

### Shiny 應用無法啟動

**問題**：執行 `Rscript app.R` 後無法訪問網頁

**解決方案**：
1. 檢查端口是否被占用：
   ```bash
   lsof -i :3838
   ```

2. 指定不同端口：
   ```bash
   python starlink.py shiny --port 8080
   ```

3. 檢查防火牆設定，確保端口開放

### 網頁載入緩慢

**問題**：Shiny 介面反應遲緩

**解決方案**：
1. 減少分析時間長度
2. 增加時間間隔設定
3. 檢查系統資源使用情況：
   ```bash
   top
   htop
   ```

## 數據分析問題

### 分析結果為空

**問題**：執行分析後沒有找到任何衛星

**解決方案**：
1. 檢查 TLE 數據是否最新：
   ```bash
   ls -la output/starlink_latest.tle
   ```

2. 更新 TLE 數據：
   ```bash
   rm output/starlink_latest.tle
   python starlink.py analyze
   ```

3. 調整最小仰角參數：
   ```bash
   python starlink.py analyze --min_elevation 10
   ```

### 預測功能異常

**問題**：深度學習預測結果不準確

**解決方案**：
1. 確保 PyTorch 正確安裝：
   ```python
   import torch
   print(torch.__version__)
   ```

2. 檢查 GPU 支援（如果使用）：
   ```python
   torch.cuda.is_available()
   ```

3. 重新訓練或更新預測模型

## 性能問題

### 分析速度過慢

**問題**：分析 7500+ 顆衛星耗時過長

**解決方案**：
1. 限制 CPU 核心數：
   ```bash
   python starlink.py analyze --cpu 4
   ```

2. 減少分析時間範圍：
   ```bash
   python starlink.py analyze --duration 30
   ```

3. 增加時間間隔：
   ```bash
   python starlink.py analyze --interval 5
   ```

### 記憶體不足

**問題**：出現 MemoryError 或系統變慢

**解決方案**：
1. 監控記憶體使用：
   ```bash
   free -h
   ```

2. 減少並行處理數量
3. 分批處理衛星數據
4. 增加系統交換空間

## 網路連接問題

### Docker 容器網路問題

**問題**：Docker 容器無法連接外部網路

**解決方案**：
1. 檢查 Docker 網路：
   ```bash
   docker network ls
   ```

2. 重啟 Docker 服務：
   ```bash
   sudo systemctl restart docker
   ```

3. 使用 host 網路模式：
   ```bash
   docker run --network host ...
   ```

## 獲取更多幫助

如果以上解決方案無法解決您的問題：

1. **查看日誌文件**：
   ```bash
   tail -f starlink.log
   ```

2. **執行健康檢查**：
   ```bash
   python starlink.py health
   ```

3. **提交 Issue**：
   在 GitHub 上提交詳細的問題描述，包括：
   - 錯誤訊息
   - 系統環境
   - 重現步驟

4. **查看其他文檔**：
   - [安裝指南](./installation.md)
   - [快速開始](./quick-start.md)
   - [常見問題](./faq.md)

---
*最後更新：2025-06-24*