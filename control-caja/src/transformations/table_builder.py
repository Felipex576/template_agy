from typing import List, Tuple
from pyspark.sql import DataFrame, SparkSession, functions as F
from pyspark.sql.types import StructType, StructField, DateType

from src.config.decorators import log_decorator, raise_decorator
from src.config.logger import logger
from src.utils.enums import CommonColumns
from src.utils.constants import BankConstants


class TableBuilder:

    def __init__(self, spark: SparkSession):
        self.spark = spark

    def add_type_column(self, base_df: DataFrame, type_str: str) -> DataFrame:
        "Adds tipo_disponible column to dataframe."
        
        if type_str == BankConstants.AVAILABLE_T0:
            return (
                base_df
                .withColumn(
                    CommonColumns.TIPO_DISPONIBLE.value, 
                    F.lit(BankConstants.AVAILABLE_T0))
                )
        elif type_str == BankConstants.AVAILABLE_T1:
            return (
                base_df
                .withColumn(
                    CommonColumns.TIPO_DISPONIBLE.value, 
                    F.lit(BankConstants.AVAILABLE_T1))
                )
        else:
            return base_df
        
    @log_decorator
    @raise_decorator
    def add_date_columns(self, base_df: DataFrame, date_list: List, type_str: str) -> DataFrame:
        """
        Adds fecha_reporte from date list and fecha_cargue with current date.

        Args:
            base_df (DataFrame): PySpark DataFrame to add date columns to.
            date_list (List[Any]): List of date objects matching the DataFrame row count.

        Returns:
            DataFrame: DataFrame with fecha_reporte and fecha_cargue date columns.
        """
        logger.info("[INFO]: Adding date columns to DataFrame...")

        base_df = self.add_type_column(base_df, type_str)
        
        rows = base_df.collect()
        data = [list(row) + [rep_date] for row, rep_date in zip(rows, date_list)]

        new_schema = StructType(
            base_df.schema.fields + [
                StructField(CommonColumns.FECHA_REPORTE.value, DateType(), True)
            ]
        )

        result_df = self.spark.createDataFrame(data, schema=new_schema)
        result_df = result_df.withColumn(CommonColumns.FECHA_GENERACION.value, F.current_date())
        
        logger.info("[DONE]: Date columns successfully added.")
        return result_df
    
    def create_table(self, income_df: DataFrame, expense_df: DataFrame, 
                     t0_df: DataFrame, t1_df: DataFrame,  summary_df: DataFrame, 
                     date_list: List) -> Tuple[DataFrame, DataFrame, DataFrame, 
                                               DataFrame, DataFrame]:
        
        
        income_df = self.add_date_columns(income_df, date_list, "")
        expense_df = self.add_date_columns(expense_df, date_list, "")
        t0_df = self.add_date_columns(t0_df, date_list, BankConstants.AVAILABLE_T0)
        t1_df = self.add_date_columns(t1_df, date_list, BankConstants.AVAILABLE_T1)
        summary_df = self.add_date_columns(summary_df, date_list, "")
    
        return income_df, expense_df, t0_df, t1_df, summary_df

        
