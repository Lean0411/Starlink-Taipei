# 常見問題 (FAQ)

這裡整理了使用 Starlink 台北衛星分析系統時的常見問題與解答。

## 目錄
- [一般問題](#一般問題)
- [技術問題](#技術問題)
- [數據相關](#數據相關)
- [性能與資源](#性能與資源)
- [部署問題](#部署問題)
- [預測功能](#預測功能)

## 一般問題

### Q: 這個系統可以做什麼？

**A:** Starlink 台北衛星分析系統可以：
- 實時追蹤 7,500+ 顆 Starlink 衛星
- 計算特定地點的衛星覆蓋率
- 預測未來的衛星可見性
- 生成詳細的分析報告和視覺化圖表
- 提供 API 接口供程式整合

### Q: 為什麼專注於台北地區？

**A:** 雖然系統預設針對台北優化，但實際上可以分析全球任何地點。只需在設定中修改經緯度座標即可：
```bash
python starlink.py analyze --lat 35.6762 --lon 139.6503  # 東京
python starlink.py analyze --lat 37.7749 --lon -122.4194  # 舊金山
```

### Q: 系統是否需要付費？

**A:** 不需要！這是一個開源專案，採用 MIT 授權，完全免費使用。

### Q: 可以商業使用嗎？

**A:** 可以。MIT 授權允許商業使用，但請注意：
- 保留原始授權聲明
- 不提供任何保證
- 作者不承擔任何責任

## 技術問題

### Q: 支援哪些作業系統？

**A:** 系統支援：
- **Linux** (Ubuntu 20.04+, Debian 10+, CentOS 7+)
- **macOS** (10.14+)
- **Windows** (10/11，建議使用 WSL2)
- **Docker** (跨平台支援)

### Q: Python 和 R 都是必需的嗎？

**A:** 視使用方式而定：
- **命令列分析**：只需要 Python
- **網頁介面**：需要 Python 和 R
- **API 服務**：只需要 Python

### Q: 可以不使用 Docker 嗎？

**A:** 當然可以！Docker 只是為了簡化部署。您可以直接安裝依賴：
```bash
# Python 依賴
pip install -r requirements.txt

# R 依賴
Rscript -e "install.packages(c('shiny', 'shinydashboard', 'plotly'))"
```

### Q: 如何更新到最新版本？

**A:** 
```bash
# 拉取最新程式碼
git pull origin main

# 更新依賴
pip install -r requirements.txt --upgrade

# 重啟服務
python starlink.py shiny
```

## 數據相關

### Q: TLE 數據多久更新一次？

**A:** 
- 系統會在每次分析時自動檢查並下載最新數據
- CelesTrak 通常每天更新多次
- 本地緩存 24 小時後自動更新

### Q: 可以使用離線數據嗎？

**A:** 可以！如果已有 TLE 文件：
1. 將文件放在 `output/` 目錄
2. 命名為 `starlink_latest.tle`
3. 系統會優先使用本地文件

### Q: 分析結果的準確度如何？

**A:** 
- **軌道計算**：使用 Skyfield，精度在幾公里內
- **預測準確度**：短期（1小時）> 95%，中期（24小時）> 85%
- **覆蓋率計算**：基於實際軌道數據，準確度高

### Q: 為什麼衛星數量會變化？

**A:** 
- SpaceX 持續發射新衛星
- 部分衛星可能脫軌或失效
- TLE 數據更新可能有延遲

## 性能與資源

### Q: 分析 7500+ 顆衛星需要多久？

**A:** 取決於硬體配置：
- **高階配置**（8核+）：< 2 秒
- **中階配置**（4核）：3-5 秒  
- **低階配置**（2核）：8-15 秒

### Q: 需要多少記憶體？

**A:** 
- **最低需求**：4GB RAM
- **建議配置**：8GB RAM
- **大量數據處理**：16GB+ RAM

### Q: 如何優化性能？

**A:** 
1. **限制 CPU 使用**：
   ```bash
   python starlink.py analyze --cpu 4
   ```

2. **調整分析參數**：
   ```bash
   python starlink.py analyze --interval 5 --duration 30
   ```

3. **使用 Docker 資源限制**：
   ```bash
   docker run --cpus="2" --memory="4g" ...
   ```

## 部署問題

### Q: 如何在雲端部署？

**A:** 支援主要雲端平台：

**AWS EC2**：
```bash
# 選擇 Ubuntu AMI
# t3.medium 或更高規格
# 開放端口 3838
```

**Google Cloud**：
```bash
# 使用 Compute Engine
# n1-standard-2 或更高
# 配置防火牆規則
```

**Azure**：
```bash
# 使用 Virtual Machines
# Standard_B2s 或更高
# 配置 NSG 規則
```

### Q: 支援容器編排嗎？

**A:** 是的！可以使用：
- **Docker Compose**（已提供）
- **Kubernetes**（需自行配置）
- **Docker Swarm**

### Q: 如何設定反向代理？

**A:** Nginx 配置範例：
```nginx
location /starlink/ {
    proxy_pass http://localhost:3838/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

## 預測功能

### Q: SCINet-SA 模型是什麼？

**A:** SCINet-SA (Sparse Convolutional Network with Self-Attention) 是：
- 專為時間序列預測設計的深度學習模型
- 結合稀疏卷積和自注意力機制
- 特別適合衛星軌道預測

### Q: 預測準確度如何提升？

**A:** 系統使用混合建模方法：
- 70% 物理模型（傳統軌道力學）
- 30% AI 模型（模式識別和修正）
- 相比純物理模型，準確度提升 15-38%

### Q: 可以自訂預測模型嗎？

**A:** 可以！在 `app/services/prediction_service.py` 中：
1. 實作新的模型類別
2. 訓練您的模型
3. 更新預測管線

### Q: 預測需要 GPU 嗎？

**A:** 不需要：
- 模型推理在 CPU 上運行良好
- GPU 只在訓練時有顯著加速
- 一般使用 CPU 即可

## 其他問題

### Q: 如何貢獻程式碼？

**A:** 請參考[貢獻指南](../development/contributing.md)：
1. Fork 專案
2. 創建功能分支
3. 提交 Pull Request

### Q: 在哪裡回報問題？

**A:** 
- GitHub Issues（推薦）
- 詳細描述問題和重現步驟
- 附上系統環境資訊

### Q: 有社群支援嗎？

**A:** 
- GitHub Discussions
- Issues 區域
- PR 歡迎各種改進

### Q: 未來發展計畫？

**A:** 規劃中的功能：
- 實時數據流處理
- 多衛星系統支援
- 移動端應用
- 更多預測模型

---

如果您的問題未在此列出，請查看[疑難排解指南](./troubleshooting.md)或提交 Issue。

*最後更新：2025-06-24*