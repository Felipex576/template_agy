"""Unit tests for QueryBuilder component."""

from datetime import date
from unittest.mock import MagicMock
import pytest

from src.queries.query_builder import QueryBuilder


@pytest.fixture
def query_builder():
    mock_spark = MagicMock()
    qb = QueryBuilder(
        spark=mock_spark,
        rtbcol_database="db_rtbcol",
        unity_database="db_unity",
        trm_database="db_trm",
        dominus_database="db_dominus",
        mambu_cc_database="db_mambu",
        checking_accounts_database="db_checking",
        adapter_database="db_adapter",
        unity_operations_table="tbl_unity_ops",
    )
    return qb


def test_normalize_dates(query_builder):
    dates = [date(2026, 1, 9), date(2026, 1, 8)]
    result = query_builder.normalize_dates(dates)
    assert result == "DATE '2026-01-09', DATE '2026-01-08'"


def test_date_between_fix(query_builder):
    def dummy_func(d):
        return f"{d}_start", f"{d}_end"

    dates = [date(2026, 1, 9)]
    condition, one_list, two_list = query_builder.date_between_fix(dates, dummy_func, "m.fecha")

    assert "m.fecha BETWEEN DATE '2026-01-09_start'" in condition
    assert "AND DATE '2026-01-09_end'" in condition
    assert one_list == ["2026-01-09_start"]
    assert two_list == ["2026-01-09_end"]


def test_get_bank_data(query_builder):
    query_builder.bank_processor.get_previous_date = MagicMock(return_value=date(2026, 1, 8))
    query_builder.bank_processor.adjust_year_end_dates = MagicMock(return_value=date(2026, 1, 8))

    mock_df = MagicMock()
    query_builder.spark.sql.return_value = mock_df

    df, prev_dates = query_builder.get_bank_data([date(2026, 1, 9)], [date(2026, 1, 8)], "tbl_bank")

    assert df == mock_df
    assert prev_dates == [date(2026, 1, 8)]
    query_builder.spark.sql.assert_called_once()
    sql_arg = query_builder.spark.sql.call_args[0][0]
    assert "glue_catalog.db_rtbcol.tbl_bank" in sql_arg
    assert "DATE '2026-01-08'" in sql_arg


def test_get_money_market_data(query_builder):
    mock_df = MagicMock()
    query_builder.spark.sql.return_value = mock_df

    df = query_builder.get_money_market_data([date(2026, 1, 9)], "tbl_mm")

    assert df == mock_df
    sql_arg = query_builder.spark.sql.call_args[0][0]
    assert "glue_catalog.db_rtbcol.tbl_mm" in sql_arg
    assert "glue_catalog.db_unity.tbl_unity_ops" in sql_arg


def test_get_unity_data(query_builder):
    query_builder.t1_processor.first_business_day = MagicMock(return_value=("2026-01-01", "2026-01-09"))
    mock_df1 = MagicMock()
    mock_df2 = MagicMock()
    query_builder.spark.sql.side_effect = [mock_df1, mock_df2]

    df1, df2, one_list, two_list = query_builder.get_unity_data([date(2026, 1, 9)], "tbl_mov_cc", "tbl_master")

    assert df1 == mock_df1
    assert df2 == mock_df2
    assert one_list == ["2026-01-01"]
    assert two_list == ["2026-01-09"]
    assert query_builder.spark.sql.call_count == 2
    sql1 = query_builder.spark.sql.call_args_list[0][0][0]
    sql2 = query_builder.spark.sql.call_args_list[1][0][0]
    assert "glue_catalog.db_unity.tbl_mov_cc" in sql1
    assert "glue_catalog.db_rtbcol.tbl_master" in sql2


def test_get_transacctions_data(query_builder):
    query_builder.t1_processor.last_business_day = MagicMock(return_value=("2026-01-01", "2026-01-09"))
    mock_df = MagicMock()
    query_builder.spark.sql.return_value = mock_df

    df, one_list, two_list = query_builder.get_transacctions_data([date(2026, 1, 9)], "tbl_multicash", "tbl_umbrella")

    assert df == mock_df
    assert one_list == ["2026-01-01"]
    assert two_list == ["2026-01-09"]
    sql_arg = query_builder.spark.sql.call_args[0][0]
    assert "glue_catalog.db_rtbcol.tbl_multicash" in sql_arg
    assert "glue_catalog.db_rtbcol.tbl_umbrella" in sql_arg


def test_get_trm_data(query_builder):
    mock_df = MagicMock()
    query_builder.spark.sql.return_value = mock_df

    df = query_builder.get_trm_data([date(2026, 1, 9)], "tbl_trm")

    assert df == mock_df
    sql_arg = query_builder.spark.sql.call_args[0][0]
    assert "glue_catalog.db_trm.tbl_trm" in sql_arg


def test_get_cdt_data(query_builder):
    mock_df = MagicMock()
    query_builder.spark.sql.return_value = mock_df

    df = query_builder.get_cdt_data([date(2026, 1, 9)], "tbl_renovacion")

    assert df == mock_df
    sql_arg = query_builder.spark.sql.call_args[0][0]
    assert "glue_catalog.db_dominus.tbl_renovacion" in sql_arg


def test_get_repurchase_data(query_builder):
    mock_df = MagicMock()
    query_builder.spark.sql.return_value = mock_df

    df = query_builder.get_repurchase_data([date(2026, 1, 9)], "tbl_ops_a", "tbl_ops_b")

    assert df == mock_df
    sql_arg = query_builder.spark.sql.call_args[0][0]
    assert "glue_catalog.db_dominus.tbl_ops_a" in sql_arg
    assert "glue_catalog.db_dominus.tbl_ops_b" in sql_arg


def test_get_pyg_derivatives_data(query_builder):
    mock_df = MagicMock()
    query_builder.spark.sql.return_value = mock_df

    df = query_builder.get_pyg_derivatives_data([date(2026, 1, 8)], "tbl_derivatives")

    assert df == mock_df
    sql_arg = query_builder.spark.sql.call_args[0][0]
    assert "glue_catalog.db_rtbcol.tbl_derivatives" in sql_arg


def test_get_ach_cycle_data(query_builder):
    mock_df = MagicMock()
    query_builder.spark.sql.return_value = mock_df

    df = query_builder.get_ach_cycle_data([date(2026, 1, 9)], "tbl_accounts", "tbl_tx", "tbl_channels")

    assert df == mock_df
    sql_arg = query_builder.spark.sql.call_args[0][0]
    assert "glue_catalog.db_mambu.tbl_accounts" in sql_arg
    assert "glue_catalog.db_mambu.tbl_tx" in sql_arg
    assert "glue_catalog.db_mambu.tbl_channels" in sql_arg


def test_get_ach_balance_data(query_builder):
    mock_df = MagicMock()
    query_builder.spark.sql.return_value = mock_df

    df = query_builder.get_ach_balance_data([date(2026, 1, 9)], [date(2026, 1, 8)], "tbl_balance", "tbl_deposit")

    assert df == mock_df
    sql_arg = query_builder.spark.sql.call_args[0][0]
    assert "glue_catalog.db_checking.tbl_balance" in sql_arg
    assert "glue_catalog.db_checking.tbl_deposit" in sql_arg


def test_get_ach_data(query_builder):
    mock_df = MagicMock()
    query_builder.spark.sql.return_value = mock_df

    df = query_builder.get_ach_data([date(2026, 1, 9)], [date(2026, 1, 8)], "tbl_adapter")

    assert df == mock_df
    sql_arg = query_builder.spark.sql.call_args[0][0]
    assert "glue_catalog.db_adapter.tbl_adapter" in sql_arg
