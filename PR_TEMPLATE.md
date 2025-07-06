## 概述
將 `refactor/clean-architecture` 分支合併到 `main` 分支。此 PR 包含重要的架構改進和新功能實作。

## 主要變更

### 🏗️ 架構改進
- 實作 Clean Architecture 設計模式
- 建立清晰的層次結構：domain、application、infrastructure、interfaces
- 實作依賴注入容器

### ✨ 新功能
- 統一依賴管理（pyproject.toml）
- 完整的錯誤處理系統
- 覆蓋率分析結果儲存和查詢 API
- 衛星位置計算服務

### 🐛 修復
- 修復 CI/CD 測試問題
- 修復 Shiny UI 效能問題
- 修復檔案路徑和組織問題

### 📝 文檔
- 更新 README.md 安裝說明
- 新增使用範例
- 改進程式碼註解

## 測試
- ✅ 所有 CI 測試通過
- ✅ 手動測試 API 端點
- ✅ Shiny UI 功能正常

## 後續工作
- 提升測試覆蓋率到 80%
- 實作 Redis 快取層
- 優化衛星資料批次處理

## 相關提交
最近的重要提交：
- f1df6f3 feat: 完成四項重要改進
- e4e0ca6 fix: 修復 minimal CI 測試的檔案路徑檢查
- bd10784 fix: 更新 CI workflow 以配合新的專案結構
- ec7afa4 refactor: 重構專案結構並優化即時衛星追蹤效能

🤖 Generated with [Claude Code](https://claude.ai/code)