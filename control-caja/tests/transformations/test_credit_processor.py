"""Unit tests for CreditProcessor transformation component."""

from unittest.mock import MagicMock
import pytest

from src.transformations.credit_processor import CreditProcessor


@pytest.fixture
def credit_processor():
    mock_spark = MagicMock()
    return CreditProcessor(mock_spark)


def test_calculate_mambu_payments(credit_processor):
    mambu_filtered = MagicMock()
    mock_row = {
        "credit_income": 5000.0,
        "credit_negative": -2000.0,
        "deposit_cros": 500.0,
        "confirming_income": 3000.0,
        "confirming_negative": -1000.0,
    }
    mambu_filtered.agg.return_value.first.return_value = mock_row

    cr_in, cr_out, conf_in, conf_out = credit_processor._calculate_mambu_payments(mambu_filtered)
    assert cr_in == 5000.0
    assert cr_out == 2500.0  # -(-2000) + 500
    assert conf_in == 3000.0
    assert conf_out == 1000.0


def test_credit_payments_empty(credit_processor):
    base_df = MagicMock()
    base_df.isEmpty.return_value = True
    today_df = MagicMock()
    today_df.isEmpty.return_value = True

    cr_inc, cr_exp, cr_adapt, conf_inc, conf_exp, sebra_list = credit_processor.credit_payments(base_df, today_df)
    assert cr_inc == 0.0
    assert cr_exp == 0.0
    assert cr_adapt == 0.0
    assert conf_inc == 0.0
    assert conf_exp == 0.0
    assert sebra_list == []


def test_credit_payments_populated(credit_processor):
    base_df = MagicMock()
    base_df.isEmpty.return_value = False
    today_df = MagicMock()
    today_df.isEmpty.return_value = False
    today_df.columns = ["reg5_datos_originador", "reg6_valor_transaccion"]

    df_sebra = MagicMock()
    df_sebra.isEmpty.return_value = False
    row_sebra = {"monto": 150.0}
    df_sebra.select.return_value.collect.return_value = [row_sebra]

    base_df.filter.side_effect = [df_sebra, MagicMock()]

    credit_processor._calculate_mambu_payments = MagicMock(return_value=(100.0, 200.0, 300.0, 400.0))
    today_df.filter.return_value.agg.return_value.first.return_value = [50.0]

    cr_inc, cr_exp, cr_adapt, conf_inc, conf_exp, sebra_list = credit_processor.credit_payments(base_df, today_df)

    assert cr_inc == 100.0
    assert cr_exp == 200.0
    assert cr_adapt == -50.0
    assert conf_inc == 300.0
    assert conf_exp == 400.0
    assert sebra_list == [150.0]
