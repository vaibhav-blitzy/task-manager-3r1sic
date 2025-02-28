# General configuration
variable "vpc_id" {
  description = "ID of the VPC where database resources will be deployed"
  type        = string
}

variable "private_subnet_ids" {
  description = "List of private subnet IDs where database resources will be deployed"
  type        = list(string)
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod) for resource naming and sizing"
  type        = string
}

variable "name_prefix" {
  description = "Prefix to be used in resource names"
  type        = string
  default     = "tms"
}

# MongoDB Atlas configuration
variable "mongodb_instance_type" {
  description = "Instance type for MongoDB cluster"
  type        = string
}

variable "mongodb_version" {
  description = "MongoDB version to deploy"
  type        = string
  default     = "5.0"
}

variable "mongodb_node_count" {
  description = "Number of nodes in MongoDB cluster"
  type        = number
  default     = 3
}

variable "mongodb_username" {
  description = "Username for MongoDB primary application access"
  type        = string
  default     = "app_user"
}

variable "mongodb_password" {
  description = "Password for MongoDB primary application access"
  type        = string
  sensitive   = true
}

variable "mongodb_database_name" {
  description = "Name of the primary MongoDB database"
  type        = string
  default     = "task_management"
}

variable "mongodb_atlas_public_key" {
  description = "MongoDB Atlas public key for API access"
  type        = string
  sensitive   = true
}

variable "mongodb_atlas_private_key" {
  description = "MongoDB Atlas private key for API access"
  type        = string
  sensitive   = true
}

variable "mongodb_atlas_org_id" {
  description = "MongoDB Atlas organization ID"
  type        = string
}

variable "mongodb_atlas_project_name" {
  description = "Name of the project in MongoDB Atlas"
  type        = string
  default     = "TaskManagementSystem"
}

variable "mongodb_backup_enabled" {
  description = "Enable automated backups for MongoDB"
  type        = bool
  default     = true
}

variable "mongodb_backup_retention_days" {
  description = "Number of days to retain MongoDB backups"
  type        = number
  default     = 7
}

variable "mongodb_encryption_at_rest" {
  description = "Enable encryption at rest for MongoDB data"
  type        = bool
  default     = true
}

# Redis ElastiCache configuration
variable "redis_node_type" {
  description = "Node type for Redis cluster"
  type        = string
}

variable "redis_version" {
  description = "Redis version to deploy"
  type        = string
  default     = "6.x"
}

variable "redis_replica_count" {
  description = "Number of read replicas in Redis cluster"
  type        = number
  default     = 2
}

variable "redis_automatic_failover" {
  description = "Enable automatic failover for Redis"
  type        = bool
  default     = true
}

variable "redis_multi_az" {
  description = "Deploy Redis across multiple availability zones"
  type        = bool
  default     = true
}

variable "redis_auth_token" {
  description = "Auth token for Redis connections"
  type        = string
  sensitive   = true
}

variable "redis_parameter_group_name" {
  description = "Name of the Redis parameter group to use, if custom configuration is needed"
  type        = string
  default     = null
}

variable "redis_backup_retention_period" {
  description = "Number of days to retain Redis backups"
  type        = number
  default     = 7
}

variable "redis_backup_window" {
  description = "Daily time range during which backups may be created"
  type        = string
  default     = "05:00-09:00"
}

variable "redis_maintenance_window" {
  description = "Weekly time range during which system maintenance can occur"
  type        = string
  default     = "sun:23:00-mon:01:00"
}

variable "redis_at_rest_encryption" {
  description = "Enable encryption at rest for Redis"
  type        = bool
  default     = true
}

variable "redis_transit_encryption" {
  description = "Enable encryption in transit for Redis"
  type        = bool
  default     = true
}

# Security and additional configuration
variable "additional_security_group_ids" {
  description = "List of additional security group IDs to attach to database resources"
  type        = list(string)
  default     = []
}

variable "allowed_cidr_blocks" {
  description = "List of CIDR blocks allowed to access the databases"
  type        = list(string)
  default     = []
}

variable "create_secrets_manager_secret" {
  description = "Whether to create AWS Secrets Manager secrets for database credentials"
  type        = bool
  default     = true
}

variable "kms_key_id" {
  description = "KMS Key ID for encrypting database credentials in Secrets Manager"
  type        = string
  default     = null
}

variable "tags" {
  description = "Tags to apply to all resources created by this module"
  type        = map(string)
  default     = {}
}