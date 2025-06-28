# MIT License
# Copyright (c) 2025 Starlink Taipei Analysis Team
#
# This file is part of the Starlink Taipei Satellite Analysis System.

"""
pytest 配置和 fixtures
"""

import sys
import os
import pytest
from unittest.mock import patch

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 模擬 torch 以避免在測試中需要安裝完整的 PyTorch
@pytest.fixture(autouse=True)
def mock_torch():
    """自動模擬 torch 模組"""
    with patch.dict('sys.modules', {
        'torch': type(sys)('torch'),
        'torch.nn': type(sys)('torch.nn'),
        'torch.nn.functional': type(sys)('torch.nn.functional'),
        'sklearn': type(sys)('sklearn'),
        'sklearn.preprocessing': type(sys)('sklearn.preprocessing'),
    }):
        # 設置必要的屬性
        sys.modules['torch'].nn = sys.modules['torch.nn']
        sys.modules['torch'].nn.Module = type('Module', (), {})
        sys.modules['torch'].nn.Linear = type('Linear', (), {})
        sys.modules['torch'].nn.Conv1d = type('Conv1d', (), {})
        sys.modules['torch'].nn.LayerNorm = type('LayerNorm', (), {})
        sys.modules['torch'].nn.Dropout = type('Dropout', (), {})
        sys.modules['torch'].nn.ModuleList = type('ModuleList', (), {})
        sys.modules['torch'].nn.functional = sys.modules['torch.nn.functional']
        sys.modules['torch'].nn.functional.softmax = lambda x, dim: x
        sys.modules['torch'].nn.functional.relu = lambda x: x
        sys.modules['torch'].FloatTensor = type('FloatTensor', (), {})
        sys.modules['torch'].device = type('device', (), {})
        sys.modules['torch'].cuda = type(sys)('cuda')
        sys.modules['torch'].cuda.is_available = lambda: False
        sys.modules['torch'].no_grad = lambda: type('no_grad', (), {'__enter__': lambda self: None, '__exit__': lambda self, *args: None})()
        sys.modules['torch'].load = lambda *args, **kwargs: {}
        sys.modules['torch'].save = lambda *args, **kwargs: None
        
        sys.modules['sklearn.preprocessing'].StandardScaler = type('StandardScaler', (), {
            'fit_transform': lambda self, X: X,
            'transform': lambda self, X: X,
            'inverse_transform': lambda self, X: X
        })
        
        yield