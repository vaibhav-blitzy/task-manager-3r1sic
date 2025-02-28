#--------------------------------------------------------------
# Task Management System - Staging Environment
#
# This is the main Terraform configuration file for the staging
# environment, which creates a production-like environment for
# pre-production validation and testing.
#--------------------------------------------------------------

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.1"
    }
  }
  backend "s3" {
    bucket         = "tms-terraform-state"
    key            = "staging/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "tms-terraform-locks"
    encrypt        = true
  }
  required_version = ">= 1.0"
}

provider "aws" {
  region = var.aws_region
  default_tags {
    tags = local.common_tags
  }
}

locals {
  common_tags = {
    Environment = var.environment
    Project     = "TaskManagementSystem"
    ManagedBy   = "Terraform"
  }
  name_prefix = "tms-${var.environment}"
}

#--------------------------------------------------------------
# Random Identifier for Unique Resource Naming
#--------------------------------------------------------------
resource "random_id" "this" {
  byte_length = 4
}

#--------------------------------------------------------------
# Network Infrastructure
#--------------------------------------------------------------
module "vpc" {
  source = "../../modules/vpc"

  name                 = "${local.name_prefix}-vpc"
  cidr                 = var.vpc_cidr
  azs                  = var.availability_zones
  public_subnets       = var.public_subnet_cidrs
  private_app_subnets  = var.private_app_subnet_cidrs
  private_data_subnets = var.private_data_subnet_cidrs
  
  enable_nat_gateway     = true
  single_nat_gateway     = false
  one_nat_gateway_per_az = true
  
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  enable_flow_log                  = var.enable_vpc_flow_logs
  flow_log_destination_type        = "cloud-watch-logs"
  flow_log_cloudwatch_log_group_retention_in_days = var.flow_logs_retention_days
  
  # VPC Endpoints for improved security and performance
  enable_s3_endpoint       = var.create_vpc_endpoints
  enable_ecr_api_endpoint  = var.create_vpc_endpoints
  enable_ecr_dkr_endpoint  = var.create_vpc_endpoints
  enable_logs_endpoint     = var.create_vpc_endpoints
  enable_cloudwatch_endpoint = var.create_vpc_endpoints
  enable_secretsmanager_endpoint = var.create_vpc_endpoints
  
  tags = var.tags
}

#--------------------------------------------------------------
# Security Groups
#--------------------------------------------------------------
module "security_groups" {
  source = "../../modules/security"
  
  name_prefix    = local.name_prefix
  vpc_id         = module.vpc.vpc_id
  environment    = var.environment
  
  # Allow internal service communication
  create_internal_services_sg     = true
  create_load_balancer_sg         = true
  create_database_sg              = true
  create_redis_sg                 = true
  
  # Define allowed CIDR blocks for ALB
  alb_ingress_cidr_blocks         = ["0.0.0.0/0"]
  
  # Reference to other security groups
  app_security_group_ids          = []
  database_security_group_ids     = []
  
  tags = var.tags
}

#--------------------------------------------------------------
# Application Load Balancer
#--------------------------------------------------------------
module "alb" {
  source = "../../modules/alb"
  
  name                = "${local.name_prefix}-alb"
  vpc_id              = module.vpc.vpc_id
  subnets             = module.vpc.public_subnets
  security_groups     = [module.security_groups.load_balancer_sg_id]
  
  # HTTPS configuration
  enable_https        = true
  certificate_arn     = var.certificate_arn
  ssl_policy          = "ELBSecurityPolicy-TLS-1-2-2017-01"
  
  # Health check settings
  health_check_path   = var.health_check_path
  health_check_timeout = 5
  health_check_interval = 30
  
  # WAF integration
  enable_waf          = var.waf_enabled
  
  # Access logs
  enable_access_logs  = true
  access_logs_bucket  = "${local.name_prefix}-alb-logs-${random_id.this.hex}"
  access_logs_prefix  = "alb-logs"
  
  tags = var.tags
}

#--------------------------------------------------------------
# WAF Configuration
#--------------------------------------------------------------
module "waf" {
  source = "../../modules/waf"
  count  = var.waf_enabled ? 1 : 0
  
  name_prefix       = local.name_prefix
  alb_arn           = module.alb.alb_arn
  
  # WAF rules
  enable_basic_rules = true
  enable_rate_limiting = true
  rate_limit_threshold = 2000
  
  tags = var.tags
}

#--------------------------------------------------------------
# ECS Cluster
#--------------------------------------------------------------
module "ecs_cluster" {
  source = "../../modules/ecs"
  
  name                      = var.ecs_cluster_name
  container_insights_enabled = var.container_insights_enabled
  capacity_providers        = ["FARGATE", "FARGATE_SPOT"]
  
  default_capacity_provider_strategy = [
    {
      capacity_provider = "FARGATE"
      weight            = 1
      base              = 1
    }
  ]
  
  tags = var.tags
}

#--------------------------------------------------------------
# IAM Roles for ECS Tasks
#--------------------------------------------------------------
module "ecs_task_execution_role" {
  source = "../../modules/iam"
  
  name_prefix           = local.name_prefix
  create_task_execution_role = true
  task_execution_role_name = var.ecs_task_execution_role_name
  
  # Additional permissions
  enable_ecr_permissions = true
  enable_logs_permissions = true
  enable_secrets_manager_permissions = true
  
  tags = var.tags
}

#--------------------------------------------------------------
# ECS Services
#--------------------------------------------------------------

# API Gateway Service
module "api_gateway_service" {
  source = "../../modules/ecs-service"
  
  name                   = "${local.name_prefix}-api-gateway"
  cluster_id             = module.ecs_cluster.cluster_id
  task_execution_role_arn = module.ecs_task_execution_role.task_execution_role_arn
  
  container_image        = "123456789012.dkr.ecr.${var.aws_region}.amazonaws.com/api-gateway:latest"
  container_cpu          = var.container_cpu["api_gateway"]
  container_memory       = var.container_memory["api_gateway"]
  desired_count          = var.api_gateway_instance_count
  
  vpc_id                 = module.vpc.vpc_id
  subnets                = module.vpc.private_app_subnets
  security_groups        = [module.security_groups.internal_services_sg_id]
  
  # Load balancer configuration
  lb_target_group_arn    = module.alb.target_groups["api-gateway"].arn
  health_check_path      = var.health_check_path
  health_check_grace_period_seconds = var.health_check_grace_period
  
  # Auto-scaling configuration
  enable_autoscaling     = var.autoscaling_enabled
  min_capacity           = var.autoscaling_parameters["api_gateway"].min_capacity
  max_capacity           = var.autoscaling_parameters["api_gateway"].max_capacity
  cpu_threshold          = var.autoscaling_parameters["api_gateway"].cpu_threshold
  memory_threshold       = var.autoscaling_parameters["api_gateway"].memory_threshold
  
  # Blue-green deployment
  enable_blue_green      = var.use_blue_green_deployment
  
  # Environment variables
  environment_variables = {
    ENVIRONMENT = var.environment
    LOG_LEVEL   = "INFO"
  }
  
  # Secret environment variables stored in AWS Secrets Manager
  secrets = [
    {
      name      = "AUTH0_DOMAIN"
      valueFrom = "arn:aws:secretsmanager:${var.aws_region}:123456789012:secret:${local.name_prefix}/auth0-domain-AbCdEf"
    },
    {
      name      = "AUTH0_CLIENT_ID"
      valueFrom = "arn:aws:secretsmanager:${var.aws_region}:123456789012:secret:${local.name_prefix}/auth0-client-id-AbCdEf"
    }
  ]
  
  tags = var.tags
}

# Authentication Service
module "auth_service" {
  source = "../../modules/ecs-service"
  
  name                   = "${local.name_prefix}-auth-service"
  cluster_id             = module.ecs_cluster.cluster_id
  task_execution_role_arn = module.ecs_task_execution_role.task_execution_role_arn
  
  container_image        = "123456789012.dkr.ecr.${var.aws_region}.amazonaws.com/auth-service:latest"
  container_cpu          = var.container_cpu["auth_service"]
  container_memory       = var.container_memory["auth_service"]
  desired_count          = var.auth_service_instance_count
  
  vpc_id                 = module.vpc.vpc_id
  subnets                = module.vpc.private_app_subnets
  security_groups        = [module.security_groups.internal_services_sg_id]
  
  # Load balancer configuration
  lb_target_group_arn    = module.alb.target_groups["auth-service"].arn
  health_check_path      = "${var.health_check_path}/auth"
  health_check_grace_period_seconds = var.health_check_grace_period
  
  # Auto-scaling configuration
  enable_autoscaling     = var.autoscaling_enabled
  min_capacity           = var.autoscaling_parameters["auth_service"].min_capacity
  max_capacity           = var.autoscaling_parameters["auth_service"].max_capacity
  cpu_threshold          = var.autoscaling_parameters["auth_service"].cpu_threshold
  memory_threshold       = var.autoscaling_parameters["auth_service"].memory_threshold
  
  # Blue-green deployment
  enable_blue_green      = var.use_blue_green_deployment
  
  # Environment variables
  environment_variables = {
    ENVIRONMENT = var.environment
    LOG_LEVEL   = "INFO"
    REDIS_HOST  = module.redis.primary_endpoint_address
    REDIS_PORT  = module.redis.primary_endpoint_port
    MONGO_URI   = "mongodb://${module.mongodb.connection_string}/auth"
  }
  
  # Secret environment variables stored in AWS Secrets Manager
  secrets = [
    {
      name      = "MONGO_USERNAME"
      valueFrom = "arn:aws:secretsmanager:${var.aws_region}:123456789012:secret:${local.name_prefix}/mongodb-username-AbCdEf"
    },
    {
      name      = "MONGO_PASSWORD"
      valueFrom = "arn:aws:secretsmanager:${var.aws_region}:123456789012:secret:${local.name_prefix}/mongodb-password-AbCdEf"
    },
    {
      name      = "AUTH0_DOMAIN"
      valueFrom = "arn:aws:secretsmanager:${var.aws_region}:123456789012:secret:${local.name_prefix}/auth0-domain-AbCdEf"
    },
    {
      name      = "AUTH0_CLIENT_ID"
      valueFrom = "arn:aws:secretsmanager:${var.aws_region}:123456789012:secret:${local.name_prefix}/auth0-client-id-AbCdEf"
    },
    {
      name      = "AUTH0_CLIENT_SECRET"
      valueFrom = "arn:aws:secretsmanager:${var.aws_region}:123456789012:secret:${local.name_prefix}/auth0-client-secret-AbCdEf"
    }
  ]
  
  tags = var.tags
}

# Task Service
module "task_service" {
  source = "../../modules/ecs-service"
  
  name                   = "${local.name_prefix}-task-service"
  cluster_id             = module.ecs_cluster.cluster_id
  task_execution_role_arn = module.ecs_task_execution_role.task_execution_role_arn
  
  container_image        = "123456789012.dkr.ecr.${var.aws_region}.amazonaws.com/task-service:latest"
  container_cpu          = var.container_cpu["task_service"]
  container_memory       = var.container_memory["task_service"]
  desired_count          = var.task_service_instance_count
  
  vpc_id                 = module.vpc.vpc_id
  subnets                = module.vpc.private_app_subnets
  security_groups        = [module.security_groups.internal_services_sg_id]
  
  # Load balancer configuration
  lb_target_group_arn    = module.alb.target_groups["task-service"].arn
  health_check_path      = "${var.health_check_path}/tasks"
  health_check_grace_period_seconds = var.health_check_grace_period
  
  # Auto-scaling configuration
  enable_autoscaling     = var.autoscaling_enabled
  min_capacity           = var.autoscaling_parameters["task_service"].min_capacity
  max_capacity           = var.autoscaling_parameters["task_service"].max_capacity
  cpu_threshold          = var.autoscaling_parameters["task_service"].cpu_threshold
  memory_threshold       = var.autoscaling_parameters["task_service"].memory_threshold
  
  # Blue-green deployment
  enable_blue_green      = var.use_blue_green_deployment
  
  # Environment variables
  environment_variables = {
    ENVIRONMENT = var.environment
    LOG_LEVEL   = "INFO"
    REDIS_HOST  = module.redis.primary_endpoint_address
    REDIS_PORT  = module.redis.primary_endpoint_port
    MONGO_URI   = "mongodb://${module.mongodb.connection_string}/tasks"
    S3_BUCKET   = module.s3_storage.bucket_name
  }
  
  # Secret environment variables stored in AWS Secrets Manager
  secrets = [
    {
      name      = "MONGO_USERNAME"
      valueFrom = "arn:aws:secretsmanager:${var.aws_region}:123456789012:secret:${local.name_prefix}/mongodb-username-AbCdEf"
    },
    {
      name      = "MONGO_PASSWORD"
      valueFrom = "arn:aws:secretsmanager:${var.aws_region}:123456789012:secret:${local.name_prefix}/mongodb-password-AbCdEf"
    }
  ]
  
  tags = var.tags
}

# Project Service
module "project_service" {
  source = "../../modules/ecs-service"
  
  name                   = "${local.name_prefix}-project-service"
  cluster_id             = module.ecs_cluster.cluster_id
  task_execution_role_arn = module.ecs_task_execution_role.task_execution_role_arn
  
  container_image        = "123456789012.dkr.ecr.${var.aws_region}.amazonaws.com/project-service:latest"
  container_cpu          = var.container_cpu["project_service"]
  container_memory       = var.container_memory["project_service"]
  desired_count          = var.project_service_instance_count
  
  vpc_id                 = module.vpc.vpc_id
  subnets                = module.vpc.private_app_subnets
  security_groups        = [module.security_groups.internal_services_sg_id]
  
  # Load balancer configuration
  lb_target_group_arn    = module.alb.target_groups["project-service"].arn
  health_check_path      = "${var.health_check_path}/projects"
  health_check_grace_period_seconds = var.health_check_grace_period
  
  # Auto-scaling configuration
  enable_autoscaling     = var.autoscaling_enabled
  min_capacity           = var.autoscaling_parameters["project_service"].min_capacity
  max_capacity           = var.autoscaling_parameters["project_service"].max_capacity
  cpu_threshold          = var.autoscaling_parameters["project_service"].cpu_threshold
  memory_threshold       = var.autoscaling_parameters["project_service"].memory_threshold
  
  # Blue-green deployment
  enable_blue_green      = var.use_blue_green_deployment
  
  # Environment variables
  environment_variables = {
    ENVIRONMENT = var.environment
    LOG_LEVEL   = "INFO"
    REDIS_HOST  = module.redis.primary_endpoint_address
    REDIS_PORT  = module.redis.primary_endpoint_port
    MONGO_URI   = "mongodb://${module.mongodb.connection_string}/projects"
  }
  
  # Secret environment variables stored in AWS Secrets Manager
  secrets = [
    {
      name      = "MONGO_USERNAME"
      valueFrom = "arn:aws:secretsmanager:${var.aws_region}:123456789012:secret:${local.name_prefix}/mongodb-username-AbCdEf"
    },
    {
      name      = "MONGO_PASSWORD"
      valueFrom = "arn:aws:secretsmanager:${var.aws_region}:123456789012:secret:${local.name_prefix}/mongodb-password-AbCdEf"
    }
  ]
  
  tags = var.tags
}

# Notification Service
module "notification_service" {
  source = "../../modules/ecs-service"
  
  name                   = "${local.name_prefix}-notification-service"
  cluster_id             = module.ecs_cluster.cluster_id
  task_execution_role_arn = module.ecs_task_execution_role.task_execution_role_arn
  
  container_image        = "123456789012.dkr.ecr.${var.aws_region}.amazonaws.com/notification-service:latest"
  container_cpu          = var.container_cpu["notification_service"]
  container_memory       = var.container_memory["notification_service"]
  desired_count          = var.notification_service_instance_count
  
  vpc_id                 = module.vpc.vpc_id
  subnets                = module.vpc.private_app_subnets
  security_groups        = [module.security_groups.internal_services_sg_id]
  
  # Load balancer configuration
  lb_target_group_arn    = module.alb.target_groups["notification-service"].arn
  health_check_path      = "${var.health_check_path}/notifications"
  health_check_grace_period_seconds = var.health_check_grace_period
  
  # Auto-scaling configuration
  enable_autoscaling     = var.autoscaling_enabled
  min_capacity           = var.autoscaling_parameters["notification_service"].min_capacity
  max_capacity           = var.autoscaling_parameters["notification_service"].max_capacity
  cpu_threshold          = var.autoscaling_parameters["notification_service"].cpu_threshold
  memory_threshold       = var.autoscaling_parameters["notification_service"].memory_threshold
  
  # Blue-green deployment
  enable_blue_green      = var.use_blue_green_deployment
  
  # Environment variables
  environment_variables = {
    ENVIRONMENT = var.environment
    LOG_LEVEL   = "INFO"
    REDIS_HOST  = module.redis.primary_endpoint_address
    REDIS_PORT  = module.redis.primary_endpoint_port
    MONGO_URI   = "mongodb://${module.mongodb.connection_string}/notifications"
  }
  
  # Secret environment variables stored in AWS Secrets Manager
  secrets = [
    {
      name      = "MONGO_USERNAME"
      valueFrom = "arn:aws:secretsmanager:${var.aws_region}:123456789012:secret:${local.name_prefix}/mongodb-username-AbCdEf"
    },
    {
      name      = "MONGO_PASSWORD"
      valueFrom = "arn:aws:secretsmanager:${var.aws_region}:123456789012:secret:${local.name_prefix}/mongodb-password-AbCdEf"
    },
    {
      name      = "SENDGRID_API_KEY"
      valueFrom = "arn:aws:secretsmanager:${var.aws_region}:123456789012:secret:${local.name_prefix}/sendgrid-api-key-AbCdEf"
    }
  ]
  
  tags = var.tags
}

# File Service
module "file_service" {
  source = "../../modules/ecs-service"
  
  name                   = "${local.name_prefix}-file-service"
  cluster_id             = module.ecs_cluster.cluster_id
  task_execution_role_arn = module.ecs_task_execution_role.task_execution_role_arn
  
  container_image        = "123456789012.dkr.ecr.${var.aws_region}.amazonaws.com/file-service:latest"
  container_cpu          = var.container_cpu["file_service"]
  container_memory       = var.container_memory["file_service"]
  desired_count          = var.file_service_instance_count
  
  vpc_id                 = module.vpc.vpc_id
  subnets                = module.vpc.private_app_subnets
  security_groups        = [module.security_groups.internal_services_sg_id]
  
  # Load balancer configuration
  lb_target_group_arn    = module.alb.target_groups["file-service"].arn
  health_check_path      = "${var.health_check_path}/files"
  health_check_grace_period_seconds = var.health_check_grace_period
  
  # Auto-scaling configuration
  enable_autoscaling     = var.autoscaling_enabled
  min_capacity           = var.autoscaling_parameters["file_service"].min_capacity
  max_capacity           = var.autoscaling_parameters["file_service"].max_capacity
  cpu_threshold          = var.autoscaling_parameters["file_service"].cpu_threshold
  memory_threshold       = var.autoscaling_parameters["file_service"].memory_threshold
  
  # Blue-green deployment
  enable_blue_green      = var.use_blue_green_deployment
  
  # Environment variables
  environment_variables = {
    ENVIRONMENT = var.environment
    LOG_LEVEL   = "INFO"
    REDIS_HOST  = module.redis.primary_endpoint_address
    REDIS_PORT  = module.redis.primary_endpoint_port
    MONGO_URI   = "mongodb://${module.mongodb.connection_string}/files"
    S3_BUCKET   = module.s3_storage.bucket_name
    CDN_DOMAIN  = var.cloudfront_enabled ? module.cloudfront[0].domain_name : ""
  }
  
  # Secret environment variables stored in AWS Secrets Manager
  secrets = [
    {
      name      = "MONGO_USERNAME"
      valueFrom = "arn:aws:secretsmanager:${var.aws_region}:123456789012:secret:${local.name_prefix}/mongodb-username-AbCdEf"
    },
    {
      name      = "MONGO_PASSWORD"
      valueFrom = "arn:aws:secretsmanager:${var.aws_region}:123456789012:secret:${local.name_prefix}/mongodb-password-AbCdEf"
    }
  ]
  
  tags = var.tags
}

# Analytics Service
module "analytics_service" {
  source = "../../modules/ecs-service"
  
  name                   = "${local.name_prefix}-analytics-service"
  cluster_id             = module.ecs_cluster.cluster_id
  task_execution_role_arn = module.ecs_task_execution_role.task_execution_role_arn
  
  container_image        = "123456789012.dkr.ecr.${var.aws_region}.amazonaws.com/analytics-service:latest"
  container_cpu          = var.container_cpu["analytics_service"]
  container_memory       = var.container_memory["analytics_service"]
  desired_count          = var.analytics_service_instance_count
  
  vpc_id                 = module.vpc.vpc_id
  subnets                = module.vpc.private_app_subnets
  security_groups        = [module.security_groups.internal_services_sg_id]
  
  # Load balancer configuration
  lb_target_group_arn    = module.alb.target_groups["analytics-service"].arn
  health_check_path      = "${var.health_check_path}/analytics"
  health_check_grace_period_seconds = var.health_check_grace_period
  
  # Auto-scaling configuration
  enable_autoscaling     = var.autoscaling_enabled
  min_capacity           = var.autoscaling_parameters["analytics_service"].min_capacity
  max_capacity           = var.autoscaling_parameters["analytics_service"].max_capacity
  cpu_threshold          = var.autoscaling_parameters["analytics_service"].cpu_threshold
  memory_threshold       = var.autoscaling_parameters["analytics_service"].memory_threshold
  
  # Blue-green deployment
  enable_blue_green      = var.use_blue_green_deployment
  
  # Environment variables
  environment_variables = {
    ENVIRONMENT = var.environment
    LOG_LEVEL   = "INFO"
    REDIS_HOST  = module.redis.primary_endpoint_address
    REDIS_PORT  = module.redis.primary_endpoint_port
    MONGO_URI   = "mongodb://${module.mongodb.connection_string}/analytics"
  }
  
  # Secret environment variables stored in AWS Secrets Manager
  secrets = [
    {
      name      = "MONGO_USERNAME"
      valueFrom = "arn:aws:secretsmanager:${var.aws_region}:123456789012:secret:${local.name_prefix}/mongodb-username-AbCdEf"
    },
    {
      name      = "MONGO_PASSWORD"
      valueFrom = "arn:aws:secretsmanager:${var.aws_region}:123456789012:secret:${local.name_prefix}/mongodb-password-AbCdEf"
    }
  ]
  
  tags = var.tags
}

# Real-time Service
module "realtime_service" {
  source = "../../modules/ecs-service"
  
  name                   = "${local.name_prefix}-realtime-service"
  cluster_id             = module.ecs_cluster.cluster_id
  task_execution_role_arn = module.ecs_task_execution_role.task_execution_role_arn
  
  container_image        = "123456789012.dkr.ecr.${var.aws_region}.amazonaws.com/realtime-service:latest"
  container_cpu          = var.container_cpu["realtime_service"]
  container_memory       = var.container_memory["realtime_service"]
  desired_count          = var.realtime_service_instance_count
  
  vpc_id                 = module.vpc.vpc_id
  subnets                = module.vpc.private_app_subnets
  security_groups        = [module.security_groups.internal_services_sg_id]
  
  # Load balancer configuration
  lb_target_group_arn    = module.alb.target_groups["realtime-service"].arn
  health_check_path      = "${var.health_check_path}/realtime"
  health_check_grace_period_seconds = var.health_check_grace_period
  
  # Auto-scaling configuration
  enable_autoscaling     = var.autoscaling_enabled
  min_capacity           = var.autoscaling_parameters["realtime_service"].min_capacity
  max_capacity           = var.autoscaling_parameters["realtime_service"].max_capacity
  cpu_threshold          = var.autoscaling_parameters["realtime_service"].cpu_threshold
  memory_threshold       = var.autoscaling_parameters["realtime_service"].memory_threshold
  
  # Blue-green deployment
  enable_blue_green      = var.use_blue_green_deployment
  
  # Environment variables
  environment_variables = {
    ENVIRONMENT = var.environment
    LOG_LEVEL   = "INFO"
    REDIS_HOST  = module.redis.primary_endpoint_address
    REDIS_PORT  = module.redis.primary_endpoint_port
    NODE_ENV    = "staging"
  }
  
  # WebSocket support
  protocol          = "HTTP"
  port              = 3000
  enable_websocket  = true
  
  tags = var.tags
}

#--------------------------------------------------------------
# MongoDB Database
#--------------------------------------------------------------
module "mongodb" {
  source = "../../modules/mongodb"
  
  name                = "${local.name_prefix}-mongodb"
  instance_type       = var.mongodb_instance_type
  instance_count      = var.mongodb_instance_count
  mongodb_version     = var.mongodb_version
  disk_size_gb        = var.mongodb_disk_size_gb
  
  # Network configuration
  vpc_id              = module.vpc.vpc_id
  subnet_ids          = module.vpc.private_data_subnets
  security_group_ids  = [module.security_groups.database_sg_id]
  
  # Backup and maintenance
  backup_enabled      = var.mongodb_backup_enabled
  backup_window       = var.database_backup_window
  maintenance_window  = var.database_maintenance_window
  
  # Monitoring
  enhanced_monitoring_enabled = var.enable_enhanced_monitoring
  
  # High availability configuration
  auto_scaling_enabled = var.mongodb_auto_scaling_enabled
  multi_az_enabled     = true
  
  # MongoDB Atlas specific configurations
  atlas_project_id    = var.mongodb_atlas_project_id
  username            = var.mongodb_username
  
  tags = var.tags
}

#--------------------------------------------------------------
# Redis Cache
#--------------------------------------------------------------
module "redis" {
  source = "../../modules/redis"
  
  name                    = "${local.name_prefix}-redis"
  node_type               = var.redis_node_type
  num_nodes               = var.redis_nodes
  redis_version           = var.redis_version
  
  # Network configuration
  vpc_id                  = module.vpc.vpc_id
  subnet_ids              = module.vpc.private_data_subnets
  security_group_ids      = [module.security_groups.redis_sg_id]
  
  # High availability configuration
  automatic_failover_enabled = var.redis_automatic_failover_enabled
  multi_az_enabled           = var.redis_multi_az_enabled
  
  # Security
  at_rest_encryption_enabled = var.redis_at_rest_encryption_enabled
  transit_encryption_enabled = var.redis_transit_encryption_enabled
  
  # Maintenance
  maintenance_window         = var.database_maintenance_window
  
  tags = var.tags
}

#--------------------------------------------------------------
# S3 Storage for Files
#--------------------------------------------------------------
module "s3_storage" {
  source = "../../modules/s3"
  
  bucket_name                 = var.storage_bucket_name
  versioning_enabled          = var.s3_versioning_enabled
  
  # Security
  block_public_access         = true
  enable_server_side_encryption = true
  
  # Lifecycle policies
  enable_lifecycle_rules      = true
  transition_to_ia_days       = 90
  transition_to_glacier_days  = 180
  expiration_days             = 365
  
  # CORS configuration for web access
  enable_cors                 = true
  allowed_origins             = ["https://${var.domain_name}"]
  allowed_methods             = ["GET", "PUT", "POST", "DELETE", "HEAD"]
  
  tags = var.tags
}

#--------------------------------------------------------------
# CloudFront CDN
#--------------------------------------------------------------
module "cloudfront" {
  source = "../../modules/cloudfront"
  count  = var.cloudfront_enabled ? 1 : 0
  
  name                = "${local.name_prefix}-cdn"
  domain_name         = var.domain_name
  s3_origin_bucket    = module.s3_storage.bucket_name
  s3_origin_path      = "/assets"
  
  # SSL/TLS configuration
  certificate_arn     = var.certificate_arn
  ssl_support_method  = "sni-only"
  minimum_protocol_version = "TLSv1.2_2019"
  
  # Cache settings
  default_ttl         = 86400    # 1 day
  max_ttl             = 31536000 # 1 year
  min_ttl             = 0
  
  # Geo restrictions
  geo_restriction_type = "none"
  
  # WAF integration
  web_acl_id          = var.waf_enabled ? module.waf[0].web_acl_id : null
  
  tags = var.tags
}

#--------------------------------------------------------------
# CloudWatch Alarms and Monitoring
#--------------------------------------------------------------
module "monitoring" {
  source = "../../modules/monitoring"
  
  name_prefix            = local.name_prefix
  environment            = var.environment
  
  # Alarm notifications
  alarm_email            = var.alarm_email
  
  # Configure monitoring for resources
  monitor_ecs_services   = true
  ecs_cluster_name       = module.ecs_cluster.cluster_name
  ecs_service_names      = [
    module.api_gateway_service.service_name,
    module.auth_service.service_name,
    module.task_service.service_name,
    module.project_service.service_name,
    module.notification_service.service_name,
    module.file_service.service_name,
    module.analytics_service.service_name,
    module.realtime_service.service_name
  ]
  
  # ALB monitoring
  monitor_alb            = true
  alb_arn                = module.alb.alb_arn
  alb_name               = module.alb.alb_name
  
  # Database monitoring
  monitor_mongodb        = true
  mongodb_identifier     = module.mongodb.identifier
  
  # Redis monitoring
  monitor_redis          = true
  redis_identifier       = module.redis.identifier
  
  # CPU and memory thresholds
  cpu_utilization_threshold = 80
  memory_utilization_threshold = 80
  
  # Error rate thresholds
  error_rate_threshold   = 5
  
  # Log retention
  log_retention_days     = var.log_retention_days
  
  tags = var.tags
}

#--------------------------------------------------------------
# Route53 DNS Configuration
#--------------------------------------------------------------
module "dns" {
  source = "../../modules/dns"
  
  domain_name         = var.domain_name
  create_alias_record = true
  alias_name          = var.domain_name
  alias_zone_id       = module.alb.alb_zone_id
  alias_target        = module.alb.alb_dns_name
  
  # Additional records
  additional_records  = var.cloudfront_enabled ? [
    {
      name  = "cdn.${var.domain_name}"
      type  = "CNAME"
      ttl   = 300
      value = module.cloudfront[0].domain_name
    }
  ] : []
  
  tags = var.tags
}

#--------------------------------------------------------------
# Outputs
#--------------------------------------------------------------
output "vpc_id" {
  description = "The ID of the VPC"
  value       = module.vpc.vpc_id
}

output "public_subnets" {
  description = "The IDs of the public subnets"
  value       = module.vpc.public_subnets
}

output "private_app_subnets" {
  description = "The IDs of the private application subnets"
  value       = module.vpc.private_app_subnets
}

output "private_data_subnets" {
  description = "The IDs of the private data subnets"
  value       = module.vpc.private_data_subnets
}

output "alb_dns_name" {
  description = "The DNS name of the application load balancer"
  value       = module.alb.alb_dns_name
}

output "ecs_cluster_name" {
  description = "The name of the ECS cluster"
  value       = module.ecs_cluster.cluster_name
}

output "mongodb_connection_string" {
  description = "The connection string for MongoDB (without credentials)"
  value       = module.mongodb.connection_string
  sensitive   = true
}

output "redis_primary_endpoint_address" {
  description = "The address of the Redis primary endpoint"
  value       = module.redis.primary_endpoint_address
}

output "storage_bucket_name" {
  description = "The name of the S3 bucket for file storage"
  value       = module.s3_storage.bucket_name
}

output "cloudfront_domain_name" {
  description = "The domain name of the CloudFront distribution"
  value       = var.cloudfront_enabled ? module.cloudfront[0].domain_name : null
}

output "domain_name" {
  description = "The domain name for the application"
  value       = var.domain_name
}