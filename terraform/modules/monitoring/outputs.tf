output "sns_topic_arn" {
  description = "ARN of the SNS topic for alerts"
  value       = aws_sns_topic.alerts.arn
}

output "dashboard_url" {
  description = "URL of the CloudWatch dashboard"
  value       = "https://console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${aws_cloudwatch_dashboard.etl_dashboard.dashboard_name}"
}

output "log_group_names" {
  description = "Names of the CloudWatch log groups"
  value       = [for lg in aws_cloudwatch_log_group.glue_jobs : lg.name]
}