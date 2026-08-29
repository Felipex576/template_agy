from datetime import date, timedelta
from typing import Tuple, List, Any
from pyspark.sql import DataFrame, SparkSession, functions as F
import holidays_co as hc
from src.config.decorators import log_decorator, raise_decorator
from src.config.logger import logger
from src.utils.constants import (UnityConstants, T1MarketConstants, 
                                 BankTranscConstants, DEFAULT_INPUT_DIC)


class T1Processor:

    def __init__(self, spark: SparkSession):
        self.spark = spark

    @staticmethod
    def is_business_day(target_date: date) -> bool:
        """
        Checks if a given date is a business day in Colombia (weekday, non-holiday, and non-Dec 31).
        """
        if target_date.weekday() >= 5:
            return False
        if target_date.month == 12 and target_date.day == 31:
            return False
        if hasattr(hc, "is_holiday_date"):
            return not hc.is_holiday_date(target_date)
        elif hasattr(hc, "is_holiday"):
            return not hc.is_holiday(target_date)
        elif hasattr(hc, "get_colombia_holidays_by_year"):
            holidays = [
                h.date if hasattr(h, "date") else h
                for h in hc.get_colombia_holidays_by_year(target_date.year)
            ]
            return target_date not in holidays
        return True

    def first_business_day(self, start_date: date) -> Tuple[str, str]:
        """Calculates date range when start_date is the first business day after non-business days."""
        formatted_start_date = start_date.strftime('%Y-%m-%d')

        if self.is_business_day(start_date):
            dias_no_habiles = []
            fecha_iterada = start_date - timedelta(days=1)

            while not self.is_business_day(fecha_iterada):
                dias_no_habiles.append(fecha_iterada)
                fecha_iterada -= timedelta(days=1)

            if dias_no_habiles:
                dia_mas_antiguo = dias_no_habiles[-1]
                return dia_mas_antiguo.strftime('%Y-%m-%d'), formatted_start_date

        return formatted_start_date, formatted_start_date

    def last_business_day(self, start_date: date) -> Tuple[str, str]:
        """Calculates date range when start_date is the last business day before non-business days."""
        formatted_start_date = start_date.strftime('%Y-%m-%d')

        if self.is_business_day(start_date):
            dias_no_habiles = []
            fecha_iterada = start_date + timedelta(days=1)

            while not self.is_business_day(fecha_iterada):
                dias_no_habiles.append(fecha_iterada)
                fecha_iterada += timedelta(days=1)

            if dias_no_habiles:
                dia_mas_antiguo = dias_no_habiles[-1]
                return formatted_start_date, dia_mas_antiguo.strftime('%Y-%m-%d')

        return formatted_start_date, formatted_start_date

    def calculate_value_sum(self, df: DataFrame, condition) -> float:
        """Calculates total sum of valor for rows matching condition."""
        result = (
            df.filter(condition)
            .agg(
                F.coalesce(
                    F.sum(F.col("valor").cast("double")),
                    F.lit(0.0)
                ).alias("total")
            )
            .first()["total"]
        )
        return float(result)

    def calculate_signed_sums(self, df: DataFrame, condition) -> Tuple[float, float]:
        """Calculates positive sum (income) and negative sum (expense) for valor column."""
        filtered = df.filter(condition)
        result = (
            filtered.agg(
                F.coalesce(
                    F.sum(F.when(F.col("valor") > 0, F.col("valor").cast("double"))),
                    F.lit(0.0)
                ).alias("income"),
                F.coalesce(
                    F.sum(F.when(F.col("valor") < 0, F.col("valor").cast("double"))),
                    F.lit(0.0)
                ).alias("expense")
            )
            .first()
        )
        return float(result["income"]), float(result["expense"])

    def calculate_turnover(self, df: DataFrame, condition) -> float:
        """Calculates the sum of valor_de_giro for rows matching condition."""
        result = (
            df.filter(condition)
            .agg(
                F.coalesce(
                    F.sum(F.col("valor_de_giro").cast("double")),
                    F.lit(0.0)
                ).alias("total")
            )
            .first()["total"]
        )
        return float(result)

    def calculate_simultaneous(self, df: DataFrame, sim_type: str, species_pattern: str) -> float:
        """Calculates total turnover sum for simultaneous (SIM) operations."""
        condition = (
            (F.col("clasificacion") == T1MarketConstants.SIM) &
            (F.col("cod_central_deposito").isin(T1MarketConstants.CENTRAL_DEPOSITORIES)) &
            (F.col("tipo_sim") == sim_type) &
            (F.col("codigo_especie").rlike(species_pattern))
        )
        return self.calculate_turnover(df, condition)

    def calculate_outright(self, df: DataFrame, operation_type: str, is_tes: bool) -> float:
        """Calculates total turnover sum for outright (NORMAL non-MONEYMARKET) operations."""
        species_cond = (
            F.col("codigo_especie").rlike(T1MarketConstants.SPECIES_TES_PATTERN)
            if is_tes
            else ~F.col("codigo_especie").rlike(T1MarketConstants.SPECIES_TES_PATTERN)
        )
        condition = (
            (F.col("clasificacion") == T1MarketConstants.NORMAL) &
            (F.col("nemotecnico") != T1MarketConstants.MONEYMARKET) &
            (F.col("cod_central_deposito").isin(T1MarketConstants.CENTRAL_DEPOSITORIES)) &
            (F.col("tipo_operacion") == operation_type) &
            species_cond
        )
        return self.calculate_turnover(df, condition)

    def calculate_repo(self, df: DataFrame, operation_type: str, sim_type: str) -> float:
        """Calculates total turnover sum for REPO operations."""
        condition = (
            (F.col("clasificacion") == T1MarketConstants.REPO) &
            (F.col("cod_central_deposito").isin(T1MarketConstants.CENTRAL_DEPOSITORIES)) &
            (F.col("tipo_operacion") == operation_type) &
            (F.col("tipo_sim") == sim_type)
        )
        return self.calculate_turnover(df, condition)

    def calculate_dollar(self, df: DataFrame, operation_type: str) -> float:
        """Calculates total turnover sum for dollar (NORMAL MONEYMARKET) operations."""
        condition = (
            (F.col("clasificacion") == T1MarketConstants.NORMAL) &
            (F.col("nemotecnico") == T1MarketConstants.MONEYMARKET) &
            (F.col("genera_detalle") == T1MarketConstants.GENERATE_DETAIL_YES) &
            (F.col("tipo_operacion") == operation_type)
        )
        return self.calculate_turnover(df, condition)

    def calculate_ttv(self, df: DataFrame, operation_type: str) -> float:
        """Calculates total turnover sum for TTV operations."""
        condition = (
            (F.col("clasificacion") == T1MarketConstants.TTV) &
            (F.col("tipo_operacion") == operation_type)
        )
        return self.calculate_turnover(df, condition)
    
    @log_decorator
    @raise_decorator
    def normalize_unity(self, base_df: DataFrame) -> Tuple[float, float, float, float, float, 
                                                           float, float, float, float, float, 
                                                           float, float, float, float, float, 
                                                           float, List[float]]:
        """
        Calculates normalized Unity movement aggregates.

        Args:
            base_df (DataFrame): PySpark DataFrame containing Unity movement records.

        Returns:
            Tuple[float, ..., List[float]]: A 17-element tuple containing calculated totals and SEBRA movements list.
        """
        logger.info("[INFO]: Running normalize unity processor...")
        
        if base_df.isEmpty():
            return (
                0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                0.0, 0.0, 0.0, 0.0, 0.0, 0.0, []
            )

        ing_sebra_exchange, egr_sebra_exchange = self.calculate_signed_sums(
            base_df, F.col("concepto") == UnityConstants.EXCHANGE_SEBRA
        )

        repurchases = self.calculate_value_sum(
            base_df, F.col("concepto") == UnityConstants.OPERATIONS
        )

        due_cdt = self.calculate_value_sum(
            base_df, F.col("concepto") == UnityConstants.ISSUING_PAYMENTS
        )

        yields = self.calculate_value_sum(
            base_df, F.col("concepto") == UnityConstants.PAYMENT_RETURNS
        )

        ing_derivatives_otc, egr_derivatives_otc = self.calculate_signed_sums(
            base_df, F.col("concepto") == UnityConstants.DERIVATIVES_OTC
        )

        sebra_df = base_df.filter(F.col("concepto") == UnityConstants.THIRD_HEADING)
        movs_sebra = [float(row["valor"]) for row in sebra_df.select("valor").collect()]

        op_ing_other_income, op_egr_other_income = self.calculate_signed_sums(
            base_df, F.col("concepto").isin(UnityConstants.OTHER_INCOME)
        )

        op_gmf = self.calculate_value_sum(
            base_df, F.col("concepto") == UnityConstants.GMF_CONCEPT
        )

        op_pay_findeter = self.calculate_value_sum(
            base_df, F.col("concepto") == UnityConstants.INTEREST_PAYMENTS
        )

        op_expense_sebra = self.calculate_value_sum(
            base_df, F.col("concepto").isin(UnityConstants.EXPENSE_SEBRA)
        )

        op_ing_other_ops, op_egr_other_ops = self.calculate_signed_sums(
            base_df, F.col("concepto").isin(UnityConstants.OTHER_OPS)
        )
        
        logger.info("[DONE]: Normalize unity processor.")

        return (ing_sebra_exchange, egr_sebra_exchange * -1, UnityConstants.INCOME_BREB, 
                UnityConstants.EXPENSE_BREB * -1, repurchases * -1, due_cdt * -1, yields, ing_derivatives_otc, 
                egr_derivatives_otc * -1, op_ing_other_income, op_egr_other_income * -1, op_gmf * -1, 
                op_pay_findeter * -1, op_expense_sebra * -1, op_ing_other_ops, op_egr_other_ops * -1, 
                movs_sebra)
    
    @log_decorator
    @raise_decorator
    def t1_market_today(self, base_df: DataFrame, start_date: date) -> List[Any]:
        """Calculates money market position summary dictionary for T+1 reconciliation.

        Args:
            base_df (DataFrame): PySpark DataFrame containing TES money market operations (dfOperacionesMercadoTES).
            start_date (date): Operation date.

        Returns:
            List[Any]: A 2-element list containing a dictionary with cash flow categories and a status string.
        """
        
        logger.info("[INFO]: Running T1 money market processor.")
        
        if base_df.isEmpty():
            return DEFAULT_INPUT_DIC
        
        input_date = start_date.strftime('%Y-%m-%d')

        filtered_df = base_df.filter(
            (F.col("fecha_operacion") == input_date) &
            (F.col("fecha_cumplimiento") == input_date)
        )

        simult_tes_act_sell = self.calculate_simultaneous(
            filtered_df, T1MarketConstants.SIM_ACTIVE, T1MarketConstants.SPECIES_TES_PATTERN
        )
        simult_tes_pas_buy = self.calculate_simultaneous(
            filtered_df, T1MarketConstants.SIM_PASSIVE, T1MarketConstants.SPECIES_TES_PATTERN
        )
        simult_priv_act_sell = self.calculate_simultaneous(
            filtered_df, T1MarketConstants.SIM_ACTIVE, T1MarketConstants.SPECIES_PRIVATE_PATTERN
        )
        simult_priv_pas_buy = self.calculate_simultaneous(
            filtered_df, T1MarketConstants.SIM_PASSIVE, T1MarketConstants.SPECIES_PRIVATE_PATTERN
        )

        definitives_buy_tes = self.calculate_outright(
            filtered_df, T1MarketConstants.OPERATION_BUY, is_tes=True
        )
        definitives_sell_tes = self.calculate_outright(
            filtered_df, T1MarketConstants.OPERATION_SELL, is_tes=True
        )
        definitives_buy_priv = self.calculate_outright(
            filtered_df, T1MarketConstants.OPERATION_BUY, is_tes=False
        )
        definitives_sell_priv = self.calculate_outright(
            filtered_df, T1MarketConstants.OPERATION_SELL, is_tes=False
        )

        repos_active_income = self.calculate_repo(
            filtered_df, T1MarketConstants.OPERATION_SELL, T1MarketConstants.SIM_ACTIVE
        )
        repos_passive_income = self.calculate_repo(
            filtered_df, T1MarketConstants.OPERATION_SELL, T1MarketConstants.SIM_PASSIVE
        )
        repos_active_outcome = self.calculate_repo(
            filtered_df, T1MarketConstants.OPERATION_BUY, T1MarketConstants.SIM_ACTIVE
        )
        repos_passive_outcome = self.calculate_repo(
            filtered_df, T1MarketConstants.OPERATION_BUY, T1MarketConstants.SIM_PASSIVE
        )

        dollar_buy = self.calculate_dollar(filtered_df, T1MarketConstants.OPERATION_BUY)
        dollar_sell = self.calculate_dollar(filtered_df, T1MarketConstants.OPERATION_SELL)

        ttv_income = self.calculate_ttv(filtered_df, T1MarketConstants.OPERATION_SELL)
        ttv_outcome = self.calculate_ttv(filtered_df, T1MarketConstants.OPERATION_BUY)

        logger.info("[DONE]: T1 money market processor.")
        
        return [
            {
                "incomeComercialesCop": 0.0,
                "incomeRepos": repos_passive_income,
                "incomeSimultaneaTES": simult_tes_pas_buy,
                "incomeSimultaneaPrivada": simult_priv_pas_buy,
                "incomeVentaDivisas": dollar_sell,
                "incomeSwapCaja": repos_active_income,
                "incomeCDT": 0.0,
                "incomeBonos": 0.0,
                "incomeCreditoCapital": 0.0,
                "incomeCreditoINT8ereses": 0.0,
                "incomeTIDIS": definitives_sell_tes,
                "incomeTCO": definitives_sell_priv,
                "incomeTDA": ttv_income,
                "outcomeEncaje": 0.0,
                "outcomeComercialesCop": 0.0,
                "outcomeDepositoRemunerado": 0.0,
                "outcomeRepos": repos_active_outcome,
                "outcomeSimultaneaTES": simult_tes_act_sell,
                "outcomeSimultaneaPrivada": simult_priv_act_sell,
                "outcomeCompraDivisas": dollar_buy,
                "outcomeSwapCaja": repos_passive_outcome,
                "outcomeRecompras": 0.0,
                "outcomeDesembolsos": 0.0,
                "outcomeTIDIS": definitives_buy_tes,
                "outcomeTCO": definitives_buy_priv,
                "outcomeTDA": ttv_outcome,
                "outcomeSEBRA": 0.0,
            },
            T1MarketConstants.DEFAULT_REGISTER_STATUS
        ]

    def calculate_bank_currency_sums(self, df: DataFrame, currency: str) -> Tuple[float, float]:
        """Calculates income (monto >= 0) and outcome (monto < 0) for a specified currency."""
        currency_df = df.filter(F.col("moneda") == currency)
        result = (
            currency_df.agg(
                F.coalesce(
                    F.sum(F.when(F.col("monto") >= 0, F.col("monto").cast("double"))),
                    F.lit(0.0)
                ).alias("income"),
                F.coalesce(
                    F.sum(F.when(F.col("monto") < 0, F.col("monto").cast("double"))),
                    F.lit(0.0)
                ).alias("outcome")
            )
            .first()
        )
        return float(result["income"]), float(result["outcome"])

    @log_decorator
    @raise_decorator
    def bank_transactions(self, base_df: DataFrame) -> Tuple[float, float, float, float]:
        """Calculates bank transaction totals for COP and USD currencies for T+1 reconciliation.

        Args:
            base_df (DataFrame): PySpark DataFrame containing bank transaction records (df_final).

        Returns:
            Tuple[float, float, float, float]: (bank_cop_income, bank_cop_outcome, bank_usd_income, bank_usd_outcome)
        """
        
        logger.info("[INFO]: Running bank transactions processor.")
        
        if base_df.isEmpty():
            return 0.0, 0.0, 0.0, 0.0

        filtered_df = base_df.filter(
            ~F.col("cuenta_bancaria").isin(BankTranscConstants.EXCLUDE_ACCOUNTS)
        )

        bank_cop_income, bank_cop_outcome = self.calculate_bank_currency_sums(
            filtered_df, BankTranscConstants.CURRENCY_COP
        )
        bank_usd_income, bank_usd_outcome = self.calculate_bank_currency_sums(
            filtered_df, BankTranscConstants.CURRENCY_USD
        )

        bank_cop_outcome_pos = -bank_cop_outcome if bank_cop_outcome != 0.0 else 0.0
        bank_usd_outcome_pos = -bank_usd_outcome if bank_usd_outcome != 0.0 else 0.0

        logger.info("[DONE]: Bank transactions processor.")
        
        return bank_cop_income, bank_cop_outcome_pos, bank_usd_income, bank_usd_outcome_pos