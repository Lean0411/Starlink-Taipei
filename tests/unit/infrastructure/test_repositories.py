"""基礎設施層 Repository 的單元測試"""

import pytest
import asyncio
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import requests
from src.infrastructure.repositories.celestrak_satellite_repository import CelestrakSatelliteRepository
from src.domain.entities.satellite import Satellite


class TestCelestrakSatelliteRepository:
    """測試 Celestrak 衛星資料庫"""

    @pytest.fixture
    def mock_tle_data(self):
        """模擬 TLE 數據"""
        return """STARLINK-1234
1 47562U 21009A   25001.50000000  .00001234  00000-0  12345-4 0  9999
2 47562  53.0540  100.1234   0001500  90.0000 270.1234  15.06390000123456
STARLINK-5678
1 47563U 21009B   25001.50000000  .00001234  00000-0  12345-4 0  9999
2 47563  53.0540  100.1234   0001500  90.0000 270.1234  15.06390000123456"""

    @patch("requests.get")
    @pytest.mark.asyncio
    async def test_get_active_satellites_success(self, mock_get, mock_tle_data):
        """測試成功獲取活躍衛星"""
        # 設置模擬響應
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = mock_tle_data
        mock_get.return_value = mock_response

        repo = CelestrakSatelliteRepository()
        satellites = await repo.get_active_satellites()

        # 驗證結果
        assert len(satellites) == 2
        assert all(isinstance(sat, Satellite) for sat in satellites)
        assert satellites[0].name == "STARLINK-1234"
        assert satellites[1].name == "STARLINK-5678"
        assert all(sat.is_active for sat in satellites)

    @patch("requests.get")
    @pytest.mark.asyncio
    async def test_get_active_satellites_api_error(self, mock_get):
        """測試 API 錯誤處理"""
        # 模擬 API 錯誤
        mock_get.side_effect = requests.RequestException("Connection error")

        repo = CelestrakSatelliteRepository()
        satellites = await repo.get_active_satellites()

        # 應該返回空列表而不是拋出異常
        assert satellites == []

    @patch("requests.get")
    @pytest.mark.asyncio
    async def test_get_active_satellites_invalid_response(self, mock_get):
        """測試無效響應處理"""
        # 模擬無效的 TLE 數據
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "Invalid TLE data"
        mock_get.return_value = mock_response

        repo = CelestrakSatelliteRepository()
        satellites = await repo.get_active_satellites()

        # 應該返回空列表
        assert satellites == []

    @patch("requests.get")
    @pytest.mark.asyncio
    async def test_get_satellite_by_id_found(self, mock_get, mock_tle_data):
        """測試通過 ID 獲取衛星 - 找到"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = mock_tle_data
        mock_get.return_value = mock_response

        repo = CelestrakSatelliteRepository()
        satellite = await repo.get_satellite_by_id("47562")

        assert satellite is not None
        assert satellite.satellite_id == "47562"
        assert satellite.name == "STARLINK-1234"

    @patch("requests.get")
    @pytest.mark.asyncio
    async def test_get_satellite_by_id_not_found(self, mock_get, mock_tle_data):
        """測試通過 ID 獲取衛星 - 未找到"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = mock_tle_data
        mock_get.return_value = mock_response

        repo = CelestrakSatelliteRepository()
        satellite = await repo.get_satellite_by_id("99999")

        assert satellite is None

    def test_parse_tle_valid(self):
        """測試解析有效的 TLE"""
        repo = CelestrakSatelliteRepository()

        tle_data = """STARLINK-1234
1 47562U 21009A   25001.50000000  .00001234  00000-0  12345-4 0  9999
2 47562  53.0540  100.1234   0001500  90.0000 270.1234  15.06390000123456"""

        satellites = repo._parse_tle_data(tle_data)

        assert len(satellites) == 1
        satellite = satellites[0]
        assert satellite.satellite_id == "47562"
        assert satellite.name == "STARLINK-1234"
        assert satellite.orbital_elements.inclination == pytest.approx(53.0540, rel=0.0001)
        assert satellite.orbital_elements.eccentricity == pytest.approx(0.0001500, rel=0.0001)

    def test_parse_tle_invalid(self):
        """測試解析無效的 TLE"""
        repo = CelestrakSatelliteRepository()

        # 無效的 TLE 格式
        invalid_tle_data = """INVALID
NOT A TLE
INVALID DATA"""

        satellites = repo._parse_tle_data(invalid_tle_data)
        assert len(satellites) == 0

    @patch("requests.get")
    @pytest.mark.asyncio
    async def test_get_satellites_by_name_pattern(self, mock_get, mock_tle_data):
        """測試通過名稱模式獲取衛星"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = mock_tle_data
        mock_get.return_value = mock_response

        repo = CelestrakSatelliteRepository()
        satellites = await repo.get_satellites_by_name_pattern("STARLINK")

        assert len(satellites) == 2
        assert all("STARLINK" in sat.name for sat in satellites)

    @pytest.mark.asyncio
    async def test_tle_cache(self):
        """測試 TLE 緩存機制"""
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = """STARLINK-1234
1 47562U 21009A   25001.50000000  .00001234  00000-0  12345-4 0  9999
2 47562  53.0540  100.1234   0001500  90.0000 270.1234  15.06390000123456"""
            mock_get.return_value = mock_response

            repo = CelestrakSatelliteRepository()

            # 第一次調用
            satellites1 = await repo.get_active_satellites()
            assert len(satellites1) == 1

            # 第二次調用應該使用緩存
            satellites2 = await repo.get_active_satellites()
            assert len(satellites2) == 1

            # API 應該只被調用一次
            assert mock_get.call_count == 1
