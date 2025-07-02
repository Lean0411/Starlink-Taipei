"""
領域層常量定義
"""

from datetime import timedelta


class SatelliteConstants:
    """衛星相關常量"""

    # TLE 格式常量
    TLE_LINE1_PREFIX = "1 "
    TLE_LINE2_PREFIX = "2 "
    TLE_LINE_LENGTH = 69
    TLE_SATELLITE_ID_START = 2
    TLE_SATELLITE_ID_END = 7
    TLE_EPOCH_YEAR_START = 18
    TLE_EPOCH_YEAR_END = 20
    TLE_EPOCH_DAY_START = 20
    TLE_EPOCH_DAY_END = 32

    # TLE Line 2 索引位置
    TLE_INCLINATION_START = 8
    TLE_INCLINATION_END = 16
    TLE_RAAN_START = 17
    TLE_RAAN_END = 25
    TLE_ECCENTRICITY_START = 26
    TLE_ECCENTRICITY_END = 33
    TLE_ARG_PERIGEE_START = 34
    TLE_ARG_PERIGEE_END = 42
    TLE_MEAN_ANOMALY_START = 43
    TLE_MEAN_ANOMALY_END = 51
    TLE_MEAN_MOTION_START = 52
    TLE_MEAN_MOTION_END = 63

    # 年份轉換常量
    YEAR_2000 = 2000
    YEAR_1900 = 1900
    YEAR_CUTOFF = 50

    # 軌道計算常量
    ECCENTRICITY_MULTIPLIER = 1e7
    KM_TO_METERS = 1000.0

    # 衛星 ID 格式
    SATELLITE_ID_PATTERN = r"^[A-Z0-9-]+$"
    STARLINK_ID_PREFIX = "STARLINK-"


class CacheConstants:
    """快取相關常量"""

    DEFAULT_CACHE_DIR = "data"
    DEFAULT_CACHE_FILE = "starlink_tle_cache.json"
    DEFAULT_CACHE_DURATION_HOURS = 24
    MIN_CACHE_DURATION_HOURS = 1
    MAX_CACHE_DURATION_HOURS = 168  # 一週

    # 快取大小限制
    MAX_SATELLITES_IN_CACHE = 10000


class PredictionConstants:
    """預測相關常量"""

    # 預測時間尺度（小時）
    SHORT_TERM_HOURS = 1
    MEDIUM_TERM_HOURS = 24
    LONG_TERM_HOURS = 168  # 7 天

    # 預測參數
    DEFAULT_MIN_ELEVATION = 25.0  # 度
    DEFAULT_MIN_SATELLITES_FOR_WINDOW = 30
    DEFAULT_PREDICTION_INTERVAL_MINUTES = 5

    # 不確定性參數
    BASE_UNCERTAINTY_SATELLITES = 2.0
    BASE_UNCERTAINTY_ELEVATION = 1.5
    BASE_UNCERTAINTY_COVERAGE = 3.0


class ObserverConstants:
    """觀測者相關常量"""

    # 台北預設位置
    TAIPEI_LATITUDE = 25.0330
    TAIPEI_LONGITUDE = 121.5654
    TAIPEI_ALTITUDE = 10.0  # 公尺

    # 觀測限制
    MIN_ELEVATION = 0.0
    MAX_ELEVATION = 90.0
    MIN_AZIMUTH = 0.0
    MAX_AZIMUTH = 360.0


class TimeConstants:
    """時間相關常量"""

    # 儒略日期常量
    JULIAN_DATE_EPOCH = 2440587.5  # 1970年1月1日 00:00:00 UTC
    SECONDS_PER_DAY = 86400.0

    # 時間間隔
    ONE_HOUR = timedelta(hours=1)
    ONE_DAY = timedelta(days=1)
    ONE_WEEK = timedelta(days=7)


class NetworkConstants:
    """網路相關常量"""

    # Celestrak API
    CELESTRAK_BASE_URL = "https://celestrak.org"
    CELESTRAK_TLE_ENDPOINT = "/NORAD/elements/gp.php"
    CELESTRAK_STARLINK_GROUP = "starlink"
    CELESTRAK_TLE_FORMAT = "tle"

    # 請求逾時
    DEFAULT_REQUEST_TIMEOUT = 30  # 秒
    MAX_REQUEST_RETRIES = 3
    RETRY_DELAY = 1  # 秒
