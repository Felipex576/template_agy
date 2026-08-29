"""Unit tests for CycleProcessor transformation component."""

from unittest.mock import MagicMock
import pytest

from src.transformations.ach_cycle_processor import CycleProcessor
from src.utils.constants import CycleConstants


@pytest.fixture
def cycle_processor():
    mock_spark = MagicMock()
    return CycleProcessor(mock_spark)


def test_build_slot_expressions(cycle_processor):
    slots = [("00:00:00", "08:30:00"), ("08:30:01", "11:00:00")]
    exprs = cycle_processor._build_slot_expressions("ACH", slots, is_withdrawal=True, prefix="ret")
    assert len(exprs) == 2


def test_normalize_ach_cycle_empty(cycle_processor):
    mock_df = MagicMock()
    mock_df.isEmpty.return_value = True

    res = cycle_processor.nomrmalize_ach_cycle(mock_df)
    assert res == (
        CycleConstants.WITHDRAWALS_ACH,
        CycleConstants.DEPOSIT_ACH,
        CycleConstants.WITHDRAWALS_REVERSALS,
        CycleConstants.DEBIT_SEBRA,
        CycleConstants.CREDIT_SEBRA,
        CycleConstants.DEBIT_RETURNS_SEBRA,
        CycleConstants.CREDIT_RETURNS_SEBRA
    )


def test_normalize_ach_cycle_populated(cycle_processor):
    mock_df = MagicMock()
    mock_df.isEmpty.return_value = False

    mock_row = {
        "ret_0": 10.0, "ret_1": 20.0, "ret_2": 30.0, "ret_3": 40.0, "ret_4": 50.0,
        "dep_0": 11.0, "dep_1": 21.0, "dep_2": 31.0, "dep_3": 41.0, "dep_4": 51.0,
        "dev_0": 1.0, "dev_1": 2.0, "dev_2": 3.0, "dev_3": 4.0, "dev_4": 5.0,
        "debit_sebra": 100.0, "credit_sebra": 200.0,
        "debit_returns_sebra": 300.0, "credit_returns_sebra": 400.0
    }
    mock_df.filter.return_value.agg.return_value.first.return_value = mock_row

    withdrawals, deposits, reversals, d_sebra, c_sebra, d_ret, c_ret = cycle_processor.nomrmalize_ach_cycle(mock_df)

    assert withdrawals == [10.0, 20.0, 30.0, 40.0, 50.0]
    assert deposits == [11.0, 21.0, 31.0, 41.0, 51.0]
    assert reversals == [1.0, 2.0, 3.0, 4.0, 5.0]
    assert d_sebra == 100.0
    assert c_sebra == 200.0
    assert d_ret == 300.0
    assert c_ret == 400.0


def test_account_variation_empty(cycle_processor):
    mock_df = MagicMock()
    mock_df.isEmpty.return_value = True
    assert cycle_processor.account_variation(mock_df) == 0.0


def test_account_variation_populated(cycle_processor):
    mock_df = MagicMock()
    mock_df.isEmpty.return_value = False

    row_max = {"total_balance": 5000.0}
    row_min = {"total_balance": 3000.0}
    mock_df.orderBy.return_value.select.return_value.collect.return_value = [row_max, row_min]

    variation = cycle_processor.account_variation(mock_df)
    assert variation == 2000.0
