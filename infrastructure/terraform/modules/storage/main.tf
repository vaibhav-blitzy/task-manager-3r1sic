terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

# File Attachments Bucket
resource "aws_s3_bucket" "attachments" {
  count  = var.create_attachment_bucket ? 1 : 0
  bucket = var.attachment_bucket_name != null ? var.attachment_bucket_name : "${var.project_name}-${var.environment}-attachments"
  
  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-attachments"
    }
  )
}

# Bucket versioning for attachments
resource "aws_s3_bucket_versioning" "attachments" {
  count  = var.create_attachment_bucket ? 1 : 0
  bucket = aws_s3_bucket.attachments[0].id
  
  versioning_configuration {
    status = var.attachment_bucket_versioning ? "Enabled" : "Suspended"
  }
}

# Server-side encryption for attachments
resource "aws_s3_bucket_server_side_encryption_configuration" "attachments" {
  count  = var.create_attachment_bucket && var.enable_bucket_encryption ? 1 : 0
  bucket = aws_s3_bucket.attachments[0].id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = var.kms_key_id != null ? "aws:kms" : "AES256"
      kms_master_key_id = var.kms_key_id
    }
  }
}

# Block public access for attachments
resource "aws_s3_bucket_public_access_block" "attachments" {
  count  = var.create_attachment_bucket ? 1 : 0
  bucket = aws_s3_bucket.attachments[0].id

  block_public_acls       = !var.allow_public_access
  block_public_policy     = !var.allow_public_access
  ignore_public_acls      = !var.allow_public_access
  restrict_public_buckets = !var.allow_public_access
}

# Lifecycle configuration for attachments
resource "aws_s3_bucket_lifecycle_configuration" "attachments" {
  count  = var.create_attachment_bucket ? 1 : 0
  bucket = aws_s3_bucket.attachments[0].id

  # If custom rules are provided, use them
  dynamic "rule" {
    for_each = var.attachment_bucket_lifecycle_rules
    content {
      id     = lookup(rule.value, "id", "rule-${rule.key}")
      status = lookup(rule.value, "status", "Enabled")

      dynamic "transition" {
        for_each = lookup(rule.value, "transitions", [])
        content {
          days          = lookup(transition.value, "days", null)
          storage_class = lookup(transition.value, "storage_class", "STANDARD_IA")
        }
      }

      dynamic "noncurrent_version_transition" {
        for_each = lookup(rule.value, "noncurrent_version_transitions", [])
        content {
          noncurrent_days = lookup(noncurrent_version_transition.value, "days", null)
          storage_class   = lookup(noncurrent_version_transition.value, "storage_class", "STANDARD_IA")
        }
      }

      dynamic "expiration" {
        for_each = lookup(rule.value, "expiration", null) != null ? [rule.value.expiration] : []
        content {
          days                         = lookup(expiration.value, "days", null)
          expired_object_delete_marker = lookup(expiration.value, "expired_object_delete_marker", null)
        }
      }
    }
  }

  # If no custom rules provided, add default rules
  dynamic "rule" {
    for_each = length(var.attachment_bucket_lifecycle_rules) == 0 ? [1] : []
    content {
      id     = "default-transition-to-ia"
      status = "Enabled"

      transition {
        days          = 90
        storage_class = "STANDARD_IA"
      }

      noncurrent_version_transition {
        noncurrent_days = 30
        storage_class   = "STANDARD_IA"
      }

      expiration {
        expired_object_delete_marker = true
      }
    }
  }
}

# CORS configuration for attachments
resource "aws_s3_bucket_cors_configuration" "attachments" {
  count  = var.create_attachment_bucket ? 1 : 0
  bucket = aws_s3_bucket.attachments[0].id

  # If custom CORS rules are provided, use them
  dynamic "cors_rule" {
    for_each = var.attachment_bucket_cors_rules
    content {
      allowed_headers = lookup(cors_rule.value, "allowed_headers", ["*"])
      allowed_methods = lookup(cors_rule.value, "allowed_methods", ["GET", "PUT", "POST"])
      allowed_origins = lookup(cors_rule.value, "allowed_origins", ["*"])
      expose_headers  = lookup(cors_rule.value, "expose_headers", ["ETag"])
      max_age_seconds = lookup(cors_rule.value, "max_age_seconds", 3000)
    }
  }

  # If no custom rules provided, add a default rule
  dynamic "cors_rule" {
    for_each = length(var.attachment_bucket_cors_rules) == 0 ? [1] : []
    content {
      allowed_headers = ["*"]
      allowed_methods = ["GET", "PUT", "POST"]
      allowed_origins = ["*"]  # Should be restricted to application domains in production
      expose_headers  = ["ETag"]
      max_age_seconds = 3000
    }
  }
}

# Replica bucket for attachments (cross-region replication)
resource "aws_s3_bucket" "attachments_replica" {
  count    = var.create_attachment_bucket && var.enable_cross_region_replication ? 1 : 0
  provider = aws.replica
  
  bucket = "${var.attachment_bucket_name != null ? var.attachment_bucket_name : "${var.project_name}-${var.environment}-attachments"}-replica"
  
  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-attachments-replica"
    }
  )
}

# Block public access for replica
resource "aws_s3_bucket_public_access_block" "attachments_replica" {
  count    = var.create_attachment_bucket && var.enable_cross_region_replication ? 1 : 0
  provider = aws.replica
  bucket   = aws_s3_bucket.attachments_replica[0].id

  block_public_acls       = !var.allow_public_access
  block_public_policy     = !var.allow_public_access
  ignore_public_acls      = !var.allow_public_access
  restrict_public_buckets = !var.allow_public_access
}

# Server-side encryption for replica
resource "aws_s3_bucket_server_side_encryption_configuration" "attachments_replica" {
  count    = var.create_attachment_bucket && var.enable_cross_region_replication && var.enable_bucket_encryption ? 1 : 0
  provider = aws.replica
  bucket   = aws_s3_bucket.attachments_replica[0].id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = var.kms_key_id != null ? "aws:kms" : "AES256"
      kms_master_key_id = var.kms_key_id
    }
  }
}

# Versioning for replica
resource "aws_s3_bucket_versioning" "attachments_replica" {
  count    = var.create_attachment_bucket && var.enable_cross_region_replication ? 1 : 0
  provider = aws.replica
  bucket   = aws_s3_bucket.attachments_replica[0].id
  
  versioning_configuration {
    status = "Enabled"
  }
}

# IAM role for replication
resource "aws_iam_role" "replication" {
  count = var.create_attachment_bucket && var.enable_cross_region_replication ? 1 : 0
  name  = "${var.project_name}-${var.environment}-s3-replication-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = "sts:AssumeRole",
        Effect = "Allow",
        Principal = {
          Service = "s3.amazonaws.com"
        }
      }
    ]
  })

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-s3-replication-role"
    }
  )
}

# IAM policy for replication
resource "aws_iam_policy" "replication" {
  count = var.create_attachment_bucket && var.enable_cross_region_replication ? 1 : 0
  name  = "${var.project_name}-${var.environment}-s3-replication-policy"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = [
          "s3:GetReplicationConfiguration",
          "s3:ListBucket"
        ],
        Effect = "Allow",
        Resource = [
          aws_s3_bucket.attachments[0].arn
        ]
      },
      {
        Action = [
          "s3:GetObjectVersionForReplication",
          "s3:GetObjectVersionAcl",
          "s3:GetObjectVersionTagging"
        ],
        Effect = "Allow",
        Resource = [
          "${aws_s3_bucket.attachments[0].arn}/*"
        ]
      },
      {
        Action = [
          "s3:ReplicateObject",
          "s3:ReplicateDelete",
          "s3:ReplicateTags"
        ],
        Effect = "Allow",
        Resource = [
          "${aws_s3_bucket.attachments_replica[0].arn}/*"
        ]
      }
    ]
  })
}

# Attach policy to role
resource "aws_iam_role_policy_attachment" "replication" {
  count      = var.create_attachment_bucket && var.enable_cross_region_replication ? 1 : 0
  role       = aws_iam_role.replication[0].name
  policy_arn = aws_iam_policy.replication[0].arn
}

# Replication configuration for attachments
resource "aws_s3_bucket_replication_configuration" "attachments" {
  count  = var.create_attachment_bucket && var.enable_cross_region_replication ? 1 : 0
  bucket = aws_s3_bucket.attachments[0].id
  role   = aws_iam_role.replication[0].arn

  rule {
    id     = "replica-all"
    status = "Enabled"

    destination {
      bucket        = aws_s3_bucket.attachments_replica[0].arn
      storage_class = "STANDARD"
    }
  }

  # Must have bucket versioning enabled first
  depends_on = [
    aws_s3_bucket_versioning.attachments
  ]
}

# Backups Bucket
resource "aws_s3_bucket" "backups" {
  count  = var.create_backup_bucket ? 1 : 0
  bucket = var.backup_bucket_name != null ? var.backup_bucket_name : "${var.project_name}-${var.environment}-backups"
  
  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-backups"
    }
  )
}

# Server-side encryption for backups
resource "aws_s3_bucket_server_side_encryption_configuration" "backups" {
  count  = var.create_backup_bucket && var.enable_bucket_encryption ? 1 : 0
  bucket = aws_s3_bucket.backups[0].id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = var.kms_key_id != null ? "aws:kms" : "AES256"
      kms_master_key_id = var.kms_key_id
    }
  }
}

# Block public access for backups
resource "aws_s3_bucket_public_access_block" "backups" {
  count  = var.create_backup_bucket ? 1 : 0
  bucket = aws_s3_bucket.backups[0].id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Lifecycle configuration for backups
resource "aws_s3_bucket_lifecycle_configuration" "backups" {
  count  = var.create_backup_bucket ? 1 : 0
  bucket = aws_s3_bucket.backups[0].id

  rule {
    id     = "backup-retention"
    status = "Enabled"

    transition {
      days          = 30
      storage_class = "GLACIER"
    }

    expiration {
      days = var.backup_retention_days
    }
  }
}

# Logs Bucket
resource "aws_s3_bucket" "logs" {
  count  = var.create_logs_bucket ? 1 : 0
  bucket = var.logs_bucket_name != null ? var.logs_bucket_name : "${var.project_name}-${var.environment}-logs"
  
  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-logs"
    }
  )
}

# Server-side encryption for logs
resource "aws_s3_bucket_server_side_encryption_configuration" "logs" {
  count  = var.create_logs_bucket && var.enable_bucket_encryption ? 1 : 0
  bucket = aws_s3_bucket.logs[0].id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = var.kms_key_id != null ? "aws:kms" : "AES256"
      kms_master_key_id = var.kms_key_id
    }
  }
}

# Block public access for logs
resource "aws_s3_bucket_public_access_block" "logs" {
  count  = var.create_logs_bucket ? 1 : 0
  bucket = aws_s3_bucket.logs[0].id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Lifecycle configuration for logs
resource "aws_s3_bucket_lifecycle_configuration" "logs" {
  count  = var.create_logs_bucket ? 1 : 0
  bucket = aws_s3_bucket.logs[0].id

  rule {
    id     = "log-retention"
    status = "Enabled"

    transition {
      days          = 30
      storage_class = "GLACIER"
    }

    expiration {
      days = var.logs_retention_days
    }
  }
}

# Static Assets Bucket
resource "aws_s3_bucket" "static" {
  bucket = "${var.project_name}-${var.environment}-static"
  
  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-static"
    }
  )
}

# Server-side encryption for static
resource "aws_s3_bucket_server_side_encryption_configuration" "static" {
  count  = var.enable_bucket_encryption ? 1 : 0
  bucket = aws_s3_bucket.static.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = var.kms_key_id != null ? "aws:kms" : "AES256"
      kms_master_key_id = var.kms_key_id
    }
  }
}

# Block public access for static
resource "aws_s3_bucket_public_access_block" "static" {
  bucket = aws_s3_bucket.static.id

  block_public_acls       = true
  block_public_policy     = !var.allow_public_access
  ignore_public_acls      = true
  restrict_public_buckets = !var.allow_public_access
}

# CORS configuration for static
resource "aws_s3_bucket_cors_configuration" "static" {
  bucket = aws_s3_bucket.static.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET"]
    allowed_origins = ["*"]  # Should be restricted to application domains in production
    expose_headers  = ["ETag"]
    max_age_seconds = 3000
  }
}

# Module outputs
output "attachment_bucket_id" {
  description = "ID of the file attachments S3 bucket"
  value       = var.create_attachment_bucket ? aws_s3_bucket.attachments[0].id : null
}

output "attachment_bucket_arn" {
  description = "ARN of the file attachments S3 bucket"
  value       = var.create_attachment_bucket ? aws_s3_bucket.attachments[0].arn : null
}

output "backup_bucket_id" {
  description = "ID of the backups S3 bucket"
  value       = var.create_backup_bucket ? aws_s3_bucket.backups[0].id : null
}

output "backup_bucket_arn" {
  description = "ARN of the backups S3 bucket"
  value       = var.create_backup_bucket ? aws_s3_bucket.backups[0].arn : null
}

output "logs_bucket_id" {
  description = "ID of the logs S3 bucket"
  value       = var.create_logs_bucket ? aws_s3_bucket.logs[0].id : null
}

output "logs_bucket_arn" {
  description = "ARN of the logs S3 bucket"
  value       = var.create_logs_bucket ? aws_s3_bucket.logs[0].arn : null
}

output "static_bucket_id" {
  description = "ID of the static assets S3 bucket"
  value       = aws_s3_bucket.static.id
}

output "static_bucket_arn" {
  description = "ARN of the static assets S3 bucket"
  value       = aws_s3_bucket.static.arn
}