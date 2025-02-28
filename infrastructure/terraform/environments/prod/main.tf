# main.tf for Task Management System Production Environment

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
    key            = "production/terraform.tfstate"
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

provider "aws" {
  alias  = "dr_region"
  region = var.dr_region
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

# Random string for unique resource naming
resource "random_string" "suffix" {
  length  = 8
  special = false
  upper   = false
}

# VPC and Networking Module
module "vpc" {
  source = "../../modules/vpc"

  name_prefix          = local.name_prefix
  environment          = var.environment
  vpc_cidr             = var.vpc_cidr
  availability_zones   = var.availability_zones
  private_subnet_cidrs = var.private_subnet_cidrs
  public_subnet_cidrs  = var.public_subnet_cidrs
  database_subnet_cidrs = var.database_subnet_cidrs
  enable_nat_gateway   = true
  single_nat_gateway   = false  # One NAT Gateway per AZ for high availability
  tags                 = local.common_tags
}

# VPC in DR Region
module "vpc_dr" {
  source = "../../modules/vpc"
  providers = {
    aws = aws.dr_region
  }

  name_prefix          = "${local.name_prefix}-dr"
  environment          = var.environment
  vpc_cidr             = var.dr_vpc_cidr
  availability_zones   = var.dr_availability_zones
  private_subnet_cidrs = var.dr_private_subnet_cidrs
  public_subnet_cidrs  = var.dr_public_subnet_cidrs
  database_subnet_cidrs = var.dr_database_subnet_cidrs
  enable_nat_gateway   = true
  single_nat_gateway   = false
  tags                 = local.common_tags
}

# Security Groups
module "security_groups" {
  source = "../../modules/security"

  name_prefix = local.name_prefix
  environment = var.environment
  vpc_id      = module.vpc.vpc_id
  vpc_cidr    = var.vpc_cidr
  allowed_ips = var.allowed_ips
}

# Security Groups in DR Region
module "security_groups_dr" {
  source = "../../modules/security"
  providers = {
    aws = aws.dr_region
  }

  name_prefix = "${local.name_prefix}-dr"
  environment = var.environment
  vpc_id      = module.vpc_dr.vpc_id
  vpc_cidr    = var.dr_vpc_cidr
  allowed_ips = var.allowed_ips
}

# Load Balancer
module "alb" {
  source = "../../modules/alb"

  name_prefix        = local.name_prefix
  environment        = var.environment
  vpc_id             = module.vpc.vpc_id
  public_subnet_ids  = module.vpc.public_subnet_ids
  security_group_ids = [module.security_groups.alb_security_group_id]
  ssl_certificate_arn = var.ssl_certificate_arn
  waf_acl_arn        = module.waf.waf_acl_arn
  tags               = local.common_tags
}

# Load Balancer in DR Region
module "alb_dr" {
  source = "../../modules/alb"
  providers = {
    aws = aws.dr_region
  }

  name_prefix        = "${local.name_prefix}-dr"
  environment        = var.environment
  vpc_id             = module.vpc_dr.vpc_id
  public_subnet_ids  = module.vpc_dr.public_subnet_ids
  security_group_ids = [module.security_groups_dr.alb_security_group_id]
  ssl_certificate_arn = var.dr_ssl_certificate_arn
  waf_acl_arn        = module.waf_dr.waf_acl_arn
  tags               = local.common_tags
}

# ECS Cluster
module "ecs" {
  source = "../../modules/ecs"

  name_prefix           = local.name_prefix
  environment           = var.environment
  vpc_id                = module.vpc.vpc_id
  private_subnet_ids    = module.vpc.private_subnet_ids
  security_group_ids    = [module.security_groups.ecs_security_group_id]
  alb_target_group_arns = module.alb.target_group_arns
  execution_role_arn    = module.iam.ecs_execution_role_arn
  task_role_arn         = module.iam.ecs_task_role_arn
  ecs_services          = var.ecs_services
  ecs_task_cpu          = var.ecs_task_cpu
  ecs_task_memory       = var.ecs_task_memory
  container_image_url   = var.container_image_url
  desired_count         = var.ecs_desired_count
  enable_auto_scaling   = true
  min_capacity          = var.ecs_min_capacity
  max_capacity          = var.ecs_max_capacity
  tags                  = local.common_tags
}

# ECS Cluster in DR Region
module "ecs_dr" {
  source = "../../modules/ecs"
  providers = {
    aws = aws.dr_region
  }

  name_prefix           = "${local.name_prefix}-dr"
  environment           = var.environment
  vpc_id                = module.vpc_dr.vpc_id
  private_subnet_ids    = module.vpc_dr.private_subnet_ids
  security_group_ids    = [module.security_groups_dr.ecs_security_group_id]
  alb_target_group_arns = module.alb_dr.target_group_arns
  execution_role_arn    = module.iam_dr.ecs_execution_role_arn
  task_role_arn         = module.iam_dr.ecs_task_role_arn
  ecs_services          = var.ecs_services
  ecs_task_cpu          = var.ecs_task_cpu
  ecs_task_memory       = var.ecs_task_memory
  container_image_url   = var.container_image_url
  desired_count         = var.dr_ecs_desired_count  # Possibly reduced for DR
  enable_auto_scaling   = true
  min_capacity          = var.dr_ecs_min_capacity
  max_capacity          = var.dr_ecs_max_capacity
  tags                  = local.common_tags
}

# DocumentDB (MongoDB compatible)
module "documentdb" {
  source = "../../modules/documentdb"

  name_prefix            = local.name_prefix
  environment            = var.environment
  engine_version         = var.documentdb_version
  master_username        = var.documentdb_master_username
  master_password        = var.documentdb_master_password
  instance_class         = var.documentdb_instance_class
  instances              = var.documentdb_instances
  vpc_id                 = module.vpc.vpc_id
  subnet_ids             = module.vpc.database_subnet_ids
  security_group_ids     = [module.security_groups.documentdb_security_group_id]
  backup_retention       = var.documentdb_backup_retention
  preferred_backup_window = var.documentdb_backup_window
  parameters             = var.documentdb_parameters
  enabled_cloudwatch_logs = var.documentdb_cloudwatch_logs
  tags                   = local.common_tags
}

# DocumentDB in DR Region
module "documentdb_dr" {
  source = "../../modules/documentdb"
  providers = {
    aws = aws.dr_region
  }

  name_prefix            = "${local.name_prefix}-dr"
  environment            = var.environment
  engine_version         = var.documentdb_version
  master_username        = var.documentdb_master_username
  master_password        = var.documentdb_master_password
  instance_class         = var.documentdb_instance_class
  instances              = var.documentdb_instances
  vpc_id                 = module.vpc_dr.vpc_id
  subnet_ids             = module.vpc_dr.database_subnet_ids
  security_group_ids     = [module.security_groups_dr.documentdb_security_group_id]
  backup_retention       = var.documentdb_backup_retention
  preferred_backup_window = var.documentdb_backup_window
  parameters             = var.documentdb_parameters
  enabled_cloudwatch_logs = var.documentdb_cloudwatch_logs
  tags                   = local.common_tags
}

# ElastiCache Redis
module "elasticache" {
  source = "../../modules/elasticache"

  name_prefix               = local.name_prefix
  environment               = var.environment
  engine_version            = var.redis_version
  node_type                 = var.redis_node_type
  parameter_group_name      = var.redis_parameter_group
  num_cache_nodes           = var.redis_num_cache_nodes
  vpc_id                    = module.vpc.vpc_id
  subnet_ids                = module.vpc.database_subnet_ids
  security_group_ids        = [module.security_groups.redis_security_group_id]
  maintenance_window        = var.redis_maintenance_window
  snapshot_retention        = var.redis_snapshot_retention
  snapshot_window           = var.redis_snapshot_window
  auto_minor_version_upgrade = true
  multi_az_enabled          = true
  automatic_failover_enabled = true
  tags                      = local.common_tags
}

# ElastiCache Redis in DR Region
module "elasticache_dr" {
  source = "../../modules/elasticache"
  providers = {
    aws = aws.dr_region
  }

  name_prefix               = "${local.name_prefix}-dr"
  environment               = var.environment
  engine_version            = var.redis_version
  node_type                 = var.redis_node_type
  parameter_group_name      = var.redis_parameter_group
  num_cache_nodes           = var.redis_num_cache_nodes
  vpc_id                    = module.vpc_dr.vpc_id
  subnet_ids                = module.vpc_dr.database_subnet_ids
  security_group_ids        = [module.security_groups_dr.redis_security_group_id]
  maintenance_window        = var.redis_maintenance_window
  snapshot_retention        = var.redis_snapshot_retention
  snapshot_window           = var.redis_snapshot_window
  auto_minor_version_upgrade = true
  multi_az_enabled          = true
  automatic_failover_enabled = true
  tags                      = local.common_tags
}

# S3 Buckets
module "s3" {
  source = "../../modules/s3"

  name_prefix     = local.name_prefix
  environment     = var.environment
  random_suffix   = random_string.suffix.result
  logging_enabled = true
  versioning      = true
  lifecycle_rules = var.s3_lifecycle_rules
  kms_key_id      = module.kms.s3_key_id
  tags            = local.common_tags
}

# S3 Replication to DR Region
module "s3_replication" {
  source = "../../modules/s3-replication"

  source_bucket_name      = module.s3.bucket_name
  source_bucket_arn       = module.s3.bucket_arn
  destination_bucket_name = "${local.name_prefix}-dr-${random_string.suffix.result}"
  destination_region      = var.dr_region
  replication_role_name   = "${local.name_prefix}-replication-role"
  kms_key_id              = module.kms.s3_key_id
  tags                    = local.common_tags
}

# CloudFront Distribution
module "cloudfront" {
  source = "../../modules/cloudfront"

  name_prefix        = local.name_prefix
  environment        = var.environment
  alb_domain_name    = module.alb.alb_dns_name
  s3_bucket_domain   = module.s3.bucket_domain_name
  ssl_certificate_arn = var.cloudfront_certificate_arn
  waf_acl_id         = module.waf.waf_acl_id
  price_class        = var.cloudfront_price_class
  geo_restrictions   = var.cloudfront_geo_restrictions
  tags               = local.common_tags
}

# IAM Roles
module "iam" {
  source = "../../modules/iam"

  name_prefix       = local.name_prefix
  environment       = var.environment
  tags              = local.common_tags
}

# IAM Roles in DR Region
module "iam_dr" {
  source = "../../modules/iam"
  providers = {
    aws = aws.dr_region
  }

  name_prefix       = "${local.name_prefix}-dr"
  environment       = var.environment
  tags              = local.common_tags
}

# KMS Keys for Encryption
module "kms" {
  source = "../../modules/kms"

  name_prefix       = local.name_prefix
  environment       = var.environment
  tags              = local.common_tags
}

# KMS Keys in DR Region
module "kms_dr" {
  source = "../../modules/kms"
  providers = {
    aws = aws.dr_region
  }

  name_prefix       = "${local.name_prefix}-dr"
  environment       = var.environment
  tags              = local.common_tags
}

# WAF for API Security
module "waf" {
  source = "../../modules/waf"

  name_prefix       = local.name_prefix
  environment       = var.environment
  alb_arn           = module.alb.alb_arn
  ip_whitelist      = var.waf_ip_whitelist
  rate_limit        = var.waf_rate_limit
  tags              = local.common_tags
}

# WAF in DR Region
module "waf_dr" {
  source = "../../modules/waf"
  providers = {
    aws = aws.dr_region
  }

  name_prefix       = "${local.name_prefix}-dr"
  environment       = var.environment
  alb_arn           = module.alb_dr.alb_arn
  ip_whitelist      = var.waf_ip_whitelist
  rate_limit        = var.waf_rate_limit
  tags              = local.common_tags
}

# Route53 for DNS Management
module "route53" {
  source = "../../modules/route53"

  domain_name         = var.domain_name
  cloudfront_domain   = module.cloudfront.domain_name
  failover_enabled    = true
  primary_endpoint    = module.alb.alb_dns_name
  secondary_endpoint  = module.alb_dr.alb_dns_name
  health_check_path   = var.health_check_path
  tags                = local.common_tags
}

# Monitoring and Logs
module "monitoring" {
  source = "../../modules/monitoring"

  name_prefix        = local.name_prefix
  environment        = var.environment
  vpc_id             = module.vpc.vpc_id
  alb_arn            = module.alb.alb_arn
  ecs_cluster_name   = module.ecs.cluster_name
  documentdb_cluster = module.documentdb.cluster_identifier
  elasticache_id     = module.elasticache.cluster_id
  s3_bucket_id       = module.s3.bucket_id
  log_retention_days = var.log_retention_days
  alarm_actions      = var.alarm_action_arns
  ok_actions         = var.ok_action_arns
  tags               = local.common_tags
}

# Monitoring in DR Region
module "monitoring_dr" {
  source = "../../modules/monitoring"
  providers = {
    aws = aws.dr_region
  }

  name_prefix        = "${local.name_prefix}-dr"
  environment        = var.environment
  vpc_id             = module.vpc_dr.vpc_id
  alb_arn            = module.alb_dr.alb_arn
  ecs_cluster_name   = module.ecs_dr.cluster_name
  documentdb_cluster = module.documentdb_dr.cluster_identifier
  elasticache_id     = module.elasticache_dr.cluster_id
  s3_bucket_id       = module.s3_replication.destination_bucket_id
  log_retention_days = var.log_retention_days
  alarm_actions      = var.dr_alarm_action_arns
  ok_actions         = var.dr_ok_action_arns
  tags               = local.common_tags
}

# Secrets Management
module "secrets" {
  source = "../../modules/secrets"

  name_prefix        = local.name_prefix
  environment        = var.environment
  documentdb_secret  = {
    username = var.documentdb_master_username
    password = var.documentdb_master_password
    host     = module.documentdb.endpoint
    port     = module.documentdb.port
  }
  redis_secret       = {
    host = module.elasticache.endpoint
    port = module.elasticache.port
  }
  kms_key_id         = module.kms.secrets_key_id
  tags               = local.common_tags
}

# Secrets in DR Region
module "secrets_dr" {
  source = "../../modules/secrets"
  providers = {
    aws = aws.dr_region
  }

  name_prefix        = "${local.name_prefix}-dr"
  environment        = var.environment
  documentdb_secret  = {
    username = var.documentdb_master_username
    password = var.documentdb_master_password
    host     = module.documentdb_dr.endpoint
    port     = module.documentdb_dr.port
  }
  redis_secret       = {
    host = module.elasticache_dr.endpoint
    port = module.elasticache_dr.port
  }
  kms_key_id         = module.kms_dr.secrets_key_id
  tags               = local.common_tags
}

# AWS Config for Compliance Monitoring
module "config" {
  source = "../../modules/config"

  name_prefix        = local.name_prefix
  environment        = var.environment
  logging_bucket     = module.s3.bucket_name
  tags               = local.common_tags
}

# AWS Config in DR Region
module "config_dr" {
  source = "../../modules/config"
  providers = {
    aws = aws.dr_region
  }

  name_prefix        = "${local.name_prefix}-dr"
  environment        = var.environment
  logging_bucket     = module.s3_replication.destination_bucket_name
  tags               = local.common_tags
}

# GuardDuty for Threat Detection
module "guardduty" {
  source = "../../modules/guardduty"

  name_prefix        = local.name_prefix
  environment        = var.environment
  findings_bucket    = module.s3.bucket_name
  tags               = local.common_tags
}

# GuardDuty in DR Region
module "guardduty_dr" {
  source = "../../modules/guardduty"
  providers = {
    aws = aws.dr_region
  }

  name_prefix        = "${local.name_prefix}-dr"
  environment        = var.environment
  findings_bucket    = module.s3_replication.destination_bucket_name
  tags               = local.common_tags
}

# Backup Plans for All Resources
module "backup" {
  source = "../../modules/backup"

  name_prefix        = local.name_prefix
  environment        = var.environment
  documentdb_arn     = module.documentdb.cluster_arn
  elasticache_arn    = module.elasticache.cluster_arn
  backup_vault_name  = "${local.name_prefix}-backup-vault"
  backup_schedule    = var.backup_schedule
  retention_period   = var.backup_retention_days
  tags               = local.common_tags
}

# Backup Plans in DR Region
module "backup_dr" {
  source = "../../modules/backup"
  providers = {
    aws = aws.dr_region
  }

  name_prefix        = "${local.name_prefix}-dr"
  environment        = var.environment
  documentdb_arn     = module.documentdb_dr.cluster_arn
  elasticache_arn    = module.elasticache_dr.cluster_arn
  backup_vault_name  = "${local.name_prefix}-dr-backup-vault"
  backup_schedule    = var.backup_schedule
  retention_period   = var.backup_retention_days
  tags               = local.common_tags
}

# CloudTrail for API Logging
module "cloudtrail" {
  source = "../../modules/cloudtrail"

  name_prefix        = local.name_prefix
  environment        = var.environment
  logging_bucket     = module.s3.bucket_name
  kms_key_id         = module.kms.cloudtrail_key_id
  tags               = local.common_tags
}

# CloudTrail in DR Region
module "cloudtrail_dr" {
  source = "../../modules/cloudtrail"
  providers = {
    aws = aws.dr_region
  }

  name_prefix        = "${local.name_prefix}-dr"
  environment        = var.environment
  logging_bucket     = module.s3_replication.destination_bucket_name
  kms_key_id         = module.kms_dr.cloudtrail_key_id
  tags               = local.common_tags
}