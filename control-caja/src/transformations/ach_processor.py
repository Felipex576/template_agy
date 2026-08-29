from datetime import date
from typing import Tuple, List, Optional, Union
from pyspark.sql import DataFrame, SparkSession, functions as F
from src.config.decorators import log_decorator, raise_decorator
from src.config.logger import logger
from src.utils.constants import AchConstants


class AchProcessor:

    def __init__(self, spark: SparkSession):
        self.spark = spark

    def _calculate_matched_refunds(self, df: DataFrame) -> float:
        """Calculates matched amount between unauthorized OUT (cycle >= 4) and sent refunds."""
        out_rows = df.filter(
            F.col("name").endswith(AchConstants.OUT_SUFFIX) &
            (F.col("status") == AchConstants.UNAUTHORIZED_STATUS) &
            (F.col("cycle") >= AchConstants.CYCLE_THRESHOLD)
        )
        sent_rows = df.filter(F.col("transaction_type") == AchConstants.SENT_REFUND_TYPE)

        if out_rows.isEmpty() or sent_rows.isEmpty():
            return 0.0

        join_cols = [
            "reg6_cuenta_receptora", "rec_ent", "reg5_nombre_originador",
            "orig_ent", "reg6_nombre_cliente_receptor", "reg6_valor_transaccion", 
            "amount"
        ]

        out_grouped = (
            out_rows
            .withColumnRenamed("reg6_entidad_receptora", "rec_ent")
            .withColumnRenamed("reg5_entidad_originadora", "orig_ent")
            .groupBy(*join_cols).agg(F.count(F.lit(1)).alias("count_out"))
        )

        sent_grouped = (
            sent_rows
            .withColumnRenamed("reg5_entidad_originadora", "rec_ent")
            .withColumnRenamed("reg6_entidad_receptora", "orig_ent")
            .groupBy(*join_cols).agg(F.count(F.lit(1)).alias("count_sent"))
        )

        matched = out_grouped.join(sent_grouped, on=join_cols, how="inner")
        total = matched.agg(
            F.coalesce(F.sum(F.least("count_out", "count_sent") * F.col("amount")), F.lit(0.0)).alias("total")
        ).first()["total"]

        return float(total or 0.0)

    
    @log_decorator
    @raise_decorator
    def normalize_refunds(self, base_df: DataFrame, 
                          report_date: Optional[Union[str, date]] = None) -> Tuple[DataFrame, List[float], 
                                                                                   List[float]]:
        """
        Normalizes ACH refunds and calculates ACH CUD deposits and returns to send.

        Args:
            base_df (DataFrame): PySpark DataFrame containing ACH conciliation data for today and yesterday.
            report_date (Optional[Union[str, date]]): Optional target operation date.

        Returns:
            Tuple[DataFrame, List[float], List[float]]: Filtered today DataFrame, ACH CUD deposits list, and send returns list.
        """
        
        logger.info("[INFO]: Running normalize refunds processor...")
        
        if base_df.isEmpty():
            return (base_df, list(AchConstants.ACH_DEPOSIT_CUD), 
                    list(AchConstants.SEND_RETURNS))

        # Parse cycle from 'name' (e.g. '.1.OUT') and amount from 'reg6_valor_transaccion' (removing 2 decimal digits)
        df = (
            base_df
            .withColumn(
                "val_str",
                F.col("reg6_valor_transaccion").cast("string")
            )
            .withColumn(
                "cycle",
                F.split(F.col("name"), "\\.")[1].cast("int")
            )
            .withColumn(
                "amount",
                F.expr(
                    "substring(val_str, 1, length(val_str) - 2)"
                ).cast("double")
            )
            .drop("val_str")
        )

        # Split today and yesterday based on 'fecha'
        today_date = str(report_date)[:10] if report_date else df.agg(F.max("fecha_consulta").cast("string")).first()[0]
        today_df = df.filter(F.col("fecha_consulta").cast("string").startswith(today_date))
        yesterday_df = df.filter(~F.col("fecha_consulta").cast("string").startswith(today_date))   

        ach_deposit_cud = list(AchConstants.ACH_DEPOSIT_CUD)
        send_returns = list(AchConstants.SEND_RETURNS)

        # Process today (hoy = True)
        if not today_df.isEmpty():
            today_out = (
                F.col("name").endswith(AchConstants.OUT_SUFFIX) &
                (F.col("status") == AchConstants.UNAUTHORIZED_STATUS)
            )
            agg_exprs = [
                F.coalesce(F.sum(F.when(today_out & (F.col("cycle") == i), F.col("amount"))), F.lit(0.0)).alias(f"c_{i}")
                for i in range(1, AchConstants.TOTAL_CYCLES + 1)
            ]
            row = today_df.agg(*agg_exprs).first()

            for i in range(1, AchConstants.TOTAL_CYCLES + 1):
                cycle_val = float(row[f"c_{i}"] or 0.0)
                ach_deposit_cud[i - 1] = cycle_val
                if i < AchConstants.CYCLE_THRESHOLD:
                    send_returns[i] = cycle_val

            send_returns[4] = self._calculate_matched_refunds(today_df)

        # Process yesterday (hoy = False)
        if not yesterday_df.isEmpty():
            yesterday_out = (
                F.col("name").endswith(AchConstants.OUT_SUFFIX) &
                (F.col("status") == AchConstants.UNAUTHORIZED_STATUS) &
                (F.col("cycle") >= AchConstants.CYCLE_THRESHOLD)
            )
            yesterday_total = float(
                yesterday_df.filter(yesterday_out).agg(F.coalesce(F.sum("amount"), F.lit(0.0))).first()[0] or 0.0
            )
            send_returns[0] = yesterday_total - self._calculate_matched_refunds(yesterday_df)

        logger.info("[DONE]: Normalize refunds processor.")
        
        return today_df, ach_deposit_cud, send_returns        