from pyspark.sql import DataFrame, SparkSession, functions as F
from src.config.decorators import log_decorator, raise_decorator
from src.config.logger import logger
from datetime import datetime, date
from typing import List, Tuple
from src.utils.classes import ProcessingDataFrames
from src.transformations.trm_processor import TrmProcessor
from src.transformations.available_table import AvailableTable
from src.transformations.capture_unit_processor import CaptureProcessor


class ReportBuilder:

    def __init__(self, spark: SparkSession):
        self.spark = spark
        self.trm_processor = TrmProcessor(self.spark)
        self.available_table = AvailableTable(self.spark)
        self.capture_processor = CaptureProcessor(self.spark)

    @staticmethod
    def convert_to_date(value: str | date) -> date:
        """Converts string or date value to date object."""
        if isinstance(value, date):
            return value

        value = value.strip()

        if value.upper().startswith("DATE"):
            value = value[4:].strip()

        return datetime.strptime(value, "%Y-%m-%d").date()

    def filter_date_df(self, base_df: DataFrame, col_name: str, 
                       filter_date: str | date) -> DataFrame:
        """Filters DataFrame by exact date match."""
        filter_date = self.convert_to_date(filter_date)

        return base_df.filter(F.col(col_name) == F.lit(filter_date))

    def filter_two_dates(self, base_df: DataFrame, col_name: str, 
                         date_one: str, date_two: str) -> DataFrame:
        """Filters DataFrame within date range (inclusive)."""
        date_one = self.convert_to_date(date_one)
        date_two = self.convert_to_date(date_two)

        return base_df.filter(
            (F.col(col_name) >= F.lit(date_one)) & (F.col(col_name) <= F.lit(date_two))
        )

    def union_dataframes(self, base_df: DataFrame, union_df: DataFrame) -> DataFrame:
        """Combines two DataFrames by column names."""
        return base_df.unionByName(union_df)

    
    @log_decorator
    @raise_decorator
    def create_report(self, date_list: List, previous_list: List, bank_dates: List, 
                      bank_1_dates: List, one_list: List, two_list: List, 
                      tr_one_list: List, tr_two_list: List, 
                      dfs: ProcessingDataFrames) -> Tuple[DataFrame, DataFrame, DataFrame, 
                                                          DataFrame, DataFrame]:
        """
        Orchestrates daily transformations across multiple dates and accumulates results.

        Args:
            8 date Lists: Lists of target dates, previous dates, bank dates, and intermediate filter date lists.
            dfs (ProcessingDataFrames): Container holding source and accumulated DataFrames.

        Returns:
            Tuple[DataFrame, DataFrame, DataFrame, DataFrame, DataFrame]: 5 accumulated DataFrames (T0, T1, income, expense, and summary).
        """
        logger.info("[INFO]: Running create report processor...")
        
        for (current_date, prev_date, bd, 
             bd_1, od_1, od_2, tr_1, tr_2) in zip(date_list, previous_list, bank_dates, 
                                                  bank_1_dates, one_list, two_list,
                                                  tr_one_list, tr_two_list):
                 
            logger.info(f"[INFO]: Running create report... Date: {current_date}")
            
            trm = self.trm_processor.normalize_trm(
                self.filter_date_df(dfs.trm_df, "fecha", prev_date)
            )

            trm_1 = self.trm_processor.normalize_trm(
                self.filter_date_df(dfs.trm_1_df, "fecha", current_date)
            )
            available_t0_df, bank_usd, total = self.available_table.create_available_df(
                self.filter_date_df(dfs.bank_df, "fecha_movimiento", bd), trm
            )
            available_t1_df, bank_usd_1, total_1 = (
                self.available_table.create_available_df(
                    self.filter_date_df(dfs.bank_1_df, "fecha_movimiento", bd_1), trm_1
                )
            )

            income_df, expense_df, total_income, total_expense = (
                self.capture_processor.process_data(
                    self.filter_date_df(dfs.money_market_df, "fecha_cuadre", current_date),
                    self.filter_two_dates(dfs.unity_df, "fecha", od_1, od_2),
                    dfs.master_unity_df,
                    self.filter_date_df(dfs.cdt_df, "fecha_operacion", current_date),
                    self.filter_date_df(dfs.pyg_df, "fecha_inicial", prev_date),
                    self.filter_date_df(dfs.ach_cycle_df, "fecha_valor", current_date),
                    self.filter_two_dates(dfs.ach_df, "fecha_consulta", current_date, prev_date),
                    self.filter_two_dates(dfs.transactions_df, "fecha_mvto", tr_1, tr_2),
                    self.filter_date_df(dfs.issuance_df, "fecha_inicio", current_date),
                    self.filter_two_dates(dfs.ach_balance_df, "fecha_saldo", current_date, prev_date),
                    trm,
                    bank_usd,
                    bank_usd_1,
                    current_date,
                )
            )

            summary_df = self.capture_processor.create_summary_df(
                total, total_1, total_income, total_expense
            )

            if all(
                df is None
                for df in (dfs.final_income_df, dfs.final_expense_df, 
                           dfs.final_t0_df, dfs.final_t1_df, dfs.final_summary_df)):
                dfs.final_income_df = income_df
                dfs.final_expense_df = expense_df
                dfs.final_t0_df = available_t0_df
                dfs.final_t1_df = available_t1_df
                dfs.final_summary_df = summary_df

            else:
                dfs.final_income_df = self.union_dataframes(dfs.final_income_df, income_df)
                dfs.final_expense_df = self.union_dataframes(dfs.final_expense_df, expense_df)
                dfs.final_t0_df = self.union_dataframes(dfs.final_t0_df, available_t0_df)
                dfs.final_t1_df = self.union_dataframes(dfs.final_t1_df, available_t1_df)
                dfs.final_summary_df = self.union_dataframes(dfs.final_summary_df, summary_df)
                
            logger.info(f"[DONE]: Create report. Date: {current_date}.")

        logger.info("[DONE]: Create report processor.")
        
        return (
            dfs.final_income_df,
            dfs.final_expense_df,
            dfs.final_t0_df,
            dfs.final_t1_df,
            dfs.final_summary_df,
        )
