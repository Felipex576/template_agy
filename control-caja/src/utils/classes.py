from dataclasses import dataclass
from pyspark.sql import DataFrame


@dataclass
class ProcessingDataFrames:
    trm_df: DataFrame
    trm_1_df: DataFrame
    bank_df: DataFrame
    bank_1_df: DataFrame
    money_market_df: DataFrame
    unity_df: DataFrame
    master_unity_df: DataFrame
    cdt_df: DataFrame
    pyg_df: DataFrame
    ach_cycle_df: DataFrame
    ach_df: DataFrame
    transactions_df: DataFrame
    issuance_df: DataFrame
    ach_balance_df: DataFrame
    final_t0_df: DataFrame
    final_t1_df: DataFrame
    final_income_df: DataFrame
    final_expense_df: DataFrame
    final_summary_df: DataFrame