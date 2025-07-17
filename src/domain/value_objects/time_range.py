"""
時間範圍值物件
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class TimeRange:
    """時間範圍值物件
    
    表示一段時間區間，包含開始和結束時間。
    這是一個不可變的值物件。
    """
    
    start: datetime
    end: datetime
    
    @property
    def duration_seconds(self) -> float:
        """持續時間（秒）"""
        return (self.end - self.start).total_seconds()
    
    @property
    def duration_minutes(self) -> float:
        """持續時間（分鐘）"""
        return self.duration_seconds / 60
    
    @property
    def duration_hours(self) -> float:
        """持續時間（小時）"""
        return self.duration_seconds / 3600
    
    def contains(self, time: datetime) -> bool:
        """檢查時間點是否在範圍內
        
        Args:
            time: 要檢查的時間點
            
        Returns:
            bool: 是否在範圍內（包含邊界）
        """
        return self.start <= time <= self.end
    
    def overlaps(self, other: "TimeRange") -> bool:
        """檢查是否與另一個時間範圍重疊
        
        Args:
            other: 另一個時間範圍
            
        Returns:
            bool: 是否重疊
        """
        return not (self.end < other.start or self.start > other.end)
    
    def is_valid(self) -> bool:
        """檢查時間範圍是否有效
        
        Returns:
            bool: 是否有效（結束時間不早於開始時間）
        """
        return self.end >= self.start
    
    def __str__(self) -> str:
        """字串表示"""
        return f"{self.start.isoformat()} - {self.end.isoformat()}"