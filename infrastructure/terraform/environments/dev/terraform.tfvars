# =============================================================================
# Task Management System - Development Environment Configuration
# =============================================================================
# This file contains specific values for Terraform variables used in the
# development environment deployment of the Task Management System.
# =============================================================================

# -----------------------------------------------------------------------------
# General Configuration
# -----------------------------------------------------------------------------
aws_region  = "us-east-1"
environment = "dev"

# -----------------------------------------------------------------------------
# Networking Configuration
# -----------------------------------------------------------------------------
vpc_cidr            = "10.0.0.0/16"
availability_zones  = ["us-east-1a", "us-east-1b"]
public_subnet_cidrs = ["10.0.1.0/24", "10.0.2.0/24"]
private_subnet_cidrs = ["10.0.3.0/24", "10.0.4.0/24"]
database_subnet_cidrs = ["10.0.5.0/24", "10.0.6.0/24"]

# -----------------------------------------------------------------------------
# Service Instance Configuration
# -----------------------------------------------------------------------------
api_gateway_instance_type = "t3.small"
api_gateway_instance_count = 2
auth_service_instance_type = "t3.small"
auth_service_instance_count = 2
task_service_instance_type = "t3.small"
task_service_instance_count = 2
project_service_instance_type = "t3.small"
project_service_instance_count = 2
notification_service_instance_type = "t3.small"
notification_service_instance_count = 2
file_service_instance_type = "t3.small"
file_service_instance_count = 2
analytics_service_instance_type = "t3.small"
analytics_service_instance_count = 2
realtime_service_instance_type = "t3.small"
realtime_service_instance_count = 2

# -----------------------------------------------------------------------------
# ECS and Fargate Configuration
# -----------------------------------------------------------------------------
ecs_cluster_name = "task-management-dev"

fargate_cpu = {
  api_gateway = 1024
  auth = 1024
  task = 1024
  project = 1024
  notification = 1024
  file = 1024
  analytics = 1024
  realtime = 1024
}

fargate_memory = {
  api_gateway = 2048
  auth = 2048
  task = 2048
  project = 2048
  notification = 2048
  file = 2048
  analytics = 2048
  realtime = 2048
}

auto_scaling_min_capacity = {
  api_gateway = 2
  auth = 2
  task = 2
  project = 2
  notification = 2
  file = 2
  analytics = 2
  realtime = 2
}

auto_scaling_max_capacity = {
  api_gateway = 4
  auth = 4
  task = 4
  project = 4
  notification = 4
  file = 4
  analytics = 4
  realtime = 4
}

# -----------------------------------------------------------------------------
# Database Configuration
# -----------------------------------------------------------------------------
mongodb_instance_type = "m5.large"
mongodb_node_count = 3
documentdb_engine_version = "5.0"

# -----------------------------------------------------------------------------
# Redis Cache Configuration
# -----------------------------------------------------------------------------
redis_instance_type = "cache.t3.small"
redis_node_count = 2
elasticache_redis_engine_version = "6.x"

# -----------------------------------------------------------------------------
# DNS and Content Delivery Configuration
# -----------------------------------------------------------------------------
cloudfront_enabled = true
route53_domain_name = "dev.taskmanagement.example.com"
alb_ssl_certificate_arn = "arn:aws:acm:us-east-1:123456789012:certificate/example-cert"

# -----------------------------------------------------------------------------
# Storage Configuration
# -----------------------------------------------------------------------------
s3_attachment_bucket_name = "task-management-dev-attachments"

# -----------------------------------------------------------------------------
# Monitoring and Logging Configuration
# -----------------------------------------------------------------------------
cloudwatch_logs_retention_days = 7
enable_waf = true
enable_guardduty = true
enable_xray = true

# -----------------------------------------------------------------------------
# Backup Configuration
# -----------------------------------------------------------------------------
backup_retention_days = 7

# -----------------------------------------------------------------------------
# Resource Tagging
# -----------------------------------------------------------------------------
tags = {
  Environment = "Development"
  Project = "Task Management System"
  Owner = "DevOps Team"
  ManagedBy = "Terraform"
}