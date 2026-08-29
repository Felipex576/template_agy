"""Unit tests for BankProcessor transformation component."""

from datetime import date, timedelta
from unittest.mock import MagicMock, patch
import pytest

from src.transformations.bank_processor import BankProcessor
from src.utils.constants import BankConstants


@pytest.fixture
def bank_processor():
    mock_spark = MagicMock()
    return BankProcessor(mock_spark)


def test_get_previous_date(bank_processor):
    # Before 2026-03-13 -> returns start_date - 1 day
    start_date = date(2026, 1, 9)
    end_date = date(2026, 1, 8)
    res = bank_processor.get_previous_date(start_date, end_date)
    assert res == date(2026, 1, 8)

    # On or after 2026-03-13 -> returns end_date
    start_date_later = date(2026, 3, 15)
    end_date_later = date(2026, 3, 14)
    res_later = bank_processor.get_previous_date(start_date_later, end_date_later)
    assert res_later == date(2026, 3, 14)


def test_adjust_year_end_dates(bank_processor):
    # start_date is Dec 31
    d_start = date(2025, 12, 31)
    d_prev = date(2025, 12, 30)
    res = bank_processor.adjust_year_end_dates(d_start, d_prev)
    assert res == date(2026, 1, 1)

    # previous_date is Dec 31
    d_start2 = date(2026, 1, 2)
    d_prev2 = date(2025, 12, 31)
    res2 = bank_processor.adjust_year_end_dates(d_start2, d_prev2)
    assert res2 == date(2026, 1, 1)


def test_calculate_ban_rep(bank_processor):
    mock_df = MagicMock()
    mock_row = {"saldo_bancario_final": 1000.0}
    mock_df.filter.return_value.agg.return_value.first.return_value = mock_row

    res = bank_processor.calculate_ban_rep(mock_df, "62015990")
    assert res == 1000.0


def test_get_balance(bank_processor):
    mock_df = MagicMock()
    result_df = MagicMock()
    mock_row = {"saldo": 5000.0}
    mock_df.filter.return_value.agg.return_value.first.return_value = mock_row

    # without bank/bank_type
    bal = bank_processor.get_balance(mock_df, result_df, ["12345"])
    assert bal == 5000.0

    # with bank and bank_type
    bal2 = bank_processor.get_balance(mock_df, result_df, ["12345"], bank="Bancolombia", bank_type="Ahorros")
    assert bal2 == 5000.0


def test_trm_convert(bank_processor):
    mock_df = MagicMock()
    result_df = MagicMock()
    mock_row = {"saldo_bancario_final": 10000.0, "saldo_en_canje": 2000.0}
    mock_df.filter.return_value.agg.return_value.first.return_value = mock_row

    # by bank
    res = bank_processor.trm_convert(mock_df, result_df, bank="BofA")
    assert res == 8000.0

    # by account
    res2 = bank_processor.trm_convert(mock_df, result_df, account="1901751916")
    assert res2 == 8000.0


def test_bank_balances_empty(bank_processor):
    mock_df = MagicMock()
    mock_df.isEmpty.return_value = True

    result = bank_processor.bank_balances(mock_df)
    assert len(result) == 17
    assert all(val == 0.0 for val in result)


def test_bank_balances_populated(bank_processor):
    mock_df = MagicMock()
    mock_df.isEmpty.return_value = False

    with patch.object(bank_processor, "calculate_ban_rep", return_value=100.0), \
         patch.object(bank_processor, "get_balance", return_value=50.0), \
         patch.object(bank_processor, "trm_convert", return_value=30.0):

        result = bank_processor.bank_balances(mock_df)
        assert len(result) == 17
        assert result[0] == 100.0
        assert result[3] == 50.0
        assert result[10] == 30.0
