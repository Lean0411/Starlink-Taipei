"""
依賴注入容器 - 管理應用程式的依賴關係
"""

import inspect
from typing import Any, Dict, Optional, Type
import os
import logging

from ...application.services.satellite_service import SatelliteService
from ...application.services.batch_processing_service import BatchProcessingService
from ...application.use_cases.analyze_coverage_use_case import AnalyzeCoverageUseCase
from ...application.use_cases.get_coverage_use_case import GetCoverageUseCase
from ...application.use_cases.predict_coverage_use_case import PredictCoverageUseCase
from ...domain.repositories.coverage_repository import CoverageRepository
from ...domain.repositories.satellite_repository import SatelliteRepository
from ...domain.services.coverage_analyzer import CoverageAnalyzer
from ...domain.services.optimized_coverage_analyzer import OptimizedCoverageAnalyzer
from ...domain.services.orbit_calculator import OrbitCalculator
from ...domain.services.prediction_service import PredictionService
from ...domain.services.cache_service import CacheService
from ..external_services.orbit_prediction_service import OrbitPredictionService
from ..external_services.skyfield_orbit_calculator import SkyfieldOrbitCalculator
from ..repositories.celestrak_satellite_repository import CelestrakSatelliteRepository
from ..repositories.in_memory_coverage_repository import InMemoryCoverageRepository
from ..cache.redis_cache_service import RedisCacheService, REDIS_AVAILABLE
from ..cache.memory_cache_service import MemoryCacheService

logger = logging.getLogger(__name__)


class Container:
    """依賴注入容器

    負責管理和注入應用程式的所有依賴
    """

    def __init__(self):
        """初始化容器"""
        self._services: Dict[Type, Any] = {}
        self._factories: Dict[Type, callable] = {}
        self._setup()

    def _setup(self):
        """設定依賴關係"""
        # 註冊快取服務
        self.register_factory(CacheService, self._create_cache_service)
        
        # 註冊基礎設施服務
        self.register_singleton(OrbitCalculator, SkyfieldOrbitCalculator)
        self.register_singleton(SatelliteRepository, CelestrakSatelliteRepository)
        self.register_singleton(CoverageRepository, InMemoryCoverageRepository)

        # 註冊領域服務
        self.register_factory(CoverageAnalyzer, self._create_coverage_analyzer)
        self.register_factory(PredictionService, self._create_prediction_service)

        # 註冊應用服務
        self.register_factory(BatchProcessingService, self._create_batch_processing_service)
        self.register_factory(SatelliteService, self._create_satellite_service)
        self.register_factory(AnalyzeCoverageUseCase, self._create_analyze_coverage_use_case)
        self.register_factory(GetCoverageUseCase, self._create_get_coverage_use_case)
        self.register_factory(PredictCoverageUseCase, self._create_predict_coverage_use_case)

    def register_singleton(self, interface: Type, implementation: Type):
        """註冊單例服務

        Args:
            interface: 介面類型
            implementation: 實作類型
        """
        if interface not in self._services:
            self._services[interface] = implementation()

    def register_factory(self, interface: Type, factory: callable):
        """註冊工廠方法

        Args:
            interface: 介面類型
            factory: 工廠方法
        """
        self._factories[interface] = factory

    def resolve(self, interface: Type) -> Any:
        """解析依賴

        Args:
            interface: 要解析的介面類型

        Returns:
            Any: 解析的實例

        Raises:
            ValueError: 如果無法解析依賴
        """
        # 檢查是否有單例
        if interface in self._services:
            return self._services[interface]

        # 檢查是否有工廠
        if interface in self._factories:
            return self._factories[interface]()

        # 嘗試自動創建
        if inspect.isclass(interface):
            return self._auto_resolve(interface)

        raise ValueError(f"無法解析依賴: {interface}")

    def _auto_resolve(self, cls: Type) -> Any:
        """自動解析類別的依賴

        Args:
            cls: 要解析的類別

        Returns:
            Any: 創建的實例
        """
        # 獲取建構函數參數
        sig = inspect.signature(cls.__init__)
        params = sig.parameters

        # 解析每個參數
        kwargs = {}
        for name, param in params.items():
            if name == "self":
                continue

            # 獲取參數類型
            param_type = param.annotation
            if param_type != inspect.Parameter.empty:
                # 遞迴解析依賴
                kwargs[name] = self.resolve(param_type)

        return cls(**kwargs)

    def _create_satellite_service(self) -> SatelliteService:
        """創建衛星服務"""
        orbit_calculator = self.resolve(OrbitCalculator)
        return SatelliteService(orbit_calculator)

    def _create_batch_processing_service(self) -> BatchProcessingService:
        """創建批次處理服務"""
        orbit_calculator = self.resolve(OrbitCalculator)
        return BatchProcessingService(orbit_calculator, batch_size=500)
    
    def _create_coverage_analyzer(self) -> CoverageAnalyzer:
        """創建覆蓋率分析器（使用優化版本）"""
        orbit_calculator = self.resolve(OrbitCalculator)
        batch_processor = self.resolve(BatchProcessingService)
        return OptimizedCoverageAnalyzer(orbit_calculator, batch_processor)

    def _create_analyze_coverage_use_case(self) -> AnalyzeCoverageUseCase:
        """創建分析覆蓋率用例"""
        satellite_repository = self.resolve(SatelliteRepository)
        coverage_analyzer = self.resolve(CoverageAnalyzer)
        coverage_repository = self.resolve(CoverageRepository)
        return AnalyzeCoverageUseCase(satellite_repository, coverage_analyzer, coverage_repository)

    def _create_prediction_service(self) -> PredictionService:
        """創建預測服務"""
        orbit_calculator = self.resolve(OrbitCalculator)
        return OrbitPredictionService(orbit_calculator)

    def _create_get_coverage_use_case(self) -> GetCoverageUseCase:
        """創建獲取覆蓋率用例"""
        coverage_repository = self.resolve(CoverageRepository)
        return GetCoverageUseCase(coverage_repository)
    
    def _create_predict_coverage_use_case(self) -> PredictCoverageUseCase:
        """創建預測覆蓋用例"""
        satellite_repository = self.resolve(SatelliteRepository)
        prediction_service = self.resolve(PredictionService)
        return PredictCoverageUseCase(satellite_repository, prediction_service)
    
    def _create_cache_service(self) -> CacheService:
        """創建快取服務
        
        優先使用 Redis，如果不可用則使用記憶體快取
        """
        # 從環境變數讀取設定
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        redis_password = os.getenv("REDIS_PASSWORD", None)
        
        if REDIS_AVAILABLE:
            try:
                # 嘗試建立 Redis 連線
                cache_service = RedisCacheService(
                    host=redis_host,
                    port=redis_port,
                    password=redis_password
                )
                logger.info("使用 Redis 快取服務")
                return cache_service
            except Exception as e:
                logger.warning(f"無法連線到 Redis，切換到記憶體快取: {e}")
        else:
            logger.warning("Redis 套件未安裝，使用記憶體快取")
        
        # 後備方案：使用記憶體快取
        return MemoryCacheService(max_size=10000)


# 全域容器實例
_container: Optional[Container] = None


def get_container() -> Container:
    """獲取容器實例

    Returns:
        Container: 容器實例
    """
    global _container
    if _container is None:
        _container = Container()
    return _container


def reset_container():
    """重置容器（主要用於測試）"""
    global _container
    _container = None
