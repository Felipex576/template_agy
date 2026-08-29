from typing import Tuple, List
from pyspark.sql import DataFrame, SparkSession, functions as F

from src.config.decorators import log_decorator, raise_decorator
from src.config.logger import logger
from src.utils.constants import CycleConstants


class CycleProcessor:

    def __init__(self, spark: SparkSession):
        self.spark = spark

    @staticmethod
    def _build_slot_expressions(channel: str, slots: List[Tuple[str, str]], 
                                is_withdrawal: bool = False, prefix: str = "slot"):
        """Builds list of PySpark aggregation expressions for time slots of a given channel."""
        monto_col = -F.col("monto").cast("double") if is_withdrawal else F.col("monto").cast("double")
        time_str = F.substring(F.col("fecha_hora_valor").cast("string"), 12, 8)

        exprs = []
        for idx, (start_time, end_time) in enumerate(slots):
            cond = (F.col("canal") == channel) & (time_str >= start_time) & (time_str <= end_time)
            exprs.append(
                F.coalesce(F.sum(F.when(cond, monto_col)), F.lit(0.0)).alias(f"{prefix}_{idx}")
            )
        return exprs

    @log_decorator
    @raise_decorator
    def nomrmalize_ach_cycle(self, base_df: DataFrame) -> Tuple[List[float], List[float], List[float], 
                                                                float, float, float, float]:
        """
        Normalizes ACH cycle transactions and calculates channel totals per time slot.

        Args:
            base_df (DataFrame): PySpark DataFrame containing ACH cycle transactions.

        Returns:
            Tuple[List[float], List[float], List[float], float, float, float, float]:
                Calculated totals for ACH and SEBRA movements.
        """
        logger.info("[INFO]: Running normalize ach cycle processor...")
        
        if base_df.isEmpty():
            return (CycleConstants.WITHDRAWALS_ACH, CycleConstants.DEPOSIT_ACH,
                    CycleConstants.WITHDRAWALS_REVERSALS, CycleConstants.DEBIT_SEBRA,
                    CycleConstants.CREDIT_SEBRA, CycleConstants.DEBIT_RETURNS_SEBRA,
                    CycleConstants.CREDIT_RETURNS_SEBRA)
            
        
        base_df = base_df.filter(
            F.col("Canal").isin(CycleConstants.CONCEPTS_ACH)
        )
        
        ret_exprs = self._build_slot_expressions(
            CycleConstants.ACH_WITHDRAWAL, CycleConstants.WITHDRAWAL_SLOTS, is_withdrawal=True, prefix="ret"
        )
        dep_exprs = self._build_slot_expressions(
            CycleConstants.ACH_DEPOSIT, CycleConstants.DEPOSIT_SLOTS, is_withdrawal=False, prefix="dep"
        )
        dev_exprs = self._build_slot_expressions(
            CycleConstants.ACH_RETURN, CycleConstants.DEPOSIT_SLOTS, is_withdrawal=False, prefix="dev"
        )

        sebra_exprs = [
            F.coalesce(
                F.sum(F.when(F.col("canal") == CycleConstants.DEBIT_TRANSFER_SEBRA, F.abs(F.col("monto").cast("double")))),
                F.lit(0.0)
            ).alias("debit_sebra"),
            F.coalesce(
                F.sum(F.when(F.col("canal") == CycleConstants.CREDIT_TRANSFER_SEBRA, F.col("monto").cast("double"))),
                F.lit(0.0)
            ).alias("credit_sebra"),
            F.coalesce(
                F.sum(F.when(F.col("canal") == CycleConstants.RETURN_DEBIT_FUNDS_SEBRA, F.col("monto").cast("double"))),
                F.lit(0.0)
            ).alias("debit_returns_sebra"),
            F.coalesce(
                F.sum(F.when(F.col("canal") == CycleConstants.RETURN_CREDIT_FUNDS_SEBRA, F.abs(F.col("monto").cast("double")))),
                F.lit(0.0)
            ).alias("credit_returns_sebra"),
        ]

        all_exprs = ret_exprs + dep_exprs + dev_exprs + sebra_exprs
        row = base_df.agg(*all_exprs).first()

        withdrawals_ach = [float(row[f"ret_{i}"]) for i in range(5)]
        deposit_ach = [float(row[f"dep_{i}"]) for i in range(5)]
        withdrawals_reversals = [float(row[f"dev_{i}"]) for i in range(5)]

        debit_sebra = float(row["debit_sebra"])
        credit_sebra = float(row["credit_sebra"])
        debit_returns_sebra = float(row["debit_returns_sebra"])
        credit_returns_sebra = float(row["credit_returns_sebra"])

        logger.info("[DONE]: Normalize ach cycle processor.")        
        
        return (withdrawals_ach, deposit_ach, withdrawals_reversals, 
                debit_sebra, credit_sebra, debit_returns_sebra, 
                credit_returns_sebra)
               
    def account_variation(self, base_df: DataFrame) -> float:
        """
        Calculates account balance variation between the last two balance dates.

        Args:
            base_df (DataFrame): PySpark DataFrame containing account balance records.

        Returns:
            float: Account balance difference between dates.
        """
        logger.info("[INFO]: Running Account variation processor.")
        
        if base_df.isEmpty():
            return float(0.0)
        
        valores = (
            base_df
            .orderBy(F.col("fecha_saldo").desc())
            .select("total_balance")
            .collect()
            )

        logger.info("[DONE]: Account variation processor.")
        
        return float(
            valores[0]["total_balance"] - valores[1]["total_balance"]
        )
        
        
    