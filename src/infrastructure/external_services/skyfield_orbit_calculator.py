"""
使用 Skyfield 的軌道計算器實作
"""
from datetime import datetime
from typing import Tuple, Dict, Any
import json

try:
    from skyfield.api import load, EarthSatellite, wgs84
    from skyfield.timelib import Time
    SKYFIELD_AVAILABLE = True
except ImportError:
    SKYFIELD_AVAILABLE = False

from ...domain.services.orbit_calculator import OrbitCalculator
from ...domain.entities.satellite import Satellite
from ...domain.value_objects.position import Position


class SkyfieldOrbitCalculator(OrbitCalculator):
    """使用 Skyfield 庫的軌道計算器實作
    
    這是基礎設施層的具體實作，依賴外部套件
    """
    
    def __init__(self):
        """初始化 Skyfield 軌道計算器"""
        if not SKYFIELD_AVAILABLE:
            raise ImportError("Skyfield 套件未安裝，請執行: pip install skyfield")
        
        self.ts = load.timescale()
        self._satellite_cache: Dict[str, EarthSatellite] = {}
    
    def _get_skyfield_satellite(self, satellite: Satellite) -> EarthSatellite:
        """獲取或創建 Skyfield 衛星物件
        
        Args:
            satellite: 領域衛星實體
            
        Returns:
            EarthSatellite: Skyfield 衛星物件
        """
        if satellite.satellite_id in self._satellite_cache:
            return self._satellite_cache[satellite.satellite_id]
        
        # 從衛星實體重建 TLE
        # 這裡需要將領域模型轉換為 Skyfield 需要的格式
        # 實際實作中，可能需要在衛星實體中保存原始 TLE 行
        tle_line1 = self._build_tle_line1(satellite)
        tle_line2 = self._build_tle_line2(satellite)
        
        skyfield_sat = EarthSatellite(tle_line1, tle_line2, satellite.name, self.ts)
        self._satellite_cache[satellite.satellite_id] = skyfield_sat
        
        return skyfield_sat
    
    def _build_tle_line1(self, satellite: Satellite) -> str:
        """構建 TLE 第一行
        
        這是簡化版本，實際應用中需要完整的 TLE 格式
        """
        # TLE Line 1 格式（簡化）
        return f"1 {satellite.satellite_id}U 00000A   {satellite.orbital_elements.epoch.strftime('%y%j.%f')[:14]}  .00000000  00000-0  00000-0 0  9999"
    
    def _build_tle_line2(self, satellite: Satellite) -> str:
        """構建 TLE 第二行"""
        oe = satellite.orbital_elements
        return f"2 {satellite.satellite_id} {oe.inclination:8.4f} {oe.raan:8.4f} {oe.eccentricity*1e7:07.0f} {oe.arg_perigee:8.4f} {oe.mean_anomaly:8.4f} {oe.mean_motion:11.8f}00000"
    
    def calculate_position(self, satellite: Satellite, time: datetime) -> Position:
        """計算衛星位置
        
        Args:
            satellite: 衛星實體
            time: 計算時間
            
        Returns:
            Position: 衛星位置
        """
        skyfield_sat = self._get_skyfield_satellite(satellite)
        t = self.ts.utc(time.year, time.month, time.day, time.hour, time.minute, time.second)
        
        geocentric = skyfield_sat.at(t)
        subpoint = wgs84.subpoint(geocentric)
        
        return Position(
            latitude=subpoint.latitude.degrees,
            longitude=subpoint.longitude.degrees,
            elevation=subpoint.elevation.km * 1000  # 轉換為公尺
        )
    
    def calculate_pass_details(
        self,
        satellite: Satellite,
        observer_position: Position,
        time: datetime
    ) -> Tuple[float, float, float]:
        """計算衛星相對於觀測者的詳細資訊
        
        Args:
            satellite: 衛星實體
            observer_position: 觀測者位置
            time: 計算時間
            
        Returns:
            Tuple[float, float, float]: (方位角, 仰角, 距離)
        """
        skyfield_sat = self._get_skyfield_satellite(satellite)
        t = self.ts.utc(time.year, time.month, time.day, time.hour, time.minute, time.second)
        
        # 創建觀測者位置
        observer = wgs84.latlon(
            observer_position.latitude,
            observer_position.longitude,
            observer_position.elevation
        )
        
        # 計算相對位置
        difference = skyfield_sat - observer
        topocentric = difference.at(t)
        alt, az, distance = topocentric.altaz()
        
        return (
            az.degrees,  # 方位角
            alt.degrees,  # 仰角
            distance.km  # 距離（公里）
        )
    
    def is_sunlit(self, satellite: Satellite, time: datetime) -> bool:
        """檢查衛星是否被太陽照射
        
        Args:
            satellite: 衛星實體
            time: 計算時間
            
        Returns:
            bool: 是否被太陽照射
        """
        skyfield_sat = self._get_skyfield_satellite(satellite)
        t = self.ts.utc(time.year, time.month, time.day, time.hour, time.minute, time.second)
        
        # 檢查衛星是否在地球陰影中
        sunlit = skyfield_sat.at(t).is_sunlit(load('de421.bsp'))
        
        return bool(sunlit)