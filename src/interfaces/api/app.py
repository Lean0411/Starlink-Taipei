"""
FastAPI 應用程式主入口
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum

from ...infrastructure.container.container import get_container
from ...application.use_cases.analyze_coverage_use_case import AnalyzeCoverageUseCase
from ...application.use_cases.predict_coverage_use_case import PredictCoverageUseCase
from ...application.dto.coverage_request import CoverageRequest, ObserverDTO
from ...application.dto.prediction_request import PredictionRequest
from ...domain.entities.prediction import PredictionTimeScale


# Enums
class TimeScaleEnum(str, Enum):
    short_term = "short_term"
    medium_term = "medium_term"
    long_term = "long_term"


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
                "min_elevation": 25.0,
            }
        }


class PredictionRequestModel(BaseModel):
    """預測請求模型"""
    
    observer_latitude: float = Field(..., ge=-90, le=90, description="觀測者緯度")
    observer_longitude: float = Field(..., ge=-180, le=180, description="觀測者經度")
    observer_altitude: float = Field(0.0, description="觀測者高度（公尺）")
    time_scale: TimeScaleEnum = Field(TimeScaleEnum.medium_term, description="預測時間尺度")
    start_time: Optional[datetime] = Field(None, description="預測開始時間")
    min_elevation: float = Field(25.0, ge=0, le=90, description="最小仰角（度）")
    satellite_ids: Optional[List[str]] = Field(None, description="要分析的衛星ID列表")
    min_satellites_for_window: int = Field(30, gt=0, description="最佳窗口的最少衛星數")
    
    class Config:
        schema_extra = {
            "example": {
                "observer_latitude": 25.0330,
                "observer_longitude": 121.5654,
                "observer_altitude": 10.0,
                "time_scale": "medium_term",
                "min_elevation": 25.0,
                "min_satellites_for_window": 30
            }
        }


# 創建 FastAPI 應用
app = FastAPI(
    title="Starlink Taipei Satellite Analysis API", 
    description="衛星覆蓋率分析與預測 API", 
    version="2.1.0"
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
    get_container()
    # 可以在這裡預載入資料


@app.get("/")
async def root():
    """根路徑"""
    return {
        "message": "Starlink Taipei Satellite Analysis API",
        "version": "2.0.0",
        "endpoints": {"analyze_coverage": "/api/v1/coverage/analyze", "health": "/health", "docs": "/docs"},
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
            satellite_filter=request.satellite_filter,
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
                    "total_snapshots": result.statistics.total_snapshots,
                },
                "optimal_windows": result.optimal_windows,
                "snapshots_count": len(result.snapshots),
            },
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


@app.post("/api/v1/predict")
async def predict_coverage(request: PredictionRequestModel):
    """預測衛星覆蓋
    
    Args:
        request: 預測請求
        
    Returns:
        預測結果
    """
    try:
        # 獲取用例
        container = get_container()
        use_case = container.resolve(PredictCoverageUseCase)
        
        # 轉換請求
        prediction_request = PredictionRequest(
            observer=ObserverDTO(
                latitude=request.observer_latitude,
                longitude=request.observer_longitude,
                altitude=request.observer_altitude
            ),
            time_scale=PredictionTimeScale(request.time_scale.value),
            start_time=request.start_time,
            min_elevation=request.min_elevation,
            satellite_ids=request.satellite_ids,
            min_satellites_for_window=request.min_satellites_for_window
        )
        
        # 執行預測
        result = use_case.execute(prediction_request)
        
        # 返回結果
        return {
            "status": "success",
            "data": {
                "prediction_id": result.prediction_id,
                "time_scale": result.time_scale,
                "created_at": result.created_at,
                "observer_location": result.observer_location,
                "start_time": result.start_time,
                "end_time": result.end_time,
                "total_satellites": result.total_satellites,
                "analyzed_satellites": result.analyzed_satellites,
                "statistics": {
                    "satellites": result.statistics.satellites,
                    "elevation": result.statistics.elevation,
                    "coverage": result.statistics.coverage,
                    "optimal_windows_count": result.statistics.optimal_windows_count,
                    "peak_hours": result.statistics.peak_hours
                } if result.statistics else None,
                "optimal_windows": [
                    {
                        "start_time": window.start_time,
                        "end_time": window.end_time,
                        "avg_satellites": window.avg_satellites,
                        "max_elevation": window.max_elevation,
                        "duration_minutes": window.duration_minutes
                    }
                    for window in result.optimal_windows
                ],
                "prediction_points_count": len(result.prediction_points)
            }
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"內部錯誤: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

