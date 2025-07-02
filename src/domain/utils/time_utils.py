"""
時間處理工具函數
"""

from datetime import datetime
from typing import Any


class TimeUtils:
    """時間處理工具類"""

    @staticmethod
    def datetime_to_skyfield(ts: Any, dt: datetime) -> Any:
        """將 datetime 轉換為 Skyfield 時間物件

        Args:
            ts: Skyfield Timescale 物件
            dt: datetime 物件

        Returns:
            Skyfield Time 物件
        """
        return ts.utc(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)

    @staticmethod
    def julian_date_to_datetime(jd: float) -> datetime:
        """將儒略日期轉換為 datetime

        Args:
            jd: 儒略日期

        Returns:
            datetime 物件
        """
        # 儒略日期起始點：西元前4713年1月1日中午12點
        # Unix 時間戳起始點：1970年1月1日 00:00:00 UTC
        # 儒略日期 2440587.5 = 1970年1月1日 00:00:00 UTC
        unix_timestamp = (jd - 2440587.5) * 86400.0
        return datetime.utcfromtimestamp(unix_timestamp)

    @staticmethod
    def datetime_to_julian_date(dt: datetime) -> float:
        """將 datetime 轉換為儒略日期

        Args:
            dt: datetime 物件

        Returns:
            儒略日期
        """
        # 計算從 Unix 紀元開始的秒數
        unix_timestamp = dt.timestamp()
        # 轉換為儒略日期
        return unix_timestamp / 86400.0 + 2440587.5
