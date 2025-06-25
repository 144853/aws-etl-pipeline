-- Migration 002: Add Summary Tables
-- Description: Add aggregated summary tables for reporting
-- Date: 2025-01-02
-- Author: ETL Pipeline

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM schema_migrations WHERE version = 2) THEN
        RAISE NOTICE 'Migration 002 already applied, skipping...';
        RETURN;
    END IF;
    
    -- Set search path
    SET search_path TO sales_dw, public;
    
    -- Add new columns to sales_fact
    ALTER TABLE sales_fact 
    ADD COLUMN IF NOT EXISTS price_category VARCHAR(50),
    ADD COLUMN IF NOT EXISTS discount_tier VARCHAR(50),
    ADD COLUMN IF NOT EXISTS category VARCHAR(100),
    ADD COLUMN IF NOT EXISTS supplier VARCHAR(255);
    
    -- Create daily sales summary table
    CREATE TABLE daily_sales_summary (
        summary_id SERIAL PRIMARY KEY,
        extraction_date DATE NOT NULL,
        category VARCHAR(100) NOT NULL,
        daily_revenue DECIMAL(15,2) NOT NULL,
        daily_transaction_count INTEGER NOT NULL,
        daily_avg_transaction DECIMAL(12,2) NOT NULL,
        daily_max_transaction DECIMAL(12,2) NOT NULL,
        aggregation_level VARCHAR(50) DEFAULT 'daily',
        created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        
        CONSTRAINT uk_daily_summary UNIQUE (extraction_date, category)
    );
    
    -- Create product sales summary table
    CREATE TABLE product_sales_summary (
        summary_id SERIAL PRIMARY KEY,
        product_id INTEGER NOT NULL,
        product_name VARCHAR(255) NOT NULL,
        category VARCHAR(100),
        product_total_revenue DECIMAL(15,2) NOT NULL,
        product_transaction_count INTEGER NOT NULL,
        product_avg_transaction DECIMAL(12,2) NOT NULL,
        aggregation_level VARCHAR(50) DEFAULT 'product',
        created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        
        CONSTRAINT uk_product_summary UNIQUE (product_id)
    );
    
    -- Add indexes for summary tables
    CREATE INDEX idx_daily_summary_date ON daily_sales_summary(extraction_date);
    CREATE INDEX idx_daily_summary_category ON daily_sales_summary(category);
    CREATE INDEX idx_product_summary_revenue ON product_sales_summary(product_total_revenue DESC);
    
    -- Record migration
    INSERT INTO schema_migrations (version, description) 
    VALUES (2, 'Added summary tables for daily and product-level aggregations');
    
    RAISE NOTICE 'Migration 002 completed successfully';
END $$;