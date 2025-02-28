terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
    mongodbatlas = {
      source  = "mongodb/mongodbatlas"
      version = "~> 1.4"
    }
  }
  required_version = ">= 1.0.0"
}

# Local variables for environment-specific configurations
locals {
  # Environment-specific MongoDB configurations
  mongodb_instance_size_map = {
    "dev"     = { instance_size = "M10", cluster_type = "REPLICASET", electable_nodes = 3 }
    "staging" = { instance_size = "M20", cluster_type = "REPLICASET", electable_nodes = 3 }
    "prod"    = { instance_size = "M30", cluster_type = "REPLICASET", electable_nodes = 3 }
  }
  
  # Default to development if environment not found
  mongodb_config = lookup(local.mongodb_instance_size_map, var.environment, local.mongodb_instance_size_map["dev"])
  
  # Environment-specific Redis configurations
  redis_instance_size_map = {
    "dev"     = "cache.t3.small"
    "staging" = "cache.t3.medium"
    "prod"    = "cache.m5.large"
  }
  
  # Common naming prefix with environment
  name_prefix = "${var.name_prefix}-${var.environment}"
  
  # Tag merging - add environment tag
  common_tags = merge(
    var.tags,
    {
      Environment = var.environment
      ManagedBy   = "Terraform"
      Service     = "Database"
    }
  )
}

# Data source to get current AWS account ID
data "aws_caller_identity" "current" {}

# Data source to get VPC details
data "aws_vpc" "selected" {
  id = var.vpc_id
}

#---------------------------------------------------------------
# MongoDB Atlas Configuration
#---------------------------------------------------------------

# Create a MongoDB Atlas Project
resource "mongodbatlas_project" "tms_project" {
  name   = "${local.name_prefix}-${var.mongodb_atlas_project_name}"
  org_id = var.mongodb_atlas_org_id
}

# Create MongoDB Atlas Cluster
resource "mongodbatlas_cluster" "tms_cluster" {
  project_id             = mongodbatlas_project.tms_project.id
  name                   = "${local.name_prefix}-mongodb-cluster"
  
  # Cluster configuration
  provider_name          = "AWS"
  provider_region_name   = "US_EAST_1" # This should be dynamic in production
  provider_instance_size_name = var.mongodb_instance_type != null ? var.mongodb_instance_type : local.mongodb_config.instance_size
  mongo_db_major_version = var.mongodb_version
  cluster_type           = local.mongodb_config.cluster_type
  
  # Replication configuration
  replication_specs {
    num_shards = 1
    regions_config {
      region_name     = "US_EAST_1" # This should be dynamic in production
      electable_nodes = local.mongodb_config.electable_nodes
      priority        = 7
      read_only_nodes = 0
    }
  }
  
  # Backup configuration
  backup_enabled               = var.mongodb_backup_enabled
  pit_enabled                  = var.mongodb_backup_enabled
  auto_scaling_disk_gb_enabled = true
  
  # Security configuration
  encryption_at_rest_provider = var.mongodb_encryption_at_rest ? "AWS" : "NONE"
}

# Create MongoDB Atlas Database User
resource "mongodbatlas_database_user" "app_user" {
  username           = var.mongodb_username
  password           = var.mongodb_password
  project_id         = mongodbatlas_project.tms_project.id
  auth_database_name = "admin"
  
  roles {
    role_name     = "readWrite"
    database_name = var.mongodb_database_name
  }
  
  scopes {
    name = mongodbatlas_cluster.tms_cluster.name
    type = "CLUSTER"
  }
}

# Setup network access for MongoDB Atlas
resource "mongodbatlas_project_ip_access_list" "app_ips" {
  for_each = toset(var.allowed_cidr_blocks)
  
  project_id = mongodbatlas_project.tms_project.id
  cidr_block = each.value
  comment    = "Allow access from application servers"
}

# Create MongoDB Atlas Network Container for VPC Peering
resource "mongodbatlas_network_container" "vpc_container" {
  project_id       = mongodbatlas_project.tms_project.id
  atlas_cidr_block = "192.168.248.0/21" # This CIDR must not overlap with VPC CIDR
  provider_name    = "AWS"
  region_name      = "US_EAST_1" # This should be dynamic in production
}

# Create VPC peering for secure MongoDB connection
resource "mongodbatlas_network_peering" "aws_peer" {
  project_id             = mongodbatlas_project.tms_project.id
  container_id           = mongodbatlas_network_container.vpc_container.id
  provider_name          = "AWS"
  route_table_cidr_block = data.aws_vpc.selected.cidr_block
  vpc_id                 = var.vpc_id
  aws_account_id         = data.aws_caller_identity.current.account_id
  region_name            = "us-east-1" # This should be dynamic in production
}

# Accept the VPC peering connection
resource "aws_vpc_peering_connection_accepter" "accept_peering" {
  vpc_peering_connection_id = mongodbatlas_network_peering.aws_peer.connection_id
  auto_accept               = true
  
  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-mongodb-peer"
    }
  )
}

# Create route table entries for VPC peering
resource "aws_route" "mongodb_routes" {
  count = length(var.private_subnet_ids)
  
  route_table_id            = data.aws_subnet.private_subnets[count.index].route_table_id
  destination_cidr_block    = mongodbatlas_network_container.vpc_container.atlas_cidr_block
  vpc_peering_connection_id = aws_vpc_peering_connection_accepter.accept_peering.vpc_peering_connection_id
}

# Get information about the private subnets
data "aws_subnet" "private_subnets" {
  count = length(var.private_subnet_ids)
  id    = var.private_subnet_ids[count.index]
}

#---------------------------------------------------------------
# AWS Security Groups
#---------------------------------------------------------------

# Create Security Group for MongoDB Atlas
resource "aws_security_group" "mongodb_sg" {
  name        = "${local.name_prefix}-mongodb-sg"
  description = "Security group for MongoDB Atlas connection"
  vpc_id      = var.vpc_id
  
  # Allow MongoDB connections (Port 27017)
  ingress {
    from_port   = 27017
    to_port     = 27017
    protocol    = "tcp"
    cidr_blocks = var.allowed_cidr_blocks
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-mongodb-sg"
    }
  )
}

# Create Security Group for Redis ElastiCache
resource "aws_security_group" "redis_sg" {
  name        = "${local.name_prefix}-redis-sg"
  description = "Security group for Redis ElastiCache"
  vpc_id      = var.vpc_id
  
  # Allow Redis connections (Port 6379)
  ingress {
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = var.allowed_cidr_blocks
  }
  
  # Add ingress rule for additional security groups if specified
  dynamic "ingress" {
    for_each = var.additional_security_group_ids
    content {
      from_port       = 6379
      to_port         = 6379
      protocol        = "tcp"
      security_groups = [ingress.value]
    }
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-redis-sg"
    }
  )
}

#---------------------------------------------------------------
# Redis ElastiCache Configuration
#---------------------------------------------------------------

# Create ElastiCache subnet group for Redis
resource "aws_elasticache_subnet_group" "redis_subnet_group" {
  name       = "${local.name_prefix}-redis-subnet-group"
  subnet_ids = var.private_subnet_ids
  
  tags = local.common_tags
}

# Create ElastiCache parameter group for Redis
resource "aws_elasticache_parameter_group" "redis_param_group" {
  name   = "${local.name_prefix}-redis-params"
  family = "redis6.x"
  
  # Example parameters - adjust based on your requirements
  parameter {
    name  = "maxmemory-policy"
    value = "volatile-lru"
  }
  
  tags = local.common_tags
}

# Create Redis ElastiCache Replication Group
resource "aws_elasticache_replication_group" "redis_cluster" {
  replication_group_id          = "${local.name_prefix}-redis"
  replication_group_description = "Redis cluster for Task Management System"
  node_type                     = var.redis_node_type != null ? var.redis_node_type : lookup(local.redis_instance_size_map, var.environment, local.redis_instance_size_map["dev"])
  port                          = 6379
  parameter_group_name          = var.redis_parameter_group_name != null ? var.redis_parameter_group_name : aws_elasticache_parameter_group.redis_param_group.name
  subnet_group_name             = aws_elasticache_subnet_group.redis_subnet_group.name
  security_group_ids            = concat([aws_security_group.redis_sg.id], var.additional_security_group_ids)
  
  # Redis version
  engine_version                = var.redis_version
  
  # High availability configuration
  automatic_failover_enabled    = var.redis_automatic_failover
  multi_az_enabled              = var.redis_multi_az
  num_cache_clusters            = 1 + var.redis_replica_count
  
  # Authentication
  auth_token                    = var.redis_auth_token
  transit_encryption_enabled    = var.redis_transit_encryption
  at_rest_encryption_enabled    = var.redis_at_rest_encryption
  
  # Backup configuration
  snapshot_retention_limit      = var.redis_backup_retention_period
  snapshot_window               = var.redis_backup_window
  maintenance_window            = var.redis_maintenance_window
  
  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-redis"
    }
  )
}

#---------------------------------------------------------------
# AWS Secrets Manager Configuration
#---------------------------------------------------------------

# For MongoDB Secret in AWS Secrets Manager
resource "aws_secretsmanager_secret" "mongodb_creds" {
  count       = var.create_secrets_manager_secret ? 1 : 0
  name        = "${local.name_prefix}/mongodb-credentials"
  description = "MongoDB Atlas credentials for Task Management System"
  kms_key_id  = var.kms_key_id
  
  tags = local.common_tags
}

resource "aws_secretsmanager_secret_version" "mongodb_creds" {
  count         = var.create_secrets_manager_secret ? 1 : 0
  secret_id     = aws_secretsmanager_secret.mongodb_creds[0].id
  secret_string = jsonencode({
    username              = var.mongodb_username
    password              = var.mongodb_password
    connection_string     = mongodbatlas_cluster.tms_cluster.connection_strings[0].standard
    srv_connection_string = mongodbatlas_cluster.tms_cluster.connection_strings[0].standard_srv
    database_name         = var.mongodb_database_name
  })
}

# For Redis Secret in AWS Secrets Manager
resource "aws_secretsmanager_secret" "redis_creds" {
  count       = var.create_secrets_manager_secret ? 1 : 0
  name        = "${local.name_prefix}/redis-credentials"
  description = "Redis ElastiCache credentials for Task Management System"
  kms_key_id  = var.kms_key_id
  
  tags = local.common_tags
}

resource "aws_secretsmanager_secret_version" "redis_creds" {
  count         = var.create_secrets_manager_secret ? 1 : 0
  secret_id     = aws_secretsmanager_secret.redis_creds[0].id
  secret_string = jsonencode({
    auth_token       = var.redis_auth_token
    primary_endpoint = aws_elasticache_replication_group.redis_cluster.primary_endpoint_address
    reader_endpoint  = aws_elasticache_replication_group.redis_cluster.reader_endpoint_address
    port             = 6379
  })
}

#---------------------------------------------------------------
# Outputs
#---------------------------------------------------------------

# MongoDB outputs
output "mongodb_connection_string" {
  description = "Connection string for MongoDB Atlas cluster"
  value       = mongodbatlas_cluster.tms_cluster.connection_strings[0].standard_srv
  sensitive   = true
}

output "mongodb_hosts" {
  description = "List of MongoDB host endpoints for application connection"
  value       = split(",", replace(mongodbatlas_cluster.tms_cluster.connection_strings[0].standard, "mongodb://", ""))
  sensitive   = true
}

output "mongodb_security_group_id" {
  description = "ID of the security group created for MongoDB access"
  value       = aws_security_group.mongodb_sg.id
}

# Redis outputs
output "redis_primary_endpoint" {
  description = "Primary endpoint for Redis replication group"
  value       = aws_elasticache_replication_group.redis_cluster.primary_endpoint_address
}

output "redis_reader_endpoint" {
  description = "Reader endpoint for Redis replication group for read operations"
  value       = aws_elasticache_replication_group.redis_cluster.reader_endpoint_address
}

output "redis_security_group_id" {
  description = "ID of the security group created for Redis access"
  value       = aws_security_group.redis_sg.id
}