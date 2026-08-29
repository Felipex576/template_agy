"""Unit tests for MoneyMarketProcessor transformation component."""

from datetime import date
from unittest.mock import MagicMock, patch
import pytest

from src.transformations.money_market_processor import MoneyMarketProcessor


@pytest.fixture
def money_market_processor():
    mock_spark = MagicMock()
    return MoneyMarketProcessor(mock_spark)


def test_calculate_turnover_sum_none(money_market_processor):
    mock_df = MagicMock()
    mock_df.filter.return_value.agg.return_value.first.return_value = {"total": 0.0}
    assert money_market_processor.calculate_turnover_sum(mock_df, None) == 0.0


def test_calculate_turnover_sum_value(money_market_processor):
    mock_df = MagicMock()
    mock_df.filter.return_value.agg.return_value.first.return_value = {"total": 45000.0}
    assert money_market_processor.calculate_turnover_sum(mock_df, None) == 45000.0


def test_calculate_simultaneous(money_market_processor):
    mock_df = MagicMock()
    with patch.object(money_market_processor, "calculate_turnover_sum", return_value=123.0):
        res = money_market_processor.calculate_simultaneous(mock_df, "A", "CT")
        assert res == 123.0


def test_calculate_definitive(money_market_processor):
    mock_df = MagicMock()
    with patch.object(money_market_processor, "calculate_turnover_sum", return_value=456.0):
        res_tes = money_market_processor.calculate_definitive(mock_df, "C", is_tes=True)
        assert res_tes == 456.0

        res_priv = money_market_processor.calculate_definitive(mock_df, "V", is_tes=False)
        assert res_priv == 456.0


def test_calculate_repo(money_market_processor):
    mock_df = MagicMock()
    with patch.object(money_market_processor, "calculate_turnover_sum", return_value=789.0):
        res = money_market_processor.calculate_repo(mock_df, "P")
        assert res == 789.0


def test_calculate_dollar(money_market_processor):
    mock_df = MagicMock()
    with patch.object(money_market_processor, "calculate_turnover_sum", return_value=101.0):
        res = money_market_processor.calculate_dollar(mock_df, "C")
        assert res == 101.0


def test_calculate_ttv(money_market_processor):
    mock_df = MagicMock()
    with patch.object(money_market_processor, "calculate_turnover_sum", return_value=202.0):
        res = money_market_processor.calculate_ttv(mock_df, "V")
        assert res == 202.0


def test_money_market_today_empty(money_market_processor):
    mock_df = MagicMock()
    mock_df.isEmpty.return_value = True

    result = money_market_processor.money_market_today(mock_df, date(2026, 1, 9))
    assert len(result) == 14
    assert all(val == 0.0 for val in result)


def test_money_market_today_populated(money_market_processor):
    mock_df = MagicMock()
    mock_df.isEmpty.return_value = False
    mock_df.filter.return_value = mock_df

    with patch.object(money_market_processor, "calculate_simultaneous", return_value=10.0), \
         patch.object(money_market_processor, "calculate_definitive", return_value=20.0), \
         patch.object(money_market_processor, "calculate_repo", return_value=30.0), \
         patch.object(money_market_processor, "calculate_dollar", return_value=40.0), \
         patch.object(money_market_processor, "calculate_ttv", return_value=50.0):

        result = money_market_processor.money_market_today(mock_df, date(2026, 1, 9))
        assert len(result) == 14
        assert result[0] == 10.0   # simult_tes_act_sell
        assert result[4] == -20.0  # definitives_buy_tes * -1
        assert result[8] == 30.0   # repos_active_income
        assert result[10] == -40.0 # dollar_buy * -1
        assert result[11] == 40.0  # dollar_sell
        assert result[12] == 50.0  # ttv_income
        assert result[13] == -50.0 # ttv_outflow * -1
