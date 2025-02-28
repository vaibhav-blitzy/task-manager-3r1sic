# AWS Configuration
aws_region               = "us-east-1"
environment              = "production"
aws_account_id           = "123456789012"

# Networking
vpc_cidr                 = "10.0.0.0/16"
availability_zones       = ["us-east-1a", "us-east-1b", "us-east-1c"]
private_subnet_cidrs     = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
public_subnet_cidrs      = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]
enable_nat_gateway       = true
single_nat_gateway       = false
create_vpc_endpoints     = true
vpc_endpoint_services    = ["s3", "ecr.api", "ecr.dkr", "logs", "cloudwatch", "secretsmanager", "monitoring"]
enable_vpc_flow_logs     = true
flow_logs_retention_days = 90

# Domain Configuration
domain_name              = "taskmanagement.example.com"
certificate_arn          = "arn:aws:acm:us-east-1:123456789012:certificate/abcdef12-3456-7890-abcd-ef1234567890"
cloudfront_enabled       = true

# Database Configuration
mongodb_instance_type       = "m5.2xlarge"
mongodb_node_count          = 5
mongodb_backup_enabled      = true
mongodb_auto_scaling_enabled = true
mongodb_atlas_project_id    = "5f9f1b9b1a1c2f1a2f2f2f2f"
database_backup_window      = "01:00-02:00"
database_maintenance_window = "Sun:02:00-Sun:03:00"

# Redis Configuration
redis_node_type                   = "cache.m5.large"
redis_replica_count               = 3
redis_automatic_failover_enabled  = true
redis_at_rest_encryption_enabled  = true
redis_transit_encryption_enabled  = true

# ECS Task Configuration - CPU Units
ecs_task_cpu = {
  api_gateway       = 1024
  auth_service      = 1024
  task_service      = 2048
  project_service   = 1024
  notification_service = 512
  file_service      = 2048
  analytics_service = 2048
  realtime_service  = 2048
}

# ECS Task Configuration - Memory Units (MB)
ecs_task_memory = {
  api_gateway       = 2048
  auth_service      = 2048
  task_service      = 4096
  project_service   = 2048
  notification_service = 1024
  file_service      = 4096
  analytics_service = 8192
  realtime_service  = 4096
}

# Auto-scaling Configuration - Minimum Capacity
min_capacity = {
  api_gateway       = 4
  auth_service      = 4
  task_service      = 6
  project_service   = 4
  notification_service = 3
  file_service      = 4
  analytics_service = 2
  realtime_service  = 4
}

# Auto-scaling Configuration - Maximum Capacity
max_capacity = {
  api_gateway       = 12
  auth_service      = 12
  task_service      = 20
  project_service   = 12
  notification_service = 10
  file_service      = 12
  analytics_service = 6
  realtime_service  = 12
}

# WAF Configuration
enable_waf = true
waf_rules  = ["AWSManagedRulesCommonRuleSet", "AWSManagedRulesKnownBadInputsRuleSet", "AWSManagedRulesSQLiRuleSet"]

# S3 Configuration
storage_bucket_name           = "task-management-prod-files"
s3_versioning_enabled         = true
s3_lifecycle_rules_enabled    = true
s3_standard_ia_transition_days = 90
s3_glacier_transition_days    = 180

# Backup and Disaster Recovery
backup_retention_days         = 30
enable_dr_region              = true
dr_region                     = "us-west-2"
enable_cross_region_replication = true
multi_az_enabled              = true

# Security
enable_encryption             = true
kms_key_id                    = "arn:aws:kms:us-east-1:123456789012:key/1234abcd-12ab-34cd-56ef-1234567890ab"

# Monitoring and Logging
enable_cloudtrail             = true
cloudwatch_retention_days     = 30
enable_guardduty              = true
health_check_path             = "/health"
health_check_interval         = 30
alarm_email                   = "alerts@example.com"
enable_performance_insights   = true

# Deployment Configuration
use_blue_green_deployment     = true

# External Service Integration
sendgrid_api_key_ssm_param    = "/task-management/production/sendgrid_api_key"
auth0_domain_ssm_param        = "/task-management/production/auth0_domain"

# Resource Tagging
tags = {
  Environment = "Production",
  Project     = "Task Management System",
  ManagedBy   = "Terraform",
  Owner       = "DevOps Team",
  CostCenter  = "CC-12345",
  Compliance  = "SOC2,GDPR"
}