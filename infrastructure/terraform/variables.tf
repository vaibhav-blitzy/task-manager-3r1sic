# -----------------------------------------------------------------------------
# Task Management System - Terraform Variables
# -----------------------------------------------------------------------------
# This file defines input variables for Terraform to configure infrastructure
# resources for the Task Management System, including networking, compute,
# database, storage, and monitoring configurations.
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# General Configuration
# -----------------------------------------------------------------------------

variable "environment" {
  description = "The deployment environment (prod, staging, dev)"
  type        = string
  default     = "dev"
}

variable "aws_region" {
  description = "The AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "name_prefix" {
  description = "Prefix to add to resource names for consistent identification"
  type        = string
  default     = "tms"
}

# -----------------------------------------------------------------------------
# Networking Configuration
# -----------------------------------------------------------------------------

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "List of availability zones to use for high availability"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

variable "waf_enabled" {
  description = "Enable AWS WAF for the application load balancer"
  type        = bool
  default     = true
}

# -----------------------------------------------------------------------------
# Database Configuration
# -----------------------------------------------------------------------------

variable "mongo_instance_type" {
  description = "Instance type for MongoDB cluster"
  type        = string
  default     = "m5.large"
}

variable "mongodb_version" {
  description = "MongoDB version to deploy"
  type        = string
  default     = "5.0"
}

variable "redis_node_type" {
  description = "Node type for Redis cluster used for caching and real-time features"
  type        = string
  default     = "cache.t3.medium"
}

variable "redis_version" {
  description = "Redis version to deploy"
  type        = string
  default     = "6.x"
}

variable "enable_multi_az" {
  description = "Enable Multi-AZ deployment for database resources"
  type        = bool
  default     = false
}

variable "backup_retention_days" {
  description = "Number of days to retain automated backups"
  type        = number
  default     = 7
}

# -----------------------------------------------------------------------------
# Compute Configuration (ECS Task Definitions)
# -----------------------------------------------------------------------------

variable "task_cpu" {
  description = "CPU units allocated to each microservice ECS task"
  type        = map(number)
  default     = {
    "api_gateway"          = 512
    "auth_service"         = 512
    "task_service"         = 1024
    "project_service"      = 512
    "notification_service" = 256
    "file_service"         = 1024
    "analytics_service"    = 1024
    "realtime_service"     = 512
  }
}

variable "task_memory" {
  description = "Memory (MB) allocated to each microservice ECS task"
  type        = map(number)
  default     = {
    "api_gateway"          = 1024
    "auth_service"         = 1024
    "task_service"         = 2048
    "project_service"      = 1024
    "notification_service" = 512
    "file_service"         = 2048
    "analytics_service"    = 4096
    "realtime_service"     = 1024
  }
}

variable "ecr_repository_urls" {
  description = "Map of service names to ECR repository URLs for container images"
  type        = map(string)
}

# -----------------------------------------------------------------------------
# Storage Configuration
# -----------------------------------------------------------------------------

variable "s3_versioning_enabled" {
  description = "Enable versioning for S3 buckets used for file storage"
  type        = bool
  default     = true
}

variable "s3_lifecycle_rules" {
  description = "Lifecycle rules for S3 buckets to manage object transitions and expirations"
  type        = list(any)
  default     = []
}

# -----------------------------------------------------------------------------
# Monitoring and Logging Configuration
# -----------------------------------------------------------------------------

variable "alarm_actions" {
  description = "List of ARNs to notify when CloudWatch alarms trigger"
  type        = list(string)
  default     = []
}

variable "log_retention_days" {
  description = "Number of days to retain CloudWatch logs"
  type        = number
  default     = 30
}