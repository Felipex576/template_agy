---
name: athena-trino-sql
description: Universal Presto and Trino SQL reference for Amazon Athena queries against Glue Data Catalog, Parquet, and Apache Iceberg tables. Activate when writing, optimizing, or debugging Athena queries, data validation scripts, reconciliation logic, and complex analytical SQL.
---

# Universal Athena (Presto / Trino) SQL Engineering Patterns

Production-grade SQL guide, engine function equivalences, and query optimization reference for **Amazon Athena** (Athena Engine v3 powered by **Trino / Presto**) querying Data Lakes on **AWS Glue Data Catalog** and **Apache Iceberg** tables.

---

## 1. When to Activate This Skill

- Writing or optimizing SQL queries executed in Amazon Athena or through PySpark `spark.sql()`.
- Migrating SQL queries from MySQL, PostgreSQL, or Oracle to Presto/Trino SQL.
- Injecting constants, business parameters, and multi-stage CTEs into queries.
- Querying, optimizing, and maintaining Apache Iceberg tables (Time-Travel, metadata inspection, compaction).
- Performing data reconciliation, financial audits, duplicate checks, and partition pruning.
- Diagnosing slow queries, timeout errors, or unexpected Athena scan costs.

---

## 2. SQL Engine Equivalences Matrix (MySQL / Oracle $\rightarrow$ Trino / Presto)

Athena runs on the **Trino (formerly PrestoSQL)** distributed engine. Standard RDBMS functions often have different names, arguments, or behaviors:

| Task / Concept | MySQL / Oracle | Trino / Presto (Athena) | Notes & Differences |
|---|---|---|---|
| **Null Replacement** | `IFNULL(a, b)` / `NVL(a, b)` | `COALESCE(a, b)` | `COALESCE` supports $N$ arguments. |
| **Safe Type Casting** | `CAST(a AS SIGNED)` | `TRY_CAST(a AS BIGINT)` | `TRY_CAST` returns `NULL` on error instead of failing the query. |
| **Division by Zero** | `a / b` (returns `NULL` in MySQL) | `TRY(a / b)` or `a / NULLIF(b, 0)` | Trino throws `Division by zero` error unless wrapped in `TRY` or `NULLIF`. |
| **String to Date** | `STR_TO_DATE('2026-08-28', '%Y-%m-%d')` | `date_parse('2026-08-28', '%Y-%m-%d')` | Returns `TIMESTAMP`. Wrap in `CAST(... AS DATE)` if date only. |
| **Date to String** | `DATE_FORMAT(d, '%Y-%m-%d')` | `format_datetime(d, 'yyyy-MM-dd')` | Uses **Joda-Time** format strings (`yyyy-MM-dd HH:mm:ss`), NOT `%Y-%m-%d`. |
| **Date Literal** | `'2026-08-28'` | `DATE '2026-08-28'` | Explicit typed literal. |
| **Date Arithmetic** | `DATE_ADD(d, INTERVAL 1 DAY)` | `date_add('day', 1, d)` or `d + INTERVAL '1' DAY` | Unit is the first string argument in `date_add`. |
| **Date Difference** | `DATEDIFF(end, start)` | `date_diff('day', start, end)` | Trino requires 3 arguments: `unit`, `start_date`, `end_date`. |
| **Current Timestamp** | `NOW()` / `SYSDATE()` | `CURRENT_TIMESTAMP` / `now()` | Returns `TIMESTAMP WITH TIME ZONE`. |
| **String Concatenation** | `CONCAT(a, b)` or `a \|\| b` | `CONCAT(a, b)` or `a \|\| b` | Identical syntax; `CONCAT(a, b, c)` supported. |
| **Group Aggregation** | `GROUP_CONCAT(col SEPARATOR ',')` | `array_join(array_agg(col), ', ')` | Aggregates into an array first, then joins. |
| **String Split Extraction**| `SUBSTRING_INDEX(str, ',', 1)` | `split(str, ',')[1]` | Trino arrays are **1-indexed** (`[1]` is the first element). |
| **Regular Expressions** | `REGEXP_LIKE(s, p)` | `regexp_like(s, p)` | Uses Java regular expression syntax. |
| **Pagination / Offset** | `LIMIT 10, 20` | `OFFSET 10 LIMIT 20` | Standard ANSI SQL pagination. |

---

## 3. Using Constants & Parameters in Queries

To avoid repeating hardcoded literals across complex queries, define a `constants` Common Table Expression (CTE) or inject parameters cleanly:

### Pattern A: CTE-Based Query Constants (Pure SQL)
```sql
WITH constants AS (
    SELECT 
        DATE '2026-08-28' AS target_date,
        'ACTIVE'          AS required_status,
        1000000.0         AS high_value_threshold,
        ARRAY['COP', 'USD'] AS supported_currencies
),
filtered_transactions AS (
    SELECT 
        t.transaction_id,
        t.account_id,
        t.amount,
        t.currency,
        t.status,
        t.fecha_cargue
    FROM glue_catalog.finance_db.fact_transactions t
    CROSS JOIN constants c
    WHERE t.fecha_cargue = format_datetime(c.target_date, 'yyyy-MM-dd')
      AND t.status = c.required_status
      AND contains(c.supported_currencies, t.currency)
)
SELECT 
    f.account_id,
    f.currency,
    SUM(f.amount) AS total_amount,
    CASE 
        WHEN SUM(f.amount) >= c.high_value_threshold THEN 'HIGH_TIER'
        ELSE 'STANDARD_TIER'
    END AS tier_classification
FROM filtered_transactions f
CROSS JOIN constants c
GROUP BY f.account_id, f.currency, c.high_value_threshold;
```

### Pattern B: Parameterized Interpolation in Python / PySpark (`QueryBuilder`)
```python
class QueryBuilder:
    def __init__(self, spark, database_name: str):
        self.spark = spark
        self.database = database_name

    def get_reconciliation_query(self, report_date: str, entity_code: str) -> str:
        """Builds parameterized SQL with escaped constants."""
        return f"""
            WITH params AS (
                SELECT 
                    DATE '{report_date}' AS ref_date,
                    '{entity_code}'       AS ref_entity
            )
            SELECT 
                b.account_id,
                b.final_balance,
                b.fecha_cargue
            FROM {self.database}.tbl_balances b
            INNER JOIN params p 
                ON b.fecha_cargue = format_datetime(p.ref_date, 'yyyy-MM-dd')
               AND b.entity_code = p.ref_entity
        """
```

---

## 4. Apache Iceberg Tables in Amazon Athena

Amazon Athena (Engine v3) natively supports Apache Iceberg ACID tables, hidden partitioning, schema evolution, and time travel.

### 4.1. Time-Travel Queries
Query the exact state of an Iceberg table as it existed historically:

```sql
-- 1. Query by historical timestamp
SELECT * 
FROM glue_catalog.market_db.tbl_positions 
FOR TIMESTAMP AS OF (current_timestamp - INTERVAL '7' DAY)
WHERE fecha_cargue = '2026-08-21';

-- 2. Query by specific snapshot ID
SELECT * 
FROM glue_catalog.market_db.tbl_positions 
FOR VERSION AS OF 4829104928104928104;
```

### 4.2. Inspecting Iceberg Metadata Tables
Append `$table_suffix` to inspect internal snapshots, data files, and manifests:

```sql
-- List all committed snapshots and commit operations
SELECT 
    snapshot_id, 
    committed_at, 
    operation, 
    summary['total-records'] AS total_records,
    summary['added-data-files'] AS added_files
FROM glue_catalog.market_db."tbl_positions$snapshots"
ORDER BY committed_at DESC;

-- Inspect physical S3 Parquet files, row counts, and partition sizes
SELECT 
    file_path, 
    file_format, 
    record_count, 
    file_size_in_bytes,
    partition
FROM glue_catalog.market_db."tbl_positions$files"
LIMIT 50;

-- Inspect active partitions and summary stats
SELECT * 
FROM glue_catalog.market_db."tbl_positions$partitions";
```

### 4.3. Iceberg Table Optimization & Maintenance

#### 1. Compaction (Fixing Small Files):
Use `OPTIMIZE` to rewrite and merge thousands of small Parquet files into optimal ~128MB–512MB files:
```sql
-- Compact specific partition
OPTIMIZE glue_catalog.market_db.tbl_positions 
REWRITE DATA USING BIN_PACK 
WHERE fecha_cargue = '2026-08-28';
```

#### 2. Vacuum (Purging Expired Snapshots & Orphan Files):
```sql
-- 1. Configure retention threshold in table properties (e.g. 7 days = 604800 seconds)
ALTER TABLE glue_catalog.market_db.tbl_positions 
SET TBLPROPERTIES ('vacuum_max_snapshot_age_seconds' = '604800');

-- 2. Physically remove expired snapshots and orphan S3 objects
VACUUM glue_catalog.market_db.tbl_positions;
```

---

## 5. High-Performance SQL Patterns

### 5.1. Window Functions for Deduplication & Running Balances
```sql
WITH ranked_records AS (
    SELECT 
        account_id,
        transaction_id,
        transaction_date,
        amount,
        -- Running balance
        SUM(amount) OVER (
            PARTITION BY account_id 
            ORDER BY transaction_date, transaction_id
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS running_balance,
        -- Deduplication rank (keep latest ingestion)
        ROW_NUMBER() OVER (
            PARTITION BY account_id, transaction_id 
            ORDER BY load_timestamp DESC
        ) AS dedup_rank
    FROM glue_catalog.finance_db.fact_movements
    WHERE fecha_cargue = '2026-08-28'
)
SELECT 
    account_id,
    transaction_id,
    transaction_date,
    amount,
    running_balance
FROM ranked_records
WHERE dedup_rank = 1;
```

### 5.2. Working with JSON, Arrays & Complex Types
```sql
SELECT 
    event_id,
    -- Extract scalar JSON attributes
    json_extract_scalar(raw_payload, '$.customer.id') AS customer_id,
    TRY_CAST(json_extract_scalar(raw_payload, '$.financial.amount') AS DOUBLE) AS amount,
    
    -- Filter array items using lambda expressions
    filter(tags_array, x -> length(x) > 3) AS filtered_tags,
    
    -- Transform array elements using lambda expressions
    transform(currency_rates, x -> x * 1.19) AS rates_with_tax
FROM glue_catalog.events_db.tbl_raw_events
WHERE fecha_cargue = '2026-08-28';
```

---

## 6. End-to-End Reconciliation Template (T-0 vs T-1)

```sql
WITH params AS (
    SELECT 
        DATE '2026-08-27' AS date_t0,
        DATE '2026-08-28' AS date_t1
),
t0_data AS (
    SELECT 
        entity_code,
        SUM(final_balance) AS total_balance_t0
    FROM glue_catalog.finance_db.daily_balances
    WHERE fecha_cargue = format_datetime((SELECT date_t0 FROM params), 'yyyy-MM-dd')
    GROUP BY entity_code
),
t1_data AS (
    SELECT 
        entity_code,
        SUM(final_balance) AS total_balance_t1
    FROM glue_catalog.finance_db.daily_balances
    WHERE fecha_cargue = format_datetime((SELECT date_t1 FROM params), 'yyyy-MM-dd')
    GROUP BY entity_code
),
movements AS (
    SELECT 
        entity_code,
        SUM(CASE WHEN movement_type = 'INCOME' THEN amount ELSE -amount END) AS net_cashflow
    FROM glue_catalog.finance_db.cashflow_movements
    WHERE fecha_cargue = format_datetime((SELECT date_t1 FROM params), 'yyyy-MM-dd')
    GROUP BY entity_code
)
SELECT 
    COALESCE(t0.entity_code, t1.entity_code, m.entity_code) AS entity_code,
    COALESCE(t0.total_balance_t0, 0.0) AS balance_t0,
    COALESCE(t1.total_balance_t1, 0.0) AS balance_t1,
    COALESCE(m.net_cashflow, 0.0) AS net_movements,
    (COALESCE(t1.total_balance_t1, 0.0) - COALESCE(t0.total_balance_t0, 0.0)) AS actual_delta,
    ((COALESCE(t1.total_balance_t1, 0.0) - COALESCE(t0.total_balance_t0, 0.0)) - COALESCE(m.net_cashflow, 0.0)) AS variance
FROM t0_data t0
FULL OUTER JOIN t1_data t1 ON t0.entity_code = t1.entity_code
FULL OUTER JOIN movements m ON COALESCE(t0.entity_code, t1.entity_code) = m.entity_code;
```

---

## 7. Guardrails & Cost Optimization Checklist

| Rule | Severity | Rationale |
|---|---|---|
| **Filter by Partition Key (`WHERE fecha_cargue = ...`)** | **CRITICAL** | Reduces Athena S3 scan costs by up to 99% and avoids full table scans. |
| **Explicit Column Selection (No `SELECT *`)** | **CRITICAL** | Parquet/ORC columnar engines only read data stripes of requested columns. |
| **Use `TRY_CAST` instead of `CAST`** | **HIGH** | Prevents whole queries from failing when single bad records occur. |
| **Use `approx_distinct(col)` for massive counts** | **MEDIUM** | Computes distinct counts with ~2% error rate, using a fraction of memory. |
| **Compact Iceberg tables with `OPTIMIZE`** | **MEDIUM** | Eliminates small file overhead and improves Athena query speed significantly. |
| **Avoid Unbounded Cartesian Joins (`CROSS JOIN`)** | **FORBIDDEN** | Generates explosive $O(N \times M)$ memory footprints that crash query workers. |
