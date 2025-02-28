# Terraform configuration for Task Management System - Development Environment
# This file defines all infrastructure resources needed for the development environment
# by instantiating shared modules with environment-specific parameters.

terraform {
  required_version = ">= 1.0.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
  
  # Store Terraform state in an S3 bucket with locking via DynamoDB
  backend "s3" {
    bucket         = "task-management-system-terraform-state"
    key            = "environments/dev/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-state-lock"
    encrypt        = true
  }
}

# Configure AWS provider for the development environment
provider "aws" {
  region = "us-east-1"
  
  default_tags {
    tags = {
      Environment = "dev"
      Project     = "task-management-system"
      ManagedBy   = "terraform"
    }
  }
}

# Define local variables for development environment configuration
locals {
  environment_name = "dev"
  
  common_tags = {
    Environment = local.environment_name
    Project     = "task-management-system"
  }
  
  # Network configuration
  vpc_cidr = "10.0.0.0/16"
  availability_zones = ["us-east-1a", "us-east-1b"]
  
  # Instance types for dev environment based on sizing guidelines from the technical specifications
  instance_types = {
    api_gateway          = "t3.small"
    auth_service         = "t3.small"
    task_service         = "t3.small"
    project_service      = "t3.small"
    notification_service = "t3.small"
    database             = "m5.large"  # MongoDB/DocumentDB
    redis                = "cache.t3.small"
  }
}

# VPC and networking infrastructure
module "vpc" {
  source = "../../modules/vpc"
  
  environment        = local.environment_name
  vpc_cidr           = local.vpc_cidr
  availability_zones = local.availability_zones
  tags               = local.common_tags
}

# ECS cluster for container orchestration
module "ecs" {
  source = "../../modules/ecs"
  
  environment      = local.environment_name
  vpc_id           = module.vpc.vpc_id
  private_subnets  = module.vpc.private_subnets
  tags             = local.common_tags
}

# MongoDB database (or DocumentDB depending on module implementation)
module "database" {
  source = "../../modules/database"
  
  environment     = local.environment_name
  vpc_id          = module.vpc.vpc_id
  private_subnets = module.vpc.private_subnets
  instance_type   = local.instance_types.database
  tags            = local.common_tags
}

# Redis cache for session management and real-time features
module "redis" {
  source = "../../modules/redis"
  
  environment     = local.environment_name
  vpc_id          = module.vpc.vpc_id
  private_subnets = module.vpc.private_subnets
  instance_type   = local.instance_types.redis
  tags            = local.common_tags
}

# S3 buckets for file storage and attachments
module "s3" {
  source = "../../modules/s3"
  
  environment = local.environment_name
  tags        = local.common_tags
}

# ECR repositories for container images of all microservices
module "ecr" {
  source = "../../modules/ecr"
  
  environment = local.environment_name
  # Define repositories for all microservices in the system
  repository_names = [
    "auth-service", 
    "task-service", 
    "project-service", 
    "notification-service", 
    "file-service", 
    "analytics-service", 
    "realtime-service"
  ]
  tags = local.common_tags
}

# IAM roles and policies for services
module "iam" {
  source = "../../modules/iam"
  
  environment = local.environment_name
  tags        = local.common_tags
}

# Application Load Balancer for routing traffic to services
module "alb" {
  source = "../../modules/alb"
  
  environment    = local.environment_name
  vpc_id         = module.vpc.vpc_id
  public_subnets = module.vpc.public_subnets
  tags           = local.common_tags
}

# Security Groups for controlling traffic between services
module "security_groups" {
  source = "../../modules/security-groups"
  
  environment = local.environment_name
  vpc_id      = module.vpc.vpc_id
  tags        = local.common_tags
}

# CloudWatch for monitoring and observability
module "cloudwatch" {
  source = "../../modules/cloudwatch"
  
  environment = local.environment_name
  tags        = local.common_tags
}

# Outputs to expose important information about created resources
output "vpc_id" {
  description = "The ID of the VPC"
  value       = module.vpc.vpc_id
}

output "ecs_cluster_name" {
  description = "The name of the ECS cluster"
  value       = module.ecs.cluster_name
}

output "database_endpoint" {
  description = "The endpoint of the MongoDB database"
  value       = module.database.endpoint
  sensitive   = true
}

output "redis_endpoint" {
  description = "The endpoint of the Redis cache"
  value       = module.redis.endpoint
  sensitive   = true
}

output "s3_bucket_name" {
  description = "The name of the S3 bucket for file storage"
  value       = module.s3.bucket_name
}

output "ecr_repository_urls" {
  description = "The URLs of the ECR repositories"
  value       = module.ecr.repository_urls
}

output "load_balancer_dns" {
  description = "The DNS name of the load balancer"
  value       = module.alb.dns_name
}