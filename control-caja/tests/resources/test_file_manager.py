"""Unit tests for FileManager component."""

from datetime import date
from unittest.mock import Mock, patch
import zipfile
import io
import pytest

from src.resources.file_manager import FileManager


@patch("src.resources.file_manager.boto3.client")
def test_file_manager_init(mock_boto):
    mock_s3 = Mock()
    mock_boto.return_value = mock_s3
    mock_spark = Mock()

    fm = FileManager(
        spark=mock_spark,
        trusted_bucket="trusted-bucket",
        zip_path="zip/path",
        entity="Banco",
        chronos_bucket="chronos-bucket",
        output_file_path="output/file.zip"
    )

    assert fm.trusted_bucket == "trusted-bucket"
    assert fm.entity == "Banco"
    assert fm.s3_client == mock_s3


@patch("src.resources.file_manager.boto3.client")
def test_upload_file(mock_boto):
    mock_s3 = Mock()
    mock_boto.return_value = mock_s3
    mock_spark = Mock()

    fm = FileManager(
        spark=mock_spark,
        trusted_bucket="trusted-bucket",
        zip_path="zip/path",
        entity="Banco",
        chronos_bucket="chronos-bucket",
        output_file_path="output/file.zip"
    )

    fake_excel_bytes = b"fake excel content"
    fm.upload_file(fake_excel_bytes, date(2026, 1, 9))

    assert mock_s3.put_object.call_count == 2

    # Check put_object arguments for trusted bucket
    call_trusted = mock_s3.put_object.call_args_list[0][1]
    assert call_trusted["Bucket"] == "trusted-bucket"
    assert "f_control_caja_Banco20260109.zip" in call_trusted["Key"]

    # Verify zip content
    zip_bytes = call_trusted["Body"]
    with zipfile.ZipFile(io.BytesIO(zip_bytes), mode="r") as zf:
        namelist = zf.namelist()
        assert "f_control_caja_Banco20260109.xlsx" in namelist
        assert zf.read("f_control_caja_Banco20260109.xlsx") == fake_excel_bytes

    # Check put_object arguments for chronos bucket
    call_chronos = mock_s3.put_object.call_args_list[1][1]
    assert call_chronos["Bucket"] == "chronos-bucket"
    assert call_chronos["Key"] == "output/file.zip"
