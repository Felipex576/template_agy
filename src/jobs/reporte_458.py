import sys
from awsglue.utils import getResolvedOptions
from src.config.spark_setup import initialize
from src.config.logger import get_logger
from src.utils.constants import REQUIRED_JOB_ARGS

logger = get_logger("reporte_458")

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
