from pyspark.sql import DataFrame, SparkSession, functions as F
from src.config.decorators import log_decorator, raise_decorator
from src.config.logger import logger

from src.utils.constants import UnityConstants

class UnityProcessor:

    def __init__(self, spark: SparkSession):
        self.spark = spark
        
    def join_dataframes(self, base_df: DataFrame, 
                        master_df: DataFrame) -> DataFrame:
        """Performs left join between base Unity DataFrame and master homologation DataFrame."""
        return (
            base_df
            .join(
                master_df, 
                base_df["concepto"] == master_df["codigo_contable"],
                "left")
            )
           
    def process_concept(self, base_df: DataFrame) -> DataFrame:
        """Categorizes and derives concept codes based on classification and operation type."""
        result_df = (
            base_df
            .withColumn(
                "sufijo_liquidacion",
                F.expr("right(liquidacion, 2)")
                )
            .withColumn(
                "concepto",
                F.when(F.col("concepto").isNull(),
                       F.when(
                           F.col("clasificacion") == UnityConstants.NORMAL,
                           F.when(
                               F.col("sufijo_liquidacion") == UnityConstants.SB,
                               F.lit(UnityConstants.LIQUIDATION[0]))
                           .when(
                               (F.col("sufijo_liquidacion") != UnityConstants.SB) &
                               (F.col("sufijo_liquidacion") != UnityConstants.OF),
                               F.lit(UnityConstants.LIQUIDATION[1]))
                           .when(
                               F.col("sufijo_liquidacion") == UnityConstants.OF,
                               F.lit(UnityConstants.LIQUIDATION[2]))
                           )
                       .when(
                           F.col("clasificacion") == UnityConstants.SIM,
                           F.when(
                               (F.col("tipo_operacion") == UnityConstants.VV) &
                               F.col("fecha_futura").isNull(),
                               F.lit(UnityConstants.OP_TYPE[0]))
                           .when(
                               (F.col("tipo_operacion") == UnityConstants.VV) &
                               F.col("fecha_futura").isNotNull(),
                               F.lit(UnityConstants.OP_TYPE[1]))
                           .when(
                               (F.col("tipo_operacion") == UnityConstants.CC) &
                               F.col("fecha_futura").isNull(),
                               F.lit(UnityConstants.OP_TYPE[2]))
                           .when(
                               (F.col("tipo_operacion") == UnityConstants.CC) &
                               F.col("fecha_futura").isNotNull(),
                               F.lit(UnityConstants.OP_TYPE[3]))
                           )
                       .when(
                           F.col("clasificacion") == UnityConstants.TTV,
                           F.lit(UnityConstants.CLASIFY[0])
                           )
                       .when(
                           F.col("clasificacion") == UnityConstants.REPO,
                           F.when(
                               F.col("tipo_operacion") == UnityConstants.CC,
                               F.lit(UnityConstants.CLASIFY[1]))
                           .when(
                               F.col("tipo_operacion") == UnityConstants.VV,
                               F.lit(UnityConstants.CLASIFY[2]))
                           )
                       )
                .otherwise(F.col("concepto"))
                )
            ).select("concepto", "valor", "cod_tipo_movimiento", 
                     "fecha", "cuenta_bancaria", "rendimiento")
        
        return result_df
        
    def process_value(self, join_df: DataFrame) -> DataFrame:
        """Applies concept names and signs to values based on movement type."""
        final_df = (
            join_df
            .withColumn(
                "concepto",
                F.when(
                    F.col("rendimiento").isNotNull(),
                    F.lit(UnityConstants.LIT_CONCEPT[0]))
                .when(
                    F.col("concepto") == UnityConstants.CONCEPT[0],
                    F.lit(UnityConstants.LIT_CONCEPT[1]))
                .when(
                    F.col("concepto").isin(UnityConstants.CONCEPT[1], 
                                           UnityConstants.CONCEPT[2]),
                    F.lit(UnityConstants.LIT_CONCEPT[2]))
                .when(
                    F.col("concepto") == UnityConstants.CONCEPT[3],
                    F.lit(UnityConstants.LIT_CONCEPT[3]))
                .otherwise(
                    F.coalesce(
                        F.col("concepto_cud"),
                        F.concat(
                            F.lit("Falta Homologación: "),
                            F.col("concepto")))
                    )
                )
            .withColumn(
                "valor",
                F.when(
                    F.col("cod_tipo_movimiento") == UnityConstants.ND,
                    F.lit(-1) * F.col("valor"))
                .otherwise(
                    F.col("valor"))
                )
            )
        
        return final_df
    
    @log_decorator
    @raise_decorator    
    def process_unity(self, base_df: DataFrame, master_df: DataFrame) -> DataFrame:
        """
        Processes raw Unity movements and joins with homologation master data.

        Args:
            base_df (DataFrame): PySpark DataFrame containing Unity movements.
            master_df (DataFrame): PySpark DataFrame containing master homologation data.

        Returns:
            DataFrame: Processed and normalized Unity DataFrame.
        """
        logger.info("[INFO]: Running unity processor...")
        
        unity_df = self.process_concept(base_df)
        join_df = self.join_dataframes(unity_df, master_df)
        
        logger.info("[DONE]: Unity processor.")
        
        return self.process_value(join_df)
        