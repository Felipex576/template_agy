<#
.SYNOPSIS
    Interactive Installer for Data Pipeline Architecture, Synapse Protocol, and Agent Skills/Subagents.
.DESCRIPTION
    Scaffolds new enterprise AWS Glue/PySpark data pipelines or injects the Synapse persistent memory & 
    agent intelligence layer (.agents/, .synapse/) into existing projects.
#>

param(
    [string]$TargetDir = (Get-Location).Path,
    [string]$TemplateSourceDir = $PSScriptRoot,
    [Nullable[bool]]$IsNew = $null,
    [string]$ProjectName = "",
    [Nullable[bool]]$InstallAgents = $null,
    [string]$Branch = "feature/template_v1"
)

$ErrorActionPreference = "Stop"

function Print-Header {
    Write-Host "=================================================================" -ForegroundColor Cyan
    Write-Host "    Synapse Protocol & Data Pipeline Architecture Installer     " -ForegroundColor Yellow
    Write-Host "=================================================================" -ForegroundColor Cyan
}

function Copy-Agent-Layer {
    param([string]$Destination)

    Write-Host "`n[*] Installing AI Agent Layer (.agents, .synapse, adapters)..." -ForegroundColor Cyan
    
    $hasLocalSource = $false
    if (-not [string]::IsNullOrWhiteSpace($TemplateSourceDir)) {
        if (Test-Path (Join-Path $TemplateSourceDir ".agents")) {
            $hasLocalSource = $true
            $sourceAgents = Join-Path $TemplateSourceDir ".agents"
            $sourceSynapse = Join-Path $TemplateSourceDir ".synapse"
            $sourceGemini = Join-Path $TemplateSourceDir ".gemini"
        }
    }

    # If local source does not exist (remote one-liner execution via iex), download from GitHub
    if (-not $hasLocalSource) {
        Write-Host "  [*] Remote execution detected. Downloading template archive from GitHub ($Branch)..." -ForegroundColor Cyan
        
        $zipUrl = "https://github.com/Felipex576/template_agy/archive/refs/heads/$Branch.zip"
        $tempZip = Join-Path $env:TEMP "template_agy_main.zip"
        $tempExtract = Join-Path $env:TEMP "template_agy_extracted"

        if (Test-Path $tempExtract) { Remove-Item -Path $tempExtract -Recurse -Force }
        
        try {
            Invoke-WebRequest -Uri $zipUrl -OutFile $tempZip -UseBasicParsing
        } catch {
            # Fallback to main branch
            $zipUrl = "https://github.com/Felipex576/template_agy/archive/refs/heads/main.zip"
            Invoke-WebRequest -Uri $zipUrl -OutFile $tempZip -UseBasicParsing
        }
        
        Expand-Archive -Path $tempZip -DestinationPath $tempExtract -Force
        
        # Dynamically locate the extracted repo root directory
        $extractedDir = Get-ChildItem -Path $tempExtract -Directory | Select-Object -First 1
        $repoRoot = $extractedDir.FullName
        $sourceAgents = Join-Path $repoRoot ".agents"
        $sourceSynapse = Join-Path $repoRoot ".synapse"
        $sourceGemini = Join-Path $repoRoot ".gemini"
    }

    # Destination folders
    $targetAgents = Join-Path $Destination ".agents"
    $targetSynapse = Join-Path $Destination ".synapse"
    $targetGemini = Join-Path $Destination ".gemini"

    # Copy agent components
    if (Test-Path $sourceAgents) {
        if (-not (Test-Path $targetAgents)) {
            New-Item -ItemType Directory -Path $targetAgents -Force | Out-Null
        }
        Copy-Item -Path "$sourceAgents\*" -Destination $targetAgents -Recurse -Force
        
        # Mirror subagents to .claude/agents for native Claude Code discovery
        $subagentsSrc = Join-Path $sourceAgents "subagents"
        if (Test-Path $subagentsSrc) {
            $claudeAgents = Join-Path $Destination ".claude\agents"
            if (-not (Test-Path $claudeAgents)) { New-Item -ItemType Directory -Path $claudeAgents -Force | Out-Null }
            Copy-Item -Path "$subagentsSrc\*" -Destination $claudeAgents -Recurse -Force
        }
        
        Write-Host "  [+] Copied .agents/ (Skills, Subagents, AGENTS.md)" -ForegroundColor Green
    }

    if (Test-Path $sourceSynapse) {
        if (-not (Test-Path $targetSynapse)) {
            New-Item -ItemType Directory -Path $targetSynapse -Force | Out-Null
        }
        Copy-Item -Path "$sourceSynapse\*" -Destination $targetSynapse -Recurse -Force
        Write-Host "  [+] Copied .synapse/ (Persistent Memory, SDD Protocol)" -ForegroundColor Green
    }

    if (Test-Path $sourceGemini) {
        if (-not (Test-Path $targetGemini)) {
            New-Item -ItemType Directory -Path $targetGemini -Force | Out-Null
        }
        Copy-Item -Path "$sourceGemini\*" -Destination $targetGemini -Recurse -Force
        Write-Host "  [+] Copied .gemini/ (GEMINI.md)" -ForegroundColor Green
    }

    # Generate CLAUDE.md adapter
    $claudePath = Join-Path $Destination "CLAUDE.md"
    $claudeContent = @"
# Master Data Pipeline Architecture & Guidelines
Please strictly follow the master engineering guidelines in `.agents/AGENTS.md` and the memory/SDD lifecycle in `.synapse/PROTOCOL.md`.
"@
    Set-Content -Path $claudePath -Value $claudeContent -Force -Encoding UTF8
    Write-Host "  [+] Generated CLAUDE.md adapter" -ForegroundColor Green

    # Cleanup temp files if any
    if ($tempZip -and (Test-Path $tempZip)) { Remove-Item -Path $tempZip -Force -ErrorAction SilentlyContinue }
    if ($tempExtract -and (Test-Path $tempExtract)) { Remove-Item -Path $tempExtract -Recurse -Force -ErrorAction SilentlyContinue }
}

function Scaffold-New-Project {
    param(
        [string]$Destination,
        [string]$ProjectName
    )

    $kebabProject = $ProjectName.Replace("_", "-")
    Write-Host "`n[*] Scaffolding full 6-layer architecture for project '$ProjectName'..." -ForegroundColor Cyan

    # 1. Create standard directory structure
    $directories = @(
        "src/config", "src/jobs", "src/queries", "src/resources", "src/transformations", "src/utils/extra_files",
        "tests/config", "tests/jobs", "tests/queries", "tests/resources", "tests/transformations",
        "serverless-files/analytics/resources"
    )

    foreach ($dir in $directories) {
        $path = Join-Path $Destination $dir
        New-Item -ItemType Directory -Path $path -Force | Out-Null
    }
    Write-Host "  [+] Created standard folder hierarchy (src, tests, serverless-files)" -ForegroundColor Green

    # 2. Scaffolding standard config/
    $loggerContent = @"
import logging

def get_logger(name: str = "glue_job") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
"@
    Set-Content -Path (Join-Path $Destination "src/config/logger.py") -Value $loggerContent -Force -Encoding UTF8

    $decoratorsContent = @"
import functools
import time
from src.config.logger import get_logger

logger = get_logger("decorators")

def log_decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger.info(f"Executing: {func.__qualname__}")
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        logger.info(f"Completed: {func.__qualname__} in {elapsed:.2f}s")
        return result
    return wrapper

def raise_decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__qualname__}: {str(e)}", exc_info=True)
            raise
    return wrapper
"@
    Set-Content -Path (Join-Path $Destination "src/config/decorators.py") -Value $decoratorsContent -Force -Encoding UTF8

    $sparkSetupContent = @"
import sys
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.context import SparkContext
from pyspark.sql import SparkSession

def initialize(job_name: str):
    spark_context = SparkContext.getOrCreate()
    glue_context = GlueContext(spark_context)
    spark = glue_context.spark_session
    job = Job(glue_context)
    job.init(job_name, {})
    return glue_context, spark, job
"@
    Set-Content -Path (Join-Path $Destination "src/config/spark_setup.py") -Value $sparkSetupContent -Force -Encoding UTF8

    # 3. Scaffolding utils/
    $constantsContent = @"
REQUIRED_JOB_ARGS = [
    "JOB_NAME",
    "REPORT_DATE",
    "CATALOG_DATABASE",
    "TRUSTED_BUCKET",
    "PROJECT_BUCKET_NAME"
]

PARTITION_KEYS = ["fecha_cargue"]
MERGE_KEYS = ["id_registro"]
"@
    Set-Content -Path (Join-Path $Destination "src/utils/constants.py") -Value $constantsContent -Force -Encoding UTF8

    $enumsContent = @"
from enum import Enum

class TargetColumns(Enum):
    ID_REGISTRO = "id_registro"
    FECHA_CARGUE = "fecha_cargue"
    VALOR_TOTAL = "valor_total"
    ESTADO = "estado"
    FECHA_PROCESO = "fecha_proceso"
"@
    Set-Content -Path (Join-Path $Destination "src/utils/enums.py") -Value $enumsContent -Force -Encoding UTF8

    $classesContent = @"
from dataclasses import dataclass
from pyspark.sql import DataFrame

@dataclass(frozen=True)
class ProcessingDataFrames:
    raw_data: DataFrame
    processed_data: DataFrame = None
    final_summary: DataFrame = None
"@
    Set-Content -Path (Join-Path $Destination "src/utils/classes.py") -Value $classesContent -Force -Encoding UTF8

    # 4. Scaffolding jobs/ entrypoint
    $jobContent = @"
import sys
from awsglue.utils import getResolvedOptions
from src.config.spark_setup import initialize
from src.config.logger import get_logger
from src.utils.constants import REQUIRED_JOB_ARGS

logger = get_logger("$ProjectName")

def main():
    args = getResolvedOptions(sys.argv, REQUIRED_JOB_ARGS)
    glue_context, spark, job = initialize(args["JOB_NAME"])
    logger.info(f"Starting pipeline {args['JOB_NAME']} for cut-off date: {args['REPORT_DATE']}")
    
    # 1. Extraction (queries/)
    # 2. Transformations (transformations/)
    # 3. Persistence (resources/)
    
    job.commit()
    logger.info(f"Pipeline {args['JOB_NAME']} successfully completed.")

if __name__ == "__main__":
    main()
"@
    Set-Content -Path (Join-Path $Destination "src/jobs/$ProjectName.py") -Value $jobContent -Force -Encoding UTF8

    # 5. Scaffolding tests/conftest.py (Zero-JVM harness)
    $conftestContent = @"
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
"@
    Set-Content -Path (Join-Path $Destination "tests/conftest.py") -Value $conftestContent -Force -Encoding UTF8

    # 6. Scaffolding IaC & CI/CD
    $serverlessRoot = @"
service: `$`{self:custom.project}-$kebabProject
frameworkVersion: "3"
useDotenv: true

provider: `$`{file(./serverless-files/analytics/provider.yml)}
custom: `$`{file(./serverless-files/analytics/custom.yml)}

package:
  individually: true
  exclude:
    - ./**

plugins:
  - serverless-python-requirements
  - serverless-plugin-common-excludes

resources:
  - `$`{file(./serverless-files/analytics/resources/roles.yml)}
  - `$`{file(./serverless-files/analytics/resources/jobs.yml)}
"@
    Set-Content -Path (Join-Path $Destination "serverless-$kebabProject.yml") -Value $serverlessRoot -Force -Encoding UTF8

    $providerYaml = @"
name: aws
stage: `$`{self:custom.stage}
runtime: python3.11
lambdaHashingVersion: 20201221
deploymentBucket:
  name: `$`{self:custom.deploymentBucketName}
  maxPreviousDeploymentArtifacts: 10
stackTags:
  Ambiente: `$`{self:custom.stage}
  Aplicativo: `$`{self:custom.tagAplicativo}
  Area: `$`{self:custom.tagArea}
  Celula: `$`{self:custom.tagCelula}
  Compania: `$`{self:custom.tagCompania}
  Despliegue: ServerlessFramework
  Disponibilidad: `$`{self:custom.tagDisponibilidad}
  Producto: `$`{self:custom.tagProducto}
  Proyecto: `$`{self:custom.tagProyecto}
"@
    Set-Content -Path (Join-Path $Destination "serverless-files/analytics/provider.yml") -Value $providerYaml -Force -Encoding UTF8

    $customYaml = @"
stage: `$`{opt:stage, 'dev'}
project: `$`{env:project}

analyticsAccountIdStage:
  dev: `$`{env:analyticsAccountIdDEV}
  uat: `$`{env:analyticsAccountIdUAT}
  pdn: `$`{env:analyticsAccountIdPDN}
analyticsAccountId: `$`{self:custom.analyticsAccountIdStage.`$`{self:custom.stage}}

kmsARNStage:
  dev: `$`{env:arnKmsDEV}
  uat: `$`{env:arnKmsUAT}
  pdn: `$`{env:arnKmsPDN}
kmsARN: `$`{self:custom.kmsARNStage.`$`{self:custom.stage}}

jobNumberOfWorkersStage:
  dev: `$`{env:jobNumberOfWorkersDEV, 2}
  uat: `$`{env:jobNumberOfWorkersUAT, 4}
  pdn: `$`{env:jobNumberOfWorkersPDN, 10}
jobNumberOfWorkers: `$`{self:custom.jobNumberOfWorkersStage.`$`{self:custom.stage}}

glueJobVersion: "4.0"
dataLakeNameTrusted: s3-`$`{self:custom.analyticsAccountId}-datalake-`$`{self:custom.stage}-trusted
dataLakeNameStaging: s3-`$`{self:custom.analyticsAccountId}-datalake-`$`{self:custom.stage}-staging
"@
    Set-Content -Path (Join-Path $Destination "serverless-files/analytics/custom.yml") -Value $customYaml -Force -Encoding UTF8

    # 7. Environment & Config files
    Set-Content -Path (Join-Path $Destination ".coveragerc") -Value "[run]`nomit =`n    src/jobs/*`n    tests/*`n    src/config/*" -Force -Encoding UTF8
    Set-Content -Path (Join-Path $Destination "requirements.txt") -Value "pytest==7.4.4`npytest-cov==4.1.0`nopenpyxl==3.1.5`nholidays-co==1.1.3" -Force -Encoding UTF8
    Set-Content -Path (Join-Path $Destination ".env.example") -Value "project=$kebabProject`nstage=dev`nprojectBucket=s3-bucket-example" -Force -Encoding UTF8
    Set-Content -Path (Join-Path $Destination ".dockerignore") -Value ".git`n.synapse`n*.pyc`n__pycache__" -Force -Encoding UTF8

    Write-Host "  [+] Generated boilerplate files (config, utils, jobs, tests, serverless, docker)" -ForegroundColor Green
}

# ==============================================================================
# MAIN ENTRYPOINT
# ==============================================================================
Print-Header

# Determine IsNew
if ($null -eq $IsNew) {
    $rawInput = Read-Host "`n¿Es este un proyecto nuevo? (s/n)"
    $isNewBool = ($rawInput -match "^[sSyY]")
} else {
    $isNewBool = $IsNew
}

if ($isNewBool) {
    if ([string]::IsNullOrWhiteSpace($ProjectName)) {
        $ProjectName = Read-Host "`nIngresa el nombre del proyecto/job en snake_case (ej: control_caja)"
    }
    if ([string]::IsNullOrWhiteSpace($ProjectName)) {
        $ProjectName = "data_pipeline"
    }

    Scaffold-New-Project -Destination $TargetDir -ProjectName $ProjectName
    Copy-Agent-Layer -Destination $TargetDir

    Write-Host "`n=================================================================" -ForegroundColor Green
    Write-Host "  ¡Proyecto '$ProjectName' creado e inicializado con éxito!      " -ForegroundColor Yellow
    Write-Host "=================================================================" -ForegroundColor Green
    Write-Host "Estructura lista en:" -ForegroundColor Cyan
    Write-Host "  • src/          (Orchestration, Queries, Transformations, Resources)"
    Write-Host "  • tests/        (Zero-JVM test suite & conftest.py)"
    Write-Host "  • serverless/   (Modular Serverless v3 Infrastructure)"
    Write-Host "  • .agents/      (Universal Skills & Specialized Subagents)"
    Write-Host "  • .synapse/     (Persistent Memory & SDD Specification)"
} else {
    if ($null -eq $InstallAgents) {
        $rawInstall = Read-Host "`n¿Deseas instalar las skills, subagentes y memoria persistente en este proyecto? (s/n)"
        $installAgentsBool = ($rawInstall -match "^[sSyY]")
    } else {
        $installAgentsBool = $InstallAgents
    }

    if ($installAgentsBool) {
        Copy-Agent-Layer -Destination $TargetDir
        Write-Host "`n=================================================================" -ForegroundColor Green
        Write-Host "  ¡Capa de IA instalada exitosamente en .agents/ y .synapse/!    " -ForegroundColor Yellow
        Write-Host "=================================================================" -ForegroundColor Green
        Write-Host "Tu código fuente existente se mantuvo intacto." -ForegroundColor Cyan
    } else {
        Write-Host "`nOperación cancelada. No se realizaron cambios." -ForegroundColor Yellow
    }
}
