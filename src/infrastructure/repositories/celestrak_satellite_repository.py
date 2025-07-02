"""
Celestrak 衛星資料庫實作
"""

import json
import logging
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

try:
    import aiohttp

    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

from ...domain.constants import CacheConstants, NetworkConstants, SatelliteConstants
from ...domain.entities.satellite import Satellite
from ...domain.repositories.satellite_repository import SatelliteRepository
from ...domain.value_objects.orbital_elements import OrbitalElements

logger = logging.getLogger(__name__)


class CelestrakSatelliteRepository(SatelliteRepository):
    """從 Celestrak 獲取衛星 TLE 資料的資料庫實作"""

    CELESTRAK_URL = f"{NetworkConstants.CELESTRAK_BASE_URL}{NetworkConstants.CELESTRAK_TLE_ENDPOINT}?GROUP={NetworkConstants.CELESTRAK_STARLINK_GROUP}&FORMAT={NetworkConstants.CELESTRAK_TLE_FORMAT}"
    CACHE_FILE = f"{CacheConstants.DEFAULT_CACHE_DIR}/{CacheConstants.DEFAULT_CACHE_FILE}"
    CACHE_DURATION_HOURS = CacheConstants.DEFAULT_CACHE_DURATION_HOURS

    def __init__(self, cache_dir: str = "data"):
        """初始化 Celestrak 資料庫

        Args:
            cache_dir: 快取目錄
        """
        # 驗證路徑安全性
        cache_path = Path(cache_dir).resolve()
        base_path = Path.cwd().resolve()

        # 確保快取目錄在專案目錄內
        try:
            cache_path.relative_to(base_path)
        except ValueError:
            raise ValueError(f"Cache directory must be within project directory: {cache_dir}")

        self.cache_dir = cache_path
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_file = self.cache_dir / "starlink_tle_cache.json"
        self._satellites_cache: Optional[List[Satellite]] = None
        self._satellites_index: Dict[str, Satellite] = {}

    async def get_all_satellites(self) -> List[Satellite]:
        """獲取所有衛星"""
        if self._satellites_cache is None:
            await self._load_satellites()
        return self._satellites_cache or []

    async def get_active_satellites(self) -> List[Satellite]:
        """獲取所有活躍的衛星"""
        all_satellites = await self.get_all_satellites()
        return [sat for sat in all_satellites if sat.is_active]

    async def get_satellite_by_id(self, satellite_id: str) -> Optional[Satellite]:
        """根據 ID 獲取衛星"""
        # 驗證衛星 ID 格式
        if not self._validate_satellite_id(satellite_id):
            logger.warning(f"Invalid satellite ID format: {satellite_id}")
            return None

        # 使用索引快速查找
        if not self._satellites_index:
            await self.get_all_satellites()

        return self._satellites_index.get(satellite_id)

    async def get_satellites_by_name_pattern(self, pattern: str) -> List[Satellite]:
        """根據名稱模式獲取衛星"""
        all_satellites = await self.get_all_satellites()

        # 將通配符轉換為正則表達式
        regex_pattern = pattern.replace("*", ".*").replace("?", ".")
        regex = re.compile(regex_pattern, re.IGNORECASE)

        return [sat for sat in all_satellites if regex.match(sat.name)]

    async def update_satellite_tle(self, satellite_id: str, tle_data: dict) -> bool:
        """更新衛星的 TLE 資料"""
        # 在這個實作中，我們不支援單獨更新
        # 實際應用中可能需要實作此功能
        return False

    async def get_last_update_time(self) -> Optional[datetime]:
        """獲取最後更新時間"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r") as f:
                    cache_data = json.load(f)
                    last_update_str = cache_data.get("last_update")
                    if last_update_str:
                        return datetime.fromisoformat(last_update_str)
            except (FileNotFoundError, json.JSONDecodeError, ValueError, KeyError) as e:
                logger.warning(f"Unable to read cache data: {e}")
        return None

    async def _load_satellites(self) -> None:
        """載入衛星資料"""
        # 檢查快取
        if await self._is_cache_valid():
            await self._load_from_cache()
        else:
            await self._load_from_network()

    async def _is_cache_valid(self) -> bool:
        """檢查快取是否有效"""
        if not self.cache_file.exists():
            return False

        last_update = await self.get_last_update_time()
        if last_update is None:
            return False

        hours_since_update = (datetime.now() - last_update).total_seconds() / 3600
        return hours_since_update < self.CACHE_DURATION_HOURS

    async def _load_from_cache(self) -> None:
        """從快取載入"""
        with open(self.cache_file, "r") as f:
            cache_data = json.load(f)

        self._satellites_cache = []
        self._satellites_index = {}
        for sat_data in cache_data.get("satellites", []):
            satellite = self._parse_satellite_data(sat_data)
            if satellite:
                self._satellites_cache.append(satellite)
                self._satellites_index[satellite.satellite_id] = satellite

    async def _load_from_network(self) -> None:
        """從網路載入"""
        if not AIOHTTP_AVAILABLE:
            # 如果沒有 aiohttp，嘗試使用同步方式
            import requests

            response = requests.get(self.CELESTRAK_URL)
            tle_data = response.text
        else:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.CELESTRAK_URL) as response:
                    tle_data = await response.text()

        # 解析 TLE 資料
        satellites = self._parse_tle_data(tle_data)
        self._satellites_cache = satellites

        # 建立索引
        self._satellites_index = {sat.satellite_id: sat for sat in satellites}

        # 儲存到快取
        await self._save_to_cache(satellites)

    def _parse_tle_data(self, tle_data: str) -> List[Satellite]:
        """解析 TLE 資料"""
        satellites = []
        lines = tle_data.strip().split("\n")

        i = 0
        while i < len(lines):
            if i + 2 < len(lines):
                name = lines[i].strip()
                line1 = lines[i + 1].strip()
                line2 = lines[i + 2].strip()

                if line1.startswith("1 ") and line2.startswith("2 "):
                    satellite = self._create_satellite_from_tle(name, line1, line2)
                    if satellite:
                        satellites.append(satellite)

                i += 3
            else:
                break

        return satellites

    def _create_satellite_from_tle(self, name: str, line1: str, line2: str) -> Optional[Satellite]:
        """從 TLE 創建衛星實體"""
        try:
            # 驗證 TLE 格式
            if not (
                line1.startswith(SatelliteConstants.TLE_LINE1_PREFIX)
                and line2.startswith(SatelliteConstants.TLE_LINE2_PREFIX)
                and len(line1) >= SatelliteConstants.TLE_LINE_LENGTH
                and len(line2) >= SatelliteConstants.TLE_LINE_LENGTH
            ):
                logger.warning(f"Invalid TLE format for satellite: {name}")
                return None

            # 解析 TLE Line 1
            satellite_id = line1[SatelliteConstants.TLE_SATELLITE_ID_START : SatelliteConstants.TLE_SATELLITE_ID_END].strip()

            # 驗證衛星 ID
            if not self._validate_satellite_id(satellite_id):
                logger.warning(f"Invalid satellite ID in TLE: {satellite_id}")
                return None
            epoch_year = int(line1[SatelliteConstants.TLE_EPOCH_YEAR_START : SatelliteConstants.TLE_EPOCH_YEAR_END])
            epoch_day = float(line1[SatelliteConstants.TLE_EPOCH_DAY_START : SatelliteConstants.TLE_EPOCH_DAY_END])

            # 解析 TLE Line 2
            inclination = float(line2[SatelliteConstants.TLE_INCLINATION_START : SatelliteConstants.TLE_INCLINATION_END])
            raan = float(line2[SatelliteConstants.TLE_RAAN_START : SatelliteConstants.TLE_RAAN_END])
            eccentricity = float(
                "0." + line2[SatelliteConstants.TLE_ECCENTRICITY_START : SatelliteConstants.TLE_ECCENTRICITY_END]
            )
            arg_perigee = float(line2[SatelliteConstants.TLE_ARG_PERIGEE_START : SatelliteConstants.TLE_ARG_PERIGEE_END])
            mean_anomaly = float(line2[SatelliteConstants.TLE_MEAN_ANOMALY_START : SatelliteConstants.TLE_MEAN_ANOMALY_END])
            mean_motion = float(line2[SatelliteConstants.TLE_MEAN_MOTION_START : SatelliteConstants.TLE_MEAN_MOTION_END])

            # 計算 epoch 時間
            year = (
                SatelliteConstants.YEAR_2000 + epoch_year
                if epoch_year < SatelliteConstants.YEAR_CUTOFF
                else SatelliteConstants.YEAR_1900 + epoch_year
            )
            epoch = datetime(year, 1, 1) + timedelta(days=epoch_day - 1)

            # 創建軌道元素
            orbital_elements = OrbitalElements(
                epoch=epoch,
                inclination=inclination,
                raan=raan,
                eccentricity=eccentricity,
                arg_perigee=arg_perigee,
                mean_anomaly=mean_anomaly,
                mean_motion=mean_motion,
            )

            # 創建衛星實體
            return Satellite(satellite_id=satellite_id, name=name, orbital_elements=orbital_elements, is_active=True)

        except (ValueError, IndexError) as e:
            logger.error(f"Failed to parse TLE for {name}: {e}")
            return None

    def _parse_satellite_data(self, data: dict) -> Optional[Satellite]:
        """從字典解析衛星資料"""
        try:
            orbital_elements = OrbitalElements(
                epoch=datetime.fromisoformat(data["orbital_elements"]["epoch"]),
                inclination=data["orbital_elements"]["inclination"],
                raan=data["orbital_elements"]["raan"],
                eccentricity=data["orbital_elements"]["eccentricity"],
                arg_perigee=data["orbital_elements"]["arg_perigee"],
                mean_anomaly=data["orbital_elements"]["mean_anomaly"],
                mean_motion=data["orbital_elements"]["mean_motion"],
                bstar=data["orbital_elements"].get("bstar", 0.0),
            )

            return Satellite(
                satellite_id=data["satellite_id"],
                name=data["name"],
                orbital_elements=orbital_elements,
                launch_date=datetime.fromisoformat(data["launch_date"]) if data.get("launch_date") else None,
                is_active=data.get("is_active", True),
            )
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Failed to parse satellite data: {e}")
            return None

    async def _save_to_cache(self, satellites: List[Satellite]) -> None:
        """儲存到快取"""
        cache_data = {"last_update": datetime.now().isoformat(), "satellites": []}

        for sat in satellites:
            sat_data = {
                "satellite_id": sat.satellite_id,
                "name": sat.name,
                "orbital_elements": {
                    "epoch": sat.orbital_elements.epoch.isoformat(),
                    "inclination": sat.orbital_elements.inclination,
                    "raan": sat.orbital_elements.raan,
                    "eccentricity": sat.orbital_elements.eccentricity,
                    "arg_perigee": sat.orbital_elements.arg_perigee,
                    "mean_anomaly": sat.orbital_elements.mean_anomaly,
                    "mean_motion": sat.orbital_elements.mean_motion,
                    "bstar": sat.orbital_elements.bstar,
                },
                "launch_date": sat.launch_date.isoformat() if sat.launch_date else None,
                "is_active": sat.is_active,
            }
            cache_data["satellites"].append(sat_data)

        with open(self.cache_file, "w") as f:
            json.dump(cache_data, f, indent=2)

    def _validate_satellite_id(self, satellite_id: str) -> bool:
        """驗證衛星 ID 格式"""
        # 允許數字、字母和連字符
        return bool(re.match(SatelliteConstants.SATELLITE_ID_PATTERN, satellite_id, re.IGNORECASE))
