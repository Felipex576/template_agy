"""Unit tests for CaptureProcessor transformation component."""

from datetime import date
from unittest.mock import MagicMock, patch
import pytest

from src.transformations.capture_unit_processor import CaptureProcessor
from src.utils.enums import Incomes, Expenses, Summary


@pytest.fixture
def capture_processor():
    mock_spark = MagicMock()
    return CaptureProcessor(mock_spark)


def test_create_schema(capture_processor):
    schema = capture_processor.create_schema(Incomes)
    assert len(schema.fields) == len(Incomes)
    assert schema.fields[0].name == Incomes.CREDITO_005.value


def test_create_dataframe(capture_processor):
    mock_df = MagicMock()
    capture_processor.spark.createDataFrame.return_value = mock_df

    schema = capture_processor.create_schema(Incomes)
    data = [0.0] * len(Incomes)

    df = capture_processor.create_dataframe(data, schema)
    assert df == mock_df
    capture_processor.spark.createDataFrame.assert_called_once_with([data], schema=schema)


def test_add_columns(capture_processor):
    mock_df = MagicMock()
    mock_df.columns = [Incomes.CREDITO_005.value]

    mock_with_col = MagicMock()
    mock_df.withColumn.return_value = mock_with_col
    mock_with_col.select.return_value.first.return_value = [1500.0]

    res_df, total = capture_processor.add_columns(mock_df)
    assert res_df == mock_with_col
    assert total == 1500.0


def test_create_summary_df(capture_processor):
    mock_df = MagicMock()
    capture_processor.spark.createDataFrame.return_value = mock_df

    df = capture_processor.create_summary_df(total=1200.0, total_1=1000.0, total_income=500.0, total_expense=300.0)
    assert df == mock_df
    capture_processor.spark.createDataFrame.assert_called_once()


def test_process_data(capture_processor):
    mm_df = MagicMock()
    unity_df = MagicMock()
    master_unity_df = MagicMock()
    cdt_df = MagicMock()
    pyg_df = MagicMock()
    ach_cycle_df = MagicMock()
    ach_df = MagicMock()
    tx_df = MagicMock()
    issuance_df = MagicMock()
    ach_balance_df = MagicMock()
    report_date = date(2026, 1, 9)

    capture_processor.money_market_processor.money_market_today = MagicMock(return_value=[0.0] * 14)
    capture_processor.unity_processor.process_unity = MagicMock(return_value=MagicMock())
    capture_processor.t1_processor.normalize_unity = MagicMock(return_value=(
        0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, []
    ))
    capture_processor.cdt_processor.cdt_renewals = MagicMock(return_value=100.0)
    capture_processor.pyg_processor.pyg_derivatives = MagicMock(return_value=50.0)
    capture_processor.ach_cycle_processor.nomrmalize_ach_cycle = MagicMock(return_value=(
        [0.0]*5, [0.0]*5, [0.0]*5, 0.0, 0.0, 0.0, 0.0
    ))
    capture_processor.ach_processor.normalize_refunds = MagicMock(return_value=(MagicMock(), [0.0]*5, [0.0]*5))
    capture_processor.credit_processor.credit_payments = MagicMock(return_value=(10.0, 20.0, 30.0, 40.0, 50.0, []))

    input_dic_mock = [{
        "incomeVentaDivisas": 0.0,
        "outcomeCompraDivisas": 0.0,
        "incomeTIDIS": 0.0,
        "incomeTCO": 0.0,
        "incomeSwapCaja": 0.0,
        "incomeSimultaneaTES": 0.0,
        "incomeSimultaneaPrivada": 0.0,
        "incomeRepos": 0.0,
        "incomeTDA": 0.0,
        "incomeCDT": 0.0,
        "incomeBonos": 0.0,
        "outcomeSwapCaja": 0.0,
        "outcomeTDA": 0.0,
        "outcomeSimultaneaTES": 0.0,
        "outcomeSimultaneaPrivada": 0.0,
        "outcomeRepos": 0.0,
        "outcomeTIDIS": 0.0,
        "outcomeTCO": 0.0,
        "BancosCopIncome": 0.0,
        "BancosCopOutcome": 0.0,
        "BancosUsdIncome": 0.0,
        "BancosUsdOutcome": 0.0,
    }, "OK"]
    capture_processor.input_processor.create_input = MagicMock(return_value=(input_dic_mock, 0.0, 0.0, 0.0))

    mock_df_inc = MagicMock()
    mock_df_exp = MagicMock()
    capture_processor.create_dataframe = MagicMock(side_effect=[mock_df_inc, mock_df_exp])
    capture_processor.add_columns = MagicMock(side_effect=[(mock_df_inc, 1000.0), (mock_df_exp, 800.0)])

    income_df, expense_df, tot_inc, tot_exp = capture_processor.process_data(
        mm_df, unity_df, master_unity_df, cdt_df, pyg_df, ach_cycle_df, ach_df, tx_df,
        issuance_df, ach_balance_df, trm=4000.0, bank_usd=100.0, bank_usd_1=100.0,
        report_date=report_date
    )

    assert income_df == mock_df_inc
    assert expense_df == mock_df_exp
    assert tot_inc == 1000.0
    assert tot_exp == 800.0
