variable "aws_region" {
  description = "The AWS region to deploy production resources"
  type        = string
  default     = "us-east-1"
}

variable "aws_account_id" {
  description = "The AWS account ID where resources will be deployed"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "tags" {
  description = "Common tags to be applied to all resources"
  type        = map(string)
  default     = {
    Environment = "production"
    ManagedBy   = "terraform"
    Project     = "task-management-system"
  }
}

variable "vpc_cidr" {
  description = "CIDR block for the production VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "List of availability zones to use for resources"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b", "us-east-1c"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for the private subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for the public subnets"
  type        = list(string)
  default     = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]
}

variable "enable_nat_gateway" {
  description = "Whether to create NAT Gateways for private subnet internet access"
  type        = bool
  default     = true
}

variable "single_nat_gateway" {
  description = "Whether to use a single NAT Gateway for all private subnets"
  type        = bool
  default     = false
}

variable "mongodb_instance_type" {
  description = "Instance type for MongoDB servers"
  type        = string
  default     = "m5.2xlarge"
}

variable "mongodb_node_count" {
  description = "Number of nodes in the MongoDB cluster"
  type        = number
  default     = 5
}

variable "redis_node_type" {
  description = "Node type for Redis cache"
  type        = string
  default     = "cache.m5.large"
}

variable "redis_replica_count" {
  description = "Number of read replicas for Redis"
  type        = number
  default     = 3
}

variable "ecs_task_cpu" {
  description = "Map of CPU units for different service types"
  type        = map(number)
  default     = {
    "api_gateway"       = 1024
    "auth_service"      = 1024
    "task_service"      = 2048
    "project_service"   = 1024
    "notification_service" = 512
    "file_service"      = 2048
    "analytics_service" = 2048
    "realtime_service"  = 2048
  }
}

variable "ecs_task_memory" {
  description = "Map of memory units for different service types"
  type        = map(number)
  default     = {
    "api_gateway"       = 2048
    "auth_service"      = 2048
    "task_service"      = 4096
    "project_service"   = 2048
    "notification_service" = 1024
    "file_service"      = 4096
    "analytics_service" = 8192
    "realtime_service"  = 4096
  }
}

variable "min_capacity" {
  description = "Map of minimum task count for auto-scaling"
  type        = map(number)
  default     = {
    "api_gateway"       = 4
    "auth_service"      = 4
    "task_service"      = 6
    "project_service"   = 4
    "notification_service" = 3
    "file_service"      = 4
    "analytics_service" = 2
    "realtime_service"  = 4
  }
}

variable "max_capacity" {
  description = "Map of maximum task count for auto-scaling"
  type        = map(number)
  default     = {
    "api_gateway"       = 12
    "auth_service"      = 12
    "task_service"      = 20
    "project_service"   = 12
    "notification_service" = 10
    "file_service"      = 12
    "analytics_service" = 6
    "realtime_service"  = 12
  }
}

variable "domain_name" {
  description = "Domain name for the application"
  type        = string
  default     = "taskmanagement.example.com"
}

variable "certificate_arn" {
  description = "ARN of the SSL certificate for the domain"
  type        = string
}

variable "enable_waf" {
  description = "Whether to enable AWS WAF for the application"
  type        = bool
  default     = true
}

variable "waf_rules" {
  description = "List of WAF rule IDs to apply"
  type        = list(string)
  default     = ["AWSManagedRulesCommonRuleSet", "AWSManagedRulesKnownBadInputsRuleSet", "AWSManagedRulesSQLiRuleSet"]
}

variable "s3_versioning_enabled" {
  description = "Whether to enable versioning for S3 buckets"
  type        = bool
  default     = true
}

variable "s3_lifecycle_rules_enabled" {
  description = "Whether to enable lifecycle rules for S3 buckets"
  type        = bool
  default     = true
}

variable "s3_standard_ia_transition_days" {
  description = "Days before transitioning objects to STANDARD_IA storage class"
  type        = number
  default     = 90
}

variable "s3_glacier_transition_days" {
  description = "Days before transitioning objects to GLACIER storage class"
  type        = number
  default     = 180
}

variable "backup_retention_days" {
  description = "Number of days to retain backups"
  type        = number
  default     = 30
}

variable "enable_cloudtrail" {
  description = "Whether to enable CloudTrail for API auditing"
  type        = bool
  default     = true
}

variable "cloudwatch_retention_days" {
  description = "Number of days to retain CloudWatch logs"
  type        = number
  default     = 30
}

variable "enable_guardduty" {
  description = "Whether to enable GuardDuty for threat detection"
  type        = bool
  default     = true
}

variable "enable_dr_region" {
  description = "Whether to set up disaster recovery in a secondary region"
  type        = bool
  default     = true
}

variable "dr_region" {
  description = "The secondary region for disaster recovery"
  type        = string
  default     = "us-west-2"
}

variable "enable_cross_region_replication" {
  description = "Whether to enable cross-region replication for S3 buckets"
  type        = bool
  default     = true
}

variable "multi_az_enabled" {
  description = "Whether to enable Multi-AZ for database deployments"
  type        = bool
  default     = true
}

variable "enable_encryption" {
  description = "Whether to enable encryption for sensitive data"
  type        = bool
  default     = true
}

variable "kms_key_id" {
  description = "KMS key ID for encryption of sensitive data"
  type        = string
}

variable "health_check_path" {
  description = "Path for health check endpoints"
  type        = string
  default     = "/health"
}

variable "health_check_interval" {
  description = "Interval for health checks in seconds"
  type        = number
  default     = 30
}

variable "alarm_email" {
  description = "Email address for CloudWatch alarms"
  type        = string
}

variable "enable_performance_insights" {
  description = "Whether to enable Performance Insights for database monitoring"
  type        = bool
  default     = true
}

variable "sendgrid_api_key_ssm_param" {
  description = "SSM parameter name that contains the SendGrid API key"
  type        = string
  default     = "/task-management/production/sendgrid_api_key"
}

variable "auth0_domain_ssm_param" {
  description = "SSM parameter name that contains the Auth0 domain"
  type        = string
  default     = "/task-management/production/auth0_domain"
}