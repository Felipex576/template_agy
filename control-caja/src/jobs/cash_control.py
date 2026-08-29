import sys
from awsglue.utils import getResolvedOptions

from src.config.decorators import log_decorator, raise_decorator
from src.config.logger import logger
from src.config.spark_setup import initialize
from src.transformations.format_date import FormatDate
from src.queries.query_builder import QueryBuilder
from src.transformations.report_builder import ReportBuilder
from src.transformations.table_builder import TableBuilder
from src.resources.table_manager import TableManager
from src.utils.classes import ProcessingDataFrames
from src.resources.excel_manager import ExcelManager
from src.resources.file_manager import FileManager

from src.utils.constants import REQUIRED_JOB_ARGS, PARTITION_KEYS, MERGE_KEYS, MERGE_AVAILABLE


class CashControl:
    """Orchestrate report control caja generation and persistence."""
    
    def __init__(self, args):
        """Initialize the control caja report class."""
        
        self.glue_context, self.spark, self.job = initialize()
        self.job_name = args["JOB_NAME"]      
        self.report_date = args["REPORT_DATE"]
        self.report_name = args['REPORT_TYPE'].lower().replace(" ", "_")
        self.entity = args["COMPANY"]
        self.market_database = args["MARKET_DATABASE"]
        self.income_table = args['INCOME_TABLE']
        self.expense_table = args['EXPENSE_TABLE']
        self.available_table = args['AVAILABLE_TABLE']
        self.summary_table = args['SUMMARY_TABLE']
        # Databases
        self.rtbcol_database = args["RTBCOL_DATABASE"]
        self.unity_database = args["UNITY_DATABASE"]
        self.trm_database = args["TRM_DATABASE"]
        self.dominus_database = args["DOMINUS_DATABASE"]
        self.mambu_cc_database = args["MAMBU_CC_DATABASE"]
        self.checking_accounts_database = args["CHECKING_ACCOUNTS_DATABASE"]
        self.adapter_database = args["ADAPTER_DATABASE"]
        # Tables
        self.unity_operations_table = args["UNITY_OPERATIONS_TABLE"]
        self.bank_balances_table = args["BANK_BALANCES_TABLE"]
        self.money_market_table = args["MONEY_MARKET_TABLE"]
        self.cc_movements_table = args["CC_MOVEMENTS_TABLE"]
        self.master_homologation_table = args["MASTER_HOMOLOGATION_TABLE"]
        self.multicash_movements_table = args["MULTICASH_MOVEMENTS_TABLE"]
        self.umbrella_master_table = args["UMBRELLA_MASTER_TABLE"]
        self.trm_table = args["TRM_TABLE"]
        self.renewal_operations_table = args["RENEWAL_OPERATIONS_TABLE"]
        self.operations_a_table = args["OPERATIONS_A_TABLE"]
        self.operations_b_table = args["OPERATIONS_B_TABLE"]
        self.standardized_derivatives_table = args["STANDARDIZED_DERIVATIVES_TABLE"]
        self.mambu_accounts_table = args["MAMBU_ACCOUNTS_TABLE"]
        self.mambu_transactions_table = args["MAMBU_TRANSACTIONS_TABLE"]
        self.mambu_channels_table = args["MAMBU_CHANNELS_TABLE"]
        self.balance_table = args["BALANCE_TABLE"]
        self.deposit_account_table = args["DEPOSIT_ACCOUNT_TABLE"]
        self.reconciliation_adapter_table = args["RECONCILIATION_ADAPTER_TABLE"]
        self.trusted_bucket = args['TRUSTED_BUCKET']
        self.prefix_data = args['PREFIX_DATA'] 
        self.prefix_file = args['PREFIX_FILE']
        self.project_bucket = args['PROJECT_BUCKET_NAME']
        self.output_file_path = args['OUTPUT_FILE_PATH']
        self.chronos_bucket = args["CHRONOS_BUCKET_NAME"]
        
        self.income_path = f"s3://{self.trusted_bucket}/{self.prefix_data}/{self.report_name}/{self.income_table}/"
        self.expense_path = f"s3://{self.trusted_bucket}/{self.prefix_data}/{self.report_name}/{self.expense_table}/"
        self.available_path = f"s3://{self.trusted_bucket}/{self.prefix_data}/{self.report_name}/{self.available_table}/"
        self.summary_path = f"s3://{self.trusted_bucket}/{self.prefix_data}/{self.report_name}/{self.summary_table}/"
        self.income_table = f"glue_catalog.{self.market_database}.{self.income_table}"
        self.expense_table = f"glue_catalog.{self.market_database}.{self.expense_table}"
        self.available_table = f"glue_catalog.{self.market_database}.{self.available_table}"
        self.summary_table = f"glue_catalog.{self.market_database}.{self.summary_table}"
        self.zip_path = f"{self.prefix_file}/{self.report_name}/{self.entity}"       
        
        self.format_date = FormatDate()
        self.query_builder = QueryBuilder(
            self.spark, self.rtbcol_database, self.unity_database, self.trm_database,
            self.dominus_database, self.mambu_cc_database, self.checking_accounts_database,
            self.adapter_database, self.unity_operations_table
        )
        self.report_builder = ReportBuilder(self.spark)
        self.table_builder = TableBuilder(self.spark)
        self.table_manager = TableManager(self.spark)
        self.excel_manager = ExcelManager(self.spark)
        self.file_manager = FileManager(
            self.spark, self.trusted_bucket, self.zip_path, self.entity, 
            self.chronos_bucket, self.output_file_path
        )

        self.job.init(self.job_name, {})

    @log_decorator
    @raise_decorator
    def run(self):
        logger.info(f"Running {self.report_name} report generation process...")
        
        self.report_date = self.format_date.parse_report_date(self.report_date) 
        logger.info(f"Parsed date: {self.report_date}")
               
        date_list = self.format_date.get_last_business_days(self.report_date)
        previous_list, next_list = self.format_date.get_all_dates(date_list) 
               
        bank_df, bank_dates = self.query_builder.get_bank_data(date_list, previous_list, self.bank_balances_table)
        bank_1_df, bank_1_dates = self.query_builder.get_bank_data(next_list, date_list, self.bank_balances_table)
        
        unity_df, master_unity_df, one_list, two_list = self.query_builder.get_unity_data(
            date_list, self.cc_movements_table, self.master_homologation_table
        )
        
        transactions_df, tr_one_list, tr_two_list = self.query_builder.get_transacctions_data(
            date_list, self.multicash_movements_table, self.umbrella_master_table
        )
              
        dfs = ProcessingDataFrames(
            trm_df = self.query_builder.get_trm_data(previous_list, self.trm_table),
            trm_1_df = self.query_builder.get_trm_data(date_list, self.trm_table),
            bank_df = bank_df,
            bank_1_df = bank_1_df,
            money_market_df = self.query_builder.get_money_market_data(date_list, self.money_market_table),
            unity_df = unity_df,
            master_unity_df = master_unity_df,
            cdt_df = self.query_builder.get_cdt_data(date_list, self.renewal_operations_table),
            pyg_df = self.query_builder.get_pyg_derivatives_data(previous_list, self.standardized_derivatives_table),
            ach_cycle_df = self.query_builder.get_ach_cycle_data(
                date_list, self.mambu_accounts_table, self.mambu_transactions_table, self.mambu_channels_table
            ),
            ach_df = self.query_builder.get_ach_data(date_list, previous_list, self.reconciliation_adapter_table),
            transactions_df = transactions_df,
            issuance_df = self.query_builder.get_repurchase_data(
                date_list, self.operations_a_table, self.operations_b_table
            ),
            ach_balance_df = self.query_builder.get_ach_balance_data(
                date_list, previous_list, self.balance_table, self.deposit_account_table
            ),
            final_t0_df = None,
            final_t1_df = None,
            final_income_df = None,
            final_expense_df = None,
            final_summary_df = None
        )
        
        (final_income_df, final_expense_df, final_t0_df, 
         final_t1_df, final_summary_df) = self.report_builder.create_report(
             date_list, previous_list, bank_dates, bank_1_dates, 
             one_list, two_list, tr_one_list, tr_two_list, dfs
         )
         
        excel_bytes = self.excel_manager.generate_excel(
            final_income_df, final_expense_df, final_t0_df, 
            final_t1_df, final_summary_df, date_list
        )
        
        (final_income_df, final_expense_df, final_t0_df, 
         final_t1_df, final_summary_df) = self.table_builder.create_table(
             final_income_df, final_expense_df, final_t0_df, 
             final_t1_df, final_summary_df, date_list
         )
         
        available_df = self.report_builder.union_dataframes(final_t0_df, final_t1_df)
        
        self.table_manager.upload_table(
            final_income_df, self.income_path, self.income_table, 
            PARTITION_KEYS, MERGE_KEYS
        )
        self.table_manager.upload_table(
            final_expense_df, self.expense_path, self.expense_table, 
            PARTITION_KEYS, MERGE_KEYS
        )
        self.table_manager.upload_table(
            available_df, self.available_path, self.available_table, 
            PARTITION_KEYS, MERGE_AVAILABLE
        )
        self.table_manager.upload_table(
            final_summary_df, self.summary_path, self.summary_table, 
            PARTITION_KEYS, MERGE_KEYS
        )
                
        logger.info("# [INFO]: uploading zip file to S3...")
        self.file_manager.upload_file(excel_bytes, self.report_date)
        
        logger.info(f"[INFO]: Report {self.report_name} generation process completed.")


def main():
    try:
        args = getResolvedOptions(sys.argv, REQUIRED_JOB_ARGS)
    except Exception as e:
        logger.error(f"# [ERROR]: Missing required job arguments: {e}")
        raise ValueError(f"Missing required job arguments: {e}")

    cash_control = CashControl(args)
    cash_control.run()
    logger.info("# [INFO]: Job completed successfully.")


if __name__ == "__main__":
    main()
