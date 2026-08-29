from typing import Tuple
from pyspark.sql import DataFrame, SparkSession, functions as F

from src.config.decorators import log_decorator, raise_decorator
from src.config.logger import logger
from src.utils.constants import CdtConstants


class CdtProcessor:

    def __init__(self, spark: SparkSession):
        self.spark = spark
    
    @log_decorator
    @raise_decorator
    def cdt_renewals(self, base_df: DataFrame) -> float:
        """
        Calculates total CDT renewals from renewal records.

        Args:
            base_df (DataFrame): PySpark DataFrame containing CDT renewal records.

        Returns:
            float: Total renewals sum.
        """
        logger.info("[INFO]: Running cdt renewals processor...")
        
        if base_df.isEmpty():
            return 0.0

        logger.info("[DONE]: Cdt renewals processor.")
        
        return float(
            base_df.agg(
                F.coalesce(
                    F.sum("total_renewal"),
                    F.lit(0.0))
                .alias("renewals"))
            .first()["renewals"])

    def calculate_column_sum(self, df: DataFrame, value_col: str) -> float:
        """Calculates total sum or single rounded value for a given column based on row count."""
        if df.isEmpty():
            return 0.0

        row = df.agg(
            F.count("*").alias("cnt"),
            F.coalesce(F.sum(F.col(value_col).cast("double")), F.lit(0.0)).alias("total_sum"),
            F.coalesce(F.first(F.col(value_col).cast("double")), F.lit(0.0)).alias("first_val")
        ).first()

        cnt = row["cnt"]
        if cnt > 1:
            return float(row["total_sum"])
        elif cnt == 1:
            return float(round(row["first_val"], 2))
        return 0.0
    
    @log_decorator
    @raise_decorator
    def issuance_repurchase(self, base_df: DataFrame) -> Tuple[float, float, float]:
        """Calculates repurchases, CDT issuances, and bond issuances totals for T+1 reconciliation.

        Args:
            base_df (DataFrame): PySpark DataFrame containing operation records with flat columns.

        Returns:
            Tuple[float, float, float]: (repurchases, cdt_issuances, bond_issuances)
        """
        
        logger.info("[INFO]: Running issuance repurchase processor.")
        
        if base_df.isEmpty():
            return 0.0, 0.0, 0.0

        df_repurchases = base_df.filter(
            (F.col("tipo_participacion") == CdtConstants.PARTICIPATION_TYPE_REPURCHASE))

        df_cdt_issuances = base_df.filter(
            F.col("codigo_isin").startswith(CdtConstants.IS_IN_CODE) &
            (F.col("tipo_participacion") == CdtConstants.PARTICIPATION_TYPE_ISSUANCE))

        df_bond_issuances = base_df.filter(
            F.col("codigo_isin").startswith(CdtConstants.ISIN_CODE_BONOS) &
            (F.col("tipo_participacion") == CdtConstants.PARTICIPATION_TYPE_ISSUANCE))

        repurchases = self.calculate_column_sum(df_repurchases, "precio_contado")
        cdt_issuances = self.calculate_column_sum(df_cdt_issuances, "saldo")
        bond_issuances = self.calculate_column_sum(df_bond_issuances, "saldo")

        logger.info("[DONE]: Issuance repurchase processor.")
        
        return repurchases, cdt_issuances, bond_issuances
