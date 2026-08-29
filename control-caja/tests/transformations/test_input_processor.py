"""Unit tests for InputProcessor transformation component."""

from datetime import date, datetime
from unittest.mock import MagicMock
import pytest

from src.transformations.input_processor import InputProcessor
from src.utils.constants import DEFAULT_INPUT_DIC


@pytest.fixture
def input_processor():
    mock_spark = MagicMock()
    return InputProcessor(mock_spark)


def test_create_input_today(input_processor):
    today = datetime.today().date()
    mm_df = MagicMock()
    tx_df = MagicMock()
    iss_df = MagicMock()
    ach_df = MagicMock()

    inp_dic, acc_var, mov_inc, mov_exp = input_processor.create_input(
        today, mm_df, tx_df, iss_df, ach_df, [], []
    )
    assert inp_dic == DEFAULT_INPUT_DIC
    assert acc_var == 0.0
    assert mov_inc == 0.0
    assert mov_exp == 0.0


def test_create_input_historical(input_processor):
    hist_date = date(2025, 1, 9)
    mm_df = MagicMock()
    tx_df = MagicMock()
    iss_df = MagicMock()
    ach_df = MagicMock()

    base_market_dic = [{
        "BancosCopIncome": 0.0, "BancosCopOutcome": 0.0,
        "BancosUsdIncome": 0.0, "BancosUsdOutcome": 0.0,
        "outcomeRecompras": 0.0, "incomeCDT": 0.0, "incomeBonos": 0.0
    }, "OK"]

    input_processor.t1_processor.t1_market_today = MagicMock(return_value=base_market_dic)
    input_processor.t1_processor.bank_transactions = MagicMock(return_value=(10.0, 20.0, 30.0, 40.0))
    input_processor.cdt_processor.issuance_repurchase = MagicMock(return_value=(50.0, 60.0, 70.0))
    input_processor.ach_cycle_processor.account_variation = MagicMock(return_value=15.0)

    sebra_credit = [100.0]
    movs_sebra = [100.0, 200.0, -50.0]

    inp_dic, acc_var, mov_inc, mov_exp = input_processor.create_input(
        hist_date, mm_df, tx_df, iss_df, ach_df, sebra_credit, movs_sebra
    )

    assert inp_dic[0]["BancosCopIncome"] == 10.0
    assert inp_dic[0]["BancosCopOutcome"] == 20.0
    assert inp_dic[0]["outcomeRecompras"] == 50.0
    assert acc_var == 15.0
    assert mov_inc == 200.0
    assert mov_exp == -50.0
