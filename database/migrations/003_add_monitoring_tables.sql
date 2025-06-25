-- Migration 003: Add Monitoring Tables
-- Description: Add ETL job monitoring and logging capabilities
-- Date: 2025-01-03
-- Author: ETL Pipeline

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM schema_migrations WHERE version = 3) THEN
        RAISE NOTICE 'Migration 003 already applied, skipping...';
        RETURN;
    END IF;
    
    -- Set search path
    SET search_path TO sales_dw, public;
    
    -- Create ETL job log table
    CREATE TABLE etl_job_log (
        log_id SERIAL PRIMARY KEY,
        job_name VARCHAR(255) NOT NULL,
        job_type VARCHAR(100) NOT NULL, -- extract, transform, load
        start_timestamp TIMESTAMP NOT NULL,
        end_timestamp TIMESTAMP,
        status VARCHAR(50) NOT NULL, -- running, success, failed
        records_processed INTEGER DEFAULT 0,
        error_message TEXT,
        environment VARCHAR(50) NOT NULL,
        created_by VARCHAR(100) DEFAULT 'etl_pipeline'
    );
    
    -- Create data quality log table
    CREATE TABLE data_quality_log (
        quality_id SERIAL PRIMARY KEY,
        job_name VARCHAR(255) NOT NULL,
        table_name VARCHAR(255) NOT NULL,
        check_name VARCHAR(255) NOT NULL,
        check_type VARCHAR(100) NOT NULL, -- count, null_check, duplicate_check, business_rule
        expected_value VARCHAR(255),
        actual_value VARCHAR(255),
        status VARCHAR(50) NOT NULL, -- pass, fail, warning
        check_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        environment VARCHAR(50) NOT NULL
    );
    
    -- Create performance metrics table
    CREATE TABLE etl_performance_metrics (
        metric_id SERIAL PRIMARY KEY,
        job_name VARCHAR(255) NOT NULL,
        execution_date DATE NOT NULL,
        duration_seconds INTEGER NOT NULL,
        records_per_second DECIMAL(10,2),
        cpu_usage_percent DECIMAL(5,2),
        memory_usage_mb INTEGER,
        environment VARCHAR(50) NOT NULL,
        created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Add indexes for monitoring tables
    CREATE INDEX idx_etl_log_job_name ON etl_job_log(job_name);
    CREATE INDEX idx_etl_log_start_time ON etl_job_log(start_timestamp);
    CREATE INDEX idx_etl_log_status ON etl_job_log(status);
    CREATE INDEX idx_etl_log_environment ON etl_job_log(environment);
    
    CREATE INDEX idx_quality_log_job_name ON data_quality_log(job_name);
    CREATE INDEX idx_quality_log_table_name ON data_quality_log(table_name);
    CREATE INDEX idx_quality_log_status ON data_quality_log(status);
    CREATE INDEX idx_quality_log_timestamp ON data_quality_log(check_timestamp);
    
    CREATE INDEX idx_performance_job_name ON etl_performance_metrics(job_name);
    CREATE INDEX idx_performance_execution_date ON etl_performance_metrics(execution_date);
    
    -- Create views for monitoring
    CREATE OR REPLACE VIEW etl_job_status_summary AS
    SELECT 
        job_name,
        environment,
        COUNT(*) as total_runs,
        COUNT(CASE WHEN status = 'success' THEN 1 END) as successful_runs,
        COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_runs,
        AVG(EXTRACT(EPOCH FROM (end_timestamp - start_timestamp))) as avg_duration_seconds,
        MAX(start_timestamp) as last_run_time,
        MAX(CASE WHEN status = 'success' THEN start_timestamp END) as last_successful_run
    FROM etl_job_log
    WHERE start_timestamp >= CURRENT_DATE - INTERVAL '30 days'
    GROUP BY job_name, environment;
    
    CREATE OR REPLACE VIEW data_quality_summary AS
    SELECT 
        table_name,
        check_type,
        environment,
        COUNT(*) as total_checks,
        COUNT(CASE WHEN status = 'pass' THEN 1 END) as passed_checks,
        COUNT(CASE WHEN status = 'fail' THEN 1 END) as failed_checks,
        COUNT(CASE WHEN status = 'warning' THEN 1 END) as warning_checks,
        ROUND(COUNT(CASE WHEN status = 'pass' THEN 1 END) * 100.0 / COUNT(*), 2) as pass_rate_percent
    FROM data_quality_log
    WHERE check_timestamp >= CURRENT_DATE - INTERVAL '7 days'
    GROUP BY table_name, check_type, environment;
    
    -- Record migration
    INSERT INTO schema_migrations (version, description) 
    VALUES (3, 'Added monitoring tables for ETL job logging and data quality tracking');
    
    RAISE NOTICE 'Migration 003 completed successfully';
END $$;