# File storage bucket outputs
output "file_bucket_name" {
  description = "The name of the S3 bucket used for storing user file attachments"
  value       = aws_s3_bucket.file_storage.bucket
}

output "file_bucket_arn" {
  description = "The ARN of the S3 bucket used for storing user file attachments"
  value       = aws_s3_bucket.file_storage.arn
}

output "file_bucket_domain_name" {
  description = "The domain name of the S3 bucket used for direct file access if needed"
  value       = aws_s3_bucket.file_storage.bucket_regional_domain_name
}

# Static assets bucket outputs
output "static_assets_bucket_name" {
  description = "The name of the S3 bucket used for storing frontend static assets"
  value       = aws_s3_bucket.static_assets.bucket
}

output "static_assets_bucket_arn" {
  description = "The ARN of the S3 bucket used for storing frontend static assets"
  value       = aws_s3_bucket.static_assets.arn
}

# Backup bucket outputs
output "backup_bucket_name" {
  description = "The name of the S3 bucket used for storing database and system backups"
  value       = aws_s3_bucket.backups.bucket
}

output "backup_bucket_arn" {
  description = "The ARN of the S3 bucket used for storing database and system backups"
  value       = aws_s3_bucket.backups.arn
}

# CloudFront distribution outputs
output "cloudfront_distribution_id" {
  description = "The ID of the CloudFront distribution used for content delivery"
  value       = aws_cloudfront_distribution.static_assets.id
}

output "cloudfront_distribution_domain_name" {
  description = "The domain name of the CloudFront distribution for accessing static assets"
  value       = aws_cloudfront_distribution.static_assets.domain_name
}

# IAM role for file uploads
output "file_upload_iam_role_arn" {
  description = "The ARN of the IAM role used for pre-signed URL generation for file uploads"
  value       = aws_iam_role.file_upload.arn
}