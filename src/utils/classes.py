from dataclasses import dataclass
from pyspark.sql import DataFrame

@dataclass(frozen=True)
class ProcessingDataFrames:
    raw_data: DataFrame
    processed_data: DataFrame = None
    final_summary: DataFrame = None
