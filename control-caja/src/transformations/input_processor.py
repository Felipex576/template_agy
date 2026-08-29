from datetime import datetime, date
from pyspark.sql import DataFrame, SparkSession
from typing import Any, List, Tuple
from src.config.decorators import log_decorator, raise_decorator
from src.config.logger import logger
from src.transformations.t_1_processor import T1Processor
from src.transformations.cdt_processor import CdtProcessor
from src.transformations.ach_cycle_processor import CycleProcessor
from src.transformations.t_1_processor import T1Processor
from src.utils.constants import DEFAULT_INPUT_DIC


class InputProcessor:

    def __init__(self, spark: SparkSession):
        self.spark = spark
        self.t1_processor = T1Processor(self.spark)
        self.cdt_processor = CdtProcessor(self.spark)
        self.ach_cycle_processor = CycleProcessor(self.spark)
        
        
    @log_decorator
    @raise_decorator
    def create_input(self, report_date: date, money_market_df: DataFrame, 
                     transactions_df: DataFrame, issuance_df: DataFrame, 
                     ach_balance_df: DataFrame, sebra_credit: List, 
                     movs_sebra: List) -> Tuple[List[Any], float, float, float]:
        """
        Creates input dictionary structure and calculates variations for T+1 reconciliation.

        Args:
            report_date (date): Target report date.
            4 DataFrames: DataFrames for money market, transactions, issuance, and ach balance.
            sebra_credit (List): List of SEBRA credit amounts.
            movs_sebra (List): List of SEBRA movement values.

        Returns:
            Tuple[List[Any], float, float, float]: Input dictionary list, account variation, SEBRA income sum, and SEBRA expense sum.
        """
        logger.info("[INFO]: Running create input processor...")
        
        if report_date == datetime.today().date():
            input_dic =  DEFAULT_INPUT_DIC
            account_variation = 0.0
            movs_sebra_inc = 0.0
            movs_sebra_exp = 0.0
        else:
            input_dic = self.t1_processor.t1_market_today(money_market_df, report_date)
            
            (input_dic[0]['BancosCopIncome'], input_dic[0]['BancosCopOutcome'], input_dic[0]['BancosUsdIncome'], 
             input_dic[0]['BancosUsdOutcome']) = self.t1_processor.bank_transactions(transactions_df)
            
            (input_dic[0]['outcomeRecompras'], input_dic[0]['incomeCDT'], 
             input_dic[0]['incomeBonos']) = self.cdt_processor.issuance_repurchase(issuance_df)
            account_variation = self.ach_cycle_processor.account_variation(ach_balance_df)
            
            movs_sebra = [item for item in movs_sebra if item not in sebra_credit]
            movs_sebra_inc = sum(x for x in movs_sebra if x > 0.0)
            movs_sebra_exp = sum(x for x in movs_sebra if x < 0.0)
        
        logger.info("[DONE]: Create input processor.")
        
        return input_dic, account_variation, movs_sebra_inc, movs_sebra_exp