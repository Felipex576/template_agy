"""Unit tests for AchProcessor transformation component."""

from unittest.mock import MagicMock, patch
import pytest

from src.transformations.ach_processor import AchProcessor
from src.utils.constants import AchConstants


@pytest.fixture
def ach_processor():
    mock_spark = MagicMock()
    return AchProcessor(mock_spark)


def test_calculate_matched_refunds_empty(ach_processor):
    mock_df = MagicMock()
    mock_df.filter.return_value.isEmpty.return_value = True
    assert ach_processor._calculate_matched_refunds(mock_df) == 0.0


def test_calculate_matched_refunds_populated(ach_processor):
    mock_df = MagicMock()
    out_rows = MagicMock()
    sent_rows = MagicMock()
    out_rows.isEmpty.return_value = False
    sent_rows.isEmpty.return_value = False

    mock_df.filter.side_effect = [out_rows, sent_rows]
    matched_mock = MagicMock()
    out_rows.withColumnRenamed.return_value.withColumnRenamed.return_value.groupBy.return_value.agg.return_value.join.return_value = matched_mock
    matched_mock.agg.return_value.first.return_value = {"total": 1234.56}

    assert ach_processor._calculate_matched_refunds(mock_df) == 1234.56


def test_normalize_refunds_empty(ach_processor):
    mock_df = MagicMock()
    mock_df.isEmpty.return_value = True

    today_df, dep_cud, send_ret = ach_processor.normalize_refunds(mock_df, "2026-01-09")
    assert today_df == mock_df
    assert dep_cud == list(AchConstants.ACH_DEPOSIT_CUD)
    assert send_ret == list(AchConstants.SEND_RETURNS)


def test_normalize_refunds_populated(ach_processor):
    mock_df = MagicMock()
    mock_df.isEmpty.return_value = False

    df_transformed = MagicMock()
    mock_df.withColumn.return_value.withColumn.return_value.withColumn.return_value.drop.return_value = df_transformed

    today_mock = MagicMock()
    yesterday_mock = MagicMock()
    today_mock.isEmpty.return_value = False
    yesterday_mock.isEmpty.return_value = False

    df_transformed.filter.side_effect = [today_mock, yesterday_mock]

    today_mock.agg.return_value.first.return_value = {
        "c_1": 10.0, "c_2": 20.0, "c_3": 30.0, "c_4": 40.0, "c_5": 50.0
    }
    yesterday_mock.filter.return_value.agg.return_value.first.return_value = [100.0]

    with patch.object(ach_processor, "_calculate_matched_refunds", return_value=15.0):
        res_today_df, dep_cud, send_ret = ach_processor.normalize_refunds(mock_df, "2026-01-09")

        assert res_today_df == today_mock
        assert dep_cud == [10.0, 20.0, 30.0, 40.0, 50.0]
        assert send_ret[1] == 10.0
        assert send_ret[2] == 20.0
        assert send_ret[3] == 30.0
        assert send_ret[4] == 15.0
        assert send_ret[0] == 85.0
