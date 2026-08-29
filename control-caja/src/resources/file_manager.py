import boto3
import io
import zipfile
from pyspark.sql import SparkSession
from datetime import datetime, date
from src.config.logger import logger
from src.config.decorators import raise_decorator, log_decorator

class FileManager():
    """Handle report file packaging and uploads to S3."""

    def __init__(self, spark: SparkSession, trusted_bucket :str, zip_path: str, 
                 entity: str, chronos_bucket: str, output_file_path: str):
        self.spark = spark
        self.trusted_bucket = trusted_bucket
        self.zip_path = zip_path 
        self.entity = entity
        self.s3_client = boto3.client('s3')
        self.chronos_bucket = chronos_bucket
        self.output_file_path = output_file_path
             

    @log_decorator
    @raise_decorator   
    def upload_file(self, excel_bytes: bytes, report_date: date) -> None: 
        """
        Package Excel and text outputs in a ZIP file and upload it to S3.

        Args:
            excel_bytes (bytes): Serialized Excel workbook bytes.
            report_date (date): Report date in date format.

        Returns:
            None.
        """
        
        formatted_date = report_date.strftime("%Y%m%d")
        self.zip_path = f"{self.zip_path}/{report_date}"
        zip_key = f"{self.zip_path}/f_control_caja_{self.entity}{formatted_date}.zip"
        
        excel_name = f"f_control_caja_{self.entity}{formatted_date}.xlsx"
        
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr(
                excel_name,
                excel_bytes
            )
        
        zip_buffer.seek(0)
        
        self.s3_client.put_object(
            Body= zip_buffer.getvalue(),
            Bucket=self.trusted_bucket,
            Key=zip_key
        )
        logger.info(f"[INFO]: Zip uploaded to s3://{self.trusted_bucket}/{zip_key}")
        
        self.s3_client.put_object(
            Body= zip_buffer.getvalue(),
            Bucket=self.chronos_bucket,
            Key=self.output_file_path
        )
        logger.info(f"[INFO]: Zip uploaded to s3://{self.chronos_bucket}/{self.output_file_path}")
