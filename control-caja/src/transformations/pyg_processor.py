from pyspark.sql import DataFrame, SparkSession, functions as F
from src.config.decorators import log_decorator, raise_decorator
from src.config.logger import logger


class PygProcessor:

    def __init__(self, spark: SparkSession):
        self.spark = spark
        
    @log_decorator
    @raise_decorator
    def pyg_derivatives(self, base_df: DataFrame) -> float:
        """
        Calculates total P&G standardized derivatives utility.

        Args:
            base_df (DataFrame): PySpark DataFrame containing derivatives standardized records.

        Returns:
            float: Total derivatives utility sum.
        """
        logger.info("[INFO]: Running pyg derivatives processor...")
        
        if base_df.isEmpty():
            return 0.0
        
        dues = (
            base_df
            .agg(
                F.coalesce(
                    F.sum("utilidad"), 
                    F.lit(0.0)))
            .first()[0])
        
        logger.info("[DONE]: Pyg derivatives processor.")
        
        return float(dues)