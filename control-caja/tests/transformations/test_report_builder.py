"""Unit tests for ReportBuilder transformation component."""

from datetime import date
from unittest.mock import MagicMock, patch
import pytest

from src.transformations.report_builder import ReportBuilder
from src.utils.classes import ProcessingDataFrames


@pytest.fixture
def report_builder():
    mock_spark = MagicMock()
    return ReportBuilder(mock_spark)


def test_convert_to_date(report_builder):
    d = date(2026, 1, 9)
    assert report_builder.convert_to_date(d) == d
    assert report_builder.convert_to_date("2026-01-09") == d
    assert report_builder.convert_to_date("DATE 2026-01-09") == d


def test_filter_date_df(report_builder):
    mock_df = MagicMock()
    mock_res = MagicMock()
    mock_df.filter.return_value = mock_res

    res = report_builder.filter_date_df(mock_df, "fecha", "2026-01-09")
    assert res == mock_res
    mock_df.filter.assert_called_once()


def test_filter_two_dates(report_builder):
    mock_df = MagicMock()
    mock_res = MagicMock()
    mock_df.filter.return_value = mock_res

    res = report_builder.filter_two_dates(mock_df, "fecha", "2026-01-01", "2026-01-09")
    assert res == mock_res
    mock_df.filter.assert_called_once()


def test_union_dataframes(report_builder):
    df1 = MagicMock()
    df2 = MagicMock()
    mock_res = MagicMock()
    df1.unionByName.return_value = mock_res

    res = report_builder.union_dataframes(df1, df2)
    assert res == mock_res
    df1.unionByName.assert_called_once_with(df2)


def test_create_report(report_builder):
    date_list = [date(2026, 1, 9), date(2026, 1, 8)]
    previous_list = [date(2026, 1, 8), date(2026, 1, 7)]
    bank_dates = [date(2026, 1, 8), date(2026, 1, 7)]
    bank_1_dates = [date(2026, 1, 9), date(2026, 1, 8)]
    one_list = [date(2026, 1, 1), date(2026, 1, 1)]
    two_list = [date(2026, 1, 9), date(2026, 1, 8)]
    tr_one_list = [date(2026, 1, 1), date(2026, 1, 1)]
    tr_two_list = [date(2026, 1, 9), date(2026, 1, 8)]

    dfs = ProcessingDataFrames(
        trm_df=MagicMock(),
        trm_1_df=MagicMock(),
        bank_df=MagicMock(),
        bank_1_df=MagicMock(),
        money_market_df=MagicMock(),
        unity_df=MagicMock(),
        master_unity_df=MagicMock(),
        cdt_df=MagicMock(),
        pyg_df=MagicMock(),
        ach_cycle_df=MagicMock(),
        ach_df=MagicMock(),
        transactions_df=MagicMock(),
        issuance_df=MagicMock(),
        ach_balance_df=MagicMock(),
        final_t0_df=None,
        final_t1_df=None,
        final_income_df=None,
        final_expense_df=None,
        final_summary_df=None,
    )

    report_builder.trm_processor = MagicMock()
    report_builder.available_table = MagicMock()
    report_builder.capture_processor = MagicMock()

    report_builder.trm_processor.normalize_trm.return_value = 4000.0
    report_builder.available_table.create_available_df.side_effect = [
        (MagicMock(), 100.0, 1000.0), (MagicMock(), 100.0, 1000.0),
        (MagicMock(), 100.0, 1000.0), (MagicMock(), 100.0, 1000.0)
    ]
    report_builder.capture_processor.process_data.return_value = (MagicMock(), MagicMock(), 500.0, 300.0)
    report_builder.capture_processor.create_summary_df.return_value = MagicMock()

    with patch.object(report_builder, "filter_date_df", return_value=MagicMock()), \
         patch.object(report_builder, "filter_two_dates", return_value=MagicMock()), \
         patch.object(report_builder, "union_dataframes", side_effect=lambda a, b: a):

        inc, exp, t0, t1, summary = report_builder.create_report(
            date_list, previous_list, bank_dates, bank_1_dates,
            one_list, two_list, tr_one_list, tr_two_list, dfs
        )

        assert inc is not None
        assert exp is not None
        assert t0 is not None
        assert t1 is not None
        assert summary is not None
        assert report_builder.capture_processor.process_data.call_count == 2
