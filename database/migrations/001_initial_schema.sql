-- Migration 001: Initial Schema Creation
-- Description: Create initial database schema for sales data warehouse
-- Date: 2025-01-01
-- Author: ETL Pipeline

-- Migration metadata
CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    description TEXT NOT NULL,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    applied_by VARCHAR(100) DEFAULT CURRENT_USER
);

-- Check if this migration has already been applied
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM schema_migrations WHERE version = 1) THEN
        RAISE NOTICE 'Migration 001 already applied, skipping...';
        RETURN;
    END IF;
    
    -- Create schemas
    CREATE SCHEMA IF NOT EXISTS sales_dw;
    CREATE SCHEMA IF NOT EXISTS staging;
    
    -- Set search path
    SET search_path TO sales_dw, public;
    
    -- Create base tables
    CREATE TABLE product_dim (
        product_id INTEGER PRIMARY KEY,
        product_name VARCHAR(255) NOT NULL,
        category VARCHAR(100),
        supplier VARCHAR(255),
        price_category VARCHAR(50),
        created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_active BOOLEAN DEFAULT TRUE
    );
    
    CREATE TABLE date_dim (
        date_key DATE PRIMARY KEY,
        year INTEGER NOT NULL,
        month INTEGER NOT NULL,
        day INTEGER NOT NULL,
        quarter INTEGER NOT NULL,
        month_name VARCHAR(20) NOT NULL,
        day_of_week INTEGER NOT NULL,
        day_name VARCHAR(20) NOT NULL,
        is_weekend BOOLEAN DEFAULT FALSE,
        is_holiday BOOLEAN DEFAULT FALSE
    );
    
    CREATE TABLE sales_fact (
        sales_id SERIAL PRIMARY KEY,
        product_id INTEGER NOT NULL,
        product_name VARCHAR(255) NOT NULL,
        price DECIMAL(10,2) NOT NULL,
        quantity INTEGER NOT NULL,
        total_amount DECIMAL(12,2) NOT NULL,
        extraction_timestamp TIMESTAMP NOT NULL,
        extraction_date DATE NOT NULL,
        load_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        record_hash VARCHAR(64) NOT NULL,
        is_active BOOLEAN DEFAULT TRUE,
        created_by VARCHAR(100) DEFAULT 'etl_pipeline'
    );
    
    -- Add constraints
    ALTER TABLE sales_fact ADD CONSTRAINT fk_sales_date 
        FOREIGN KEY (extraction_date) REFERENCES date_dim(date_key);
    
    ALTER TABLE sales_fact ADD CONSTRAINT chk_positive_price 
        CHECK (price >= 0);
    
    ALTER TABLE sales_fact ADD CONSTRAINT chk_positive_quantity 
        CHECK (quantity >= 0);
    
    ALTER TABLE sales_fact ADD CONSTRAINT chk_positive_total 
        CHECK (total_amount >= 0);
    
    -- Create basic indexes
    CREATE INDEX idx_sales_fact_product_id ON sales_fact(product_id);
    CREATE INDEX idx_sales_fact_extraction_date ON sales_fact(extraction_date);
    CREATE INDEX idx_sales_fact_load_timestamp ON sales_fact(load_timestamp);
    
    -- Record migration
    INSERT INTO schema_migrations (version, description) 
    VALUES (1, 'Initial schema creation with basic tables and constraints');
    
    RAISE NOTICE 'Migration 001 completed successfully';
END $$;