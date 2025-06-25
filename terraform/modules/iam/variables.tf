variable "environment" {
  description = "Environment name"
  type        = string
}

variable "project_name" {
  description = "Project name"
  type        = string
}

variable "script_bucket_arn" {
  description = "ARN of the scripts bucket"
  type        = string
}

variable "data_bucket_arn" {
  description = "ARN of the data bucket"
  type        = string
}

variable "processed_bucket_arn" {
  description = "ARN of the processed bucket"
  type        = string
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}