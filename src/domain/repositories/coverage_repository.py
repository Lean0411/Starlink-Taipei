"""
覆蓋率儲存庫介面 - 領域層
"""

from abc import ABC, abstractmethod
from typing import Optional

from ..entities.coverage_analysis import CoverageAnalysis


class CoverageRepository(ABC):
    """覆蓋率分析結果儲存庫介面"""
    
    @abstractmethod
    def save(self, coverage: CoverageAnalysis) -> None:
        """保存覆蓋率分析結果
        
        Args:
            coverage: 覆蓋率分析結果
        """
        pass
    
    @abstractmethod
    def find_by_id(self, coverage_id: str) -> Optional[CoverageAnalysis]:
        """根據 ID 查找覆蓋率分析結果
        
        Args:
            coverage_id: 覆蓋率分析 ID
            
        Returns:
            Optional[CoverageAnalysis]: 找到的分析結果，如果不存在則返回 None
        """
        pass
    
    @abstractmethod
    def delete(self, coverage_id: str) -> bool:
        """刪除覆蓋率分析結果
        
        Args:
            coverage_id: 覆蓋率分析 ID
            
        Returns:
            bool: 是否成功刪除
        """
        pass