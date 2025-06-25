# Production Environment Configuration
# Terraform variables for production environment

# Basic Configuration
aws_region      = "us-east-1"
environment     = "prod"
project_name    = "etl-pipeline"
bucket_prefix   = "etl-pipeline-prod"

# S3 Configuration
s3_retention_days = 2555  # 7 years

# Networking Configuration
vpc_cidr = "10.2.0.0/16"
availability_zones = ["us-east-1a", "us-east-1b", "us-east-1c"]

# RDS Configuration
db_instance_class     = "db.r5.large"
db_allocated_storage  = 500
db_name              = "etl_db_prod"
db_username          = "etl_user"
backup_retention_period = 30

# Glue Job Configuration
glue_job_configs = {
  "extract-sales-data" = {
    script_location    = "s3://etl-pipeline-prod-scripts/extract/extract_sales_data.py"
    job_language      = "python"
    max_capacity      = 10
    timeout           = 240
    max_retries       = 3
    worker_type       = "G.1X"
    number_of_workers = 10
  }
  "transform-sales-data" = {
    script_location    = "s3://etl-pipeline-prod-scripts/transform/transform_sales_data.py"
    job_language      = "python"
    max_capacity      = 20
    timeout           = 360
    max_retries       = 3
    worker_type       = "G.1X"
    number_of_workers = 20
  }
  "load-sales-data" = {
    script_location    = "s3://etl-pipeline-prod-scripts/load/load_sales_data.py"
    job_language      = "python"
    max_capacity      = 10
    timeout           = 240
    max_retries       = 3
    worker_type       = "G.1X"
    number_of_workers = 10
  }
}

# Monitoring Configuration
log_retention_days = 90
job_duration_threshold = 7200  # 2 hours
alert_email = "prod-alerts@company.com"

# Common Tags
common_tags = {
  Environment = "prod"
  Project     = "etl-pipeline"
  Owner       = "data-engineering"
  CostCenter  = "engineering"
  ManagedBy   = "terraform"
  DataClassification = "confidential"
  BackupRequired = "true"
}