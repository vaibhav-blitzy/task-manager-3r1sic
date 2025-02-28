#--------------------------------------------------------------
# Task Management System - Staging Environment Variables
#
# This file defines all Terraform variables for the staging 
# environment configuration, providing a near-production
# environment for testing application behavior.
#--------------------------------------------------------------

#--------------------------------------------------------------
# Environment and Region Configuration
#--------------------------------------------------------------
variable "environment" {
  description = "The deployment environment name used for resource naming and tagging"
  type        = string
  default     = "staging"
}

variable "aws_region" {
  description = "AWS region where the staging environment resources will be deployed"
  type        = string
  default     = "us-east-1"
}

#--------------------------------------------------------------
# Network Configuration
#--------------------------------------------------------------
variable "vpc_cidr" {
  description = "CIDR block for the staging environment VPC"
  type        = string
  default     = "10.1.0.0/16"
}

variable "availability_zones" {
  description = "Availability zones to use for high availability in the staging environment"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b", "us-east-1c"]
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets in the staging environment"
  type        = list(string)
  default     = ["10.1.1.0/24", "10.1.2.0/24", "10.1.3.0/24"]
}

variable "private_app_subnet_cidrs" {
  description = "CIDR blocks for private application subnets in the staging environment"
  type        = list(string)
  default     = ["10.1.10.0/24", "10.1.11.0/24", "10.1.12.0/24"]
}

variable "private_data_subnet_cidrs" {
  description = "CIDR blocks for private data subnets in the staging environment"
  type        = list(string)
  default     = ["10.1.20.0/24", "10.1.21.0/24", "10.1.22.0/24"]
}

variable "domain_name" {
  description = "Domain name for the staging environment"
  type        = string
  default     = "staging.taskmanagement.example.com"
}

variable "enable_vpc_flow_logs" {
  description = "Whether to enable VPC flow logs for network monitoring"
  type        = bool
  default     = true
}

variable "flow_logs_retention_days" {
  description = "Number of days to retain VPC flow logs"
  type        = number
  default     = 30
}

variable "create_vpc_endpoints" {
  description = "Whether to create VPC endpoints for AWS services"
  type        = bool
  default     = true
}

variable "vpc_endpoint_services" {
  description = "AWS services to create VPC endpoints for"
  type        = list(string)
  default     = ["s3", "ecr.api", "ecr.dkr", "logs", "cloudwatch", "secretsmanager"]
}

#--------------------------------------------------------------
# ECS Cluster Configuration
#--------------------------------------------------------------
variable "ecs_cluster_name" {
  description = "Name of the ECS cluster for the staging environment"
  type        = string
  default     = "task-management-staging"
}

variable "container_insights_enabled" {
  description = "Whether to enable CloudWatch Container Insights for the ECS cluster"
  type        = bool
  default     = true
}

variable "ecs_task_execution_role_name" {
  description = "Name of the IAM role for ECS task execution"
  type        = string
  default     = "task-management-staging-execution"
}

#--------------------------------------------------------------
# Service Instance Configuration
#--------------------------------------------------------------
variable "api_gateway_instance_count" {
  description = "Number of API Gateway service instances to run in staging"
  type        = number
  default     = 2
}

variable "auth_service_instance_count" {
  description = "Number of Authentication service instances to run in staging"
  type        = number
  default     = 2
}

variable "task_service_instance_count" {
  description = "Number of Task service instances to run in staging"
  type        = number
  default     = 4
}

variable "project_service_instance_count" {
  description = "Number of Project service instances to run in staging"
  type        = number
  default     = 2
}

variable "notification_service_instance_count" {
  description = "Number of Notification service instances to run in staging"
  type        = number
  default     = 2
}

variable "file_service_instance_count" {
  description = "Number of File service instances to run in staging"
  type        = number
  default     = 2
}

variable "analytics_service_instance_count" {
  description = "Number of Analytics service instances to run in staging"
  type        = number
  default     = 2
}

variable "realtime_service_instance_count" {
  description = "Number of Real-time service instances to run in staging"
  type        = number
  default     = 2
}

#--------------------------------------------------------------
# Container Resource Allocation
#--------------------------------------------------------------
variable "container_cpu" {
  description = "CPU units allocated to each microservice container in staging"
  type        = map(number)
  default     = {
    "api_gateway"         = 1024
    "auth_service"        = 1024
    "task_service"        = 2048
    "project_service"     = 1024
    "notification_service" = 512
    "file_service"        = 2048
    "analytics_service"   = 2048
    "realtime_service"    = 1024
  }
}

variable "container_memory" {
  description = "Memory (MB) allocated to each microservice container in staging"
  type        = map(number)
  default     = {
    "api_gateway"         = 2048
    "auth_service"        = 2048
    "task_service"        = 4096
    "project_service"     = 2048
    "notification_service" = 1024
    "file_service"        = 4096
    "analytics_service"   = 8192
    "realtime_service"    = 2048
  }
}

#--------------------------------------------------------------
# Database Configuration - MongoDB
#--------------------------------------------------------------
variable "mongodb_instance_type" {
  description = "MongoDB instance type for the staging environment"
  type        = string
  default     = "m5.xlarge"
}

variable "mongodb_instance_count" {
  description = "Number of MongoDB instances for high availability in staging"
  type        = number
  default     = 3
}

variable "mongodb_version" {
  description = "MongoDB version to use in the staging environment"
  type        = string
  default     = "5.0"
}

variable "mongodb_disk_size_gb" {
  description = "Disk size in GB for MongoDB instances in staging"
  type        = number
  default     = 100
}

variable "mongodb_backup_enabled" {
  description = "Whether to enable automated backups for MongoDB"
  type        = bool
  default     = true
}

variable "mongodb_auto_scaling_enabled" {
  description = "Whether to enable auto-scaling for MongoDB"
  type        = bool
  default     = true
}

variable "mongodb_atlas_project_id" {
  description = "MongoDB Atlas project ID for the staging environment"
  type        = string
}

variable "mongodb_username" {
  description = "Username for MongoDB authentication"
  type        = string
  default     = "app_user"
}

variable "database_backup_window" {
  description = "Time window for database backups in UTC"
  type        = string
  default     = "02:00-03:00"
}

variable "database_maintenance_window" {
  description = "Weekly maintenance window for database instances"
  type        = string
  default     = "Sun:03:00-Sun:04:00"
}

#--------------------------------------------------------------
# Cache Configuration - Redis
#--------------------------------------------------------------
variable "redis_node_type" {
  description = "Redis node type for the staging environment"
  type        = string
  default     = "cache.t3.medium"
}

variable "redis_nodes" {
  description = "Number of Redis nodes for the staging environment"
  type        = number
  default     = 2
}

variable "redis_version" {
  description = "Redis version to use in the staging environment"
  type        = string
  default     = "6.x"
}

variable "redis_automatic_failover_enabled" {
  description = "Whether to enable automatic failover for Redis in staging"
  type        = bool
  default     = true
}

variable "redis_multi_az_enabled" {
  description = "Whether to enable Multi-AZ deployment for Redis in staging"
  type        = bool
  default     = true
}

variable "redis_at_rest_encryption_enabled" {
  description = "Whether to enable encryption at rest for Redis"
  type        = bool
  default     = true
}

variable "redis_transit_encryption_enabled" {
  description = "Whether to enable encryption in transit for Redis"
  type        = bool
  default     = true
}

#--------------------------------------------------------------
# Storage and CDN Configuration
#--------------------------------------------------------------
variable "storage_bucket_name" {
  description = "Name of the S3 bucket for file storage in staging"
  type        = string
  default     = "task-management-staging-files"
}

variable "s3_versioning_enabled" {
  description = "Whether to enable versioning for S3 buckets in staging"
  type        = bool
  default     = true
}

variable "cloudfront_enabled" {
  description = "Whether to enable CloudFront CDN for static assets in staging"
  type        = bool
  default     = true
}

variable "certificate_arn" {
  description = "ARN of the SSL certificate for the staging domain"
  type        = string
}

#--------------------------------------------------------------
# Monitoring and Logging Configuration
#--------------------------------------------------------------
variable "log_retention_days" {
  description = "Number of days to retain CloudWatch logs in staging"
  type        = number
  default     = 30
}

variable "backup_retention_days" {
  description = "Number of days to retain automated backups in staging"
  type        = number
  default     = 15
}

variable "alarm_email" {
  description = "Email address for CloudWatch alarms notifications"
  type        = string
  default     = "staging-alerts@example.com"
}

variable "enable_enhanced_monitoring" {
  description = "Whether to enable enhanced monitoring for database instances"
  type        = bool
  default     = true
}

variable "enable_performance_insights" {
  description = "Whether to enable performance insights for database instances"
  type        = bool
  default     = true
}

#--------------------------------------------------------------
# Security Configuration
#--------------------------------------------------------------
variable "waf_enabled" {
  description = "Whether to enable AWS WAF for the staging environment"
  type        = bool
  default     = true
}

#--------------------------------------------------------------
# Auto-scaling Configuration
#--------------------------------------------------------------
variable "autoscaling_enabled" {
  description = "Whether to enable auto-scaling for services in staging"
  type        = bool
  default     = true
}

variable "autoscaling_parameters" {
  description = "Auto-scaling parameters for each service in staging"
  type        = map(object({
    min_capacity    = number
    max_capacity    = number
    cpu_threshold   = number
    memory_threshold = number
  }))
  default     = {
    "api_gateway" = {
      min_capacity    = 2
      max_capacity    = 6
      cpu_threshold   = 70
      memory_threshold = 70
    }
    "auth_service" = {
      min_capacity    = 2
      max_capacity    = 6
      cpu_threshold   = 70
      memory_threshold = 70
    }
    "task_service" = {
      min_capacity    = 4
      max_capacity    = 12
      cpu_threshold   = 70
      memory_threshold = 70
    }
    "project_service" = {
      min_capacity    = 2
      max_capacity    = 6
      cpu_threshold   = 70
      memory_threshold = 70
    }
    "notification_service" = {
      min_capacity    = 2
      max_capacity    = 6
      cpu_threshold   = 70
      memory_threshold = 70
    }
    "file_service" = {
      min_capacity    = 2
      max_capacity    = 6
      cpu_threshold   = 70
      memory_threshold = 70
    }
    "analytics_service" = {
      min_capacity    = 2
      max_capacity    = 6
      cpu_threshold   = 70
      memory_threshold = 70
    }
    "realtime_service" = {
      min_capacity    = 2
      max_capacity    = 6
      cpu_threshold   = 70
      memory_threshold = 70
    }
  }
}

#--------------------------------------------------------------
# Deployment Configuration
#--------------------------------------------------------------
variable "use_blue_green_deployment" {
  description = "Whether to use blue-green deployment strategy for ECS services"
  type        = bool
  default     = true
}

variable "health_check_path" {
  description = "Path for health check endpoint used by load balancers"
  type        = string
  default     = "/health"
}

variable "health_check_grace_period" {
  description = "Grace period in seconds for health checks after task start"
  type        = number
  default     = 120
}

#--------------------------------------------------------------
# Authentication Configuration
#--------------------------------------------------------------
variable "auth0_domain" {
  description = "Auth0 domain for authentication service integration"
  type        = string
}

variable "auth0_client_id" {
  description = "Auth0 client ID for authentication service integration"
  type        = string
}

#--------------------------------------------------------------
# Resource Tagging
#--------------------------------------------------------------
variable "tags" {
  description = "Tags to apply to all resources in the staging environment"
  type        = map(string)
  default     = {
    "Environment" = "Staging"
    "Project"     = "Task Management System"
    "ManagedBy"   = "Terraform"
    "Owner"       = "DevOps Team"
  }
}