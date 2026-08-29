"""Unit tests for PygProcessor transformation component."""

from unittest.mock import MagicMock
import pytest

from src.transformations.pyg_processor import PygProcessor


@pytest.fixture
def pyg_processor():
    mock_spark = MagicMock()
    return PygProcessor(mock_spark)


def test_pyg_derivatives_empty(pyg_processor):
    mock_df = MagicMock()
    mock_df.isEmpty.return_value = True
    assert pyg_processor.pyg_derivatives(mock_df) == 0.0


def test_pyg_derivatives_populated(pyg_processor):
    mock_df = MagicMock()
    mock_df.isEmpty.return_value = False
    mock_df.agg.return_value.first.return_value = [75000.0]
    assert pyg_processor.pyg_derivatives(mock_df) == 75000.0
