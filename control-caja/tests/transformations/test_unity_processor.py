"""Unit tests for UnityProcessor transformation component."""

from unittest.mock import MagicMock, patch
import pytest

from src.transformations.unity_processor import UnityProcessor


@pytest.fixture
def unity_processor():
    mock_spark = MagicMock()
    return UnityProcessor(mock_spark)


def test_join_dataframes(unity_processor):
    base_df = MagicMock()
    master_df = MagicMock()
    joined_mock = MagicMock()
    base_df.join.return_value = joined_mock

    res = unity_processor.join_dataframes(base_df, master_df)
    assert res == joined_mock
    base_df.join.assert_called_once()


def test_process_concept(unity_processor):
    base_df = MagicMock()
    mock_res = MagicMock()
    base_df.withColumn.return_value.withColumn.return_value.select.return_value = mock_res

    res = unity_processor.process_concept(base_df)
    assert res == mock_res


def test_process_value(unity_processor):
    join_df = MagicMock()
    mock_res = MagicMock()
    join_df.withColumn.return_value.withColumn.return_value = mock_res

    res = unity_processor.process_value(join_df)
    assert res == mock_res


def test_process_unity(unity_processor):
    base_df = MagicMock()
    master_df = MagicMock()
    concept_df = MagicMock()
    join_df = MagicMock()
    final_df = MagicMock()

    with patch.object(unity_processor, "process_concept", return_value=concept_df) as mock_pc, \
         patch.object(unity_processor, "join_dataframes", return_value=join_df) as mock_jd, \
         patch.object(unity_processor, "process_value", return_value=final_df) as mock_pv:

        result = unity_processor.process_unity(base_df, master_df)

        assert result == final_df
        mock_pc.assert_called_once_with(base_df)
        mock_jd.assert_called_once_with(concept_df, master_df)
        mock_pv.assert_called_once_with(join_df)
