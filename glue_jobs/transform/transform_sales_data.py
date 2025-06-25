#!/usr/bin/env python3
"""
ETL Transform Job: Sales Data Transformation

This Glue job transforms extracted sales data, applies business rules,
and prepares it for loading into the data warehouse.
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
from pyspark.sql.window import Window
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SalesDataTransformer:
    def __init__(self, glue_context, spark_context, job):
        self.glue_context = glue_context
        self.spark_context = spark_context
        self.job = job
        self.spark = glue_context.spark_session
        
    def read_from_catalog(self, database_name: str, table_name: str) -> DataFrame:
        """
        Read data from Glue Data Catalog
        """
        logger.info(f"Reading data from catalog: {database_name}.{table_name}")
        
        try:
            dynamic_frame = self.glue_context.create_dynamic_frame.from_catalog(
                database=database_name,
                table_name=table_name
            )
            df = dynamic_frame.toDF()
            logger.info(f"Successfully read {df.count()} records from catalog")
            return df
            
        except Exception as e:
            logger.error(f"Error reading from catalog: {str(e)}")
            raise
    
    def clean_data(self, df: DataFrame) -> DataFrame:
        """
        Clean and standardize the data
        """
        logger.info("Starting data cleaning")
        
        # Remove duplicates
        initial_count = df.count()
        df_cleaned = df.dropDuplicates()
        duplicate_count = initial_count - df_cleaned.count()
        logger.info(f"Removed {duplicate_count} duplicate records")
        
        # Handle null values
        df_cleaned = df_cleaned.fillna({
            "product_name": "Unknown Product",
            "price": 0.0,
            "quantity": 0
        })
        
        # Standardize text fields
        df_cleaned = df_cleaned.withColumn(
            "product_name", 
            trim(upper(col("product_name")))
        )
        
        # Remove invalid records
        df_cleaned = df_cleaned.filter(
            (col("price") >= 0) & 
            (col("quantity") >= 0) &
            (col("product_id").isNotNull())
        )
        
        cleaned_count = df_cleaned.count()
        removed_count = initial_count - duplicate_count - cleaned_count
        logger.info(f"Removed {removed_count} invalid records")
        logger.info(f"Data cleaning completed. Final count: {cleaned_count}")
        
        return df_cleaned
    
    def apply_business_rules(self, df: DataFrame) -> DataFrame:
        """
        Apply business transformation rules
        """
        logger.info("Applying business rules")
        
        # Calculate total amount
        df_transformed = df.withColumn(
            "total_amount",
            col("price") * col("quantity")
        )
        
        # Add product category based on price
        df_transformed = df_transformed.withColumn(
            "price_category",
            when(col("price") < 50, "Low")
            .when(col("price") < 200, "Medium")
            .otherwise("High")
        )
        
        # Add discount tier
        df_transformed = df_transformed.withColumn(
            "discount_tier",
            when(col("total_amount") > 1000, "Premium")
            .when(col("total_amount") > 500, "Standard")
            .otherwise("Basic")
        )
        
        # Calculate running totals by product
        window_spec = Window.partitionBy("product_id").orderBy("extraction_timestamp")
        df_transformed = df_transformed.withColumn(
            "running_total",
            sum("total_amount").over(window_spec)
        )
        
        # Add time-based features
        df_transformed = df_transformed.withColumn(
            "extraction_year",
            year(col("extraction_timestamp"))
        ).withColumn(
            "extraction_month",
            month(col("extraction_timestamp"))
        ).withColumn(
            "extraction_day",
            dayofmonth(col("extraction_timestamp"))
        )
        
        logger.info("Business rules applied successfully")
        return df_transformed
    
    def enrich_data(self, df: DataFrame) -> DataFrame:
        """
        Enrich data with additional information
        """
        logger.info("Enriching data")
        
        # Create product lookup data (in real scenario, this would come from another source)
        product_lookup = [
            (1, "Electronics", "Tech Corp"),
            (2, "Clothing", "Fashion Inc"),
            (3, "Books", "Publishing House")
        ]
        
        lookup_schema = StructType([
            StructField("product_id", IntegerType(), True),
            StructField("category", StringType(), True),
            StructField("supplier", StringType(), True)
        ])
        
        lookup_df = self.spark.createDataFrame(product_lookup, lookup_schema)
        
        # Join with lookup data
        df_enriched = df.join(
            lookup_df,
            on="product_id",
            how="left"
        )
        
        # Fill missing values for new products
        df_enriched = df_enriched.fillna({
            "category": "Unknown",
            "supplier": "Unknown"
        })
        
        logger.info("Data enrichment completed")
        return df_enriched
    
    def calculate_aggregations(self, df: DataFrame) -> DataFrame:
        """
        Calculate various aggregations for analytics
        """
        logger.info("Calculating aggregations")
        
        # Daily aggregations
        daily_agg = df.groupBy(
            "extraction_date", "category"
        ).agg(
            sum("total_amount").alias("daily_revenue"),
            count("*").alias("daily_transaction_count"),
            avg("total_amount").alias("daily_avg_transaction"),
            max("total_amount").alias("daily_max_transaction")
        ).withColumn(
            "aggregation_level", lit("daily")
        )
        
        # Product aggregations
        product_agg = df.groupBy(
            "product_id", "product_name", "category"
        ).agg(
            sum("total_amount").alias("product_total_revenue"),
            count("*").alias("product_transaction_count"),
            avg("total_amount").alias("product_avg_transaction")
        ).withColumn(
            "aggregation_level", lit("product")
        )
        
        logger.info("Aggregations calculated successfully")
        return daily_agg, product_agg
    
    def data_quality_checks(self, df: DataFrame) -> bool:
        """
        Perform comprehensive data quality checks
        """
        logger.info("Performing data quality checks")
        
        quality_passed = True
        
        # Check 1: No negative amounts
        negative_amounts = df.filter(col("total_amount") < 0).count()
        if negative_amounts > 0:
            logger.error(f"Data quality check failed: {negative_amounts} records with negative amounts")
            quality_passed = False
        
        # Check 2: Price consistency
        price_inconsistency = df.filter(
            abs(col("total_amount") - (col("price") * col("quantity"))) > 0.01
        ).count()
        if price_inconsistency > 0:
            logger.error(f"Data quality check failed: {price_inconsistency} records with price inconsistency")
            quality_passed = False
        
        # Check 3: Valid timestamps
        invalid_timestamps = df.filter(col("extraction_timestamp").isNull()).count()
        if invalid_timestamps > 0:
            logger.error(f"Data quality check failed: {invalid_timestamps} records with invalid timestamps")
            quality_passed = False
        
        # Check 4: Data freshness (data should be from last 7 days)
        cutoff_date = datetime.now() - timedelta(days=7)
        old_data = df.filter(col("extraction_timestamp") < cutoff_date).count()
        if old_data > 0:
            logger.warning(f"Data freshness warning: {old_data} records older than 7 days")
        
        if quality_passed:
            logger.info("All data quality checks passed")
        
        return quality_passed
    
    def save_transformed_data(self, df: DataFrame, output_path: str, table_name: str, database_name: str):
        """
        Save transformed data to S3 and update Glue catalog
        """
        logger.info(f"Saving transformed data to: {output_path}")
        
        try:
            # Save to S3 as Parquet with partitioning
            df.write.mode("overwrite").partitionBy("extraction_date").parquet(output_path)
            
            # Update Glue catalog
            dynamic_frame = DynamicFrame.fromDF(df, self.glue_context, table_name)
            
            self.glue_context.write_dynamic_frame.from_catalog(
                frame=dynamic_frame,
                database=database_name,
                table_name=table_name,
                transformation_ctx=f"{table_name}_sink"
            )
            
            logger.info(f"Successfully saved {df.count()} records")
            
        except Exception as e:
            logger.error(f"Error saving transformed data: {str(e)}")
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
    
    logger.info(f"Starting transformation job: {args['JOB_NAME']}")
    logger.info(f"Environment: {args['ENVIRONMENT']}")
    
    try:
        # Initialize transformer
        transformer = SalesDataTransformer(glueContext, sc, job)
        
        # Read extracted data from Glue catalog
        source_df = transformer.read_from_catalog(
            database_name=args['DATABASE_NAME'],
            table_name="sales_extracted"
        )
        
        # Apply transformations
        cleaned_df = transformer.clean_data(source_df)
        business_rules_df = transformer.apply_business_rules(cleaned_df)
        enriched_df = transformer.enrich_data(business_rules_df)
        
        # Perform data quality checks
        if not transformer.data_quality_checks(enriched_df):
            raise Exception("Data quality checks failed")
        
        # Save main transformed dataset
        main_output_path = f"s3://{args['PROCESSED_BUCKET']}/transformed/sales_data/"
        transformer.save_transformed_data(
            enriched_df,
            main_output_path,
            "sales_transformed",
            args['DATABASE_NAME']
        )
        
        # Calculate and save aggregations
        daily_agg, product_agg = transformer.calculate_aggregations(enriched_df)
        
        # Save daily aggregations
        daily_output_path = f"s3://{args['PROCESSED_BUCKET']}/aggregated/daily_sales/"
        transformer.save_transformed_data(
            daily_agg,
            daily_output_path,
            "daily_sales_summary",
            args['DATABASE_NAME']
        )
        
        # Save product aggregations
        product_output_path = f"s3://{args['PROCESSED_BUCKET']}/aggregated/product_sales/"
        transformer.save_transformed_data(
            product_agg,
            product_output_path,
            "product_sales_summary",
            args['DATABASE_NAME']
        )
        
        logger.info("Transformation job completed successfully")
        
    except Exception as e:
        logger.error(f"Transformation job failed: {str(e)}")
        raise
    
    finally:
        job.commit()


if __name__ == "__main__":
    main()