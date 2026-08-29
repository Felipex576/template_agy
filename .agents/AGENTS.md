# Data Pipeline Architecture Template & Guide (AWS Glue & PySpark)

This document establishes the master engineering standard, architectural blueprint, coding conventions, and design guidelines for creating, refactoring, and maintaining data and analytics pipelines based on **AWS Glue + PySpark + Apache Iceberg + Serverless Framework**.

When building a new job under this standard, **80% of the infrastructure and structural scaffold is reusable boilerplate**, allowing developers to focus solely on SQL extraction and domain transformation logic.

---

## 1. Scope & Scenario Matrix

| Scenario | Directive for the Agent / Developer |
|---|---|
| **Create New Job** | Replicate the complete modular architecture. Implement only SQL extraction in `queries/` and domain rules in `transformations/`. |
| **Refactor Existing Job** | Intentional refactoring: decouple monolithic entrypoints by extracting queries, domain processors, and I/O managers. |
| **Minor Fix or Feature** | Maintain consistency with existing code. Modify only affected modules without altering the overall architecture. |

---

## 2. Mandatory Naming Conventions

| Element | Convention | Format | Example |
|---|---|---|---|
| **Python files & directories** | `snake_case` | Lowercase with underscores | `cash_control.py`, `table_builder.py` |
| **Classes** | `PascalCase` | Initial uppercase | `CashControl`, `QueryBuilder`, `ExcelManager` |
| **Methods & functions** | `snake_case` | Lowercase with underscores | `get_bank_data()`, `parse_report_date()` |
| **Constants in code** | `UPPER_SNAKE_CASE` | Uppercase with underscores | `REQUIRED_JOB_ARGS`, `PARTITION_KEYS`, `MERGE_KEYS` |
| **Enum members** | `UPPER_SNAKE` $\rightarrow$ `snake_case` | Key uppercase, value lowercase | `FECHA_CARGUE = "fecha_cargue"` |
| **Glue CLI Job Arguments** | `--UPPER_SNAKE_CASE` | Double hyphens and uppercase | `--REPORT_DATE`, `--TRUSTED_BUCKET`, `--JOB_NAME` |
| **AWS Glue Reserved Args** | `--kebab-case` | Lowercase with hyphens | `--extra-py-files`, `--datalake-formats` |
| **Variables in `.env`, `custom.yml` & CI/CD** | `camelCase` | Initial lowercase, camelCase | `projectBucket`, `glueJobVersion`, `analyticsAccountId` |
| **AWS Physical Resource Names** | `kebab-case` | Lowercase with prefixes/hyphens | `job-analytics-control-caja`, `s3-trusted-bucket` |
| **CloudFormation Logical IDs** | `PascalCase` | Initial uppercase | `TrustedJob`, `ControlCajaJobRole` |

> [!IMPORTANT]
> **Variable Matching Rule:** Variable names in `.env`, `custom.yml`, and the Azure DevOps Variable Group must match **identically** in `camelCase`.

---

## 3. Standard Project Directory Layout

```text
<project-root>/
├── .coveragerc                         # Test coverage exclusion configuration
├── .dockerignore                       # Docker container build exclusions
├── .env.example                        # Documented environment variables (camelCase)
├── Dockerfile                          # Reproducible container for automated testing
├── requirements.txt                    # Pinned Python dependencies
├── serverless-<service>.yml            # Root Serverless Framework entrypoint
├── serverless-files/                   # Modularized Infrastructure as Code
│   └── <service>/
│       ├── custom.yml                  # Variable mapping and stage resolution
│       ├── provider.yml                # AWS provider settings and global tags
│       └── resources/
│           ├── jobs.yml                # AWS::Glue::Job resource definitions
│           └── roles.yml               # Least-privilege IAM roles and policies
├── src/
│   ├── __init__.py
│   ├── config/                         # Standardized runtime initialization
│   │   ├── decorators.py               # @log_decorator and @raise_decorator
│   │   ├── logger.py                   # Centralized formatted logger
│   │   └── spark_setup.py              # initialize() -> (GlueContext, SparkSession, Job)
│   ├── jobs/                           # Pipeline entrypoints (ONLY orchestration)
│   │   └── <job_name>.py               # ETL workflow orchestrator
│   ├── queries/                        # Pure SQL extraction
│   │   └── query_builder.py            # Queries against Glue Data Catalog / Athena
│   ├── resources/                      # Storage I/O, catalog, and file managers
│   │   ├── excel_manager.py            # In-memory binary Excel report generation
│   │   ├── file_manager.py             # ZIP packaging and Amazon S3 transmission
│   │   └── table_manager.py            # Table creation, schema sync, and Iceberg merge
│   ├── transformations/                # Pure business logic and domain processors
│   │   ├── <domain>_processor.py       # Domain-specific transformation processors
│   │   ├── format_date.py              # Banking business days and holiday calculation
│   │   ├── report_builder.py           # Multi-processor pipeline consolidator
│   │   └── table_builder.py            # Schema normalization and audit metadata
│   └── utils/                          # Constants, Enums, and Data Transfer Objects
│       ├── classes.py                  # DTO Dataclasses for bundling DataFrames
│       ├── constants.py                # REQUIRED_JOB_ARGS, PARTITION_KEYS, MERGE_KEYS
│       └── enums.py                    # Enums for target catalog table column names
└── tests/                              # Unit test suite mirroring src/
    ├── conftest.py                     # Zero-JVM mocking harness for Glue, PySpark, and DataFoundation
    ├── config/
    ├── jobs/
    ├── queries/
    ├── resources/
    └── transformations/
```

---

## 4. Layer Responsibilities & Strict Prohibitions

| Layer / Directory | Primary Responsibility | Strict Prohibitions |
|---|---|---|
| **`jobs/`** | Parse arguments (`getResolvedOptions`), instantiate classes, coordinate method execution sequence, and persist. | **NO business logic:** no filters, joins, regex, or math calculations. |
| **`queries/`** | Extract datasets from Glue Catalog or S3 via Spark SQL parameterized by partition dates. | **NO complex transformations:** only project, filter by partition, and return DataFrames. |
| **`transformations/`** | Pure computation, mathematical formulas, joins, and normalizations. Pure and stateless. | **NO I/O or AWS calls:** no `boto3`, no direct S3 writes, no reading arguments. |
| **`resources/`** | Abstrac I/O: Iceberg table upserts, ZIP compression, in-memory Excel generation, and S3 uploads. | **NO business logic:** managers only persist or transmit data. |
| **`config/`** | Centralize Spark/Glue context initialization, logging, and lifecycle decorators. | **NO domain code:** no business constants or ETL logic. |
| **`utils/`** | Define static constants, Enums of column names, and container DTOs. | **NO mutable runtime state or I/O.** |

---

## 5. Multi-Environment Variable Resolution Hierarchy

Configuration values reside centrally in the **CI/CD Variable Group** and flow hierarchically:

```text
1. Azure DevOps (Variable Group)    $(projectBucket)                  [camelCase]
            │
            ▼
2. Archivo .env                     projectBucket="$(projectBucket)"   [camelCase = $(camelCase)]
            │  (useDotenv: true)
            ▼
3. serverless custom.yml            projectBucket: ${env:projectBucket}
            │
            ▼
4. serverless jobs.yml              "--PROJECT_BUCKET_NAME": "${self:custom.projectBucket}"
            │
            ▼
5. Python Glue Job                  args["PROJECT_BUCKET_NAME"]        [--UPPER_SNAKE_CASE]
```

### Serverless Configuration Guidelines:
- **Variables per environment (dev / uat / pdn):** Use stage maps in `custom.yml` (e.g. `kmsARNStage: {dev: ..., uat: ..., pdn: ...}`).
- **Cross-stack references:** Use `${cf:<stack-name>.<OutputKey>}` for shared resources (e.g. data lake bucket ARNs).
- **Optional CLI parameters in Python:** Extract with `getResolvedOptions` only when the flag is present in `sys.argv`, assigning fallback defaults via `.setdefault()`.

---

## 6. Persistence Rules: DataFoundation & Apache Iceberg

Persistence into transactional Apache Iceberg tables in the Glue Data Catalog must follow this exact 3-step sequence:

1. **`create_table`:** Creates or verifies the Iceberg table at the target S3 path with specified partition layout (`PARTITION_KEYS`).
2. **`synchronize_schema`:** Dynamically synchronizes and evolves the catalog table schema to match output DataFrame columns.
3. **`merge_data`:** Executes the transactional `MERGE INTO` (upsert) operation matching on business primary keys (`MERGE_KEYS`).

### Compatibility & Performance Directives:
- **Hyphenated database names:** Include in the job's `--conf`: `spark.sql.catalog.glue_catalog.glue.skip-name-validation=true`.
- **DataFrame Immutability:** Transformations must return new DataFrames; never mutate shared in-memory state.
- **Avoid `.collect()` / `.toPandas()` on Massive Datasets:** Process data using distributed PySpark transformations. Only convert small final summary DataFrames to Pandas/Excel in memory.

---

## 7. Packaging & Dependencies (`--extra-py-files`)

AWS Glue requires auxiliary libraries and the project's source code to be packaged as `.zip` files:

- **Composition of `--extra-py-files`:** Contains two comma-separated ZIP archives:
  1. `datafoundation.zip`: Shared corporate library hosted in the common dependencies bucket.
  2. `<job-name>-dependencies.zip`: Compressed archive of the project's own `src/` directory, built during CI/CD.
- **Static Templates & Files:** Store Excel templates or JSON schemas in `src/utils/extra_files/` and upload them to S3 during CI/CD.

---

## 8. Transversal Notifications

When a job must emit success or failure notifications:
- **Mechanism:** Invoke the central transversal Lambda function via `boto3` inside a `finally` block to guarantee execution on unhandled exceptions.
- **Payload Format:** Send a structured JSON payload with metadata (`JobStatus`, `JobName`, `Arguments`, `ErrorMessage`, `NotificationEmails`).
- **Rule:** Do NOT generate HTML inside the Glue job; the transversal Lambda handles HTML rendering and email dispatch.
- If orchestrated by **AWS Step Functions** or **Chronos**, notifications are delegated to the parent orchestrator.

---

## 9. Local Development, Execution & Testing with Docker Compose

Local development, debugging, and testing are conducted using the containerized environment in `docker-compose/`, which emulates the official **AWS Glue** runtime and integrates **Apache Iceberg**.

### 9.1. Prerequisites & Configuration
1. **Container Engine:** Have **Docker Desktop** or **Rancher Desktop** installed and running with `docker-compose`.
2. **Iceberg JAR Dependencies:** Download and locally place required JARs (`iceberg-spark-runtime-*.jar` and `iceberg-aws-bundle-*.jar`).
3. **Environment Variables (`docker-compose/.env`):**
   - Configure active AWS credentials (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`, `AWS_DEFAULT_REGION`, `AWS_REGION`).
4. **Volume Mounts (`docker-compose/docker-compose.yml`):**
   - Set host paths to map the repository to `/repo` and the JAR directory to `/home/glue_user/jars`.
5. **VS Code Debug Configuration (`.vscode/launch.json`):**
   - Configure a *Remote Attach* configuration with `debugpy` pointing to `localhost:5678`.

---

### 9.2. Command Workflow

#### 1. Start Container and Open Interactive Shell
```bash
# From the docker-compose/ directory
docker-compose up -d

# Open interactive bash shell inside container
docker exec -it glue-dev-container /bin/bash
```

#### 2. Run and Debug Job (inside container)
To run the job with the `debugpy` server waiting for a debugger client:

```bash
PYTHONPATH="/repo:/repo/<job-folder>:$PYTHONPATH" python3 -m debugpy --listen 0.0.0.0:5678 --wait-for-client /repo/<job-folder>/src/jobs/<job_entrypoint>.py --JOB_NAME <job_name> --REPORT_DATE <YYYY-MM-DD>
```

> **Parameters to customize:**
> - `<job-folder>`: Repository directory of the specific job (e.g. `control-caja`).
> - `<job_entrypoint>.py`: Main orchestrator script (e.g. `cash_control.py`).
> - `--JOB_NAME <job_name>`: Job identifier for Glue context.
> - `--REPORT_DATE <YYYY-MM-DD>`: Report cut-off date.
> - *Include all other mandatory parameters defined in `REQUIRED_JOB_ARGS`.*

**Attach Debugger in VS Code:**
- While the command is waiting (`wait-for-client`), switch to the **Run and Debug** view in VS Code (`Ctrl+Shift+D` or `F5`) and select **"Attach to Glue (debugpy)"**. The job execution will resume and pause at configured breakpoints.

#### 3. Run Unit Test Suite (inside container)
Execute unit tests directly with output printed to the terminal (no debugger needed):

```bash
PYTHONPATH="/repo:/repo/<job-folder>:$PYTHONPATH" python3 -m pytest /repo/<job-folder>/tests -q
```

> **Parameters to customize:**
> - `<job-folder>`: Directory of the project to test (e.g. `control-caja`).

#### 4. Exit and Shut Down Container
```bash
# Exit container shell
exit

# Stop services
docker-compose down
```

---

> [!NOTE]
> **Automated CI/CD Deployment Flow:**
> Deployments to AWS environments (`dev`, `uat`, `pdn`) are **not** executed via manual local Serverless commands. Infrastructure and code are deployed automatically through **Azure DevOps**:
> 1. Push code changes via `git push`.
> 2. Create and approve Pull Request (PR) to the target branch (`development` $\rightarrow$ `dev`, `release` $\rightarrow$ `uat`, `master` $\rightarrow$ `pdn`).
> 3. The `azure-pipeline.yml` pipeline executes automatically (unit test validation, SonarQube quality gate, S3 dependency upload, and Serverless deployment).

---

## 10. Testing Strategy & Zero-JVM Mocking

### Mocking Harness Architecture (`tests/conftest.py`)
- **Complete Isolation:** Prohibit any live cloud or network calls during unit tests.
- **Dynamic Mocks:** `awsglue`, `datafoundation`, and `pyspark` are intercepted via `MagicMock` and operator proxy classes (`MockColumn`, `MockFunctions`, `MockTypes`), enabling hundreds of unit tests to execute in seconds without a JVM.
- **Mandatory Coverage Threshold:** Maintain $\ge 80\%$ line coverage across `src/` enforced by `.coveragerc`.
- **Mirroring Structure:** Every module in `src/<layer>/<module>.py` must have a corresponding test in `tests/<layer>/test_<module>.py`.

---

## 11. Security & Guardrails

- **IAM Least Privilege:** Glue roles defined in `roles.yml` must restrict access strictly to project-assigned S3 prefixes, databases, and KMS keys.
- **Mandatory Encryption:** Encrypt all data in transit and at rest using the environment's KMS customer managed key (`kmsARNStage`).
- **Repository Safety:** Never commit `.env` files with active credentials; always use `.env.example`.

---

## 12. New Job Creation Checklist

When building a new ETL pipeline, follow this sequential 14-step checklist:

- [ ] **Step 1:** Create project folder in `snake_case`.
- [ ] **Step 2:** Replicate standard `src/config/` modules (`logger.py`, `decorators.py`, `spark_setup.py`).
- [ ] **Step 3:** Define required parameters (`REQUIRED_JOB_ARGS`), partition keys (`PARTITION_KEYS`), and merge keys (`MERGE_KEYS`) in `src/utils/constants.py`.
- [ ] **Step 4:** Define target catalog table column names in `src/utils/enums.py`.
- [ ] **Step 5 (Custom Logic):** Implement Spark SQL extraction in `src/queries/query_builder.py`.
- [ ] **Step 6 (Custom Logic):** Implement domain transformation rules in `src/transformations/*_processor.py`.
- [ ] **Step 7 (Custom Logic):** If applicable, implement file/report managers in `src/resources/`.
- [ ] **Step 8:** Assemble main orchestrator in `src/jobs/<job_name>.py` (strictly sequential coordination).
- [ ] **Step 9:** Configure `tests/conftest.py`, `.coveragerc`, and write unit tests mirroring `src/`.
- [ ] **Step 10:** Configure `Dockerfile`, `requirements.txt`, and `.dockerignore`.
- [ ] **Step 11:** Define IaC in `serverless-<service>.yml`, `provider.yml`, `custom.yml`, `jobs.yml`, and `roles.yml`.
- [ ] **Step 12:** Create `.env.example` and local `.env` with `camelCase` variables.
- [ ] **Step 13:** Register new variables in the Azure DevOps Variable Group.
- [ ] **Step 14:** Configure `azure-pipeline.yml` for automated testing, SonarQube gates, and deployment.
