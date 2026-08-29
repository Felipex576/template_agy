from pyspark.sql import SparkSession, DataFrame, functions as F
from src.config.decorators import log_decorator, raise_decorator
from src.config.logger import logger

class TrmProcessor:

    def __init__(self, spark: SparkSession):
        self.spark = spark
        
    
    @log_decorator
    @raise_decorator     
    def normalize_trm(self, base_df: DataFrame) -> float:
        """
        Normalizes and sums the TRM exchange rate for the target date.

        Args:
            base_df (DataFrame): PySpark DataFrame containing TRM records.

        Returns:
            float: Summed TRM value.
        """
        logger.info("[INFO]: Running normalize trm...")
        
        if base_df.isEmpty():
            return 0.0
        logger.info("[DONE]: Normalize trm.")
        
        return float(
            base_df.agg(
                F.coalesce(
                    F.sum("valor"), 
                    F.lit(0.0))
                .alias("total"))
            .first()["total"])