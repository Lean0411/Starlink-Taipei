"""
覆蓋率儲存庫的單元測試
"""

from datetime import datetime
import pytest
import threading

from src.infrastructure.repositories.in_memory_coverage_repository import InMemoryCoverageRepository
from src.domain.entities.coverage_analysis import CoverageAnalysis, CoverageSnapshot
from src.domain.entities.observer import Observer
from src.domain.value_objects.position import Position


class TestInMemoryCoverageRepository:
    """記憶體覆蓋率儲存庫測試"""
    
    @pytest.fixture
    def repository(self):
        """建立儲存庫實例"""
        return InMemoryCoverageRepository()
    
    @pytest.fixture
    def test_coverage(self):
        """測試用覆蓋率分析"""
        observer = Observer(
            observer_id="OBS1",
            name="Test Observer",
            position=Position(25.0330, 121.5654, 10.0)
        )
        
        coverage = CoverageAnalysis(
            coverage_id="COVERAGE123",
            observer=observer,
            start_time=datetime(2024, 1, 1, 12, 0),
            end_time=datetime(2024, 1, 1, 13, 0),
            analyzed_satellites=["SAT1", "SAT2"]
        )
        
        # 添加一些快照
        coverage.add_snapshot(CoverageSnapshot(
            timestamp=datetime(2024, 1, 1, 12, 0),
            visible_satellites=["SAT1"],
            satellite_positions={}
        ))
        
        return coverage
    
    def test_save_and_find(self, repository, test_coverage):
        """測試保存和查找"""
        # 保存
        repository.save(test_coverage)
        
        # 查找
        found = repository.find_by_id("COVERAGE123")
        
        # 驗證
        assert found is not None
        assert found.coverage_id == "COVERAGE123"
        assert found.observer.observer_id == "OBS1"
        assert len(found.snapshots) == 1
    
    def test_find_non_existent(self, repository):
        """測試查找不存在的覆蓋率"""
        found = repository.find_by_id("NON_EXISTENT")
        assert found is None
    
    def test_delete_existing(self, repository, test_coverage):
        """測試刪除存在的覆蓋率"""
        # 保存
        repository.save(test_coverage)
        
        # 刪除
        result = repository.delete("COVERAGE123")
        
        # 驗證
        assert result is True
        assert repository.find_by_id("COVERAGE123") is None
    
    def test_delete_non_existent(self, repository):
        """測試刪除不存在的覆蓋率"""
        result = repository.delete("NON_EXISTENT")
        assert result is False
    
    def test_update_existing(self, repository, test_coverage):
        """測試更新已存在的覆蓋率"""
        # 保存原始資料
        repository.save(test_coverage)
        
        # 修改並再次保存
        test_coverage.add_snapshot(CoverageSnapshot(
            timestamp=datetime(2024, 1, 1, 12, 30),
            visible_satellites=["SAT1", "SAT2"],
            satellite_positions={}
        ))
        repository.save(test_coverage)
        
        # 查找並驗證
        found = repository.find_by_id("COVERAGE123")
        assert found is not None
        assert len(found.snapshots) == 2
    
    def test_get_all(self, repository):
        """測試獲取所有覆蓋率"""
        # 建立多個覆蓋率
        for i in range(3):
            observer = Observer(f"OBS{i}", f"Observer {i}", Position(0, 0, 0))
            coverage = CoverageAnalysis(
                coverage_id=f"COVERAGE{i}",
                observer=observer,
                start_time=datetime(2024, 1, 1, i, 0),
                end_time=datetime(2024, 1, 1, i + 1, 0)
            )
            repository.save(coverage)
        
        # 獲取所有
        all_coverages = repository.get_all()
        
        # 驗證
        assert len(all_coverages) == 3
        assert "COVERAGE0" in all_coverages
        assert "COVERAGE1" in all_coverages
        assert "COVERAGE2" in all_coverages
    
    def test_thread_safety(self, repository):
        """測試執行緒安全性"""
        results = []
        errors = []
        
        def save_coverage(coverage_id):
            try:
                observer = Observer(f"OBS{coverage_id}", "Observer", Position(0, 0, 0))
                coverage = CoverageAnalysis(
                    coverage_id=f"COVERAGE{coverage_id}",
                    observer=observer,
                    start_time=datetime(2024, 1, 1),
                    end_time=datetime(2024, 1, 2)
                )
                repository.save(coverage)
                results.append(coverage_id)
            except Exception as e:
                errors.append(e)
        
        # 建立多個執行緒同時保存
        threads = []
        for i in range(10):
            thread = threading.Thread(target=save_coverage, args=(i,))
            threads.append(thread)
            thread.start()
        
        # 等待所有執行緒完成
        for thread in threads:
            thread.join()
        
        # 驗證
        assert len(errors) == 0
        assert len(results) == 10
        assert len(repository.get_all()) == 10