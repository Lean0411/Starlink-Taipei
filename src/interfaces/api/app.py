"""
FastAPI 應用程式主入口
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

from ...infrastructure.container.container import get_container
from ...application.use_cases.analyze_coverage_use_case import AnalyzeCoverageUseCase
from ...application.dto.coverage_request import CoverageRequest


# FastAPI 模型
class CoverageRequestModel(BaseModel):
    """覆蓋率分析請求模型"""
    observer_latitude: float = Field(..., ge=-90, le=90, description="觀測者緯度")
    observer_longitude: float = Field(..., ge=-180, le=180, description="觀測者經度")
    observer_elevation: float = Field(0.0, description="觀測者高度（公尺）")
    start_time: Optional[datetime] = Field(None, description="分析開始時間")
    duration_minutes: int = Field(60, gt=0, description="分析持續時間（分鐘）")
    interval_minutes: int = Field(1, gt=0, description="時間間隔（分鐘）")
    min_elevation: float = Field(25.0, ge=0, le=90, description="最小仰角（度）")
    satellite_filter: Optional[str] = Field(None, description="衛星篩選條件")
    
    class Config:
        schema_extra = {
            "example": {
                "observer_latitude": 25.0330,
                "observer_longitude": 121.5654,
                "observer_elevation": 10.0,
                "duration_minutes": 60,
                "interval_minutes": 1,
                "min_elevation": 25.0
            }
        }


# 創建 FastAPI 應用
app = FastAPI(
    title="Starlink Taipei Satellite Analysis API",
    description="衛星覆蓋率分析 API",
    version="2.0.0"
)

# 添加 CORS 中間件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """應用啟動事件"""
    # 初始化容器
    container = get_container()
    # 可以在這裡預載入資料
    

@app.get("/")
async def root():
    """根路徑"""
    return {
        "message": "Starlink Taipei Satellite Analysis API",
        "version": "2.0.0",
        "endpoints": {
            "analyze_coverage": "/api/v1/coverage/analyze",
            "health": "/health",
            "docs": "/docs"
        }
    }


@app.get("/health")
async def health_check():
    """健康檢查"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.post("/api/v1/coverage/analyze")
async def analyze_coverage(request: CoverageRequestModel):
    """分析衛星覆蓋率
    
    Args:
        request: 覆蓋率分析請求
        
    Returns:
        覆蓋率分析結果
    """
    try:
        # 獲取用例
        container = get_container()
        use_case = container.resolve(AnalyzeCoverageUseCase)
        
        # 轉換請求
        coverage_request = CoverageRequest(
            observer_latitude=request.observer_latitude,
            observer_longitude=request.observer_longitude,
            observer_elevation=request.observer_elevation,
            start_time=request.start_time,
            duration_minutes=request.duration_minutes,
            interval_minutes=request.interval_minutes,
            min_elevation=request.min_elevation,
            satellite_filter=request.satellite_filter
        )
        
        # 執行分析
        result = await use_case.execute(coverage_request)
        
        # 返回結果
        return {
            "status": "success",
            "data": {
                "coverage_id": result.coverage_id,
                "observer": result.observer,
                "start_time": result.start_time,
                "end_time": result.end_time,
                "statistics": {
                    "duration_minutes": result.statistics.duration_minutes,
                    "average_visible_count": result.statistics.average_visible_count,
                    "max_visible_count": result.statistics.max_visible_count,
                    "min_visible_count": result.statistics.min_visible_count,
                    "coverage_percentage": result.statistics.coverage_percentage,
                    "total_snapshots": result.statistics.total_snapshots
                },
                "optimal_windows": result.optimal_windows,
                "snapshots_count": len(result.snapshots)
            }
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"內部錯誤: {str(e)}")


@app.get("/api/v1/coverage/{coverage_id}")
async def get_coverage(coverage_id: str):
    """獲取特定的覆蓋率分析結果
    
    Args:
        coverage_id: 覆蓋率分析 ID
        
    Returns:
        覆蓋率分析結果
    """
    # TODO: 實作從儲存中獲取結果
    raise HTTPException(status_code=501, detail="尚未實作")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)