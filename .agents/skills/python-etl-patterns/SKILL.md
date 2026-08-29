---
name: python-etl-patterns
description: Universal Python design patterns, layered architecture standards, decorator implementations (@log_decorator, @raise_decorator), DTO modeling, type hinting, and naming conventions for enterprise ETL applications on AWS Glue. Use when designing, structuring, or reviewing Python modules in data pipelines.
---

# Universal Python Design Patterns for AWS Glue ETL Pipelines

Architectural standards, design patterns, and code conventions for creating maintainable, decoupled, and testable Python ETL applications on **AWS Glue**.

---

## 1. When to Activate This Skill

- Structuring modules, packages, and classes for an ETL/ELT pipeline.
- Implementing logging and error-handling decorators.
- Designing Data Transfer Objects (DTOs) to pass multiple DataFrames between stages.
- Defining Enums for database schemas and column names.
- Managing job parameters and environment variable resolution.
- Enforcing PEP 8 and Pythonic typing across data engineering modules.

---

## 2. Layered Architecture & Directory Contracts

Every Python ETL project strictly organizes modules into six functional layers:

```text
src/
├── config/             # Spark setup, logger, and lifecycle decorators (NO business logic)
├── jobs/               # Entrypoints and pipeline orchestration (NO calculations/filters)
├── queries/            # Data extraction and Spark SQL catalog queries (NO transformations)
├── transformations/    # Pure business rules, math, and joins (NO I/O or AWS calls)
├── resources/          # Storage, S3 uploads, Iceberg upserts, file generation
└── utils/              # Constants, Enums, and Dataclasses / DTOs
```

### Layer Responsibilities & Strict Prohibitions:

| Layer / Folder | Primary Responsibility | Strict Prohibitions |
|---|---|---|
| **`jobs/`** | Parse arguments (`getResolvedOptions`), instantiate classes, coordinate pipeline execution. | **NO business logic:** no filters, math, joins, or aggregations. |
| **`queries/`** | Extract datasets from Glue Data Catalog or S3 via Spark SQL. | **NO business rules:** only extract, project, and filter by partition. |
| **`transformations/`** | Pure computation, mathematical formulas, joins, and normalizations. | **NO I/O or AWS calls:** no `boto3`, no direct S3 writes, no reading args. |
| **`resources/`** | Handle I/O: Iceberg table upserts, file compression, S3 transmissions. | **NO business calculations:** managers only persist or transmit data. |
| **`config/`** | Centralize Spark/Glue context initialization, logging, and decorators. | **NO domain code:** no business constants or ETL logic. |
| **`utils/`** | Define static constants, Enums, and container DTOs. | **NO mutable runtime state or I/O.** |

---

## 3. Observability & Error Decorators Pattern

Standardize logging and exception handling using `@log_decorator` and `@raise_decorator` in `src/config/decorators.py`:

```python
"""Decorators used across all pipeline modules."""
import functools
from src.config.logger import logger


def log_decorator(func):
    """Logs the entry point of function execution."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger.info(f"# [INFO]: Start {func.__name__}")
        return func(*args, **kwargs)
    return wrapper


def raise_decorator(func):
    """
    Catches exceptions, logs structured error context, and re-raises
    to preserve traceback and guarantee failure propagation to the orchestrator.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as err:
            logger.error(f"# [ERROR]: In function {func.__name__}: {str(err)}")
            raise err
    return wrapper
```

### Usage Convention:
Apply `@log_decorator` and `@raise_decorator` to all public methods across `jobs/`, `queries/`, `transformations/`, and `resources/`.

---

## 4. DTO Pattern for Multi-DataFrame Pipelines

When an ETL job processes multiple DataFrames across different sources, avoid passing loose tuples or large positional argument lists. Use a structured Dataclass DTO in `src/utils/classes.py`:

```python
"""Data transfer objects for pipeline processing."""
from dataclasses import dataclass
from typing import Optional
from pyspark.sql import DataFrame


@dataclass
class ProcessingDataFrames:
    """Encapsulates all intermediary DataFrames used during pipeline execution."""
    source_primary_df: DataFrame
    source_secondary_df: DataFrame
    dim_lookup_df: DataFrame
    # Target / Result DataFrames initialized as Optional
    final_output_df: Optional[DataFrame] = None
    final_summary_df: Optional[DataFrame] = None
```

### Benefits:
- Explicit, typed attributes accessible via `dfs.source_primary_df`.
- Clean method signatures: `report_builder.create_report(date_list, dfs)`.
- Prevents positional argument bugs when new datasets are introduced.

---

## 5. Schema Type-Safety: The Enums Pattern

Never use raw string literals for column names inside transformations or queries. Define all target table columns in `src/utils/enums.py`:

```python
"""Enumerations for database column names and categorization."""
from enum import Enum


class TargetColumns(str, Enum):
    """Standard column names for the target catalog table."""
    RECORD_ID = "record_id"
    ENTITY_CODE = "entity_code"
    ACCOUNT_ID = "account_id"
    TRANSACTION_DATE = "transaction_date"
    AMOUNT = "amount"
    FEE = "fee"
    FECHA_CARGUE = "fecha_cargue"
```

### Usage in PySpark Code:
```python
from pyspark.sql import functions as F
from src.utils.enums import TargetColumns

df = base_df.withColumn(
    TargetColumns.AMOUNT.value,
    F.col("initial_balance") + F.col("movement_value")
)
```

---

## 6. Job Arguments & Parameter Resolution

Parse arguments in the `main()` entrypoint using `awsglue.utils.getResolvedOptions`:

```python
import sys
from awsglue.utils import getResolvedOptions
from src.config.logger import logger
from src.utils.constants import REQUIRED_JOB_ARGS


def main():
    try:
        # 1. Parse mandatory arguments defined in REQUIRED_JOB_ARGS
        args = getResolvedOptions(sys.argv, REQUIRED_JOB_ARGS)
    except Exception as e:
        logger.error(f"# [ERROR]: Missing required job arguments: {e}")
        raise ValueError(f"Missing required job arguments: {e}")

    # 2. Parse optional arguments gracefully
    optional_keys = ["CUSTOM_START_DATE", "EXECUTION_MODE"]
    present_optionals = [key for key in optional_keys if f"--{key}" in sys.argv]
    if present_optionals:
        opt_args = getResolvedOptions(sys.argv, present_optionals)
        args.update(opt_args)

    # 3. Instantiate and run orchestrator
    orchestrator = PipelineOrchestrator(args)
    orchestrator.run()
    logger.info("# [INFO]: Pipeline completed successfully.")
```

---

## 7. Centralized Constants (`src/utils/constants.py`)

Centralize all configuration keys and table metadata:

```python
"""Constants and metadata definitions for the pipeline."""

REQUIRED_JOB_ARGS = [
    "JOB_NAME",
    "REPORT_DATE",
    "CATALOG_DATABASE",
    "TARGET_TABLE",
    "TRUSTED_BUCKET",
    "PREFIX_DATA",
]

PARTITION_KEYS = ["fecha_cargue"]
MERGE_KEYS = ["entity_code", "account_id", "transaction_date"]

# Fixed business rules (non-configurable per environment)
DEFAULT_STATUS = "ACTIVE"
CURRENCY_CODE = "COP"
```

---

## 8. Clean Code & Type-Hinting Conventions

1. **Explicit Return Types:** Annotate all functions: `def get_data(...) -> Tuple[DataFrame, list[str]]:`.
2. **Inmutability in Processors:** Do not mutate input arguments. Return fresh DataFrames or new collections.
3. **No Catch-All Bare Excepts:** Always catch specific exceptions or use `@raise_decorator` to preserve stack traces.
