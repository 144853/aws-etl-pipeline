variable "environment" {
  description = "Environment name"
  type        = string
}

variable "project_name" {
  description = "Project name"
  type        = string
}

variable "script_bucket_name" {
  description = "S3 bucket name for Glue scripts"
  type        = string
}

variable "data_bucket_name" {
  description = "S3 bucket name for raw data"
  type        = string
}

variable "processed_bucket_name" {
  description = "S3 bucket name for processed data"
  type        = string
}

variable "glue_role_arn" {
  description = "IAM role ARN for Glue jobs"
  type        = string
  default     = ""
}

variable "glue_job_configs" {
  description = "Configuration for Glue jobs"
  type = map(object({
    script_location    = string
    job_language      = string
    max_capacity      = number
    timeout           = number
    max_retries       = number
    worker_type       = string
    number_of_workers = number
  }))
}

variable "rds_endpoint" {
  description = "RDS endpoint"
  type        = string
  default     = null
}

variable "rds_port" {
  description = "RDS port"
  type        = string
  default     = "5432"
}

variable "rds_database_name" {
  description = "RDS database name"
  type        = string
  default     = ""
}

variable "rds_username" {
  description = "RDS username"
  type        = string
  default     = ""
}

variable "rds_password" {
  description = "RDS password"
  type        = string
  default     = ""
  sensitive   = true
}

variable "availability_zone" {
  description = "Availability zone for Glue connection"
  type        = string
  default     = ""
}

variable "security_group_ids" {
  description = "Security group IDs for Glue connection"
  type        = list(string)
  default     = []
}

variable "subnet_id" {
  description = "Subnet ID for Glue connection"
  type        = string
  default     = ""
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}