from datetime import date, timedelta
from typing import Tuple
from pyspark.sql import DataFrame, SparkSession, functions as F

from src.config.decorators import log_decorator, raise_decorator
from src.config.logger import logger
from src.utils.constants import BankConstants


class BankProcessor:
    """
    Applies bank rules to bank DataFrames.
    """

    def __init__(self, spark: SparkSession):
        self.spark = spark

    @staticmethod
    def get_previous_date(start_date: date, end_date: date) -> date:
        """Determines the previous processing date based on cut-off logic."""
        if start_date < date(2026, 3, 13):
            previous_date = start_date - timedelta(days=1)
        else:
            previous_date = end_date

        return previous_date

    @staticmethod
    def adjust_year_end_dates(start_date: date, previous_date: date) -> date:
        """Adjusts dates for year-end processing exceptions."""
        if start_date.strftime('%m-%d') == '12-31':
            previous_date += timedelta(days=2)

        if previous_date.strftime('%m-%d') == '12-31':
            previous_date += timedelta(days=1)

        return previous_date

    def calculate_ban_rep(self, df: DataFrame, account: str) -> float:
        """Calculates final bank balance for a specific Banco de la República account."""
        return (
            df.filter(F.col("numero_cuenta") == account)
            .agg(
                F.coalesce(
                    F.sum("saldo_bancario_final"),
                    F.lit(0.0)
                ).alias("saldo_bancario_final")
            )
            .first()["saldo_bancario_final"]
        )

    def get_balance(self, base_df: DataFrame, result_df: DataFrame, accounts: list, 
                    bank: str = None, bank_type: str = None) -> float:
        """Calculates total bank balance filtered by accounts or bank type."""
        if bank and bank_type:
            main_filter = ((F.col("nombre_banco") == bank) & (F.col("tipo_cuenta") == bank_type))
        else:
            main_filter = F.col("numero_cuenta").isin(accounts)

        filter_df = base_df.filter(main_filter)
        result_df = result_df.unionByName(filter_df)

        return (
            filter_df
            .agg(
                F.coalesce(
                    F.sum("saldo_bancario_final"),
                    F.lit(0.0)
                ).alias("saldo")
            )
            .first()["saldo"]
        )
        
    def trm_convert(self, base_df: DataFrame, result_df: DataFrame, bank: str = None, 
                    account: str = None) -> float:
        """Calculates net balance converting exchange rate adjustments."""
        if bank:
            main_filter = F.col("nombre_banco") == bank
        else:
            main_filter = F.col("numero_cuenta") == account

        filter_df = base_df.filter(main_filter)
        result_df = result_df.unionByName(filter_df)

        result = (
            filter_df
            .agg(
                F.coalesce(
                    F.sum("saldo_bancario_final"),
                    F.lit(0.0)
                ).alias("saldo_bancario_final"),
                F.coalesce(
                    F.sum("saldo_en_canje"),
                    F.lit(0.0)
                ).alias("saldo_en_canje")
            )
            .first()
        )

        final_balance = result["saldo_bancario_final"]
        balance = result["saldo_en_canje"]

        result = final_balance - abs(balance)

        return result

    def bank_balances(self, base_df: DataFrame) -> Tuple[float, float, float, float, float, 
                                                         float, float, float, float, float, 
                                                         float, float, float, float, float, 
                                                         float, float]:
        """
        Calculates balance summaries across all registered bank accounts.

        Args:
            base_df (DataFrame): PySpark DataFrame containing bank balance records.

        Returns:
            Tuple[float, ...]: A 17-element tuple containing account balances and category totals.
        """
        if base_df.isEmpty():
            return (0.0,) * 17
        
        # Banco de la Republica - No Remunerado
        banrep_norem90 = self.calculate_ban_rep(base_df, BankConstants.BANREP_NOREM90)
        banrep_norem91 = self.calculate_ban_rep(base_df, BankConstants.BANREP_NOREM91)
        # Banco de la Republica - Remunerado
        banrep_rem = self.calculate_ban_rep(base_df, BankConstants.BANREP_REM)
        
        BankConstants.BANREP_NO_REM = banrep_norem90 + banrep_norem91
        
        result_df = (
            base_df.filter(
                F.col("numero_cuenta").isin([BankConstants.BANREP_NOREM90, 
                                             BankConstants.BANREP_NOREM91,
                                             BankConstants.BANREP_REM])))
        
        base_df = base_df.filter(F.col("nombre_titular_cuenta") == BankConstants.HOLDER_NAME)
        
        #Ahorros
        savings_dav = self.get_balance(base_df, result_df, BankConstants.BALANCE_ACCOUNT["ahorro_dav"])
        savings_occ = self.get_balance(base_df, result_df, BankConstants.BALANCE_ACCOUNT["ahorro_occ"])
        savings_bog = self.get_balance(base_df, result_df, BankConstants.BALANCE_ACCOUNT["ahorro_bog"])
        savings_banc = self.get_balance(base_df, result_df, BankConstants.BALANCE_ACCOUNT["ahorro_banc"])
        #Administrativas
        adm_dav = self.get_balance(base_df, result_df, BankConstants.BALANCE_ACCOUNT["adm_dav"])
        adm_bog = self.get_balance(base_df, result_df, BankConstants.BALANCE_ACCOUNT["adm_bog"])
        adm_banc = self.get_balance(base_df, result_df, BankConstants.BALANCE_ACCOUNT["adm_banc"])
        
        BankConstants.COMMERCIAL_COP = sum([savings_dav, savings_occ, savings_bog, savings_banc, adm_dav, adm_bog, adm_banc])
        #Dólares
        dol_cayman = self.trm_convert(base_df, result_df, BankConstants.USD_ACCOUNTS["dol_cayman"])
        dol_bofa = self.trm_convert(base_df, result_df, BankConstants.USD_ACCOUNTS["dol_bofa"])
        dol_citi = self.trm_convert(base_df, result_df, BankConstants.USD_ACCOUNTS["dol_citi"])
        dol_citi_usd = self.trm_convert(base_df, result_df, BankConstants.USD_ACCOUNTS["dol_citi_usd"])
        dol_citi2 = self.trm_convert(base_df, result_df, BankConstants.USD_ACCOUNTS["dol_citi2"])
        dol_bancol_panama = self.trm_convert(base_df, result_df, BankConstants.USD_ACCOUNTS["dol_bancol_panama"])
        bradesco = self.trm_convert(base_df, result_df, BankConstants.USD_ACCOUNTS["bradesco"])
        
        BankConstants.COMMERCIAL_USD = dol_bofa
        
        return (banrep_norem90, banrep_norem91, banrep_rem, savings_dav, savings_occ, savings_bog, 
                savings_banc, adm_dav, adm_bog, adm_banc, dol_cayman, dol_bofa, dol_citi, 
                dol_citi_usd, dol_citi2, dol_bancol_panama, bradesco)