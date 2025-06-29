"""
依賴注入容器 - 管理應用程式的依賴關係
"""

from typing import Dict, Type, Any, Optional
import inspect

from ...domain.repositories.satellite_repository import SatelliteRepository
from ...domain.services.orbit_calculator import OrbitCalculator
from ...domain.services.coverage_analyzer import CoverageAnalyzer
from ...domain.services.prediction_service import PredictionService
from ...application.use_cases.analyze_coverage_use_case import AnalyzeCoverageUseCase
from ...application.use_cases.predict_coverage_use_case import PredictCoverageUseCase
from ..repositories.celestrak_satellite_repository import CelestrakSatelliteRepository
from ..external_services.skyfield_orbit_calculator import SkyfieldOrbitCalculator
from ..external_services.orbit_prediction_service import OrbitPredictionService


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
        # 註冊基礎設施服務
        self.register_singleton(OrbitCalculator, SkyfieldOrbitCalculator)
        self.register_singleton(SatelliteRepository, CelestrakSatelliteRepository)

        # 註冊領域服務
        self.register_factory(CoverageAnalyzer, self._create_coverage_analyzer)
        self.register_factory(PredictionService, self._create_prediction_service)

        # 註冊應用服務
        self.register_factory(AnalyzeCoverageUseCase, self._create_analyze_coverage_use_case)
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

    def _create_coverage_analyzer(self) -> CoverageAnalyzer:
        """創建覆蓋率分析器"""
        orbit_calculator = self.resolve(OrbitCalculator)
        return CoverageAnalyzer(orbit_calculator)

    def _create_analyze_coverage_use_case(self) -> AnalyzeCoverageUseCase:
        """創建分析覆蓋率用例"""
        satellite_repository = self.resolve(SatelliteRepository)
        coverage_analyzer = self.resolve(CoverageAnalyzer)
        return AnalyzeCoverageUseCase(satellite_repository, coverage_analyzer)
    
    def _create_prediction_service(self) -> PredictionService:
        """創建預測服務"""
        orbit_calculator = self.resolve(OrbitCalculator)
        return OrbitPredictionService(orbit_calculator)
    
    def _create_predict_coverage_use_case(self) -> PredictCoverageUseCase:
        """創建預測覆蓋用例"""
        satellite_repository = self.resolve(SatelliteRepository)
        prediction_service = self.resolve(PredictionService)
        return PredictCoverageUseCase(satellite_repository, prediction_service)


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

