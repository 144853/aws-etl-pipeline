output "script_bucket_name" {
  description = "Name of the scripts bucket"
  value       = aws_s3_bucket.scripts.bucket
}

output "script_bucket_arn" {
  description = "ARN of the scripts bucket"
  value       = aws_s3_bucket.scripts.arn
}

output "data_bucket_name" {
  description = "Name of the data bucket"
  value       = aws_s3_bucket.data.bucket
}

output "data_bucket_arn" {
  description = "ARN of the data bucket"
  value       = aws_s3_bucket.data.arn
}

output "processed_bucket_name" {
  description = "Name of the processed data bucket"
  value       = aws_s3_bucket.processed.bucket
}

output "processed_bucket_arn" {
  description = "ARN of the processed data bucket"
  value       = aws_s3_bucket.processed.arn
}

output "backup_bucket_name" {
  description = "Name of the backup bucket"
  value       = aws_s3_bucket.backup.bucket
}

output "backup_bucket_arn" {
  description = "ARN of the backup bucket"
  value       = aws_s3_bucket.backup.arn
}