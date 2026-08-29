"""Unit tests for CdtProcessor transformation component."""

from unittest.mock import MagicMock
import pytest

from src.transformations.cdt_processor import CdtProcessor


@pytest.fixture
def cdt_processor():
    mock_spark = MagicMock()
    return CdtProcessor(mock_spark)


def test_calculate_column_sum_empty(cdt_processor):
    mock_df = MagicMock()
    mock_df.isEmpty.return_value = True
    assert cdt_processor.calculate_column_sum(mock_df, "total_renewal") == 0.0

    mock_df.isEmpty.return_value = False
    mock_df.agg.return_value.first.return_value = {"cnt": 0, "total_sum": 0.0, "first_val": 0.0}
    assert cdt_processor.calculate_column_sum(mock_df, "total_renewal") == 0.0


def test_calculate_column_sum_populated(cdt_processor):
    mock_df = MagicMock()
    mock_df.isEmpty.return_value = False
    mock_df.agg.return_value.first.return_value = {"cnt": 2, "total_sum": 150000.0, "first_val": 75000.0}
    assert cdt_processor.calculate_column_sum(mock_df, "total_renewal") == 150000.0

    mock_df.agg.return_value.first.return_value = {"cnt": 1, "total_sum": 75000.0, "first_val": 75000.0}
    assert cdt_processor.calculate_column_sum(mock_df, "total_renewal") == 75000.0


def test_cdt_renewals(cdt_processor):
    mock_df = MagicMock()
    mock_df.isEmpty.return_value = True
    assert cdt_processor.cdt_renewals(mock_df) == 0.0

    mock_df.isEmpty.return_value = False
    mock_df.agg.return_value.first.return_value = {"renewals": 50000.0}
    assert cdt_processor.cdt_renewals(mock_df) == 50000.0


def test_issuance_repurchase_empty(cdt_processor):
    mock_df = MagicMock()
    mock_df.isEmpty.return_value = True
    repurchases, cdt_issuance, bond_issuance = cdt_processor.issuance_repurchase(mock_df)
    assert repurchases == 0.0
    assert cdt_issuance == 0.0
    assert bond_issuance == 0.0


def test_issuance_repurchase_populated(cdt_processor):
    mock_df = MagicMock()
    mock_df.isEmpty.return_value = False

    filtered_mock = MagicMock()
    mock_df.filter.return_value = filtered_mock

    cdt_processor.calculate_column_sum = MagicMock(side_effect=[1000.0, 2000.0, 3000.0])

    repurchases, cdt_issuance, bond_issuance = cdt_processor.issuance_repurchase(mock_df)
    assert repurchases == 1000.0
    assert cdt_issuance == 2000.0
    assert bond_issuance == 3000.0
