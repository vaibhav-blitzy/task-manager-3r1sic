# --------------------------------------------------------------
# Task Management System - Staging Environment Configuration
# --------------------------------------------------------------

# --------------------------------------------------------------
# Environment and Region Configuration
# --------------------------------------------------------------
aws_region  = "us-east-1"
environment = "staging"

# --------------------------------------------------------------
# Network Configuration
# --------------------------------------------------------------
vpc_cidr                 = "10.1.0.0/16"
availability_zones       = ["us-east-1a", "us-east-1b", "us-east-1c"]
public_subnet_cidrs      = ["10.1.1.0/24", "10.1.2.0/24", "10.1.3.0/24"]
private_app_subnet_cidrs = ["10.1.10.0/24", "10.1.11.0/24", "10.1.12.0/24"]
private_data_subnet_cidrs = ["10.1.20.0/24", "10.1.21.0/24", "10.1.22.0/24"]
domain_name              = "staging.taskmanagement.example.com"
enable_vpc_flow_logs     = true
flow_logs_retention_days = 30
create_vpc_endpoints     = true
vpc_endpoint_services    = ["s3", "ecr.api", "ecr.dkr", "logs", "cloudwatch", "secretsmanager"]

# --------------------------------------------------------------
# ECS Cluster Configuration
# --------------------------------------------------------------
ecs_cluster_name            = "task-management-staging"
container_insights_enabled  = true
ecs_task_execution_role_name = "task-management-staging-execution"

# --------------------------------------------------------------
# Service Instance Configuration
# --------------------------------------------------------------
api_gateway_instance_count      = 2
auth_service_instance_count     = 2
task_service_instance_count     = 4
project_service_instance_count  = 2
notification_service_instance_count = 2
file_service_instance_count     = 2
analytics_service_instance_count = 2
realtime_service_instance_count  = 2

# --------------------------------------------------------------
# Container Resource Allocation
# --------------------------------------------------------------
container_cpu = {
  "api_gateway"          = 1024
  "auth_service"         = 1024
  "task_service"         = 2048
  "project_service"      = 1024
  "notification_service" = 512
  "file_service"         = 2048
  "analytics_service"    = 2048
  "realtime_service"     = 1024
}

container_memory = {
  "api_gateway"          = 2048
  "auth_service"         = 2048
  "task_service"         = 4096
  "project_service"      = 2048
  "notification_service" = 1024
  "file_service"         = 4096
  "analytics_service"    = 8192
  "realtime_service"     = 2048
}

# --------------------------------------------------------------
# Database Configuration - MongoDB
# --------------------------------------------------------------
mongodb_instance_type         = "m5.xlarge"
mongodb_instance_count        = 3
mongodb_version               = "5.0"
mongodb_disk_size_gb          = 100
mongodb_backup_enabled        = true
mongodb_auto_scaling_enabled  = true
mongodb_atlas_project_id      = "5f9f1b9b1a1c2f1a2f2f2f2f"
mongodb_username              = "app_user"
database_backup_window        = "02:00-03:00"
database_maintenance_window   = "Sun:03:00-Sun:04:00"

# --------------------------------------------------------------
# Cache Configuration - Redis
# --------------------------------------------------------------
redis_node_type                     = "cache.t3.medium"
redis_nodes                         = 2
redis_version                       = "6.x"
redis_automatic_failover_enabled    = true
redis_multi_az_enabled              = true
redis_at_rest_encryption_enabled    = true
redis_transit_encryption_enabled    = true

# --------------------------------------------------------------
# Storage and CDN Configuration
# --------------------------------------------------------------
storage_bucket_name     = "task-management-staging-files"
s3_versioning_enabled   = true
cloudfront_enabled      = true
certificate_arn         = "arn:aws:acm:us-east-1:123456789012:certificate/abcdef12-3456-7890-abcd-ef1234567890"

# --------------------------------------------------------------
# Monitoring and Logging Configuration
# --------------------------------------------------------------
log_retention_days            = 30
backup_retention_days         = 15
alarm_email                   = "staging-alerts@example.com"
enable_enhanced_monitoring    = true
enable_performance_insights   = true

# --------------------------------------------------------------
# Security Configuration
# --------------------------------------------------------------
waf_enabled = true

# --------------------------------------------------------------
# Auto-scaling Configuration
# --------------------------------------------------------------
autoscaling_enabled = true
autoscaling_parameters = {
  "api_gateway": {
    "min_capacity": 2,
    "max_capacity": 6,
    "cpu_threshold": 70,
    "memory_threshold": 70
  },
  "auth_service": {
    "min_capacity": 2,
    "max_capacity": 6,
    "cpu_threshold": 70,
    "memory_threshold": 70
  },
  "task_service": {
    "min_capacity": 4,
    "max_capacity": 12,
    "cpu_threshold": 70,
    "memory_threshold": 70
  },
  "project_service": {
    "min_capacity": 2,
    "max_capacity": 6,
    "cpu_threshold": 70,
    "memory_threshold": 70
  },
  "notification_service": {
    "min_capacity": 2,
    "max_capacity": 6,
    "cpu_threshold": 70,
    "memory_threshold": 70
  },
  "file_service": {
    "min_capacity": 2,
    "max_capacity": 6,
    "cpu_threshold": 70,
    "memory_threshold": 70
  },
  "analytics_service": {
    "min_capacity": 2,
    "max_capacity": 6,
    "cpu_threshold": 70,
    "memory_threshold": 70
  },
  "realtime_service": {
    "min_capacity": 2,
    "max_capacity": 6,
    "cpu_threshold": 70,
    "memory_threshold": 70
  }
}

# --------------------------------------------------------------
# Deployment Configuration
# --------------------------------------------------------------
use_blue_green_deployment   = true
health_check_path           = "/health"
health_check_grace_period   = 120

# --------------------------------------------------------------
# Authentication Configuration
# --------------------------------------------------------------
auth0_domain     = "dev-example.auth0.com"
auth0_client_id  = "abcdef123456"

# --------------------------------------------------------------
# Resource Tagging
# --------------------------------------------------------------
tags = {
  "Environment": "Staging",
  "Project": "Task Management System",
  "ManagedBy": "Terraform",
  "Owner": "DevOps Team"
}