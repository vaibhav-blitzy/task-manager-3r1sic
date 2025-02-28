# Basic environment variables
variable "environment" {
  description = "Defines the deployment environment (dev, staging, prod)"
  type        = string
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "taskmanagement"
}

variable "region" {
  description = "AWS region for resource deployment"
  type        = string
}

variable "tags" {
  description = "Resource tags to apply to all created resources"
  type        = map(string)
  default     = {}
}

# File attachment bucket configuration
variable "create_attachment_bucket" {
  description = "Flag to control creation of the file attachment bucket"
  type        = bool
  default     = true
}

variable "attachment_bucket_name" {
  description = "Name of the S3 bucket for file attachments"
  type        = string
  default     = null
}

variable "attachment_bucket_versioning" {
  description = "Enable versioning for file attachments"
  type        = bool
  default     = true
}

variable "attachment_bucket_lifecycle_rules" {
  description = "Lifecycle rules for the attachment bucket"
  type        = any
  default     = []
}

variable "attachment_bucket_cors_rules" {
  description = "CORS rules for the attachment bucket"
  type        = any
  default     = []
}

# Logs bucket configuration
variable "create_logs_bucket" {
  description = "Flag to control creation of the logs bucket"
  type        = bool
  default     = true
}

variable "logs_bucket_name" {
  description = "Name of the S3 bucket for logs"
  type        = string
  default     = null
}

variable "logs_retention_days" {
  description = "Number of days to retain logs"
  type        = number
  default     = 90
}

# Backup bucket configuration
variable "create_backup_bucket" {
  description = "Flag to control creation of the backup bucket"
  type        = bool
  default     = true
}

variable "backup_bucket_name" {
  description = "Name of the S3 bucket for backups"
  type        = string
  default     = null
}

variable "backup_retention_days" {
  description = "Number of days to retain backups"
  type        = number
  default     = 30
}

# Cross-region replication
variable "enable_cross_region_replication" {
  description = "Flag to enable cross-region replication for disaster recovery"
  type        = bool
  default     = false
}

variable "replication_region" {
  description = "Secondary region for cross-region replication"
  type        = string
  default     = null
}

# Encryption settings
variable "enable_bucket_encryption" {
  description = "Enable server-side encryption for all buckets"
  type        = bool
  default     = true
}

variable "kms_key_id" {
  description = "KMS key ID for bucket encryption"
  type        = string
  default     = null
}

# CloudFront configuration
variable "create_cloudfront_distribution" {
  description = "Flag to create CloudFront distribution for the attachment bucket"
  type        = bool
  default     = false
}

variable "cloudfront_price_class" {
  description = "CloudFront price class selection"
  type        = string
  default     = "PriceClass_100"
}

# VPC endpoint configuration
variable "vpc_id" {
  description = "VPC ID for S3 VPC endpoint (private access)"
  type        = string
  default     = null
}

variable "subnet_ids" {
  description = "Subnet IDs for S3 VPC endpoint"
  type        = list(string)
  default     = []
}

variable "create_vpc_endpoint" {
  description = "Flag to create a VPC endpoint for S3"
  type        = bool
  default     = false
}

# Security configuration
variable "allow_public_access" {
  description = "Control public access settings for buckets"
  type        = bool
  default     = false
}