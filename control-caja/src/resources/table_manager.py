from datafoundation.iceberg.manager import IcebergTableManager
from pyspark.sql import DataFrame, SparkSession, functions as F
from src.config.decorators import log_decorator, raise_decorator
from src.config.logger import logger


class TableManager:

    def __init__(self, spark: SparkSession):
        self.spark = spark
        self.iceberg_manager = IcebergTableManager(self.spark)
        
    
    @log_decorator
    @raise_decorator    
    def upload_table(self, base_df: DataFrame, output_path: str,
                     report_table: str, partition_keys: str,
                     merge_keys: str) -> None:
        
        self.iceberg_manager.create_table(output_path, base_df, partition_keys, report_table)
        logger.info(f"# [INFO]: Iceberg table created/verified at {output_path}")
        
        self.iceberg_manager.synchronize_schema(base_df, report_table)
        logger.info(f"# [INFO]: Schema synchronized for table {report_table}")
        
        self.iceberg_manager.merge_data(base_df, merge_keys, report_table)
        logger.info(f"# [INFO]: Data merged into table {report_table}")