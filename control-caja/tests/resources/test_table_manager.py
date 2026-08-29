"""Unit tests for TableManager component."""

from unittest.mock import Mock, patch
import pytest

from src.resources.table_manager import TableManager


@patch("src.resources.table_manager.IcebergTableManager")
def test_table_manager_init(mock_iceberg_class):
    mock_spark = Mock()
    tm = TableManager(mock_spark)
    mock_iceberg_class.assert_called_once_with(mock_spark)
    assert tm.spark == mock_spark


@patch("src.resources.table_manager.IcebergTableManager")
def test_upload_table(mock_iceberg_class):
    mock_spark = Mock()
    mock_iceberg = Mock()
    mock_iceberg_class.return_value = mock_iceberg

    tm = TableManager(mock_spark)

    mock_df = Mock()
    output_path = "s3://path/to/table/"
    report_table = "glue_catalog.db.tbl"
    partition_keys = ["fecha_reporte"]
    merge_keys = ["fecha_reporte"]

    tm.upload_table(mock_df, output_path, report_table, partition_keys, merge_keys)

    mock_iceberg.create_table.assert_called_once_with(output_path, mock_df, partition_keys, report_table)
    mock_iceberg.synchronize_schema.assert_called_once_with(mock_df, report_table)
    mock_iceberg.merge_data.assert_called_once_with(mock_df, merge_keys, report_table)
