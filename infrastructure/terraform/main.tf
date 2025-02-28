# Task Management System - Main Terraform Configuration
# This file sets up providers, backend configuration, and calls infrastructure modules.

terraform {
  required_version = ">= 1.2.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.16"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.1"
    }
  }

  backend "s3" {
    bucket         = "task-management-terraform-state"
    key            = "terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
  }
}

# Configure the AWS provider with region from variables
provider "aws" {
  region  = var.aws_region
  profile = var.aws_profile
}

# Define common tags to be applied to all resources
locals {
  common_tags = {
    Project     = "TaskManagementSystem"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# Networking module - Creates VPC, subnets, NAT gateways, route tables, and security groups
module "networking" {
  source = "./modules/networking"

  environment         = var.environment
  vpc_cidr            = var.vpc_cidr
  availability_zones  = var.availability_zones
  public_subnet_cidrs = var.public_subnet_cidrs
  private_subnet_cidrs = var.private_subnet_cidrs
  tags                = local.common_tags
}

# Database module - Provisions MongoDB and Redis databases for application data storage
module "database" {
  source = "./modules/database"

  environment          = var.environment
  vpc_id               = module.networking.vpc_id
  subnet_ids           = module.networking.private_subnet_ids
  mongodb_instance_type = var.mongodb_instance_type
  redis_node_type      = var.redis_node_type
  mongodb_version      = var.mongodb_version
  redis_version        = var.redis_version
  security_group_ids   = module.networking.database_security_group_ids
  tags                 = local.common_tags
}

# Storage module - Creates S3 buckets for file attachments, backups, and static assets
module "storage" {
  source = "./modules/storage"

  environment       = var.environment
  bucket_name       = var.storage_bucket_name
  lifecycle_rules   = var.storage_lifecycle_rules
  versioning_enabled = true
  tags              = local.common_tags
}

# Compute module - Sets up ECS cluster, Fargate services, load balancers, and ECR repositories
module "compute" {
  source = "./modules/compute"

  environment                   = var.environment
  vpc_id                        = module.networking.vpc_id
  public_subnet_ids             = module.networking.public_subnet_ids
  private_subnet_ids            = module.networking.private_subnet_ids
  ecs_cluster_name              = var.ecs_cluster_name
  container_insights            = var.container_insights_enabled
  ecr_repositories              = var.ecr_repository_names
  ecs_task_execution_role_name  = var.ecs_task_execution_role_name
  application_security_group_id = module.networking.application_security_group_id
  load_balancer_security_group_id = module.networking.load_balancer_security_group_id
  mongodb_connection_string     = module.database.mongodb_connection_string
  redis_connection_string       = module.database.redis_connection_string
  s3_bucket_name                = module.storage.bucket_name
  tags                          = local.common_tags
}

# Monitoring module - Configures CloudWatch, X-Ray, alarms and dashboards for system monitoring
module "monitoring" {
  source = "./modules/monitoring"

  environment       = var.environment
  vpc_id            = module.networking.vpc_id
  log_retention_days = var.log_retention_days
  alarm_email       = var.alarm_email
  ecs_cluster_name  = module.compute.ecs_cluster_name
  ecs_services      = module.compute.ecs_services
  enable_x_ray      = true
  dashboard_name    = "TaskManagementSystem-${var.environment}"
  tags              = local.common_tags
}

# CDN module - Sets up CloudFront distribution for content delivery and WAF for security
module "cdn" {
  source = "./modules/cdn"

  environment             = var.environment
  domain_name             = var.domain_name
  certificate_arn         = var.certificate_arn
  s3_bucket_id            = module.storage.bucket_id
  s3_bucket_arn           = module.storage.bucket_arn
  load_balancer_dns_name  = module.compute.load_balancer_dns_name
  load_balancer_zone_id   = module.compute.load_balancer_zone_id
  tags                    = local.common_tags
}