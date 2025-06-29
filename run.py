#!/usr/bin/env python3
"""
應用程式啟動腳本
"""
import sys
import asyncio
from pathlib import Path

# 添加 src 到 Python 路徑
sys.path.insert(0, str(Path(__file__).parent))


def run_api():
    """執行 API 伺服器"""
    import uvicorn
    from src.interfaces.api.app import app
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)


def run_cli():
    """執行 CLI"""
    from src.interfaces.cli.main import main
    asyncio.run(main())


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "api":
        print("🚀 啟動 API 伺服器...")
        run_api()
    else:
        print("🛰️  執行衛星分析...")
        run_cli()