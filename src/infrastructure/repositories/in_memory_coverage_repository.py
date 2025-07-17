"""
記憶體覆蓋率儲存庫實作
"""

from typing import Dict, Optional
import threading

from ...domain.entities.coverage_analysis import CoverageAnalysis
from ...domain.repositories.coverage_repository import CoverageRepository


class InMemoryCoverageRepository(CoverageRepository):
    """記憶體中的覆蓋率儲存庫實作
    
    這是一個簡單的實作，將資料存儲在記憶體中。
    實際應用中，應該使用持久化儲存（如資料庫）。
    """
    
    def __init__(self):
        """初始化儲存庫"""
        self._storage: Dict[str, CoverageAnalysis] = {}
        self._lock = threading.Lock()
    
    def save(self, coverage: CoverageAnalysis) -> None:
        """保存覆蓋率分析結果
        
        Args:
            coverage: 覆蓋率分析結果
        """
        with self._lock:
            self._storage[coverage.coverage_id] = coverage
    
    def find_by_id(self, coverage_id: str) -> Optional[CoverageAnalysis]:
        """根據 ID 查找覆蓋率分析結果
        
        Args:
            coverage_id: 覆蓋率分析 ID
            
        Returns:
            Optional[CoverageAnalysis]: 找到的分析結果
        """
        with self._lock:
            return self._storage.get(coverage_id)
    
    def delete(self, coverage_id: str) -> bool:
        """刪除覆蓋率分析結果
        
        Args:
            coverage_id: 覆蓋率分析 ID
            
        Returns:
            bool: 是否成功刪除
        """
        with self._lock:
            if coverage_id in self._storage:
                del self._storage[coverage_id]
                return True
            return False
    
    def get_all(self) -> Dict[str, CoverageAnalysis]:
        """獲取所有儲存的分析結果（用於調試）
        
        Returns:
            Dict[str, CoverageAnalysis]: 所有分析結果
        """
        with self._lock:
            return self._storage.copy()