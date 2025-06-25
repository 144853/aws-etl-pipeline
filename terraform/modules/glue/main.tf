# Glue Jobs for ETL Pipeline

# Glue Catalog Database
resource "aws_glue_catalog_database" "etl_database" {
  name = "${var.project_name}_${var.environment}_database"
  
  description = "ETL pipeline database for ${var.environment}"
}

# Glue Jobs
resource "aws_glue_job" "etl_jobs" {
  for_each = var.glue_job_configs
  
  name               = "${var.project_name}-${var.environment}-${each.key}"
  role_arn          = var.glue_role_arn
  glue_version      = "4.0"
  max_capacity      = each.value.max_capacity
  timeout           = each.value.timeout
  max_retries       = each.value.max_retries
  worker_type       = each.value.worker_type
  number_of_workers = each.value.number_of_workers

  command {
    script_location = each.value.script_location
    python_version  = "3"
  }

  default_arguments = {
    "--job-language"                     = each.value.job_language
    "--job-bookmark-option"              = "job-bookmark-enable"
    "--enable-metrics"                   = "true"
    "--enable-continuous-cloudwatch-log" = "true"
    "--enable-spark-ui"                  = "true"
    "--spark-event-logs-path"            = "s3://${var.script_bucket_name}/spark-logs/"
    "--TempDir"                          = "s3://${var.script_bucket_name}/temp/"
    "--DATABASE_NAME"                    = aws_glue_catalog_database.etl_database.name
    "--DATA_BUCKET"                      = var.data_bucket_name
    "--PROCESSED_BUCKET"                 = var.processed_bucket_name
    "--ENVIRONMENT"                      = var.environment
  }

  tags = var.tags
}

# Glue Triggers for workflow automation
resource "aws_glue_trigger" "extract_trigger" {
  name = "${var.project_name}-${var.environment}-extract-trigger"
  type = "SCHEDULED"
  
  schedule = "cron(0 2 * * ? *)"  # Daily at 2 AM
  
  actions {
    job_name = aws_glue_job.etl_jobs["extract-sales-data"].name
  }
  
  tags = var.tags
}

resource "aws_glue_trigger" "transform_trigger" {
  name = "${var.project_name}-${var.environment}-transform-trigger"
  type = "CONDITIONAL"
  
  predicate {
    conditions {
      job_name = aws_glue_job.etl_jobs["extract-sales-data"].name
      logical_operator = "EQUALS"
      state = "SUCCEEDED"
    }
  }
  
  actions {
    job_name = aws_glue_job.etl_jobs["transform-sales-data"].name
  }
  
  tags = var.tags
}

resource "aws_glue_trigger" "load_trigger" {
  name = "${var.project_name}-${var.environment}-load-trigger"
  type = "CONDITIONAL"
  
  predicate {
    conditions {
      job_name = aws_glue_job.etl_jobs["transform-sales-data"].name
      logical_operator = "EQUALS"
      state = "SUCCEEDED"
    }
  }
  
  actions {
    job_name = aws_glue_job.etl_jobs["load-sales-data"].name
  }
  
  tags = var.tags
}

# Glue Workflow
resource "aws_glue_workflow" "etl_workflow" {
  name = "${var.project_name}-${var.environment}-etl-workflow"
  
  description = "ETL workflow for ${var.environment} environment"
  
  tags = var.tags
}

# Glue Connection for RDS
resource "aws_glue_connection" "rds_connection" {
  count = var.rds_endpoint != null ? 1 : 0
  
  connection_properties = {
    JDBC_CONNECTION_URL = "jdbc:postgresql://${var.rds_endpoint}:${var.rds_port}/${var.rds_database_name}"
    USERNAME           = var.rds_username
    PASSWORD           = var.rds_password
  }

  name = "${var.project_name}-${var.environment}-rds-connection"
  
  physical_connection_requirements {
    availability_zone      = var.availability_zone
    security_group_id_list = var.security_group_ids
    subnet_id             = var.subnet_id
  }
  
  tags = var.tags
}