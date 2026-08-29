import sys
from unittest.mock import MagicMock
import pytest

class MockColumn:
    def __init__(self, name="mock_col"):
        self.name = name
    def alias(self, new_name): return MockColumn(new_name)
    def cast(self, data_type): return self
    def isin(self, *vals): return self
    def isNotNull(self): return self
    def isNull(self): return self
    def desc(self): return self
    def asc(self): return self
    def __eq__(self, other): return MockColumn()
    def __ne__(self, other): return MockColumn()
    def __add__(self, other): return MockColumn()
    def __sub__(self, other): return MockColumn()
    def __mul__(self, other): return MockColumn()
    def __truediv__(self, other): return MockColumn()
    def __and__(self, other): return MockColumn()
    def __or__(self, other): return MockColumn()
    def __invert__(self): return MockColumn()

class MockFunctions:
    @staticmethod
    def col(name): return MockColumn(name)
    @staticmethod
    def lit(val): return MockColumn(f"lit({val})")
    @staticmethod
    def when(cond, val): return MockColumn()
    @staticmethod
    def coalesce(*cols): return MockColumn()
    @staticmethod
    def sum(col): return MockColumn()
    @staticmethod
    def count(col): return MockColumn()
    @staticmethod
    def upper(col): return MockColumn()
    @staticmethod
    def concat(*cols): return MockColumn()
    @staticmethod
    def broadcast(df): return df

# Mock modules before tests import them
mock_glue = MagicMock()
mock_glue.context.GlueContext = MagicMock()
mock_glue.job.Job = MagicMock()
mock_glue.utils.getResolvedOptions = MagicMock(return_value={
    "JOB_NAME": "test_job",
    "REPORT_DATE": "2026-08-28",
    "CATALOG_DATABASE": "test_db",
    "TRUSTED_BUCKET": "s3-test-trusted",
    "PROJECT_BUCKET_NAME": "s3-test-project"
})
sys.modules["awsglue"] = mock_glue
sys.modules["awsglue.context"] = mock_glue.context
sys.modules["awsglue.job"] = mock_glue.job
sys.modules["awsglue.utils"] = mock_glue.utils

mock_pyspark = MagicMock()
mock_pyspark.sql.functions = MockFunctions
mock_pyspark.sql.DataFrame = MagicMock
sys.modules["pyspark"] = mock_pyspark
sys.modules["pyspark.sql"] = mock_pyspark.sql
sys.modules["pyspark.sql.functions"] = MockFunctions
