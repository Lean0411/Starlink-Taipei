"""
獲取覆蓋率分析結果用例
"""

from typing import Optional

from ...domain.repositories.coverage_repository import CoverageRepository
from ..dto.coverage_response import CoverageResponse


class GetCoverageUseCase:
    """獲取覆蓋率分析結果的用例"""
    
    def __init__(self, coverage_repository: CoverageRepository):
        """初始化用例
        
        Args:
            coverage_repository: 覆蓋率儲存庫
        """
        self.coverage_repository = coverage_repository
    
    async def execute(self, coverage_id: str) -> Optional[CoverageResponse]:
        """獲取覆蓋率分析結果
        
        Args:
            coverage_id: 覆蓋率分析 ID
            
        Returns:
            Optional[CoverageResponse]: 分析結果，如果不存在則返回 None
        """
        # 從儲存庫獲取分析結果
        coverage = self.coverage_repository.find_by_id(coverage_id)
        
        if coverage is None:
            return None
        
        # 轉換為回應 DTO
        # 注意：這裡沒有 optimal_windows，因為它們不是持久化的一部分
        # 如果需要，可以重新計算或將它們也存儲起來
        response = CoverageResponse.from_domain(coverage, [])
        
        return response