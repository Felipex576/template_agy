from datetime import date
from pyspark.sql import DataFrame, SparkSession, functions as F
from pyspark.sql.types import StructType, StructField, DoubleType, DateType
from src.config.decorators import log_decorator, raise_decorator
from src.config.logger import logger
from src.transformations.bank_processor import BankProcessor
from src.utils.enums import Available
from src.utils.constants import BankConstants
from typing import Tuple


class AvailableTable:

    def __init__(self, spark: SparkSession):
        self.spark = spark
        self.bank_processor = BankProcessor(self.spark) 
    
    @log_decorator
    @raise_decorator            
    def create_available_df(self, bank_df: DataFrame, trm: float) -> Tuple[DataFrame, float, float]:
        """
        Creates available funds summary DataFrame and calculates bank USD and grand total.

        Args:
            bank_df (DataFrame): PySpark DataFrame containing bank balance records.
            trm (float): Current TRM exchange rate.

        Returns:
            Tuple[DataFrame, float, float]: Available funds DataFrame, bank USD total, and grand total.
        """
        logger.info("[INFO]: Running create available processor...")
        
        (banrep_no_rem_90, banrep_no_rem_91, banrep_rem, savings_dav, savings_occ, 
         savings_bog, savings_banc, adm_dav, adm_bog, adm_banc, cayman, bofa, 
         citi, citi_usd, citi2, pan, bradesco) = self.bank_processor.bank_balances(bank_df)
        
        (cayman, bofa, citi, citi_usd, citi2, 
         pan, bradesco) = (cayman * trm, bofa * trm, citi * trm, citi_usd * trm, 
                           citi2 * trm, pan * trm, bradesco * trm)
         
        bank_rep =  banrep_rem + banrep_no_rem_90 + banrep_no_rem_91
        bank_com = savings_dav + savings_occ + savings_bog + savings_banc + adm_dav + adm_bog + adm_banc
        bank_usd = cayman + bofa + citi + citi_usd + citi2 + pan + bradesco
        total = bank_rep + bank_com + bank_usd
        
        schema = StructType([
            StructField(Available.BANCO_REPUBLICA.value, DoubleType(), True),
            StructField(Available.BANCOS_COMERCIALES.value, DoubleType(), True),
            StructField(Available.BANCOS_USD.value, DoubleType(), True),
            StructField(Available.TRM.value, DoubleType(), True),
            StructField(Available.TOTAL.value, DoubleType(), True)
        ])
        
        final_df = self.spark.createDataFrame(
            [(bank_rep, bank_com, bank_usd, trm, total)],
            schema=schema
        )
        
        logger.info("[DONE]: Create available processor.")             
        return final_df, bank_usd, total