"""Unit tests for T1Processor transformation component."""

from datetime import date
from unittest.mock import MagicMock, patch
import pytest

from src.transformations.t_1_processor import T1Processor
from src.utils.constants import DEFAULT_INPUT_DIC


@pytest.fixture
def t1_processor():
    mock_spark = MagicMock()
    return T1Processor(mock_spark)


def test_is_business_day(t1_processor):
    assert t1_processor.is_business_day(date(2026, 1, 9)) is True
    assert t1_processor.is_business_day(date(2026, 1, 10)) is False
    assert t1_processor.is_business_day(date(2025, 12, 31)) is False


def test_first_business_day(t1_processor):
    start_date, end_date = t1_processor.first_business_day(date(2026, 1, 9))
    assert isinstance(start_date, str)
    assert isinstance(end_date, str)
    assert end_date == "2026-01-09"

    # Monday test
    start_mon, end_mon = t1_processor.first_business_day(date(2026, 1, 12))
    assert isinstance(start_mon, str)


def test_last_business_day(t1_processor):
    start_date, end_date = t1_processor.last_business_day(date(2026, 1, 9))
    assert isinstance(start_date, str)
    assert isinstance(end_date, str)
    assert start_date == "2026-01-09"

    # Non-business day
    s_nb, e_nb = t1_processor.last_business_day(date(2026, 1, 10))
    assert s_nb == "2026-01-10"


def test_calculate_turnover(t1_processor):
    mock_df = MagicMock()
    mock_df.filter.return_value.agg.return_value.first.return_value = {"total": 5000.0}
    assert t1_processor.calculate_turnover(mock_df, None) == 5000.0


def test_calculate_simultaneous(t1_processor):
    mock_df = MagicMock()
    with patch.object(t1_processor, "calculate_turnover", return_value=123.0):
        assert t1_processor.calculate_simultaneous(mock_df, "A", "CT") == 123.0


def test_calculate_outright(t1_processor):
    mock_df = MagicMock()
    with patch.object(t1_processor, "calculate_turnover", return_value=456.0):
        assert t1_processor.calculate_outright(mock_df, "C", is_tes=True) == 456.0
        assert t1_processor.calculate_outright(mock_df, "V", is_tes=False) == 456.0


def test_calculate_repo(t1_processor):
    mock_df = MagicMock()
    with patch.object(t1_processor, "calculate_turnover", return_value=789.0):
        assert t1_processor.calculate_repo(mock_df, "C", "A") == 789.0


def test_calculate_dollar(t1_processor):
    mock_df = MagicMock()
    with patch.object(t1_processor, "calculate_turnover", return_value=101.0):
        assert t1_processor.calculate_dollar(mock_df, "C") == 101.0


def test_calculate_ttv(t1_processor):
    mock_df = MagicMock()
    with patch.object(t1_processor, "calculate_turnover", return_value=202.0):
        assert t1_processor.calculate_ttv(mock_df, "V") == 202.0


def test_calculate_value_sum(t1_processor):
    mock_df = MagicMock()
    mock_df.filter.return_value.agg.return_value.first.return_value = {"total": 300.0}
    assert t1_processor.calculate_value_sum(mock_df, None) == 300.0


def test_calculate_signed_sums(t1_processor):
    mock_df = MagicMock()
    mock_df.filter.return_value.agg.return_value.first.return_value = {"income": 100.0, "expense": 200.0}
    inc, out = t1_processor.calculate_signed_sums(mock_df, None)
    assert inc == 100.0
    assert out == 200.0


def test_calculate_bank_currency_sums(t1_processor):
    mock_df = MagicMock()
    mock_df.filter.return_value.agg.return_value.first.return_value = {"income": 500.0, "outcome": -300.0}
    inc, out = t1_processor.calculate_bank_currency_sums(mock_df, "COP")
    assert inc == 500.0
    assert out == -300.0


def test_normalize_unity_empty(t1_processor):
    mock_df = MagicMock()
    mock_df.isEmpty.return_value = True

    result = t1_processor.normalize_unity(mock_df)
    assert len(result) == 17
    assert result[0] == 0.0
    assert result[16] == []


def test_normalize_unity_populated(t1_processor):
    mock_df = MagicMock()
    mock_df.isEmpty.return_value = False

    row_movs = {"valor": 50.0}
    mock_df.filter.return_value.select.return_value.collect.return_value = [row_movs]

    with patch.object(t1_processor, "calculate_signed_sums", return_value=(10.0, 20.0)), \
         patch.object(t1_processor, "calculate_value_sum", return_value=30.0):

        result = t1_processor.normalize_unity(mock_df)
        assert len(result) == 17
        assert result[0] == 10.0  # ing_sebra_exchange
        assert result[1] == -20.0  # egr_sebra_exchange * -1
        assert result[16] == [50.0]


def test_t1_market_today_empty(t1_processor):
    mock_df = MagicMock()
    mock_df.isEmpty.return_value = True

    result = t1_processor.t1_market_today(mock_df, date(2026, 1, 9))
    assert result == DEFAULT_INPUT_DIC


def test_t1_market_today_populated(t1_processor):
    mock_df = MagicMock()
    mock_df.isEmpty.return_value = False
    mock_df.filter.return_value = mock_df

    with patch.object(t1_processor, "calculate_simultaneous", return_value=1.0), \
         patch.object(t1_processor, "calculate_outright", return_value=2.0), \
         patch.object(t1_processor, "calculate_repo", return_value=3.0), \
         patch.object(t1_processor, "calculate_dollar", return_value=4.0), \
         patch.object(t1_processor, "calculate_ttv", return_value=5.0):

        result = t1_processor.t1_market_today(mock_df, date(2026, 1, 9))
        assert len(result) == 2
        assert isinstance(result[0], dict)
        assert result[0]["incomeRepos"] == 3.0
        assert result[0]["incomeSimultaneaTES"] == 1.0


def test_bank_transactions_empty(t1_processor):
    mock_df = MagicMock()
    mock_df.isEmpty.return_value = True

    cop_in, cop_out, usd_in, usd_out = t1_processor.bank_transactions(mock_df)
    assert cop_in == 0.0
    assert cop_out == 0.0
    assert usd_in == 0.0
    assert usd_out == 0.0


def test_bank_transactions_populated(t1_processor):
    mock_df = MagicMock()
    mock_df.isEmpty.return_value = False

    with patch.object(t1_processor, "calculate_bank_currency_sums", side_effect=[(100.0, -50.0), (200.0, -75.0)]):
        cop_in, cop_out, usd_in, usd_out = t1_processor.bank_transactions(mock_df)
        assert cop_in == 100.0
        assert cop_out == 50.0
        assert usd_in == 200.0
        assert usd_out == 75.0
