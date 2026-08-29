from unittest.mock import patch, MagicMock

from src.config.spark_setup import initialize

@patch('src.config.spark_setup.SparkContext')
@patch('src.config.spark_setup.GlueContext')
@patch('src.config.spark_setup.Job')
def test_initialize(mock_Job, mock_GlueContext, mock_SparkContext):
    mock_spark_context = MagicMock()
    mock_glue_context = MagicMock()
    mock_spark_session = MagicMock()
    mock_job = MagicMock()

    mock_SparkContext._active_spark_context = None
    mock_SparkContext.return_value = mock_spark_context
    mock_SparkContext.getOrCreate.return_value = mock_spark_context
    mock_GlueContext.return_value = mock_glue_context
    mock_glue_context.spark_session = mock_spark_session
    mock_Job.return_value = mock_job

    glueContext, spark, job = initialize()

    mock_SparkContext.assert_called_once()
    mock_SparkContext.getOrCreate.assert_called_once()
    mock_GlueContext.assert_called_once_with(mock_spark_context)
    mock_Job.assert_called_once_with(mock_glue_context)
    
    assert glueContext == mock_glue_context
    assert spark == mock_spark_session
    assert job == mock_job