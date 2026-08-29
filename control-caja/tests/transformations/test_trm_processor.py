"""Unit tests for TrmProcessor transformation component."""

from unittest.mock import MagicMock
import pytest

from src.transformations.trm_processor import TrmProcessor


@pytest.fixture
def trm_processor():
    mock_spark = MagicMock()
    return TrmProcessor(mock_spark)


def test_normalize_trm_empty(trm_processor):
    mock_df = MagicMock()
    mock_df.isEmpty.return_value = True
    assert trm_processor.normalize_trm(mock_df) == 0.0


def test_normalize_trm_populated(trm_processor):
    mock_df = MagicMock()
    mock_df.isEmpty.return_value = False
    mock_df.agg.return_value.first.return_value = {"total": 4125.50}
    assert trm_processor.normalize_trm(mock_df) == 4125.50
