"""Unit tests for AvailableTable transformation component."""

from unittest.mock import MagicMock
import pytest

from src.transformations.available_table import AvailableTable


@pytest.fixture
def available_table():
    mock_spark = MagicMock()
    return AvailableTable(mock_spark)


def test_create_available_df(available_table):
    mock_df = MagicMock()

    balances = [10.0] * 17  # 17 balances
    available_table.bank_processor.bank_balances = MagicMock(return_value=tuple(balances))

    mock_res_df = MagicMock()
    available_table.spark.createDataFrame.return_value = mock_res_df

    df, bank_usd, total = available_table.create_available_df(mock_df, trm=4000.0)

    assert df == mock_res_df
    assert bank_usd == 10.0 * 7 * 4000.0  # 7 USD accounts * TRM
    available_table.spark.createDataFrame.assert_called_once()
