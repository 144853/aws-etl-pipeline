# Development Environment Configuration
# Terraform variables for dev environment

# Basic Configuration
aws_region      = "us-east-1"
environment     = "dev"
project_name    = "etl-pipeline"
bucket_prefix   = "etl-pipeline-dev"

# S3 Configuration
s3_retention_days = 30

# Networking Configuration
vpc_cidr = "10.0.0.0/16"
availability_zones = ["us-east-1a", "us-east-1b"]

# RDS Configuration
db_instance_class     = "db.t3.micro"
db_allocated_storage  = 20
db_name              = "etl_db_dev"
db_username          = "etl_user"
backup_retention_period = 3

# Glue Job Configuration
glue_job_configs = {
  "extract-sales-data" = {
    script_location    = "s3://etl-pipeline-dev-scripts/extract/extract_sales_data.py"
    job_language      = "python"
    max_capacity      = 2
    timeout           = 60
    max_retries       = 1
    worker_type       = "Standard"
    number_of_workers = 2
  }
  "transform-sales-data" = {
    script_location    = "s3://etl-pipeline-dev-scripts/transform/transform_sales_data.py"
    job_language      = "python"
    max_capacity      = 4
    timeout           = 120
    max_retries       = 2
    worker_type       = "Standard"
    number_of_workers = 4
  }
  "load-sales-data" = {
    script_location    = "s3://etl-pipeline-dev-scripts/load/load_sales_data.py"
    job_language      = "python"
    max_capacity      = 2
    timeout           = 60
    max_retries       = 1
    worker_type       = "Standard"
    number_of_workers = 2
  }
}

# Monitoring Configuration
log_retention_days = 14
job_duration_threshold = 1800  # 30 minutes
alert_email = "dev-team@company.com"

# Common Tags
common_tags = {
  Environment = "dev"
  Project     = "etl-pipeline"
  Owner       = "data-engineering"
  CostCenter  = "engineering"
  ManagedBy   = "terraform"
}