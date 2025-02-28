# ------------------------------------------------------------
# AWS and Environment Configuration
# ------------------------------------------------------------

variable "aws_region" {
  description = "The AWS region where resources will be provisioned"
  type        = string
}

variable "environment" {
  description = "The deployment environment (dev, staging, production)"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "production"], var.environment)
    error_message = "The environment value must be one of: dev, staging, production."
  }
}

variable "project_name" {
  description = "Name of the project used for resource naming"
  type        = string
}

variable "tags" {
  description = "A map of tags to be applied to all compute resources"
  type        = map(string)
  default     = {}
}

# ------------------------------------------------------------
# Networking Configuration
# ------------------------------------------------------------

variable "vpc_id" {
  description = "The VPC ID where compute resources will be provisioned"
  type        = string
}

variable "private_subnet_ids" {
  description = "List of private subnet IDs for compute resources"
  type        = list(string)
}

variable "public_subnet_ids" {
  description = "List of public subnet IDs for load balancers"
  type        = list(string)
}

variable "load_balancer_security_group_id" {
  description = "Security group ID for the load balancer"
  type        = string
}

variable "ecs_security_group_id" {
  description = "Security group ID for ECS services"
  type        = string
}

# ------------------------------------------------------------
# ECS Cluster Configuration
# ------------------------------------------------------------

variable "use_fargate" {
  description = "Whether to use Fargate or EC2 for the ECS cluster"
  type        = bool
  default     = true
}

variable "enable_spot_instances" {
  description = "Whether to use Fargate Spot for non-critical services"
  type        = bool
  default     = false
}

variable "ecs_task_execution_role_arn" {
  description = "ARN of the IAM role that the ECS container agent and Docker daemon can assume"
  type        = string
}

variable "ecs_task_role_arn" {
  description = "ARN of the IAM role that the Amazon ECS container can use to call AWS services"
  type        = string
}

variable "ecr_repository_url_prefix" {
  description = "ECR repository URL prefix for container images"
  type        = string
}

variable "container_image_tag" {
  description = "Tag for container images"
  type        = string
  default     = "latest"
}

variable "enable_execute_command" {
  description = "Whether to enable execute command functionality for ECS services"
  type        = bool
  default     = true
}

variable "logs_retention_in_days" {
  description = "Retention period for CloudWatch logs in days"
  type        = number
  default     = 30
}

# ------------------------------------------------------------
# Service Discovery Configuration
# ------------------------------------------------------------

variable "enable_service_discovery" {
  description = "Whether to enable service discovery for services"
  type        = bool
  default     = true
}

variable "service_discovery_namespace_id" {
  description = "ID of the service discovery namespace"
  type        = string
  default     = null
}

# ------------------------------------------------------------
# Deployment Configuration
# ------------------------------------------------------------

variable "enable_blue_green_deployment" {
  description = "Whether to enable blue-green deployment for services"
  type        = bool
  default     = false
}

variable "health_check_grace_period_seconds" {
  description = "Grace period for health checks in seconds"
  type        = number
  default     = 60
}

variable "deployment_minimum_healthy_percent" {
  description = "Minimum percentage of healthy tasks during deployment"
  type        = number
  default     = 100
}

variable "deployment_maximum_percent" {
  description = "Maximum percentage of tasks that can run during deployment"
  type        = number
  default     = 200
}

variable "deployment_circuit_breaker_enabled" {
  description = "Whether to enable the deployment circuit breaker"
  type        = bool
  default     = true
}

variable "deployment_circuit_breaker_rollback" {
  description = "Whether to enable rollback when the deployment circuit breaker is triggered"
  type        = bool
  default     = true
}

# ------------------------------------------------------------
# Load Balancer Configuration
# ------------------------------------------------------------

variable "load_balancer_idle_timeout" {
  description = "Idle timeout for the load balancer in seconds"
  type        = number
  default     = 60
}

variable "load_balancer_ssl_policy" {
  description = "SSL policy for the load balancer"
  type        = string
  default     = "ELBSecurityPolicy-TLS-1-2-2017-01"
}

variable "load_balancer_certificate_arn" {
  description = "ARN of the SSL certificate for the load balancer"
  type        = string
}

# ------------------------------------------------------------
# Service Configurations
# ------------------------------------------------------------

variable "api_gateway_config" {
  description = "Configuration for API Gateway Service"
  type = object({
    cpu                     = number
    memory                  = number
    desired_count           = number
    max_capacity            = number
    min_capacity            = number
    auto_scaling_target_value = number
  })
}

variable "auth_service_config" {
  description = "Configuration for Authentication Service"
  type = object({
    cpu                     = number
    memory                  = number
    desired_count           = number
    max_capacity            = number
    min_capacity            = number
    auto_scaling_target_value = number
  })
}

variable "task_service_config" {
  description = "Configuration for Task Service"
  type = object({
    cpu                     = number
    memory                  = number
    desired_count           = number
    max_capacity            = number
    min_capacity            = number
    auto_scaling_target_value = number
  })
}

variable "project_service_config" {
  description = "Configuration for Project Service"
  type = object({
    cpu                     = number
    memory                  = number
    desired_count           = number
    max_capacity            = number
    min_capacity            = number
    auto_scaling_target_value = number
  })
}

variable "notification_service_config" {
  description = "Configuration for Notification Service"
  type = object({
    cpu                     = number
    memory                  = number
    desired_count           = number
    max_capacity            = number
    min_capacity            = number
    auto_scaling_target_value = number
  })
}

variable "file_service_config" {
  description = "Configuration for File Service"
  type = object({
    cpu                     = number
    memory                  = number
    desired_count           = number
    max_capacity            = number
    min_capacity            = number
    auto_scaling_target_value = number
  })
}

variable "analytics_service_config" {
  description = "Configuration for Analytics Service"
  type = object({
    cpu                     = number
    memory                  = number
    desired_count           = number
    max_capacity            = number
    min_capacity            = number
    auto_scaling_target_value = number
  })
}

variable "realtime_service_config" {
  description = "Configuration for Real-time Service"
  type = object({
    cpu                     = number
    memory                  = number
    desired_count           = number
    max_capacity            = number
    min_capacity            = number
    auto_scaling_target_value = number
  })
}