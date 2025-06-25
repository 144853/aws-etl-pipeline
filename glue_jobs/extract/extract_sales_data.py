#!/usr/bin/env python3
"""
ETL Extract Job: Sales Data Extraction

This Glue job extracts sales data from various sources and stores it in S3.
"""

import sys
import boto3
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql import DataFrame
from pyspark.sql.functions import *
from pyspark.sql.types import *
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SalesDataExtractor:
    def __init__(self, glue_context, spark_context, job):
        self.glue_context = glue_context
        self.spark_context = spark_context
        self.job = job
        self.spark = glue_context.spark_session
        
    def extract_from_rds(self, connection_name: str, table_name: str) -> DataFrame:
        """
        Extract data from RDS PostgreSQL database
        """
        logger.info(f"Extracting data from RDS table: {table_name}")
        
        try:
            # Read from RDS using Glue connection
            datasource = self.glue_context.create_dynamic_frame.from_options(
                connection_type="postgresql",
                connection_options={
                    "useConnectionProperties": "true",
                    "connectionName": connection_name,
                    "dbtable": table_name
                }
            )
            
            # Convert to Spark DataFrame
            df = datasource.toDF()
            
            logger.info(f"Successfully extracted {df.count()} records from {table_name}")
            return df
            
        except Exception as e:
            logger.error(f"Error extracting data from RDS: {str(e)}")
            raise
    
    def extract_from_s3_csv(self, s3_path: str) -> DataFrame:
        """
        Extract data from CSV files in S3
        """
        logger.info(f"Extracting data from S3 CSV: {s3_path}")
        
        try:
            df = self.spark.read.option("header", "true").option("inferSchema", "true").csv(s3_path)
            logger.info(f"Successfully extracted {df.count()} records from CSV")
            return df
            
        except Exception as e:
            logger.error(f"Error extracting data from S3 CSV: {str(e)}")
            raise
    
    def extract_from_api(self, api_config: dict) -> DataFrame:
        """
        Extract data from REST API (placeholder for API integration)
        """
        logger.info(f"Extracting data from API: {api_config.get('url', 'Unknown')}")
        
        # This is a placeholder - implement actual API call logic
        # For demo purposes, creating a sample DataFrame
        sample_data = [
            (1, "Product A", 100.0, "2023-01-01"),
            (2, "Product B", 150.0, "2023-01-02"),
            (3, "Product C", 200.0, "2023-01-03")
        ]
        
        schema = StructType([
            StructField("product_id", IntegerType(), True),
            StructField("product_name", StringType(), True),
            StructField("price", DoubleType(), True),
            StructField("date_created", StringType(), True)
        ])
        
        df = self.spark.createDataFrame(sample_data, schema)
        logger.info(f"Successfully extracted {df.count()} records from API")
        return df
    
    def add_extraction_metadata(self, df: DataFrame) -> DataFrame:
        """
        Add metadata columns to extracted data
        """
        current_timestamp = datetime.now()
        
        df_with_metadata = df.withColumn("extraction_timestamp", lit(current_timestamp)) \
                           .withColumn("extraction_job", lit("extract-sales-data")) \
                           .withColumn("source_system", lit("sales_db"))
        
        return df_with_metadata
    
    def validate_data(self, df: DataFrame) -> bool:
        """
        Perform basic data validation
        """
        logger.info("Performing data validation")
        
        # Check if DataFrame is not empty
        if df.count() == 0:
            logger.error("Data validation failed: DataFrame is empty")
            return False
        
        # Check for required columns (example)
        required_columns = ["product_id", "product_name"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            logger.error(f"Data validation failed: Missing required columns: {missing_columns}")
            return False
        
        # Check for null values in critical columns
        null_counts = df.select([count(when(col(c).isNull(), c)).alias(c) for c in required_columns]).collect()[0]
        
        for col_name in required_columns:
            null_count = null_counts[col_name]
            if null_count > 0:
                logger.warning(f"Found {null_count} null values in column: {col_name}")
        
        logger.info("Data validation completed successfully")
        return True
    
    def save_to_s3(self, df: DataFrame, output_path: str, file_format: str = "parquet"):
        """
        Save DataFrame to S3
        """
        logger.info(f"Saving data to S3: {output_path}")
        
        try:
            if file_format.lower() == "parquet":
                df.write.mode("overwrite").parquet(output_path)
            elif file_format.lower() == "csv":
                df.write.mode("overwrite").option("header", "true").csv(output_path)
            else:
                raise ValueError(f"Unsupported file format: {file_format}")
            
            logger.info(f"Successfully saved {df.count()} records to {output_path}")
            
        except Exception as e:
            logger.error(f"Error saving data to S3: {str(e)}")
            raise


def main():
    # Get job parameters
    args = getResolvedOptions(sys.argv, [
        'JOB_NAME',
        'DATABASE_NAME',
        'DATA_BUCKET',
        'PROCESSED_BUCKET',
        'ENVIRONMENT'
    ])
    
    # Initialize Glue context
    sc = SparkContext()
    glueContext = GlueContext(sc)
    spark = glueContext.spark_session
    job = Job(glueContext)
    job.init(args['JOB_NAME'], args)
    
    logger.info(f"Starting extraction job: {args['JOB_NAME']}")
    logger.info(f"Environment: {args['ENVIRONMENT']}")
    
    try:
        # Initialize extractor
        extractor = SalesDataExtractor(glueContext, sc, job)
        
        # Extract data from multiple sources
        # 1. Extract from RDS (if connection exists)
        try:
            rds_df = extractor.extract_from_rds(
                connection_name=f"{args['DATABASE_NAME']}-connection",
                table_name="sales_transactions"
            )
            rds_df = extractor.add_extraction_metadata(rds_df)
        except Exception as e:
            logger.warning(f"Could not extract from RDS: {str(e)}")
            rds_df = None
        
        # 2. Extract from CSV files in S3
        csv_path = f"s3://{args['DATA_BUCKET']}/raw/sales/*.csv"
        try:
            csv_df = extractor.extract_from_s3_csv(csv_path)
            csv_df = extractor.add_extraction_metadata(csv_df)
        except Exception as e:
            logger.warning(f"Could not extract from CSV: {str(e)}")
            csv_df = None
        
        # 3. Extract from API (placeholder)
        api_config = {"url": "https://api.example.com/sales"}
        api_df = extractor.extract_from_api(api_config)
        api_df = extractor.add_extraction_metadata(api_df)
        
        # Combine all data sources
        all_dataframes = [df for df in [rds_df, csv_df, api_df] if df is not None]
        
        if not all_dataframes:
            raise Exception("No data sources available for extraction")
        
        # Union all DataFrames (assuming same schema)
        combined_df = all_dataframes[0]
        for df in all_dataframes[1:]:
            combined_df = combined_df.union(df)
        
        # Validate extracted data
        if not extractor.validate_data(combined_df):
            raise Exception("Data validation failed")
        
        # Add partitioning columns
        current_date = datetime.now().strftime("%Y-%m-%d")
        partitioned_df = combined_df.withColumn("extraction_date", lit(current_date))
        
        # Save to S3
        output_path = f"s3://{args['DATA_BUCKET']}/extracted/sales_data/extraction_date={current_date}"
        extractor.save_to_s3(partitioned_df, output_path, "parquet")
        
        # Update Glue catalog
        logger.info("Updating Glue Data Catalog")
        
        # Create/update table in Glue catalog
        dynamic_frame = DynamicFrame.fromDF(partitioned_df, glueContext, "sales_extracted")
        
        glueContext.write_dynamic_frame.from_catalog(
            frame=dynamic_frame,
            database=args['DATABASE_NAME'],
            table_name="sales_extracted",
            transformation_ctx="datasink"
        )
        
        logger.info("Extraction job completed successfully")
        
    except Exception as e:
        logger.error(f"Extraction job failed: {str(e)}")
        raise
    
    finally:
        job.commit()


if __name__ == "__main__":
    main()