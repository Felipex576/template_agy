from typing import Tuple, List
from pyspark.sql import DataFrame, SparkSession, functions as F
from src.config.decorators import log_decorator, raise_decorator
from src.config.logger import logger
from src.utils.constants import CreditConstants


class CreditProcessor:

    def __init__(self, spark: SparkSession):
        self.spark = spark
        self.sebra_credit: List[float] = []

    def _calculate_mambu_payments(self, mambu_filtered: DataFrame) -> Tuple[float, float, float, float]:
        """Calculates credit and confirming income and outcome amounts from filtered Mambu DataFrame."""
        mambu_row = mambu_filtered.agg(
            F.coalesce(
                F.sum(
                    F.when(
                        (F.col("id") == CreditConstants.CREDIT_ACCOUNT) & (F.col("monto") >= 0),
                        F.col("monto").cast("double")
                    )
                ),
                F.lit(0.0)
            ).alias("credit_income"),
            F.coalesce(
                F.sum(
                    F.when(
                        (F.col("id") == CreditConstants.CREDIT_ACCOUNT) & (F.col("monto") < 0),
                        F.col("monto").cast("double")
                    )
                ),
                F.lit(0.0)
            ).alias("credit_negative"),
            F.coalesce(
                F.sum(
                    F.when(
                        (F.col("canal") == CreditConstants.DEPOSIT_CROS) & (F.col("monto") > 0),
                        F.col("monto").cast("double")
                    )
                ),
                F.lit(0.0)
            ).alias("deposit_cros"),
            F.coalesce(
                F.sum(
                    F.when(
                        (F.col("id") == CreditConstants.CONFIRMING_ACCOUNT) & (F.col("monto") >= 0),
                        F.col("monto").cast("double")
                    )
                ),
                F.lit(0.0)
            ).alias("confirming_income"),
            F.coalesce(
                F.sum(
                    F.when(
                        (F.col("id") == CreditConstants.CONFIRMING_ACCOUNT) & (F.col("monto") < 0),
                        F.col("monto").cast("double")
                    )
                ),
                F.lit(0.0)
            ).alias("confirming_negative"),
        ).first()

        credit_income = float(mambu_row["credit_income"] or 0.0)
        credit_outcome = float((-mambu_row["credit_negative"] + mambu_row["deposit_cros"]) or 0.0)
        confirming_income = float(mambu_row["confirming_income"] or 0.0)
        confirming_outcome = float((-mambu_row["confirming_negative"]) or 0.0)

        return credit_income, credit_outcome, confirming_income, confirming_outcome

    @log_decorator
    @raise_decorator
    def credit_payments(self, base_df: DataFrame, today_df: DataFrame) -> Tuple[float, float, float, 
                                                                                float, float, List]:
        """
        Calculates credit and confirming income and outcome amounts from Mambu and Adaptor DataFrames.

        Args:
            base_df (DataFrame): PySpark DataFrame containing Mambu transactions (df_mambu).
            today_df (DataFrame): PySpark DataFrame containing Adaptor conciliation transactions (df_adaptor).

        Returns:
            Tuple[float, float, float, float, float, List]:
                Credit income, credit outcome, credit adaptor outcome,
                confirming income, confirming outcome, and SEBRA credit list.
        """
        logger.info("[INFO]: Running credit payments processor...")
        
        if base_df.isEmpty():
            (credit_income, credit_outcome,
             confirming_income, confirming_outcome) = (0.0, 0.0, 0.0, 0.0)
        
        if today_df.isEmpty():
            credit_adaptor_outcome = 0.0
            
        if not base_df.isEmpty():
            # Extract SEBRA credit list
            df_sebra = base_df.filter(
                F.col("canal").isin(CreditConstants.SEBRA_CONCEPTS) &
                F.col("id").isin(CreditConstants.CREDIT_ACCOUNTS)
            )
            self.sebra_credit = [
                float(row["monto"]) for row in df_sebra.select("monto").collect()
            ] if not df_sebra.isEmpty() else []

            # Filter out excluded concepts
            mambu_filtered = base_df.filter(~F.col("canal").isin(CreditConstants.EXCLUDE_CONCEPTS))

            # Aggregate credit and confirming income/outcomes
            (credit_income, credit_outcome,
             confirming_income, confirming_outcome) = self._calculate_mambu_payments(mambu_filtered)

        # Process Adaptor transactions
        if not today_df.isEmpty() and "reg5_datos_originador" in today_df.columns:
            adaptor_filtered = today_df.filter(
                F.ltrim(F.trim(F.col("reg5_datos_originador").cast("string")), "0") == CreditConstants.ORIGINATOR_ACCOUNT
            )

            val_str = F.trim(F.col("reg6_valor_transaccion").cast("string"))
            amount_expr = F.when(
                F.length(val_str) > 2,
                F.substring(val_str, 1, F.length(val_str) - 2).cast("double")
            ).otherwise(F.lit(0.0))

            adaptor_sum = float(
                adaptor_filtered.agg(F.coalesce(F.sum(amount_expr), F.lit(0.0))).first()[0] or 0.0
            )
            credit_adaptor_outcome = adaptor_sum * -1

        logger.info("[DONE]: Credit payments processor.")
        
        return (credit_income, credit_outcome, credit_adaptor_outcome, 
                confirming_income, confirming_outcome, self.sebra_credit)