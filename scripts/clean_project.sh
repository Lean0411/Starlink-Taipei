#!/bin/bash
# MIT License
# Copyright (c) 2025 Starlink Taipei Analysis Team
#
# 專案清理腳本

echo "🧹 開始清理專案..."

# 清理 Python 快取文件
echo "清理 Python 快取..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null
find . -type f -name "*.pyo" -delete 2>/dev/null
find . -type f -name "*.pyd" -delete 2>/dev/null
find . -type f -name ".coverage" -delete 2>/dev/null
find . -type f -name ".coverage.*" -delete 2>/dev/null

# 清理測試相關文件
echo "清理測試文件..."
rm -rf htmlcov/
rm -rf .pytest_cache/
rm -rf .tox/

# 清理日誌文件
echo "清理日誌文件..."
find . -name "*.log" -delete 2>/dev/null

# 清理臨時文件
echo "清理臨時文件..."
find . -name "*.tmp" -delete 2>/dev/null
find . -name "*.temp" -delete 2>/dev/null
find . -name "*~" -delete 2>/dev/null
find . -name ".DS_Store" -delete 2>/dev/null

# 清理 R 相關文件
echo "清理 R 相關文件..."
rm -f .Rhistory
rm -f .RData

# 保留 output 目錄但清理舊文件（超過 7 天）
if [ -d "output" ]; then
    echo "清理舊的輸出文件（超過 7 天）..."
    find output/ -type f -mtime +7 -delete 2>/dev/null
fi

echo "✅ 專案清理完成！"