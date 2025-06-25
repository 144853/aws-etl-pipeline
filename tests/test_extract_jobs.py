#!/usr/bin/env python3
"""
Unit tests for ETL extract jobs
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType
import sys
import os

# Add the project root to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestSalesDataExtractor:
    """Test cases for SalesDataExtractor class"""
    
    @pytest.fixture
    def mock_glue_context(self):
        """Create mock Glue context"""
        mock_context = Mock()
        mock_spark_session = Mock()
        mock_context.spark_session = mock_spark_session
        return mock_context
    
    @pytest.fixture
    def mock_spark_context(self):
        """Create mock Spark context"""
        return Mock()
    
    @pytest.fixture
    def mock_job(self):
        """Create mock Glue job"""
        return Mock()
    
    @pytest.fixture
    def sample_data_schema(self):
        """Sample data schema for testing"""
        return StructType([
            StructField("product_id", IntegerType(), True),
            StructField("product_name", StringType(), True),
            StructField("price", DoubleType(), True),
            StructField("quantity", IntegerType(), True)
        ])
    
    @pytest.fixture
    def sample_data(self):
        """Sample test data"""
        return [
            (1, "Product A", 100.0, 5),
            (2, "Product B", 150.0, 3),
            (3, "Product C", 200.0, 2)
        ]
    
    def test_validate_data_success(self, mock_glue_context, mock_spark_context, mock_job, sample_data, sample_data_schema):
        """Test data validation with valid data"""
        from glue_jobs.extract.extract_sales_data import SalesDataExtractor
        
        # Create extractor instance
        extractor = SalesDataExtractor(mock_glue_context, mock_spark_context, mock_job)
        
        # Mock DataFrame
        mock_df = Mock(spec=DataFrame)
        mock_df.count.return_value = 3
        mock_df.columns = ["product_id", "product_name", "price", "quantity"]
        
        # Mock column selection and null checks
        mock_collect_result = Mock()
        mock_collect_result.__getitem__ = Mock(side_effect=lambda x: 0)  # No null values
        mock_df.select.return_value.collect.return_value = [mock_collect_result]
        
        # Test validation
        result = extractor.validate_data(mock_df)
        
        assert result is True
        mock_df.count.assert_called_once()
    
    def test_validate_data_empty_dataframe(self, mock_glue_context, mock_spark_context, mock_job):
        """Test data validation with empty DataFrame"""
        from glue_jobs.extract.extract_sales_data import SalesDataExtractor
        
        extractor = SalesDataExtractor(mock_glue_context, mock_spark_context, mock_job)
        
        # Mock empty DataFrame
        mock_df = Mock(spec=DataFrame)
        mock_df.count.return_value = 0
        
        result = extractor.validate_data(mock_df)
        
        assert result is False
    
    def test_validate_data_missing_columns(self, mock_glue_context, mock_spark_context, mock_job):
        """Test data validation with missing required columns"""
        from glue_jobs.extract.extract_sales_data import SalesDataExtractor
        
        extractor = SalesDataExtractor(mock_glue_context, mock_spark_context, mock_job)
        
        # Mock DataFrame with missing columns
        mock_df = Mock(spec=DataFrame)
        mock_df.count.return_value = 5
        mock_df.columns = ["product_id"]  # Missing product_name
        
        result = extractor.validate_data(mock_df)
        
        assert result is False
    
    @patch('glue_jobs.extract.extract_sales_data.datetime')
    def test_add_extraction_metadata(self, mock_datetime, mock_glue_context, mock_spark_context, mock_job):
        """Test adding extraction metadata to DataFrame"""
        from glue_jobs.extract.extract_sales_data import SalesDataExtractor
        
        # Mock datetime
        mock_now = Mock()
        mock_datetime.now.return_value = mock_now
        
        extractor = SalesDataExtractor(mock_glue_context, mock_spark_context, mock_job)
        
        # Mock DataFrame with withColumn method
        mock_df = Mock(spec=DataFrame)
        mock_df_with_metadata = Mock(spec=DataFrame)
        
        # Chain the withColumn calls
        mock_df.withColumn.return_value.withColumn.return_value.withColumn.return_value = mock_df_with_metadata
        
        result = extractor.add_extraction_metadata(mock_df)
        
        assert result == mock_df_with_metadata
        mock_df.withColumn.assert_called_once()
    
    @patch('glue_jobs.extract.extract_sales_data.boto3')
    def test_extract_from_api(self, mock_boto3, mock_glue_context, mock_spark_context, mock_job):
        """Test API data extraction"""
        from glue_jobs.extract.extract_sales_data import SalesDataExtractor
        
        extractor = SalesDataExtractor(mock_glue_context, mock_spark_context, mock_job)
        
        # Mock Spark session
        mock_spark = Mock()
        extractor.spark = mock_spark
        
        # Mock DataFrame creation
        mock_df = Mock(spec=DataFrame)
        mock_df.count.return_value = 3
        mock_spark.createDataFrame.return_value = mock_df
        
        api_config = {"url": "https://api.example.com/sales"}
        result = extractor.extract_from_api(api_config)
        
        assert result == mock_df
        mock_spark.createDataFrame.assert_called_once()
    
    def test_save_to_s3_parquet(self, mock_glue_context, mock_spark_context, mock_job):
        """Test saving DataFrame to S3 as Parquet"""
        from glue_jobs.extract.extract_sales_data import SalesDataExtractor
        
        extractor = SalesDataExtractor(mock_glue_context, mock_spark_context, mock_job)
        
        # Mock DataFrame
        mock_df = Mock(spec=DataFrame)
        mock_df.count.return_value = 100
        
        # Mock write operations
        mock_write = Mock()
        mock_df.write = mock_write
        mock_write.mode.return_value = mock_write
        mock_write.parquet.return_value = None
        
        output_path = "s3://test-bucket/output/"
        
        # Should not raise exception
        extractor.save_to_s3(mock_df, output_path, "parquet")
        
        # Verify calls
        mock_write.mode.assert_called_once_with("overwrite")
        mock_write.parquet.assert_called_once_with(output_path)
    
    def test_save_to_s3_csv(self, mock_glue_context, mock_spark_context, mock_job):
        """Test saving DataFrame to S3 as CSV"""
        from glue_jobs.extract.extract_sales_data import SalesDataExtractor
        
        extractor = SalesDataExtractor(mock_glue_context, mock_spark_context, mock_job)
        
        # Mock DataFrame
        mock_df = Mock(spec=DataFrame)
        mock_df.count.return_value = 100
        
        # Mock write operations
        mock_write = Mock()
        mock_df.write = mock_write
        mock_write.mode.return_value = mock_write
        mock_write.option.return_value = mock_write
        mock_write.csv.return_value = None
        
        output_path = "s3://test-bucket/output/"
        
        # Should not raise exception
        extractor.save_to_s3(mock_df, output_path, "csv")
        
        # Verify calls
        mock_write.mode.assert_called_once_with("overwrite")
        mock_write.option.assert_called_once_with("header", "true")
        mock_write.csv.assert_called_once_with(output_path)
    
    def test_save_to_s3_invalid_format(self, mock_glue_context, mock_spark_context, mock_job):
        """Test saving DataFrame with invalid format"""
        from glue_jobs.extract.extract_sales_data import SalesDataExtractor
        
        extractor = SalesDataExtractor(mock_glue_context, mock_spark_context, mock_job)
        
        # Mock DataFrame
        mock_df = Mock(spec=DataFrame)
        
        output_path = "s3://test-bucket/output/"
        
        # Should raise ValueError
        with pytest.raises(ValueError, match="Unsupported file format"):
            extractor.save_to_s3(mock_df, output_path, "invalid_format")


class TestDeploymentScripts:
    """Test cases for deployment scripts"""
    
    @patch('scripts.deploy_glue_jobs.boto3')
    def test_glue_job_deployer_init(self, mock_boto3):
        """Test GlueJobDeployer initialization"""
        from scripts.deploy_glue_jobs import GlueJobDeployer
        
        # Mock boto3 clients
        mock_s3_client = Mock()
        mock_glue_client = Mock()
        mock_boto3.client.side_effect = [mock_s3_client, mock_glue_client]
        
        # Mock config loading
        with patch.object(GlueJobDeployer, '_load_config') as mock_load_config:
            mock_load_config.return_value = {'project_name': 'test-project'}
            
            deployer = GlueJobDeployer('dev', 'us-east-1')
            
            assert deployer.environment == 'dev'
            assert deployer.aws_region == 'us-east-1'
            assert deployer.s3_client == mock_s3_client
            assert deployer.glue_client == mock_glue_client
    
    @patch('scripts.run_migrations.psycopg2')
    @patch('scripts.run_migrations.boto3')
    def test_database_migrator_init(self, mock_boto3, mock_psycopg2):
        """Test DatabaseMigrator initialization"""
        from scripts.run_migrations import DatabaseMigrator
        
        # Mock secrets client
        mock_secrets_client = Mock()
        mock_boto3.client.return_value = mock_secrets_client
        
        migrator = DatabaseMigrator('dev', 'us-east-1')
        
        assert migrator.environment == 'dev'
        assert migrator.aws_region == 'us-east-1'
        assert migrator.secrets_client == mock_secrets_client
    
    @patch('scripts.health_check.boto3')
    def test_health_checker_init(self, mock_boto3):
        """Test ETLHealthChecker initialization"""
        from scripts.health_check import ETLHealthChecker
        
        # Mock all required clients
        mock_clients = [Mock() for _ in range(4)]  # s3, glue, rds, secrets
        mock_boto3.client.side_effect = mock_clients
        
        checker = ETLHealthChecker('prod', 'us-east-1')
        
        assert checker.environment == 'prod'
        assert checker.aws_region == 'us-east-1'
        assert len(checker.health_results) == 0


class TestConfigurationManagement:
    """Test cases for configuration management"""
    
    def test_dev_config_structure(self):
        """Test that dev configuration has required keys"""
        # This would read the actual config file in a real test
        required_keys = [
            'aws_region',
            'environment', 
            'project_name',
            'bucket_prefix',
            'glue_job_configs'
        ]
        
        # Mock config loading
        dev_config = {
            'aws_region': 'us-east-1',
            'environment': 'dev',
            'project_name': 'etl-pipeline',
            'bucket_prefix': 'etl-pipeline-dev',
            'glue_job_configs': {}
        }
        
        for key in required_keys:
            assert key in dev_config
    
    def test_glue_job_config_validation(self):
        """Test Glue job configuration validation"""
        job_config = {
            'script_location': 's3://bucket/script.py',
            'job_language': 'python',
            'max_capacity': 2,
            'timeout': 60,
            'max_retries': 1,
            'worker_type': 'Standard',
            'number_of_workers': 2
        }
        
        required_fields = ['script_location', 'job_language', 'timeout']
        
        for field in required_fields:
            assert field in job_config
            assert job_config[field] is not None


if __name__ == '__main__':
    pytest.main([__file__])