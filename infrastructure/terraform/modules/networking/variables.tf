variable "vpc_name" {
  description = "Name of the VPC to be created for the Task Management System"
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "enable_dns_hostnames" {
  description = "Enable DNS hostnames in the VPC for service discovery"
  type        = bool
  default     = true
}

variable "enable_dns_support" {
  description = "Enable DNS support in the VPC for name resolution"
  type        = bool
  default     = true
}

variable "environment" {
  description = "Deployment environment name (dev, staging, production)"
  type        = string
}

variable "region" {
  description = "AWS region where the networking resources will be deployed"
  type        = string
}

variable "availability_zones" {
  description = "List of availability zones to deploy resources across for high availability"
  type        = list(string)
}

variable "public_subnet_cidrs" {
  description = "List of CIDR blocks for public subnets (ALB, NAT gateways)"
  type        = list(string)
}

variable "private_app_subnet_cidrs" {
  description = "List of CIDR blocks for private application tier subnets (ECS services)"
  type        = list(string)
}

variable "private_data_subnet_cidrs" {
  description = "List of CIDR blocks for private data tier subnets (MongoDB, Redis)"
  type        = list(string)
}

variable "enable_nat_gateway" {
  description = "Enable NAT Gateway for private subnets to access internet"
  type        = bool
  default     = true
}

variable "single_nat_gateway" {
  description = "Use a single NAT Gateway instead of one per AZ (cost saving for non-prod)"
  type        = bool
  default     = false
}

variable "create_igw" {
  description = "Create Internet Gateway for public subnets"
  type        = bool
  default     = true
}

variable "enable_vpc_flow_logs" {
  description = "Enable VPC Flow Logs for network monitoring and security analysis"
  type        = bool
  default     = true
}

variable "flow_logs_retention_days" {
  description = "Retention period for VPC Flow Logs in days"
  type        = number
  default     = 90
}

variable "app_security_group_rules" {
  description = "Ingress rules for application tier security group"
  type        = list(map(any))
  default     = []
}

variable "data_security_group_rules" {
  description = "Ingress rules for data tier security group"
  type        = list(map(any))
  default     = []
}

variable "alb_security_group_rules" {
  description = "Ingress rules for application load balancer security group"
  type        = list(map(any))
  default     = []
}

variable "create_vpc_endpoints" {
  description = "Create VPC endpoints for AWS services to improve security and reduce data transfer costs"
  type        = bool
  default     = false
}

variable "vpc_endpoint_services" {
  description = "List of AWS services to create VPC endpoints for (s3, ecr, etc.)"
  type        = list(string)
  default     = ["s3"]
}

variable "tags" {
  description = "Common tags to apply to all resources for organization and cost tracking"
  type        = map(string)
  default     = {}
}