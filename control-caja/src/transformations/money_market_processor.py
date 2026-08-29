from datetime import date
from typing import Tuple
from pyspark.sql import DataFrame, SparkSession, functions as F
from src.config.decorators import log_decorator, raise_decorator
from src.config.logger import logger
from src.utils.constants import MoneyMarketConstants


class MoneyMarketProcessor:
    """
    Applies money rules to money rules DataFrames.
    """

    def __init__(self, spark: SparkSession):
        self.spark = spark

    def calculate_turnover_sum(self, df: DataFrame, condition) -> float:
        """Calculates the sum of valor_de_giro for rows matching the given condition."""
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
            (F.col("clasificacion") == MoneyMarketConstants.SIM) &
            (F.col("cod_central_deposito").isin(MoneyMarketConstants.CENTRAL_DEPOSITORIES)) &
            (F.col("tipo_sim") == sim_type) &
            (F.col("codigo_especie").rlike(species_pattern))
        )
        return self.calculate_turnover_sum(df, condition)

    def calculate_definitive(self, df: DataFrame, operation_type: str, is_tes: bool) -> float:
        """Calculates total turnover sum for definitive (NORMAL non-MONEYMARKET) operations."""
        species_cond = (
            F.col("codigo_especie").rlike(MoneyMarketConstants.SPECIES_TES_PATTERN)
            if is_tes
            else ~F.col("codigo_especie").rlike(MoneyMarketConstants.SPECIES_TES_PATTERN)
        )
        condition = (
            (F.col("clasificacion") == MoneyMarketConstants.NORMAL) &
            (F.col("nemotecnico") != MoneyMarketConstants.MONEY_MARKET_NEMO) &
            (F.col("cod_central_deposito").isin(MoneyMarketConstants.CENTRAL_DEPOSITORIES)) &
            (F.col("tipo_operacion") == operation_type) &
            species_cond
        )
        return self.calculate_turnover_sum(df, condition)

    def calculate_repo(self, df: DataFrame, sim_type: str) -> float:
        """Calculates total turnover sum for REPO operations."""
        condition = (
            (F.col("clasificacion") == MoneyMarketConstants.REPO) &
            (F.col("cod_central_deposito").isin(MoneyMarketConstants.CENTRAL_DEPOSITORIES)) &
            (F.col("tipo_sim") == sim_type)
        )
        return self.calculate_turnover_sum(df, condition)

    def calculate_dollar(self, df: DataFrame, operation_type: str) -> float:
        """Calculates total turnover sum for dollar (NORMAL MONEYMARKET) operations."""
        condition = (
            (F.col("clasificacion") == MoneyMarketConstants.NORMAL) &
            (F.col("nemotecnico") == MoneyMarketConstants.MONEY_MARKET_NEMO) &
            (F.col("genera_detalle") == MoneyMarketConstants.GENERATE_DETAIL_YES) &
            (F.col("tipo_operacion") == operation_type)
        )
        return self.calculate_turnover_sum(df, condition)

    def calculate_ttv(self, df: DataFrame, operation_type: str) -> float:
        """Calculates total turnover sum for TTV operations."""
        condition = (
            (F.col("clasificacion") == MoneyMarketConstants.TTV) &
            (F.col("tipo_operacion") == operation_type)
        )
        return self.calculate_turnover_sum(df, condition)

    @log_decorator
    @raise_decorator    
    def money_market_today(self, base_df: DataFrame, 
                           start_date: date) -> Tuple[float, float, float, float, float, 
                                                      float, float, float, float, float, 
                                                      float, float, float, float]:
        """Calculates money market aggregates for the specified target date.

        Args:
            base_df (DataFrame): PySpark DataFrame containing money market transaction records.
            start_date (date): Target operation and settlement date.

        Returns:
            Tuple[float, ...]: A 14-element tuple containing calculated totals for money market operations.
        """
        logger.info("[INFO]: Running money market processor...")
        
        if base_df.isEmpty():
            return (0.0,) * 14

        input_date = start_date.strftime('%Y-%m-%d')
        
        filtered_df = base_df.filter(
            (F.col("fecha_operacion") != input_date) & 
            (F.col("fecha_cumplimiento") == input_date)
        )

        simult_tes_active_sell = self.calculate_simultaneous(
            filtered_df, MoneyMarketConstants.SIM_ACTIVE, MoneyMarketConstants.SPECIES_TES_PATTERN
        )
        simult_tes_passive_buy = self.calculate_simultaneous(
            filtered_df, MoneyMarketConstants.SIM_PASSIVE, MoneyMarketConstants.SPECIES_TES_PATTERN
        )
        simult_priv_active_sell = self.calculate_simultaneous(
            filtered_df, MoneyMarketConstants.SIM_ACTIVE, MoneyMarketConstants.SPECIES_PRIVATE_PATTERN
        )
        simult_priv_passive_buy = self.calculate_simultaneous(
            filtered_df, MoneyMarketConstants.SIM_PASSIVE, MoneyMarketConstants.SPECIES_PRIVATE_PATTERN
        )

        definitive_buy_tes = self.calculate_definitive(
            filtered_df, MoneyMarketConstants.OPERATION_BUY, is_tes=True
        )
        definitive_sell_tes = self.calculate_definitive(
            filtered_df, MoneyMarketConstants.OPERATION_SELL, is_tes=True
        )
        definitive_buy_priv = self.calculate_definitive(
            filtered_df, MoneyMarketConstants.OPERATION_BUY, is_tes=False
        )
        definitive_sell_priv = self.calculate_definitive(
            filtered_df, MoneyMarketConstants.OPERATION_SELL, is_tes=False
        )

        repos_active = self.calculate_repo(filtered_df, MoneyMarketConstants.SIM_ACTIVE)
        repos_passive = self.calculate_repo(filtered_df, MoneyMarketConstants.SIM_PASSIVE)

        dollar_buy = self.calculate_dollar(filtered_df, MoneyMarketConstants.OPERATION_BUY)
        dollar_sell = self.calculate_dollar(filtered_df, MoneyMarketConstants.OPERATION_SELL)

        ttv_income = self.calculate_ttv(filtered_df, MoneyMarketConstants.OPERATION_SELL)
        ttv_outflow = self.calculate_ttv(filtered_df, MoneyMarketConstants.OPERATION_BUY)

        logger.info("[DONE]: Money market processor.")
                    
        return (simult_tes_active_sell, simult_tes_passive_buy * -1, simult_priv_active_sell, 
                simult_priv_passive_buy * -1, definitive_buy_tes * -1, definitive_sell_tes, 
                definitive_buy_priv * -1, definitive_sell_priv, repos_active, repos_passive * -1, 
                dollar_buy * -1, dollar_sell, ttv_income, ttv_outflow * -1)