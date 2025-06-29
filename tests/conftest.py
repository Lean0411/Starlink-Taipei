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
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# 在導入任何模組之前模擬 torch
import sys
import types

# 創建 mock 模組
torch_mock = types.ModuleType("torch")
torch_nn_mock = types.ModuleType("torch.nn")
torch_nn_functional_mock = types.ModuleType("torch.nn.functional")
sklearn_mock = types.ModuleType("sklearn")
sklearn_preprocessing_mock = types.ModuleType("sklearn.preprocessing")


# 設置必要的屬性和類
class MockModule:
    pass


class MockTensor:
    def to(self, device):
        return self


torch_mock.nn = torch_nn_mock
torch_nn_mock.Module = MockModule
torch_nn_mock.Linear = MockModule
torch_nn_mock.Conv1d = MockModule
torch_nn_mock.LayerNorm = MockModule
torch_nn_mock.Dropout = MockModule
torch_nn_mock.ModuleList = list
torch_nn_mock.functional = torch_nn_functional_mock
torch_nn_functional_mock.softmax = lambda x, dim: x
torch_nn_functional_mock.relu = lambda x: x
torch_mock.FloatTensor = MockTensor
torch_mock.device = lambda x: x
torch_mock.cuda = types.ModuleType("torch.cuda")
torch_mock.cuda.is_available = lambda: False
torch_mock.no_grad = lambda: type(
    "no_grad",
    (),
    {"__enter__": lambda self: None, "__exit__": lambda self, *args: None},
)()
torch_mock.load = lambda *args, **kwargs: {}
torch_mock.save = lambda *args, **kwargs: None

sklearn_mock.preprocessing = sklearn_preprocessing_mock
sklearn_preprocessing_mock.StandardScaler = type(
    "StandardScaler",
    (),
    {
        "fit_transform": lambda self, X: X,
        "transform": lambda self, X: X,
        "inverse_transform": lambda self, X: X,
    },
)

# 註冊 mock 模組
sys.modules["torch"] = torch_mock
sys.modules["torch.nn"] = torch_nn_mock
sys.modules["torch.nn.functional"] = torch_nn_functional_mock
sys.modules["sklearn"] = sklearn_mock
sys.modules["sklearn.preprocessing"] = sklearn_preprocessing_mock


# 模擬 torch 以避免在測試中需要安裝完整的 PyTorch
@pytest.fixture(autouse=True)
def mock_torch():
    """自動模擬 torch 模組"""
    with patch.dict(
        "sys.modules",
        {
            "torch": type(sys)("torch"),
            "torch.nn": type(sys)("torch.nn"),
            "torch.nn.functional": type(sys)("torch.nn.functional"),
            "sklearn": type(sys)("sklearn"),
            "sklearn.preprocessing": type(sys)("sklearn.preprocessing"),
        },
    ):
        # 設置必要的屬性
        sys.modules["torch"].nn = sys.modules["torch.nn"]
        sys.modules["torch"].nn.Module = type("Module", (), {})
        sys.modules["torch"].nn.Linear = type("Linear", (), {})
        sys.modules["torch"].nn.Conv1d = type("Conv1d", (), {})
        sys.modules["torch"].nn.LayerNorm = type("LayerNorm", (), {})
        sys.modules["torch"].nn.Dropout = type("Dropout", (), {})
        sys.modules["torch"].nn.ModuleList = type("ModuleList", (), {})
        sys.modules["torch"].nn.functional = sys.modules["torch.nn.functional"]
        sys.modules["torch"].nn.functional.softmax = lambda x, dim: x
        sys.modules["torch"].nn.functional.relu = lambda x: x
        sys.modules["torch"].FloatTensor = type("FloatTensor", (), {})
        sys.modules["torch"].device = type("device", (), {})
        sys.modules["torch"].cuda = type(sys)("cuda")
        sys.modules["torch"].cuda.is_available = lambda: False
        sys.modules["torch"].no_grad = lambda: type(
            "no_grad",
            (),
            {"__enter__": lambda self: None, "__exit__": lambda self, *args: None},
        )()
        sys.modules["torch"].load = lambda *args, **kwargs: {}
        sys.modules["torch"].save = lambda *args, **kwargs: None

        sys.modules["sklearn.preprocessing"].StandardScaler = type(
            "StandardScaler",
            (),
            {
                "fit_transform": lambda self, X: X,
                "transform": lambda self, X: X,
                "inverse_transform": lambda self, X: X,
            },
        )

        yield
