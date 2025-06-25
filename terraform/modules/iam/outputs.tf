output "glue_role_arn" {
  description = "ARN of the Glue service role"
  value       = aws_iam_role.glue_role.arn
}

output "glue_role_name" {
  description = "Name of the Glue service role"
  value       = aws_iam_role.glue_role.name
}

output "lambda_role_arn" {
  description = "ARN of the Lambda execution role"
  value       = aws_iam_role.lambda_role.arn
}

output "lambda_role_name" {
  description = "Name of the Lambda execution role"
  value       = aws_iam_role.lambda_role.name
}

output "eventbridge_role_arn" {
  description = "ARN of the EventBridge role"
  value       = aws_iam_role.eventbridge_role.arn
}

output "eventbridge_role_name" {
  description = "Name of the EventBridge role"
  value       = aws_iam_role.eventbridge_role.name
}

output "developers_group_name" {
  description = "Name of the developers IAM group"
  value       = aws_iam_group.developers.name
}

output "developers_group_arn" {
  description = "ARN of the developers IAM group"
  value       = aws_iam_group.developers.arn
}