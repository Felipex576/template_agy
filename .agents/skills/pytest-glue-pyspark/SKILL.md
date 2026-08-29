---
name: pytest-glue-pyspark
description: Universal testing guide, zero-JVM mocking harnesses (MockColumn, MockFunctions, MockTypes), PySpark/Glue test fixtures, test parametrization, and coverage enforcement for AWS Glue ETL pipelines using pytest. Use when writing, fixing, or reviewing unit tests for any PySpark/Glue job.
---

# Universal Pytest & Mocking Patterns for AWS Glue & PySpark

Comprehensive testing guide for writing fast, isolated, and deterministic unit tests for **AWS Glue**, **PySpark**, and **Apache Iceberg** applications without requiring an active JVM, live Spark cluster, or AWS credentials.

---

## 1. When to Activate This Skill

- Writing unit tests for PySpark DataFrame transformations and business processors.
- Implementing or updating the zero-JVM mock harness in `tests/conftest.py`.
- Testing AWS Glue job orchestrators, argument parsing, and storage managers.
- Writing parameterized tests for date calculations, edge cases, and data variations.
- Measuring, debugging, and achieving $\ge 80\%$ test coverage with `pytest-cov`.
- Running test suites inside Docker / Rancher Desktop containers.

---

## 2. The Zero-JVM Mocking Harness (`tests/conftest.py`)

To run hundreds of unit tests in seconds on standard CI/CD runners or local environments without initializing a heavyweight local JVM, `tests/conftest.py` intercepts `awsglue`, `pyspark`, and `datafoundation` at the module import level:

```python
"""Pytest configuration and zero-JVM mocks for Glue and PySpark."""
import os
import sys
from unittest.mock import MagicMock

# 1. Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# 2. Mock AWS Glue runtime modules
sys.modules['awsglue'] = MagicMock()
sys.modules['awsglue.utils'] = MagicMock()
sys.modules['awsglue.context'] = MagicMock()
sys.modules['awsglue.job'] = MagicMock()

# 3. Mock DataFoundation and Iceberg modules
datafoundation_mock = MagicMock()
sys.modules['datafoundation'] = datafoundation_mock
sys.modules['datafoundation.iceberg'] = MagicMock()
sys.modules['datafoundation.iceberg.manager'] = MagicMock()
sys.modules['datafoundation.file_transmission'] = MagicMock()


# 4. Rich PySpark Column Mock (Supports operator overloading and method chaining)
class MockColumn:
    """Mock PySpark Column supporting arithmetic, logic, comparison, and chaining."""
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


# 5. Mock PySpark SQL Functions (F.col, F.when, F.lit, F.concat, etc.)
class MockFunctions:
    def __getattr__(self, name):
        return lambda *args, **kwargs: MockColumn()


# 6. Mock PySpark SQL Types
class StructField:
    def __init__(self, name, dataType=None, nullable=True, metadata=None):
        self.name = name
        self.dataType = dataType
        self.nullable = nullable
        self.metadata = metadata or {}


class StructType:
    def __init__(self, fields=None):
        self.fields = list(fields) if fields else []
    def __iter__(self): return iter(self.fields)
    def __len__(self): return len(self.fields)
    def __add__(self, other):
        return StructType(self.fields + (other.fields if isinstance(other, StructType) else list(other)))


class MockTypes:
    StructType = StructType
    StructField = StructField
    StringType = type("StringType", (), {})
    DoubleType = type("DoubleType", (), {})
    IntegerType = type("IntegerType", (), {})
    DateType = type("DateType", (), {})
    TimestampType = type("TimestampType", (), {})
    def __getattr__(self, name): return MagicMock()


# 7. Inject PySpark Mocks
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
sys.modules['pyspark.context'] = MagicMock()
sys.modules['pyspark.conf'] = MagicMock()
```

---

## 3. Testing Transformation Processors

Test transformation logic in isolation by mocking input DataFrames:

```python
"""Tests for transformation processor."""
from unittest.mock import MagicMock
from src.transformations.domain_processor import DomainProcessor


def test_domain_processor_transform():
    # Arrange: set up mock DataFrame with chained methods
    mock_spark = MagicMock()
    mock_df = MagicMock()
    mock_df.select.return_value = mock_df
    mock_df.filter.return_value = mock_df
    mock_df.withColumn.return_value = mock_df
    mock_df.groupBy.return_value.agg.return_value = mock_df

    processor = DomainProcessor(mock_spark)

    # Act
    result_df = processor.process_records(mock_df)

    # Assert
    assert result_df is not None
    mock_df.select.assert_called()
```

---

## 4. Parameterized Testing

Use `@pytest.mark.parametrize` to validate edge cases and variations:

```python
"""Tests with multiple input variations."""
import pytest
from src.utils.formatters import clean_identifier


@pytest.mark.parametrize("raw_input,expected_output", [
    ("  acc_123  ", "ACC_123"),
    ("ACCOUNT-999", "ACCOUNT_999"),
    ("clean_id", "CLEAN_ID"),
])
def test_clean_identifier(raw_input, expected_output):
    result = clean_identifier(raw_input)
    assert result == expected_output
```

---

## 5. Testing the Job Orchestrator

Validate argument parsing and end-to-end method coordination without real I/O:

```python
"""Tests for main job orchestrator."""
from unittest.mock import patch, MagicMock
from src.jobs.pipeline_job import PipelineJob


@pytest.fixture
def mock_job_args():
    return {
        "JOB_NAME": "test-job",
        "REPORT_DATE": "2026-08-28",
        "CATALOG_DATABASE": "test_db",
        "TARGET_TABLE": "test_table",
        "TRUSTED_BUCKET": "test-bucket",
        "PREFIX_DATA": "data",
        "PROJECT_BUCKET_NAME": "project-bucket",
    }


def test_pipeline_job_run(mock_job_args):
    with patch("src.jobs.pipeline_job.initialize") as mock_init:
        mock_init.return_value = (MagicMock(), MagicMock(), MagicMock())
        
        job = PipelineJob(mock_job_args)
        job.query_builder = MagicMock()
        job.processor = MagicMock()
        job.table_manager = MagicMock()

        job.run()

        job.query_builder.get_data.assert_called()
        job.processor.transform.assert_called()
        job.table_manager.upload_table.assert_called()
```

---

## 6. Execution Commands & Coverage Configuration

### Running Tests in Container (Docker / Rancher):
```bash
# Run all tests with quiet output
PYTHONPATH="/repo:/repo/<job-folder>:$PYTHONPATH" python3 -m pytest /repo/<job-folder>/tests -q

# Run with line coverage report in terminal
PYTHONPATH="/repo:/repo/<job-folder>:$PYTHONPATH" python3 -m pytest --cov=/repo/<job-folder>/src --cov-report=term-missing /repo/<job-folder>/tests
```

### Coverage Configuration (`.coveragerc`):
```ini
[run]
source = src
omit =
    */tests/*
    */__init__.py
    conftest.py

[report]
fail_under = 80
show_missing = True
```

---

## 7. Testing Checklist & Rules

1. **Mirroring Structure:** Every module `src/<layer>/<module>.py` must have `tests/<layer>/test_<module>.py`.
2. **Zero External Calls:** Never attempt connection to S3, Glue API, or AWS Secrets Manager during unit tests.
3. **Assert Method Interactions:** Verify that critical methods like `upload_table`, `create_table`, `merge_data` are called with expected parameters using `.assert_called_with(...)`.
4. **Happy Path and Failure Path:** Write tests for normal executions and tests that assert exceptions (`pytest.raises(ValueError)`).
