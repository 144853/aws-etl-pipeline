# Staging Environment Configuration
# Terraform variables for staging environment

# Basic Configuration
aws_region      = "us-east-1"
environment     = "staging"
project_name    = "etl-pipeline"
bucket_prefix   = "etl-pipeline-staging"

# S3 Configuration
s3_retention_days = 90

# Networking Configuration
vpc_cidr = "10.1.0.0/16"
availability_zones = ["us-east-1a", "us-east-1b", "us-east-1c"]

# RDS Configuration
db_instance_class     = "db.t3.small"
db_allocated_storage  = 50
db_name              = "etl_db_staging"
db_username          = "etl_user"
backup_retention_period = 7

# Glue Job Configuration
glue_job_configs = {
  "extract-sales-data" = {
    script_location    = "s3://etl-pipeline-staging-scripts/extract/extract_sales_data.py"
    job_language      = "python"
    max_capacity      = 4
    timeout           = 120
    max_retries       = 2
    worker_type       = "Standard"
    number_of_workers = 4
  }
  "transform-sales-data" = {
    script_location    = "s3://etl-pipeline-staging-scripts/transform/transform_sales_data.py"
    job_language      = "python"
    max_capacity      = 8
    timeout           = 180
    max_retries       = 2
    worker_type       = "Standard"
    number_of_workers = 8
  }
  "load-sales-data" = {
    script_location    = "s3://etl-pipeline-staging-scripts/load/load_sales_data.py"
    job_language      = "python"
    max_capacity      = 4
    timeout           = 120
    max_retries       = 2
    worker_type       = "Standard"
    number_of_workers = 4
  }
}

# Monitoring Configuration
log_retention_days = 30
job_duration_threshold = 3600  # 1 hour
alert_email = "staging-alerts@company.com"

# Common Tags
common_tags = {
  Environment = "staging"
  Project     = "etl-pipeline"
  Owner       = "data-engineering"
  CostCenter  = "engineering"
  ManagedBy   = "terraform"
}