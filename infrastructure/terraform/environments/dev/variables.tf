# ----------------------------------------------------------
# AWS Provider Configuration
# ----------------------------------------------------------

variable "aws_region" {
  description = "AWS region where resources will be created"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name used for resource naming and tagging"
  type        = string
  default     = "dev"
}

# ----------------------------------------------------------
# Network Configuration
# ----------------------------------------------------------

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "List of availability zones to deploy resources"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_app_subnet_cidrs" {
  description = "CIDR blocks for private application subnets"
  type        = list(string)
  default     = ["10.0.10.0/24", "10.0.11.0/24"]
}

variable "private_data_subnet_cidrs" {
  description = "CIDR blocks for private data subnets"
  type        = list(string)
  default     = ["10.0.20.0/24", "10.0.21.0/24"]
}

# ----------------------------------------------------------
# ECS Configuration
# ----------------------------------------------------------

variable "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  type        = string
  default     = "task-management-dev"
}

variable "ecs_task_execution_role_name" {
  description = "Name of the IAM role for ECS task execution"
  type        = string
  default     = "task-management-dev-execution"
}

# ----------------------------------------------------------
# Service Instance Counts
# ----------------------------------------------------------

variable "api_gateway_instance_count" {
  description = "Number of API Gateway instances"
  type        = number
  default     = 2
}

variable "auth_service_instance_count" {
  description = "Number of Authentication Service instances"
  type        = number
  default     = 2
}

variable "task_service_instance_count" {
  description = "Number of Task Service instances"
  type        = number
  default     = 2
}

variable "project_service_instance_count" {
  description = "Number of Project Service instances"
  type        = number
  default     = 2
}

variable "notification_service_instance_count" {
  description = "Number of Notification Service instances"
  type        = number
  default     = 2
}

variable "file_service_instance_count" {
  description = "Number of File Service instances"
  type        = number
  default     = 2
}

variable "analytics_service_instance_count" {
  description = "Number of Analytics Service instances"
  type        = number
  default     = 2
}

variable "realtime_service_instance_count" {
  description = "Number of Real-time Service instances"
  type        = number
  default     = 2
}

# ----------------------------------------------------------
# Container Resource Allocations
# ----------------------------------------------------------

variable "container_cpu" {
  description = "CPU units allocation for containers (1024 units = 1 vCPU)"
  type        = map(number)
  default = {
    api_gateway         = 512
    auth_service        = 512
    task_service        = 1024
    project_service     = 512
    notification_service = 256
    file_service        = 1024
    analytics_service   = 1024
    realtime_service    = 512
  }
}

variable "container_memory" {
  description = "Memory allocation for containers in MiB"
  type        = map(number)
  default = {
    api_gateway         = 1024
    auth_service        = 1024
    task_service        = 2048
    project_service     = 1024
    notification_service = 512
    file_service        = 2048
    analytics_service   = 4096
    realtime_service    = 1024
  }
}

# ----------------------------------------------------------
# Database Configuration
# ----------------------------------------------------------

variable "mongodb_instance_type" {
  description = "Instance type for MongoDB cluster"
  type        = string
  default     = "m5.large"
}

variable "mongodb_instance_count" {
  description = "Number of MongoDB instances in the cluster"
  type        = number
  default     = 3
}

variable "redis_node_type" {
  description = "Node type for Redis instances"
  type        = string
  default     = "cache.t3.small"
}

variable "redis_nodes" {
  description = "Number of Redis nodes in the cluster"
  type        = number
  default     = 2
}

# ----------------------------------------------------------
# Storage Configuration
# ----------------------------------------------------------

variable "s3_versioning_enabled" {
  description = "Whether S3 versioning is enabled"
  type        = bool
  default     = true
}

# ----------------------------------------------------------
# CDN Configuration
# ----------------------------------------------------------

variable "cloudfront_enabled" {
  description = "Whether CloudFront distribution is enabled"
  type        = bool
  default     = true
}

# ----------------------------------------------------------
# DNS Configuration
# ----------------------------------------------------------

variable "route53_domain" {
  description = "Route53 domain for development environment"
  type        = string
  default     = "dev.taskmanagement.internal"
}

# ----------------------------------------------------------
# Backup Configuration
# ----------------------------------------------------------

variable "backup_retention_days" {
  description = "Number of days to retain backups"
  type        = number
  default     = 7
}

# ----------------------------------------------------------
# Security Configuration
# ----------------------------------------------------------

variable "waf_enabled" {
  description = "Whether AWS WAF is enabled for the development environment"
  type        = bool
  default     = true
}

# ----------------------------------------------------------
# Monitoring Configuration
# ----------------------------------------------------------

variable "alarm_notification_email" {
  description = "Email address for CloudWatch alarm notifications"
  type        = string
  default     = "dev-alerts@example.com"
}

# ----------------------------------------------------------
# Resource Tagging
# ----------------------------------------------------------

variable "tags" {
  description = "Default tags to apply to all resources"
  type        = map(string)
  default = {
    Environment = "Development"
    Project     = "Task Management System"
    ManagedBy   = "Terraform"
  }
}