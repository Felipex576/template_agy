---
name: serverless-glue-iac
description: Universal Infrastructure as Code (IaC) standard for AWS Glue ETL jobs, IAM security roles, KMS encryption, CloudWatch monitoring, multi-environment variable resolution, and Azure Pipelines CI/CD automation using Serverless Framework v3. Activate when creating, configuring, or reviewing Serverless YAML architectures and Azure DevOps deployment pipelines for data pipelines.
---

# Universal Serverless Framework & YAML IaC for AWS Glue

Production-ready standard for declaring, structuring, and deploying AWS Glue ETL jobs, IAM policies, and analytics infrastructure using **Serverless Framework v3**, **AWS CloudFormation**, and **Azure Pipelines CI/CD**.

---

## 1. When to Activate This Skill

- Creating or modifying `serverless-<service>.yml` root files and modular YAML components.
- Defining `AWS::Glue::Job` resources with worker sizing (`G.1X`, `G.2X`), Iceberg extensions, and runtime parameters.
- Configuring least-privilege `AWS::IAM::Role` resources with scoped S3 and KMS permissions.
- Setting up multi-environment variable resolution (`dev`, `uat`, `pdn`) between CI/CD, `.env`, and `custom.yml`.
- Configuring `azure-pipeline.yml` for automated testing, SonarQube quality gates, dependency bundling, and Serverless deployment.
- Reviewing or validating Serverless infrastructure syntax before CI/CD deployments.

---

## 2. Standard Modular Directory Layout

Every analytics service organizes its Infrastructure as Code and deployment pipelines into modular files:

```text
<project-root>/
├── .env.example                                # Documented environment variables (camelCase)
├── azure-pipeline-<service>.yml                # Multi-stage CI/CD pipeline for Azure DevOps
├── serverless-<layer>-<project>.yml            # Root entrypoint for Serverless Framework
└── serverless-files/
    └── <layer>/
        ├── provider.yml                        # AWS provider, runtime, tags, deployment bucket
        ├── custom.yml                          # Variable mapping and stage resolution
        └── resources/
            ├── jobs.yml                        # AWS::Glue::Job resource definitions
            ├── roles.yml                       # AWS::IAM::Role and policy definitions
            └── triggers.yml                    # (Optional) AWS::Glue::Trigger schedules
```

---

## 3. Variable Resolution Chain (Hierarchy)

Configuration values flow through 5 strictly typed stages from CI/CD to Python:

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

### Stage Resolution Pattern in `custom.yml`:
For variables that change per environment (`dev`, `uat`, `pdn`), define explicit stage maps:

```yaml
# Stage resolution
stage: ${opt:stage, 'dev'}
project: ${env:project}

# Multi-stage Account IDs
analyticsAccountIdStage:
  dev: ${env:analyticsAccountIdDEV}
  uat: ${env:analyticsAccountIdUAT}
  pdn: ${env:analyticsAccountIdPDN}
analyticsAccountId: ${self:custom.analyticsAccountIdStage.${self:custom.stage}}

# Multi-stage KMS Key ARNs
kmsARNStage:
  dev: ${env:arnKmsDEV}
  uat: ${env:arnKmsUAT}
  pdn: ${env:arnKmsPDN}
kmsARN: ${self:custom.kmsARNStage.${self:custom.stage}}

# Multi-stage Worker Count
jobNumberOfWorkersStage:
  dev: ${env:jobNumberOfWorkersDEV, 2}
  uat: ${env:jobNumberOfWorkersUAT, 4}
  pdn: ${env:jobNumberOfWorkersPDN, 10}
jobNumberOfWorkers: ${self:custom.jobNumberOfWorkersStage.${self:custom.stage}}

# Dynamic Data Lake Bucket Names
dataLakeNameStaging: s3-${self:custom.analyticsAccountId}-datalake-${self:custom.stage}-staging
dataLakeNameTrusted: s3-${self:custom.analyticsAccountId}-datalake-${self:custom.stage}-trusted
```

---

## 4. Root Configuration (`serverless-<layer>-<project>.yml`)

```yaml
service: ${self:custom.project}-<job-name>
frameworkVersion: "3"
useDotenv: true

provider: ${file(./serverless-files/<layer>/provider.yml)}

custom: ${file(./serverless-files/<layer>/custom.yml)}

package:
  individually: true
  exclude:
    - ./**

plugins:
  - serverless-python-requirements
  - serverless-plugin-common-excludes

resources:
  # IAM Roles
  - ${file(./serverless-files/<layer>/resources/roles.yml)}
  # Glue Jobs
  - ${file(./serverless-files/<layer>/resources/jobs.yml)}
```

---

## 5. Provider & Tagging Configuration (`provider.yml`)

```yaml
name: aws
stage: ${self:custom.stage}
runtime: python3.11
lambdaHashingVersion: 20201221
deploymentBucket:
  name: ${self:custom.deploymentBucketName}
  maxPreviousDeploymentArtifacts: 10
stackTags:
  Ambiente: ${self:custom.stage}
  Aplicativo: ${self:custom.tagAplicativo}
  Area: ${self:custom.tagArea}
  Celula: ${self:custom.tagCelula}
  Compania: ${self:custom.tagCompania}
  Despliegue: ServerlessFramework
  Disponibilidad: ${self:custom.tagDisponibilidad}
  Producto: ${self:custom.tagProducto}
  Proyecto: ${self:custom.tagProyecto}
```

---

## 6. AWS Glue Job Resource Pattern (`resources/jobs.yml`)

```yaml
Resources:
  PipelineGlueJob:
    Type: AWS::Glue::Job
    Properties:
      Description: "ETL Batch Pipeline for <job-description>"
      Name: job-analytics-${self:custom.project}-<job-name>
      Role: !GetAtt PipelineJobRole.Arn
      ExecutionProperty:
        MaxConcurrentRuns: 10
      MaxRetries: 0
      NumberOfWorkers: ${self:custom.jobNumberOfWorkers}
      WorkerType: G.1X
      GlueVersion: ${self:custom.glueJobVersion}
      DefaultArguments:
        "--JOB_NAME": job-analytics-${self:custom.project}-<job-name>
        "--CATALOG_DATABASE": "${self:custom.catalogDatabase}"
        "--TARGET_TABLE": "${self:custom.targetTable}"
        "--TRUSTED_BUCKET": "${self:custom.dataLakeNameTrusted}"
        "--PROJECT_BUCKET_NAME": "${self:custom.projectBucket}"
        "--PREFIX_DATA": "${self:custom.prefixData}"
        "--PREFIX_FILE": "${self:custom.prefixFiles}"
        "--extra-py-files": "${self:custom.extraPythonFiles}"
        "--TempDir": !Sub "s3://${self:custom.projectBucket}/temp_trusted/"
        "--enable-continuous-cloudwatch-log": "true"
        "--enable-continuous-log-filter": "true"
        "--enable-metrics": "true"
        "--datalake-formats": "iceberg"
        "--additional-python-modules": "openpyxl==3.1.5,pydeequ,holidays-co==1.1.3"
        "--conf": "spark.sql.extensions=org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions --conf spark.sql.catalog.glue_catalog=org.apache.iceberg.spark.SparkCatalog --conf spark.sql.catalog.glue_catalog.catalog-impl=org.apache.iceberg.aws.glue.GlueCatalog --conf spark.sql.catalog.glue_catalog.io-impl=org.apache.iceberg.aws.s3.S3FileIO --conf spark.sql.catalog.glue_catalog.glue.skip-name-validation=true"
      Command:
        Name: glueetl
        ScriptLocation: !Sub "s3://${self:custom.projectBucket}/${self:custom.projectBucketJobsPath}/<job_entrypoint>.py"
```

> [!IMPORTANT]
> **Command Property Rule:** Do NOT include `PythonVersion` inside `Command:` for Glue 4.0/5.0. AWS Glue infers the Python runtime directly from `GlueVersion`.

---

## 7. IAM Least-Privilege Role Pattern (`resources/roles.yml`)

```yaml
Resources:
  PipelineJobRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: iam-${self:custom.project}-${self:custom.stage}-<job-name>Role
      AssumeRolePolicyDocument:
        Version: "2012-10-17"
        Statement:
          - Effect: Allow
            Principal:
              Service:
                - glue.amazonaws.com
            Action:
              - sts:AssumeRole
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole
        - arn:aws:iam::aws:policy/AWSGlueConsoleFullAccess
      Path: /
      Policies:
        - PolicyName: "S3DataLakeAccessPolicy"
          PolicyDocument:
            Version: "2012-10-17"
            Statement:
              - Effect: Allow
                Action:
                  - "s3:GetObject"
                  - "s3:PutObject"
                  - "s3:ListBucket"
                Resource:
                  - !Sub "arn:aws:s3:::${self:custom.dataLakeNameTrusted}"
                  - !Sub "arn:aws:s3:::${self:custom.dataLakeNameTrusted}/*"
                  - !Sub "arn:aws:s3:::${self:custom.dataLakeNameStaging}"
                  - !Sub "arn:aws:s3:::${self:custom.dataLakeNameStaging}/*"
                  - !Sub "arn:aws:s3:::${self:custom.datafoundationBucket}/*"
                  - !Sub "arn:aws:s3:::${self:custom.projectBucket}/*"
        - PolicyName: "KmsEncryptionPolicy"
          PolicyDocument:
            Version: "2012-10-17"
            Statement:
              - Effect: Allow
                Action:
                  - "kms:Encrypt"
                  - "kms:Decrypt"
                  - "kms:GenerateDataKey"
                Resource:
                  - ${self:custom.kmsARN}
```

---

## 8. Azure Pipelines CI/CD Specification (`azure-pipeline.yml`)

The multi-stage automated deployment pipeline executes tests inside Docker containers, evaluates code quality with **SonarQube**, uploads Python dependency bundles to Amazon S3, and triggers **Serverless Framework** deployment.

### Standard Pipeline Structure:

```yaml
trigger:
  branches:
    include:
      - development
      - release
      - master
  paths:
    include:
      - "<job-folder>/**"
    exclude:
      - azure-pipeline.yml*

pool: "BTG Colombia - Azure DevOPS"

resources:
  repositories:
    - repository: devops-templates
      type: git
      name: devops-templates
      ref: master

variables:
  # 1. Dynamic stage mapping based on branch
  - name: stage
    ${{ if eq(variables['Build.SourceBranchName'], 'development') }}:
      value: dev
    ${{ elseif eq(variables['Build.SourceBranchName'], 'release') }}:
      value: uat
    ${{ elseif eq(variables['Build.SourceBranchName'], 'master') }}:
      value: pdn

  # 2. Dynamic AWS Service Connection per stage
  - name: awsCredentials
    value: SVC-SERVICE-IDP-ANALYTICS-${{upper(variables.stage)}}
  - name: region
    value: us-east-1

  # 3. Variable groups
  - group: <transversal-tags-group>
  - group: <project-tags-group>
  - group: <project-variables-group>

  # 4. Serverless & deployment configs
  - name: deploymentBucketName
    value: bucket-analytics-$(stage)-serverless
  - name: pythonVersion
    value: "3.11"
  - name: serverlessVersion
    value: "3"
  - name: plugginsToInstall
    value: "serverless-python-requirements serverless-plugin-common-excludes serverless-step-functions"
  - name: serverlessFile
    value: serverless-<service>.yml

stages:
  # =========================================================
  # STAGE 1: SonarQube & Docker Container Test Execution
  # =========================================================
  - stage: Sonar_and_Upload_${{ variables.stage }}
    jobs:
      - job: tests_sonar
        displayName: Run tests in Docker and SonarQube Analysis
        steps:
          - task: SonarQubePrepare@5.13.0
            displayName: SonarQube Prepare
            inputs:
              SonarQube: "SonarQube-v25.9.0.112764"
              scannerMode: "CLI"
              configMode: "manual"
              cliProjectKey: "$(Build.Repository.Name)"
              cliProjectName: "$(Build.Repository.Name)"
              cliSources: "$(System.DefaultWorkingDirectory)/<job-folder>/src"
              extraProperties: |
                sonar.branch.name=$(Build.SourceBranchName)
                sonar.python.coverage.reportPaths=$(System.DefaultWorkingDirectory)/<job-folder>/src/coverage2.xml
                sonar.exclusions=**/tests/**, **/__init__.py, **/python-libraries/**
          - task: CmdLine@2
            displayName: Build Test Container & Extract Coverage
            inputs:
              script: |
                docker build -t test/<job-folder> $(System.DefaultWorkingDirectory)/<job-folder>
                docker run -d --name testing_<job-folder> test/<job-folder>
                docker cp testing_<job-folder>:/<container-workdir>/coverage.xml <job-folder>/src/
                docker stop testing_<job-folder>
                docker rm testing_<job-folder>
                docker rmi test/<job-folder>
                # Normalize container absolute paths to Azure Agent workspace paths
                sed "s%/<container-workdir>/src/%%g" <job-folder>/src/coverage.xml > <job-folder>/src/coverage_temp.xml
                sed "s%<source>/<container-workdir>/src</source>%<source>${SYSTEM_DEFAULTWORKINGDIRECTORY}/<job-folder>/src</source>%g" <job-folder>/src/coverage_temp.xml > <job-folder>/src/coverage2.xml
                rm <job-folder>/src/coverage_temp.xml
          - task: SonarQubeAnalyze@5
            displayName: SonarQube Analyze
          - task: SonarQubePublish@5.0.2
            displayName: SonarQube Publish
            inputs:
              pollingTimeoutSec: "300"
          - task: sonar-buildbreaker@8
            displayName: SonarQube Quality Gate Breaker
            inputs:
              SonarQube: "Sonar Qube"

  # =========================================================
  # STAGE 2: Upload Job Scripts & Dependencies to S3
  # =========================================================
  - stage: Upload_Dependencies_${{ variables.stage }}
    jobs:
      - job: upload_dependencies
        displayName: Package and Upload Dependencies to S3
        steps:
          # Upload entrypoint scripts
          - task: S3Upload@1
            displayName: Upload Job Python Scripts to S3
            inputs:
              awsCredentials: $(awsCredentials)
              regionName: $(region)
              bucketName: $(projectBucket)
              sourceFolder: $(System.DefaultWorkingDirectory)/<job-folder>/src/jobs
              globExpressions: "*.py"
              targetFolder: $(projectBucketJobsPath)

          # Compress src/ directory into dependencies zip
          - task: ArchiveFiles@2
            displayName: Archive src folder into zip
            inputs:
              rootFolderOrFile: $(System.DefaultWorkingDirectory)/<job-folder>/src
              includeRootFolder: true
              archiveType: zip
              archiveFile: $(System.DefaultWorkingDirectory)/dependencies/<job-name>-dependencies.zip
              replaceExistingArchive: true

          # Upload dependencies zip to S3
          - task: S3Upload@1
            displayName: Upload Dependencies Zip to S3
            inputs:
              awsCredentials: $(awsCredentials)
              regionName: $(region)
              bucketName: $(projectBucket)
              sourceFolder: $(System.DefaultWorkingDirectory)/dependencies
              globExpressions: "<job-name>-dependencies.zip"
              targetFolder: dependencies

          # (Optional) Upload extra static templates
          - task: S3Upload@1
            displayName: Upload Extra Files to S3
            inputs:
              awsCredentials: $(awsCredentials)
              regionName: $(region)
              bucketName: $(projectBucket)
              sourceFolder: $(System.DefaultWorkingDirectory)/<job-folder>/src/utils/extra_files
              globExpressions: "*"
              targetFolder: extra_files

  # =========================================================
  # STAGE 3: Serverless Framework Deployment
  # =========================================================
  - template: main.yml@devops-templates
    parameters:
      service: serverless
      type: code
      code: resources
      workPath: $(System.DefaultWorkingDirectory)/<job-folder>
```

### Critical Azure DevOps Configuration Rules:
1. **Container Path Normalization (`sed`):** SonarQube running on the build agent cannot resolve paths inside the Docker container (e.g. `/reporte-regulatorio/src/`). The `sed` substitution command replaces the container root with `${SYSTEM_DEFAULTWORKINGDIRECTORY}/<job-folder>/src` so coverage is accurately mapped.
2. **Quality Gate Breaker:** `sonar-buildbreaker@8` fails the pipeline immediately if coverage drops below the defined threshold ($\ge 80\%$) or critical code smells are detected.
3. **Dependencies Bundling:** The zip file generated by `ArchiveFiles@2` matches the S3 path referenced in the job's `--extra-py-files` parameter.

---

## 9. Guardrails & Best Practices Checklist

| Rule | Category | Requirement |
|---|---|---|
| **Naming Homology** | `Variables` | Variables in `.env`, `custom.yml`, and CI/CD must match in `camelCase`. |
| **Physical Resource Names** | `AWS Names` | Use `kebab-case` with stage/project prefixes: `job-analytics-${project}-${job}`. |
| **No Hardcoded Accounts / ARNs** | `Security` | Inject Account IDs and KMS ARNs via stage maps (`${self:custom.kmsARN}`). |
| **Package Exclusion** | `Packaging` | Always include `exclude: - ./**` under `package:` to prevent large zip uploads. |
| **CloudFormation References** | `IaC` | Use `${cf:<stack>.<Output>}` for cross-stack outputs (e.g. shared bucket ARNs). |
| **Path Mapping in SonarQube** | `CI/CD` | Ensure `docker cp` and `sed` path replacements match `WORKDIR` in Dockerfile. |
| **Iceberg Catalog Conf** | `Spark/Glue` | Always configure `--conf` with Iceberg extensions and catalog implementation. |
