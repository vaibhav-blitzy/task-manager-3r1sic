terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# AWS Backup vault for storing backups
resource "aws_backup_vault" "task_management_vault" {
  name        = "${var.environment}-task-management-vault"
  kms_key_arn = var.kms_key_arn
  
  tags = {
    Environment = var.environment
    Project     = "Task Management System"
    ManagedBy   = "Terraform"
  }
}

# IAM role for AWS Backup
resource "aws_iam_role" "backup_role" {
  name = "${var.environment}-aws-backup-service-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "backup.amazonaws.com"
        }
      }
    ]
  })
}

# Attach AWS managed policy for AWS Backup
resource "aws_iam_role_policy_attachment" "backup_policy" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSBackupServiceRolePolicyForBackup"
  role       = aws_iam_role.backup_role.name
}

# Attach policy for restore operations
resource "aws_iam_role_policy_attachment" "restore_policy" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSBackupServiceRolePolicyForRestores"
  role       = aws_iam_role.backup_role.name
}

# Create backup plan with multiple schedules
resource "aws_backup_plan" "task_management_backup_plan" {
  name = "${var.environment}-task-management-backup-plan"

  # Daily backup rule with 30-day retention
  rule {
    rule_name         = "daily-backup-rule"
    target_vault_name = aws_backup_vault.task_management_vault.name
    schedule          = "cron(0 3 * * ? *)" # Daily at 3:00 AM UTC
    
    lifecycle {
      delete_after = 30 # 30-day retention as specified in requirements
    }

    # Enable continuous backup for point-in-time recovery
    enable_continuous_backup = true
  }

  # Weekly backup rule with 90-day retention
  rule {
    rule_name         = "weekly-backup-rule"
    target_vault_name = aws_backup_vault.task_management_vault.name
    schedule          = "cron(0 2 ? * SUN *)" # Every Sunday at 2:00 AM UTC
    
    lifecycle {
      delete_after = 90 # 90-day retention as specified in requirements
    }
    
    # Copy to secondary region for disaster recovery if configured
    dynamic "copy_action" {
      for_each = var.enable_cross_region_backup ? [1] : []
      content {
        destination_vault_arn = var.secondary_region_vault_arn
        lifecycle {
          delete_after = 90 # Match source retention
        }
      }
    }
  }

  # Monthly backup rule with 365-day retention
  rule {
    rule_name         = "monthly-backup-rule"
    target_vault_name = aws_backup_vault.task_management_vault.name
    schedule          = "cron(0 1 1 * ? *)" # 1st day of each month at 1:00 AM UTC
    
    lifecycle {
      delete_after           = 365 # 365-day retention
      cold_storage_after     = 90  # Move to cold storage after 90 days for cost optimization
    }
    
    # Copy to secondary region for disaster recovery if configured
    dynamic "copy_action" {
      for_each = var.enable_cross_region_backup ? [1] : []
      content {
        destination_vault_arn = var.secondary_region_vault_arn
        lifecycle {
          delete_after           = 365 # Match source retention
          cold_storage_after     = 90  # Move to cold storage after 90 days
        }
      }
    }
  }

  tags = {
    Environment = var.environment
    Project     = "Task Management System"
    ManagedBy   = "Terraform"
  }
}

# Resource selection for database backups (MongoDB, Redis)
resource "aws_backup_selection" "database_backup_selection" {
  name          = "${var.environment}-database-backup-selection"
  iam_role_arn  = aws_iam_role.backup_role.arn
  plan_id       = aws_backup_plan.task_management_backup_plan.id
  
  resources = var.database_resource_arns
}

# Resource selection for storage backups (EFS, S3)
resource "aws_backup_selection" "storage_backup_selection" {
  name          = "${var.environment}-storage-backup-selection"
  iam_role_arn  = aws_iam_role.backup_role.arn
  plan_id       = aws_backup_plan.task_management_backup_plan.id
  
  resources = var.storage_resource_arns
}

# Resource selection based on tags for dynamic resources
resource "aws_backup_selection" "tagged_resource_selection" {
  name          = "${var.environment}-tagged-resource-selection"
  iam_role_arn  = aws_iam_role.backup_role.arn
  plan_id       = aws_backup_plan.task_management_backup_plan.id
  
  selection_tag {
    type  = "STRINGEQUALS"
    key   = "Backup"
    value = "true"
  }
  
  selection_tag {
    type  = "STRINGEQUALS"
    key   = "Environment"
    value = var.environment
  }
}

# Create SNS topic for backup notifications
resource "aws_sns_topic" "backup_notifications" {
  name = "${var.environment}-backup-notifications"
  
  tags = {
    Environment = var.environment
    Project     = "Task Management System"
    ManagedBy   = "Terraform"
  }
}

# Create email subscription for the SNS topic
resource "aws_sns_topic_subscription" "backup_email_subscription" {
  topic_arn = aws_sns_topic.backup_notifications.arn
  protocol  = "email"
  endpoint  = var.backup_notification_email
}

# CloudWatch Event Rule to capture AWS Backup events
resource "aws_cloudwatch_event_rule" "backup_events" {
  name        = "${var.environment}-capture-aws-backup-events"
  description = "Capture AWS Backup events and send notifications"
  
  event_pattern = jsonencode({
    source      = ["aws.backup"]
    detail_type = [
      "AWS Backup Job State Change"
    ]
  })
}

# CloudWatch Event Target for SNS notification
resource "aws_cloudwatch_event_target" "backup_events_to_sns" {
  rule      = aws_cloudwatch_event_rule.backup_events.name
  target_id = "SendToSNS"
  arn       = aws_sns_topic.backup_notifications.arn
  
  input_transformer {
    input_paths = {
      backup_job_id     = "$.detail.backupJobId"
      resource_type     = "$.detail.resourceType"
      state             = "$.detail.state"
      backup_vault_name = "$.detail.backupVaultName"
    }
    input_template = "\"AWS Backup job <backup_job_id> for resource type <resource_type> has changed state to <state>. Backup vault: <backup_vault_name>\""
  }
}

# Lambda function for backup verification
resource "aws_lambda_function" "backup_verification" {
  count           = var.enable_backup_verification ? 1 : 0
  function_name   = "${var.environment}-backup-verification"
  filename        = var.backup_verification_lambda_zip
  source_code_hash = filebase64sha256(var.backup_verification_lambda_zip)
  role            = aws_iam_role.lambda_backup_verification_role[0].arn
  handler         = "index.handler"
  runtime         = "nodejs14.x"
  timeout         = 300 # 5 minutes
  memory_size     = 512
  
  environment {
    variables = {
      BACKUP_VAULT_NAME = aws_backup_vault.task_management_vault.name
      SNS_TOPIC_ARN     = aws_sns_topic.backup_notifications.arn
    }
  }
  
  tags = {
    Environment = var.environment
    Project     = "Task Management System"
    ManagedBy   = "Terraform"
  }
}

# IAM role for Lambda backup verification
resource "aws_iam_role" "lambda_backup_verification_role" {
  count = var.enable_backup_verification ? 1 : 0
  name  = "${var.environment}-lambda-backup-verification-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# Policy for Lambda to access AWS Backup
resource "aws_iam_role_policy" "lambda_backup_verification_policy" {
  count  = var.enable_backup_verification ? 1 : 0
  name   = "${var.environment}-lambda-backup-verification-policy"
  role   = aws_iam_role.lambda_backup_verification_role[0].id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "backup:DescribeBackupVault",
          "backup:ListRecoveryPointsByBackupVault",
          "backup:DescribeRecoveryPoint"
        ]
        Effect   = "Allow"
        Resource = [
          aws_backup_vault.task_management_vault.arn,
          "${aws_backup_vault.task_management_vault.arn}/*"
        ]
      },
      {
        Action = [
          "sns:Publish"
        ]
        Effect   = "Allow"
        Resource = aws_sns_topic.backup_notifications.arn
      },
      {
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Effect   = "Allow"
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

# CloudWatch Event Rule to trigger backup verification daily
resource "aws_cloudwatch_event_rule" "daily_backup_verification" {
  count               = var.enable_backup_verification ? 1 : 0
  name                = "${var.environment}-daily-backup-verification"
  description         = "Trigger daily backup verification check"
  schedule_expression = "cron(0 8 * * ? *)" # Daily at 8:00 AM UTC
}

# CloudWatch Event Target for Lambda
resource "aws_cloudwatch_event_target" "backup_verification_target" {
  count     = var.enable_backup_verification ? 1 : 0
  rule      = aws_cloudwatch_event_rule.daily_backup_verification[0].name
  target_id = "TriggerBackupVerification"
  arn       = aws_lambda_function.backup_verification[0].arn
}

# Lambda permission to allow CloudWatch Events to invoke the function
resource "aws_lambda_permission" "allow_cloudwatch" {
  count         = var.enable_backup_verification ? 1 : 0
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.backup_verification[0].function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_backup_verification[0].arn
}

# Define variables
variable "aws_region" {
  description = "The AWS region where resources will be created"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (e.g., dev, staging, prod)"
  type        = string
}

variable "kms_key_arn" {
  description = "ARN of the KMS key used for backup encryption"
  type        = string
}

variable "enable_cross_region_backup" {
  description = "Whether to enable cross-region backup for disaster recovery"
  type        = bool
  default     = false
}

variable "secondary_region_vault_arn" {
  description = "ARN of the backup vault in the secondary region for cross-region copies"
  type        = string
  default     = ""
}

variable "database_resource_arns" {
  description = "List of ARNs for database resources to be backed up (MongoDB, Redis)"
  type        = list(string)
  default     = []
}

variable "storage_resource_arns" {
  description = "List of ARNs for storage resources to be backed up (EFS, S3)"
  type        = list(string)
  default     = []
}

variable "backup_notification_email" {
  description = "Email address to receive backup notifications"
  type        = string
}

variable "enable_backup_verification" {
  description = "Whether to enable Lambda backup verification"
  type        = bool
  default     = true
}

variable "backup_verification_lambda_zip" {
  description = "Path to the Lambda deployment package for backup verification"
  type        = string
  default     = "lambda/backup-verification.zip"
}

# Outputs
output "backup_vault_arn" {
  description = "ARN of the created backup vault for reference in other infrastructure components"
  value       = aws_backup_vault.task_management_vault.arn
}

output "backup_plan_arn" {
  description = "ARN of the backup plan for reference in other infrastructure components"
  value       = aws_backup_plan.task_management_backup_plan.arn
}

output "notification_topic_arn" {
  description = "ARN of the SNS topic for integration with other notification systems"
  value       = aws_sns_topic.backup_notifications.arn
}