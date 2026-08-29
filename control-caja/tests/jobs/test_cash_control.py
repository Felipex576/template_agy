"""Unit tests for CashControl job orchestration."""

from datetime import date
from unittest.mock import Mock, patch, MagicMock
import pytest

from src.jobs.cash_control import CashControl, main


def build_cash_control_instance():
    """Create a CashControl instance without running the production initializer."""
    instance = CashControl.__new__(CashControl)
    instance.job_name = "test_job"
    instance.report_date = "2026-01-09T05:00:00.000Z"
    instance.report_name = "control_caja"
    instance.entity = "Banco"
    instance.market_database = "market_db"
    instance.income_table = "glue_catalog.market_db.tbl_income"
    instance.expense_table = "glue_catalog.market_db.tbl_expense"
    instance.available_table = "glue_catalog.market_db.tbl_available"
    instance.summary_table = "glue_catalog.market_db.tbl_summary"

    instance.rtbcol_database = "rtbcol_db"
    instance.unity_database = "unity_db"
    instance.trm_database = "trm_db"
    instance.dominus_database = "dominus_db"
    instance.mambu_cc_database = "mambu_db"
    instance.checking_accounts_database = "checking_db"
    instance.adapter_database = "adapter_db"

    instance.unity_operations_table = "tbl_unity_ops"
    instance.bank_balances_table = "tbl_bank_balances"
    instance.money_market_table = "tbl_mm"
    instance.cc_movements_table = "tbl_cc_mov"
    instance.master_homologation_table = "tbl_master"
    instance.multicash_movements_table = "tbl_multicash"
    instance.umbrella_master_table = "tbl_umbrella"
    instance.trm_table = "tbl_trm"
    instance.renewal_operations_table = "tbl_renovacion"
    instance.operations_a_table = "tbl_ops_a"
    instance.operations_b_table = "tbl_ops_b"
    instance.standardized_derivatives_table = "tbl_derivatives"
    instance.mambu_accounts_table = "tbl_mambu_acc"
    instance.mambu_transactions_table = "tbl_mambu_tx"
    instance.mambu_channels_table = "tbl_mambu_channels"
    instance.balance_table = "tbl_balance"
    instance.deposit_account_table = "tbl_deposit"
    instance.reconciliation_adapter_table = "tbl_adapter"

    instance.trusted_bucket = "trusted-bucket"
    instance.prefix_data = "data"
    instance.prefix_file = "file"
    instance.project_bucket = "project-bucket"
    instance.output_file_path = "output/path.zip"
    instance.chronos_bucket = "chronos-bucket"
    instance.income_path = "s3://trusted/income/"
    instance.expense_path = "s3://trusted/expense/"
    instance.available_path = "s3://trusted/available/"
    instance.summary_path = "s3://trusted/summary/"
    instance.zip_path = "file/control_caja/Banco"

    instance.format_date = Mock()
    instance.query_builder = Mock()
    instance.report_builder = Mock()
    instance.table_builder = Mock()
    instance.table_manager = Mock()
    instance.excel_manager = Mock()
    instance.file_manager = Mock()

    return instance


def test_cash_control_init():
    args = {
        "JOB_NAME": "test_job",
        "REPORT_DATE": "2026-01-09T05:00:00.000Z",
        "REPORT_TYPE": "Control Caja",
        "COMPANY": "Banco",
        "MARKET_DATABASE": "market_db",
        "INCOME_TABLE": "tbl_income",
        "EXPENSE_TABLE": "tbl_expense",
        "AVAILABLE_TABLE": "tbl_available",
        "SUMMARY_TABLE": "tbl_summary",
        "RTBCOL_DATABASE": "rtbcol_db",
        "UNITY_DATABASE": "unity_db",
        "TRM_DATABASE": "trm_db",
        "DOMINUS_DATABASE": "dominus_db",
        "MAMBU_CC_DATABASE": "mambu_db",
        "CHECKING_ACCOUNTS_DATABASE": "checking_db",
        "ADAPTER_DATABASE": "adapter_db",
        "UNITY_OPERATIONS_TABLE": "tbl_unity_ops",
        "BANK_BALANCES_TABLE": "tbl_bank_balances",
        "MONEY_MARKET_TABLE": "tbl_mm",
        "CC_MOVEMENTS_TABLE": "tbl_cc_mov",
        "MASTER_HOMOLOGATION_TABLE": "tbl_master",
        "MULTICASH_MOVEMENTS_TABLE": "tbl_multicash",
        "UMBRELLA_MASTER_TABLE": "tbl_umbrella",
        "TRM_TABLE": "tbl_trm",
        "RENEWAL_OPERATIONS_TABLE": "tbl_renovacion",
        "OPERATIONS_A_TABLE": "tbl_ops_a",
        "OPERATIONS_B_TABLE": "tbl_ops_b",
        "STANDARDIZED_DERIVATIVES_TABLE": "tbl_derivatives",
        "MAMBU_ACCOUNTS_TABLE": "tbl_mambu_acc",
        "MAMBU_TRANSACTIONS_TABLE": "tbl_mambu_tx",
        "MAMBU_CHANNELS_TABLE": "tbl_mambu_channels",
        "BALANCE_TABLE": "tbl_balance",
        "DEPOSIT_ACCOUNT_TABLE": "tbl_deposit",
        "RECONCILIATION_ADAPTER_TABLE": "tbl_adapter",
        "TRUSTED_BUCKET": "trusted-bucket",
        "PREFIX_DATA": "data",
        "PREFIX_FILE": "file",
        "PROJECT_BUCKET_NAME": "project-bucket",
        "OUTPUT_FILE_PATH": "output/path.zip",
        "CHRONOS_BUCKET_NAME": "chronos-bucket",
    }

    mock_glue = Mock()
    mock_spark = Mock()
    mock_job = Mock()

    with patch("src.jobs.cash_control.initialize", return_value=(mock_glue, mock_spark, mock_job)), \
         patch("src.jobs.cash_control.FormatDate") as mock_fd, \
         patch("src.jobs.cash_control.QueryBuilder") as mock_qb, \
         patch("src.jobs.cash_control.ReportBuilder") as mock_rb, \
         patch("src.jobs.cash_control.TableBuilder") as mock_tb, \
         patch("src.jobs.cash_control.TableManager") as mock_tm, \
         patch("src.jobs.cash_control.ExcelManager") as mock_em, \
         patch("src.jobs.cash_control.FileManager") as mock_fm:

        cash_control = CashControl(args)

        assert cash_control.job_name == "test_job"
        assert cash_control.report_name == "control_caja"
        assert cash_control.entity == "Banco"
        mock_job.init.assert_called_once_with("test_job", {})


def test_cash_control_run():
    instance = build_cash_control_instance()

    date_list = ["2026-01-09", "2026-01-08"]
    previous_list = ["2026-01-08", "2026-01-07"]
    next_list = ["2026-01-13", "2026-01-09"]
    bank_dates = ["2026-01-08", "2026-01-07"]
    bank_1_dates = ["2026-01-09", "2026-01-08"]
    one_list = ["2026-01-01", "2026-01-01"]
    two_list = ["2026-01-09", "2026-01-08"]
    tr_one = ["2026-01-01", "2026-01-01"]
    tr_two = ["2026-01-09", "2026-01-08"]

    instance.format_date.parse_report_date.return_value = date(2026, 1, 9)
    instance.format_date.get_last_business_days.return_value = date_list
    instance.format_date.get_all_dates.return_value = (previous_list, next_list)

    mock_df = MagicMock()
    instance.query_builder.get_bank_data.side_effect = [
        (mock_df, bank_dates),
        (mock_df, bank_1_dates),
    ]
    instance.query_builder.get_unity_data.return_value = (mock_df, mock_df, one_list, two_list)
    instance.query_builder.get_transacctions_data.return_value = (mock_df, tr_one, tr_two)
    instance.query_builder.get_trm_data.return_value = mock_df
    instance.query_builder.get_money_market_data.return_value = mock_df
    instance.query_builder.get_cdt_data.return_value = mock_df
    instance.query_builder.get_pyg_derivatives_data.return_value = mock_df
    instance.query_builder.get_ach_cycle_data.return_value = mock_df
    instance.query_builder.get_ach_data.return_value = mock_df
    instance.query_builder.get_repurchase_data.return_value = mock_df
    instance.query_builder.get_ach_balance_data.return_value = mock_df

    inc_df, exp_df, t0_df, t1_df, sum_df = MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock()
    instance.report_builder.create_report.return_value = (inc_df, exp_df, t0_df, t1_df, sum_df)
    instance.table_builder.create_table.return_value = (inc_df, exp_df, t0_df, t1_df, sum_df)

    avail_df = MagicMock()
    instance.report_builder.union_dataframes.return_value = avail_df
    instance.excel_manager.generate_excel.return_value = b"excel_bytes"

    instance.run()

    instance.report_builder.create_report.assert_called_once()
    instance.excel_manager.generate_excel.assert_called_once_with(
        inc_df, exp_df, t0_df, t1_df, sum_df, date_list
    )
    instance.table_builder.create_table.assert_called_once_with(
        inc_df, exp_df, t0_df, t1_df, sum_df, date_list
    )
    assert instance.table_manager.upload_table.call_count == 4
    instance.file_manager.upload_file.assert_called_once_with(b"excel_bytes", date(2026, 1, 9))


def test_main_success():
    mock_args = {"JOB_NAME": "test_job"}
    with patch("src.jobs.cash_control.getResolvedOptions", return_value=mock_args), \
         patch("src.jobs.cash_control.CashControl") as mock_class:
        mock_instance = Mock()
        mock_class.return_value = mock_instance

        main()

        mock_class.assert_called_once_with(mock_args)
        mock_instance.run.assert_called_once()


def test_main_missing_args():
    with patch("src.jobs.cash_control.getResolvedOptions", side_effect=Exception("Missing arg")):
        with pytest.raises(ValueError, match="Missing required job arguments"):
            main()
