"""Module for spark setup"""

from typing import Tuple

from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.context import SparkContext
from pyspark.sql import SparkSession


def initialize() -> Tuple[GlueContext, SparkSession, Job]:
    """
    Initialize the Spark context.
    
    Returns:
        tuple: The GlueContext, SparkSession and Job objects.
    """
    if SparkContext._active_spark_context:
        sc = SparkContext._active_spark_context
    else:
        sc = SparkContext()
    
    conf = sc.getConf()
    conf.set("spark.sql.parquet.datetimeRebaseModeInRead", "CORRECTED")
    conf.set("spark.sql.parquet.datetimeRebaseModeInWrite", "CORRECTED")
    conf.set("spark.sql.sources.partitionOverwriteMode", "dynamic")
    
    sc.stop()
    sc = SparkContext.getOrCreate(conf=conf)
    
    glue_context = GlueContext(sc)
    spark_session = glue_context.spark_session
    job = Job(glue_context)
    
    return glue_context, spark_session, job