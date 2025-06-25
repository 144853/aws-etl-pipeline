output "glue_job_names" {
  description = "Names of the created Glue jobs"
  value       = [for job in aws_glue_job.etl_jobs : job.name]
}

output "glue_job_arns" {
  description = "ARNs of the created Glue jobs"
  value       = [for job in aws_glue_job.etl_jobs : job.arn]
}

output "glue_database_name" {
  description = "Name of the Glue catalog database"
  value       = aws_glue_catalog_database.etl_database.name
}

output "glue_workflow_name" {
  description = "Name of the Glue workflow"
  value       = aws_glue_workflow.etl_workflow.name
}

output "glue_connection_name" {
  description = "Name of the Glue RDS connection"
  value       = length(aws_glue_connection.rds_connection) > 0 ? aws_glue_connection.rds_connection[0].name : null
}