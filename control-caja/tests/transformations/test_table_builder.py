"""Unit tests for TableBuilder transformation component."""

from datetime import date
from unittest.mock import Mock, MagicMock, patch
import pytest

from src.transformations.table_builder import TableBuilder
from src.utils.constants import BankConstants


@pytest.fixture
def table_builder():
    mock_spark = MagicMock()
    return TableBuilder(mock_spark)


def test_add_type_column(table_builder):
    mock_df = MagicMock()
    mock_res_df = MagicMock()
    mock_df.withColumn.return_value = mock_res_df

    # Available T-0
    res_t0 = table_builder.add_type_column(mock_df, BankConstants.AVAILABLE_T0)
    assert res_t0 == mock_res_df

    # Available T-1
    res_t1 = table_builder.add_type_column(mock_df, BankConstants.AVAILABLE_T1)
    assert res_t1 == mock_res_df

    # Other type string leaves base_df unchanged
    res_other = table_builder.add_type_column(mock_df, "")
    assert res_other == mock_df


def test_add_date_columns(table_builder):
    mock_df = MagicMock()
    mock_df.schema.fields = []
    mock_row = [100.0, 200.0]  # list is iterable
    mock_df.collect.return_value = [mock_row]

    created_df = MagicMock()
    mock_final_df = MagicMock()
    table_builder.spark.createDataFrame.return_value = created_df
    created_df.withColumn.return_value = mock_final_df

    date_list = [date(2026, 1, 9)]
    res = table_builder.add_date_columns(mock_df, date_list, BankConstants.AVAILABLE_T0)

    assert res == mock_final_df
    table_builder.spark.createDataFrame.assert_called_once()
    created_df.withColumn.assert_called_once()


def test_create_table(table_builder):
    inc_df = MagicMock()
    exp_df = MagicMock()
    t0_df = MagicMock()
    t1_df = MagicMock()
    sum_df = MagicMock()
    date_list = [date(2026, 1, 9)]

    with patch.object(table_builder, "add_date_columns", side_effect=lambda df, dl, t: df):
        r_inc, r_exp, r_t0, r_t1, r_sum = table_builder.create_table(
            inc_df, exp_df, t0_df, t1_df, sum_df, date_list
        )

        assert r_inc == inc_df
        assert r_exp == exp_df
        assert r_t0 == t0_df
        assert r_t1 == t1_df
        assert r_sum == sum_df
        assert table_builder.add_date_columns.call_count == 5
