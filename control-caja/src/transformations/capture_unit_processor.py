from datetime import date
from pyspark.sql import DataFrame, SparkSession, functions as F
from pyspark.sql.types import StructType, StructField, DoubleType
from enum import Enum
from typing import Tuple, List, Type, Any
from src.config.decorators import log_decorator, raise_decorator
from src.config.logger import logger
from src.transformations.money_market_processor import MoneyMarketProcessor
from src.transformations.unity_processor import UnityProcessor
from src.transformations.t_1_processor import T1Processor
from src.transformations.cdt_processor import CdtProcessor
from src.transformations.pyg_processor import PygProcessor
from src.transformations.ach_cycle_processor import CycleProcessor
from src.transformations.ach_processor import AchProcessor
from src.transformations.credit_processor import CreditProcessor
from src.transformations.input_processor import InputProcessor
from src.utils.enums import Incomes, Expenses, CommonColumns, Summary


class CaptureProcessor:

    def __init__(self, spark: SparkSession):
        self.spark = spark
        self.money_market_processor = MoneyMarketProcessor(self.spark)
        self.unity_processor = UnityProcessor(self.spark)
        self.t1_processor = T1Processor(self.spark)
        self.cdt_processor = CdtProcessor(self.spark)
        self.pyg_processor = PygProcessor(self.spark)
        self.ach_cycle_processor = CycleProcessor(self.spark)
        self.ach_processor = AchProcessor(self.spark)
        self.credit_processor = CreditProcessor(self.spark)
        self.input_processor = InputProcessor(self.spark)
        
    
    def create_schema(self, enum_class: Type[Enum]) -> StructType:
        """Creates a StructType schema from an Enum class."""
        return StructType([
            StructField(item.value, DoubleType(), True)
            for item in enum_class
        ]) 
        
    def create_dataframe(self, data: List[Any], schema: StructType) -> DataFrame:
        """Creates a PySpark DataFrame from data and schema."""
        return self.spark.createDataFrame(
            [data],
            schema=schema
        )
        
    def add_columns(self, base_df: DataFrame) -> Tuple[DataFrame, float]:
        """Calculates total row sum column and extracts total value."""
        base_df = base_df.withColumn(
                    CommonColumns.TOTAL.value,
                    sum(F.coalesce(F.col(c), F.lit(0.0)) for c in base_df.columns)
                )
        
        total = base_df.select(CommonColumns.TOTAL.value).first()[0]
        
        return base_df, total
        
    @log_decorator
    @raise_decorator
    def process_data(self, money_market_df: DataFrame, unity_df: DataFrame, master_unity_df: DataFrame,
                     cdt_df: DataFrame, pyg_df: DataFrame, ach_cycle_df: DataFrame, ach_df: DataFrame,
                     transactions_df: DataFrame, issuance_df: DataFrame, ach_balance_df: DataFrame, trm: float,
                     bank_usd: float, bank_usd_1: float, report_date: date) -> Tuple[DataFrame, DataFrame, float, float]:
        """
        Processes financial data across multiple sources to generate income and expense DataFrames.

        Args:
            10 DataFrames: Source DataFrames for money market, unity, master unity, cdt, pyg, ach cycle, ach adaptor, transactions, issuance, and ach balance.
            trm (float): Current TRM exchange rate.
            bank_usd (float): Bank USD balance for T0.
            bank_usd_1 (float): Bank USD balance for T1.
            report_date (date): Target report date.

        Returns:
            Tuple[DataFrame, DataFrame, float, float]: Income DataFrame, expense DataFrame, total income, and total expense.
        """
        logger.info("[INFO]: Running process data...")
        
        (tes_act, tes_pas, priv_act, priv_pas, def_buy_tes, def_sell_tes, def_buy_priv, 
        def_sell_priv, repos_act, repos_pas, dolar_liquity, dolar_adm, ttv_income, 
        ttv_outcome) = self.money_market_processor.money_market_today(money_market_df, report_date)
    
        final_unity_df = self.unity_processor.process_unity(unity_df, master_unity_df)
        
        (ing_sebra_exchange, egr_sebra_exchange, income_breb, expense_breb, repurchases, due_cdt, 
         yields, ing_derivatives_otc, egr_derivatives_otc, op_ing_other_income, op_egr_other_income, 
         op_gmf, op_pay_findeter, op_expense_sebra, op_ing_other_ops, op_egr_other_ops, 
         movs_sebra) = self.t1_processor.normalize_unity(final_unity_df)             

        renewals = self.cdt_processor.cdt_renewals(cdt_df)        
        
        pyg = self.pyg_processor.pyg_derivatives(pyg_df)

        (withdrawals_ach, deposit_ach, withdrawals_reversals,  debit_sebra, credit_sebra, 
         debit_returns_sebra, credit_returns_sebra) = self.ach_cycle_processor.nomrmalize_ach_cycle(ach_cycle_df)
        
        ach_today_df, ach_deposit_cud, send_returns = self.ach_processor.normalize_refunds(ach_df, report_date)   
            
        (credit_income, credit_outcome, credit_adaptor_outcome, confirming_income, 
         confirming_outcome, sebra_credit) = self.credit_processor.credit_payments(ach_cycle_df, ach_today_df)
        
        (input_dic, account_variation, 
         movs_sebra_inc, movs_sebra_exp) = self.input_processor.create_input(report_date,money_market_df, transactions_df, 
                                                                             issuance_df, ach_balance_df, sebra_credit, movs_sebra)
        
        dollar_comp = ((dolar_adm - abs(dolar_liquity)) + input_dic[0]['incomeVentaDivisas']) - input_dic[0]['outcomeCompraDivisas']
        income_ach = sum(a + b + c for a, b, c in zip(deposit_ach, ach_deposit_cud, withdrawals_reversals)) - (credit_income + confirming_income) - account_variation
        outcome_ach = (sum(a + b for a, b in zip(withdrawals_ach, send_returns)) + abs(credit_adaptor_outcome)) - (abs(credit_outcome) + abs(confirming_outcome) + abs(credit_adaptor_outcome))
        
        income_multicash = input_dic[0].get('BancosUsdIncome', 0) * float(trm) if input_dic[0].get('BancosUsdIncome', 0) != 0.0 else float(0.0)
        expense_multicash = abs(input_dic[0].get('BancosUsdOutcome', 0)) * float(trm) if input_dic[0].get('BancosUsdOutcome', 0) != 0.0 else float(0.0)
                     
        income_schema = self.create_schema(Incomes)
        expense_schema = self.create_schema(Expenses)
        
        dollar_variation = bank_usd - bank_usd_1
        neto_multicash = income_multicash - expense_multicash
        change_variation = neto_multicash - dollar_variation
        
        income_data = [
            credit_income, confirming_income, def_sell_tes + input_dic[0]['incomeTIDIS'],
            def_sell_priv + input_dic[0]['incomeTCO'], yields, tes_act, priv_act, 
            repos_act + input_dic[0]['incomeSwapCaja'], input_dic[0]['incomeSimultaneaTES'],
            input_dic[0]['incomeSimultaneaPrivada'], input_dic[0]['incomeRepos'], 
            ttv_income + input_dic[0]['incomeTDA'], account_variation, renewals, input_dic[0]['incomeCDT'],
            pyg if pyg >= 0 else float(0.0), ing_derivatives_otc, input_dic[0]['incomeBonos'],
            float(0.0), income_ach, input_dic[0].get('BancosCopIncome', 0) + income_breb,
            income_multicash, dollar_comp, ing_sebra_exchange, op_ing_other_income + op_ing_other_ops + movs_sebra_inc + 
            (change_variation if change_variation < 0.0 else 0.0)
            ]
        
        expense_data = [
            abs(tes_pas), abs(priv_pas), abs(repos_pas) + input_dic[0]['outcomeSwapCaja'],
            abs(ttv_outcome) + input_dic[0]['outcomeTDA'], input_dic[0]['outcomeSimultaneaTES'], 
            input_dic[0]['outcomeSimultaneaPrivada'], input_dic[0]['outcomeRepos'], abs(due_cdt + renewals),
            float(0.0), abs(repurchases), abs(pyg) if pyg < 0.0 else float(0.0), egr_derivatives_otc,
            float(0.0), float(0.0), abs(credit_outcome) + abs(credit_adaptor_outcome), abs(confirming_outcome),
            abs(def_buy_tes) + input_dic[0]['outcomeTIDIS'], abs(def_buy_priv) + input_dic[0]['outcomeTCO'],
            abs(op_pay_findeter), abs(outcome_ach) if income_ach >= 0.0 else float(outcome_ach + abs(income_ach)),
            abs(op_gmf), abs(input_dic[0].get('BancosCopOutcome', 0)) + expense_breb,
            expense_multicash, abs(dollar_comp) if dollar_comp < 0.0 else 0.0, abs(op_expense_sebra), abs(egr_sebra_exchange),
            abs(op_egr_other_income + op_egr_other_ops + movs_sebra_exp) + (change_variation if change_variation >= 0.0 else 0.0)
            ]
        
        income_df = self.create_dataframe(income_data, income_schema)
        expense_df = self.create_dataframe(expense_data, expense_schema)
        
        income_df, total_income = self.add_columns(income_df)
        expense_df, total_expense = self.add_columns(expense_df)
        
        logger.info("[DONE]: Process data.")
        
        return income_df, expense_df, total_income, total_expense
        
    
    @log_decorator
    @raise_decorator   
    def create_summary_df(self, total: float, total_1: float, total_income: float, 
                          total_expense: float) -> DataFrame:
        """
        Creates summary DataFrame comparing available variation against total cash flow.

        Args:
            total (float): Available total for T0.
            total_1 (float): Available total for T1.
            total_income (float): Total calculated income.
            total_expense (float): Total calculated expense.

        Returns:
            DataFrame: Summary DataFrame with variation, flow, difference, and percentage difference.
        """
        logger.info("[INFO]: Running create summary...")
        
        available_variation = total - total_1
        total_flow = total_income - total_expense
        diff =  available_variation - total_flow
        
        if available_variation != 0.0:
            percent_diff = diff/available_variation
            percent_diff = round(percent_diff * 100, 3)
        else:
            percent_diff = None
            
        summary_data = [available_variation, total_flow, diff, percent_diff]
        
        summary_schema = self.create_schema(Summary)
        
        logger.info("[DONE]: Create summary.")
        
        return self.create_dataframe(summary_data, summary_schema)
        
            
        
        
                        
        