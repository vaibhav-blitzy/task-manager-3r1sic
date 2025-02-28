# General configuration variables
variable "environment" {
  description = "Deployment environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "resource_prefix" {
  description = "Prefix to be used for all resources created by this module"
  type        = string
  default     = "tms"
}

variable "region" {
  description = "AWS region where monitoring resources will be deployed"
  type        = string
}

variable "vpc_id" {
  description = "ID of the VPC where monitoring resources will be deployed"
  type        = string
}

variable "subnet_ids" {
  description = "List of subnet IDs where monitoring resources will be deployed"
  type        = list(string)
}

variable "tags" {
  description = "A map of tags to assign to all resources"
  type        = map(string)
  default     = {}
}

# Logging configuration
variable "cloudwatch_log_retention_days" {
  description = "Number of days to retain logs in CloudWatch Logs"
  type        = number
  default     = 30
}

# Monitoring configuration
variable "enable_detailed_monitoring" {
  description = "Whether to enable detailed monitoring for EC2 instances"
  type        = bool
  default     = true
}

variable "alarm_notification_email" {
  description = "Email address for CloudWatch alarm notifications"
  type        = string
  default     = ""
}

# Prometheus configuration
variable "prometheus_retention_period_days" {
  description = "Data retention period in days for Prometheus metrics"
  type        = number
  default     = 15
}

# Feature flags
variable "enable_prometheus" {
  description = "Whether to deploy Prometheus for metrics collection"
  type        = bool
  default     = true
}

variable "enable_grafana" {
  description = "Whether to deploy Grafana for metrics visualization"
  type        = bool
  default     = true
}

variable "enable_alertmanager" {
  description = "Whether to deploy AlertManager for alert handling"
  type        = bool
  default     = true
}

variable "enable_fluentd" {
  description = "Whether to deploy Fluentd for log aggregation"
  type        = bool
  default     = true
}

variable "enable_elasticsearch" {
  description = "Whether to deploy Elasticsearch for log storage or use existing/managed service"
  type        = bool
  default     = false
}

variable "enable_x_ray" {
  description = "Whether to enable AWS X-Ray for distributed tracing"
  type        = bool
  default     = true
}

variable "enable_custom_dashboards" {
  description = "Whether to deploy custom CloudWatch dashboards for the services"
  type        = bool
  default     = true
}

# Elasticsearch configuration
variable "elasticsearch_endpoint" {
  description = "Endpoint for existing Elasticsearch cluster (if not deploying a new one)"
  type        = string
  default     = ""
}

# Credentials (sensitive data)
variable "grafana_admin_password" {
  description = "Admin password for Grafana (sensitive value)"
  type        = string
  default     = ""
  sensitive   = true
}

# Instance types and resources
variable "prometheus_instance_type" {
  description = "EC2 instance type for Prometheus server"
  type        = string
  default     = "t3.small"
}

variable "grafana_instance_type" {
  description = "EC2 instance type for Grafana server"
  type        = string
  default     = "t3.small"
}

variable "alertmanager_instance_type" {
  description = "EC2 instance type for AlertManager server"
  type        = string
  default     = "t3.micro"
}

# Storage configuration
variable "prometheus_storage_size" {
  description = "Size in GB for Prometheus data storage"
  type        = number
  default     = 50
}

variable "elasticsearch_storage_size" {
  description = "Size in GB for Elasticsearch data storage (if enabled)"
  type        = number
  default     = 100
}

# Network configuration
variable "monitoring_security_group_ids" {
  description = "List of security group IDs to attach to monitoring resources"
  type        = list(string)
  default     = []
}

# Alert thresholds
variable "cpu_utilization_threshold" {
  description = "CPU utilization threshold percentage for triggering alarms"
  type        = number
  default     = 70
}

variable "memory_utilization_threshold" {
  description = "Memory utilization threshold percentage for triggering alarms"
  type        = number
  default     = 80
}

variable "disk_utilization_threshold" {
  description = "Disk utilization threshold percentage for triggering alarms"
  type        = number
  default     = 85
}

variable "api_latency_threshold" {
  description = "API response time threshold in milliseconds for triggering alarms"
  type        = number
  default     = 500
}

variable "error_rate_threshold" {
  description = "Error rate threshold percentage for triggering alarms"
  type        = number
  default     = 1
}

# Dashboard configuration
variable "dashboard_json_templates" {
  description = "Map of dashboard names to their JSON template content"
  type        = map(string)
  default     = {}
}