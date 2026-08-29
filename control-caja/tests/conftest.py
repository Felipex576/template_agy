"""Pytest configuration and fixtures for testing."""

import sys
import os
from unittest.mock import MagicMock

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

sys.modules['awsglue'] = MagicMock()
sys.modules['awsglue.utils'] = MagicMock()
sys.modules['awsglue.context'] = MagicMock()
sys.modules['awsglue.job'] = MagicMock()

# Mock datafoundation modules
datafoundation_mock = MagicMock()
sys.modules['datafoundation'] = datafoundation_mock
sys.modules['datafoundation.iceberg'] = MagicMock()
sys.modules['datafoundation.iceberg.manager'] = MagicMock()
sys.modules['datafoundation.file_transmission'] = MagicMock()
sys.modules['datafoundation.file_transmission.constants'] = MagicMock()
sys.modules['datafoundation.file_transmission.enums'] = MagicMock()
sys.modules['datafoundation.file_transmission.generator'] = MagicMock()


class MockColumn:
    """Mock PySpark Column supporting rich comparisons, arithmetic, and chaining."""
    def __ge__(self, other): return MockColumn()
    def __le__(self, other): return MockColumn()
    def __gt__(self, other): return MockColumn()
    def __lt__(self, other): return MockColumn()
    def __eq__(self, other): return MockColumn()
    def __ne__(self, other): return MockColumn()
    def __and__(self, other): return MockColumn()
    def __or__(self, other): return MockColumn()
    def __invert__(self): return MockColumn()
    def __neg__(self): return MockColumn()
    def __add__(self, other): return MockColumn()
    def __sub__(self, other): return MockColumn()
    def __mul__(self, other): return MockColumn()
    def __truediv__(self, other): return MockColumn()
    def __radd__(self, other): return MockColumn()
    def __rsub__(self, other): return MockColumn()
    def __getattr__(self, name): return MockColumn()
    def __call__(self, *args, **kwargs): return MockColumn()
    def __getitem__(self, item): return MockColumn()


class MockFunctions:
    """Mock pyspark.sql.functions module."""
    def __getattr__(self, name):
        return lambda *args, **kwargs: MockColumn()


class StructField:
    def __init__(self, name, dataType=None, nullable=True, metadata=None):
        self.name = name
        self.dataType = dataType
        self.nullable = nullable
        self.metadata = metadata


class StructType:
    def __init__(self, fields=None):
        self.fields = list(fields) if fields else []
    def __iter__(self):
        return iter(self.fields)
    def __len__(self):
        return len(self.fields)
    def __add__(self, other):
        return StructType(self.fields + (other.fields if isinstance(other, StructType) else list(other)))


class DoubleType: pass
class StringType: pass
class IntegerType: pass
class DateType: pass
class TimestampType: pass


class MockTypes:
    StructType = StructType
    StructField = StructField
    DoubleType = DoubleType
    StringType = StringType
    IntegerType = IntegerType
    DateType = DateType
    TimestampType = TimestampType
    def __getattr__(self, name):
        return MagicMock()


pyspark_mock = MagicMock()
pyspark_sql_mock = MagicMock()
pyspark_sql_mock.functions = MockFunctions()
pyspark_sql_mock.types = MockTypes()
pyspark_mock.sql = pyspark_sql_mock

sys.modules['pyspark'] = pyspark_mock
sys.modules['pyspark.sql'] = pyspark_sql_mock
sys.modules['pyspark.sql.functions'] = pyspark_sql_mock.functions
sys.modules['pyspark.sql.types'] = pyspark_sql_mock.types
sys.modules['pyspark.sql.window'] = MagicMock()

mock_spark_context = MagicMock()
mock_spark_context._active_spark_context = None
sys.modules['pyspark.context'] = MagicMock()
sys.modules['pyspark.context'].SparkContext = mock_spark_context
sys.modules['pyspark.conf'] = MagicMock()