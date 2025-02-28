# Terraform module for the Task Management System network infrastructure
# Creates VPC, subnets, gateways, route tables, and security groups

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

locals {
  nat_gateway_count = var.single_nat_gateway ? 1 : length(var.availability_zones)
  vpc_name = "${var.environment}-vpc"
  max_subnet_length = max(length(var.public_subnet_cidrs), length(var.private_app_subnet_cidrs), length(var.private_data_subnet_cidrs))
}

# VPC
resource "aws_vpc" "this" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = merge(
    var.tags,
    {
      Name = local.vpc_name
      Environment = var.environment
    }
  )
}

# Public Subnets
resource "aws_subnet" "public" {
  count                   = length(var.public_subnet_cidrs)
  vpc_id                  = aws_vpc.this.id
  cidr_block              = var.public_subnet_cidrs[count.index]
  availability_zone       = var.availability_zones[count.index % length(var.availability_zones)]
  map_public_ip_on_launch = true

  tags = merge(
    var.tags,
    {
      Name = "${var.environment}-public-subnet-${var.availability_zones[count.index % length(var.availability_zones)]}"
      Tier = "public"
      Environment = var.environment
    }
  )
}

# Private App Subnets
resource "aws_subnet" "private_app" {
  count                   = length(var.private_app_subnet_cidrs)
  vpc_id                  = aws_vpc.this.id
  cidr_block              = var.private_app_subnet_cidrs[count.index]
  availability_zone       = var.availability_zones[count.index % length(var.availability_zones)]
  map_public_ip_on_launch = false

  tags = merge(
    var.tags,
    {
      Name = "${var.environment}-private-app-subnet-${var.availability_zones[count.index % length(var.availability_zones)]}"
      Tier = "private"
      SubTier = "app"
      Environment = var.environment
    }
  )
}

# Private Data Subnets
resource "aws_subnet" "private_data" {
  count                   = length(var.private_data_subnet_cidrs)
  vpc_id                  = aws_vpc.this.id
  cidr_block              = var.private_data_subnet_cidrs[count.index]
  availability_zone       = var.availability_zones[count.index % length(var.availability_zones)]
  map_public_ip_on_launch = false

  tags = merge(
    var.tags,
    {
      Name = "${var.environment}-private-data-subnet-${var.availability_zones[count.index % length(var.availability_zones)]}"
      Tier = "private"
      SubTier = "data"
      Environment = var.environment
    }
  )
}

# Internet Gateway
resource "aws_internet_gateway" "this" {
  vpc_id = aws_vpc.this.id

  tags = merge(
    var.tags,
    {
      Name = "${var.environment}-igw"
      Environment = var.environment
    }
  )
}

# Elastic IPs for NAT Gateway
resource "aws_eip" "nat" {
  count  = local.nat_gateway_count
  domain = "vpc"

  tags = merge(
    var.tags,
    {
      Name = "${var.environment}-eip-nat-${count.index + 1}"
      Environment = var.environment
    }
  )

  depends_on = [aws_internet_gateway.this]
}

# NAT Gateways
resource "aws_nat_gateway" "this" {
  count         = local.nat_gateway_count
  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id

  tags = merge(
    var.tags,
    {
      Name = "${var.environment}-nat-${count.index + 1}"
      Environment = var.environment
    }
  )

  depends_on = [aws_internet_gateway.this]
}

# Route Table for Public Subnets
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.this.id

  tags = merge(
    var.tags,
    {
      Name = "${var.environment}-public-route-table"
      Tier = "public"
      Environment = var.environment
    }
  )
}

# Route to Internet Gateway for Public Subnets
resource "aws_route" "public_internet_gateway" {
  route_table_id         = aws_route_table.public.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.this.id
}

# Route Tables for Private Subnets
resource "aws_route_table" "private" {
  count  = local.nat_gateway_count
  vpc_id = aws_vpc.this.id

  tags = merge(
    var.tags,
    {
      Name = "${var.environment}-private-route-table-${count.index + 1}"
      Tier = "private"
      Environment = var.environment
    }
  )
}

# Routes to NAT Gateway for Private Subnets
resource "aws_route" "private_nat_gateway" {
  count                  = local.nat_gateway_count
  route_table_id         = aws_route_table.private[count.index].id
  destination_cidr_block = "0.0.0.0/0"
  nat_gateway_id         = aws_nat_gateway.this[count.index].id
}

# Associate Public Subnets with Public Route Table
resource "aws_route_table_association" "public" {
  count          = length(var.public_subnet_cidrs)
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# Associate Private App Subnets with Private Route Tables
resource "aws_route_table_association" "private_app" {
  count          = length(var.private_app_subnet_cidrs)
  subnet_id      = aws_subnet.private_app[count.index].id
  route_table_id = aws_route_table.private[count.index % local.nat_gateway_count].id
}

# Associate Private Data Subnets with Private Route Tables
resource "aws_route_table_association" "private_data" {
  count          = length(var.private_data_subnet_cidrs)
  subnet_id      = aws_subnet.private_data[count.index].id
  route_table_id = aws_route_table.private[count.index % local.nat_gateway_count].id
}

# Security Group for Application Load Balancer
resource "aws_security_group" "alb" {
  name        = "${var.environment}-alb-sg"
  description = "Security group for Application Load Balancer"
  vpc_id      = aws_vpc.this.id

  tags = merge(
    var.tags,
    {
      Name = "${var.environment}-alb-sg"
      Environment = var.environment
    }
  )
}

# ALB Security Group Rules
resource "aws_security_group_rule" "alb_ingress_http" {
  security_group_id = aws_security_group.alb.id
  type              = "ingress"
  from_port         = 80
  to_port           = 80
  protocol          = "tcp"
  cidr_blocks       = var.allow_http_from_cidrs
  description       = "Allow HTTP traffic from specified CIDR blocks"
}

resource "aws_security_group_rule" "alb_ingress_https" {
  security_group_id = aws_security_group.alb.id
  type              = "ingress"
  from_port         = 443
  to_port           = 443
  protocol          = "tcp"
  cidr_blocks       = var.allow_https_from_cidrs
  description       = "Allow HTTPS traffic from specified CIDR blocks"
}

resource "aws_security_group_rule" "alb_egress" {
  security_group_id = aws_security_group.alb.id
  type              = "egress"
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  cidr_blocks       = ["0.0.0.0/0"]
  description       = "Allow all outbound traffic"
}

# Security Group for Application Tier
resource "aws_security_group" "app" {
  name        = "${var.environment}-app-sg"
  description = "Security group for Application tier"
  vpc_id      = aws_vpc.this.id

  tags = merge(
    var.tags,
    {
      Name = "${var.environment}-app-sg"
      Environment = var.environment
    }
  )
}

# App Security Group Rules
resource "aws_security_group_rule" "app_ingress_alb" {
  security_group_id        = aws_security_group.app.id
  type                     = "ingress"
  from_port                = var.app_port
  to_port                  = var.app_port
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.alb.id
  description              = "Allow traffic from ALB on application port"
}

resource "aws_security_group_rule" "app_ingress_self" {
  security_group_id        = aws_security_group.app.id
  type                     = "ingress"
  from_port                = 0
  to_port                  = 65535
  protocol                 = "tcp"
  self                     = true
  description              = "Allow traffic between application instances"
}

resource "aws_security_group_rule" "app_egress" {
  security_group_id = aws_security_group.app.id
  type              = "egress"
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  cidr_blocks       = ["0.0.0.0/0"]
  description       = "Allow all outbound traffic"
}

# Security Group for Data Tier
resource "aws_security_group" "data" {
  name        = "${var.environment}-data-sg"
  description = "Security group for Data tier"
  vpc_id      = aws_vpc.this.id

  tags = merge(
    var.tags,
    {
      Name = "${var.environment}-data-sg"
      Environment = var.environment
    }
  )
}

# Data Security Group Rules
resource "aws_security_group_rule" "data_ingress_app" {
  security_group_id        = aws_security_group.data.id
  type                     = "ingress"
  from_port                = 0
  to_port                  = 65535
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.app.id
  description              = "Allow traffic from App tier"
}

resource "aws_security_group_rule" "data_ingress_self" {
  security_group_id        = aws_security_group.data.id
  type                     = "ingress"
  from_port                = 0
  to_port                  = 65535
  protocol                 = "tcp"
  self                     = true
  description              = "Allow traffic between data instances for replication"
}

resource "aws_security_group_rule" "data_egress" {
  security_group_id = aws_security_group.data.id
  type              = "egress"
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  cidr_blocks       = ["0.0.0.0/0"]
  description       = "Allow limited outbound traffic"
}

# VPC Endpoint for S3
resource "aws_vpc_endpoint" "s3" {
  vpc_id            = aws_vpc.this.id
  service_name      = "com.amazonaws.${var.region}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = concat([aws_route_table.public.id], aws_route_table.private[*].id)

  tags = merge(
    var.tags,
    {
      Name = "${var.environment}-s3-endpoint"
      Environment = var.environment
    }
  )
}

# VPC Endpoint for ECR API
resource "aws_vpc_endpoint" "ecr_api" {
  count               = var.create_ecr_endpoints ? 1 : 0
  vpc_id              = aws_vpc.this.id
  service_name        = "com.amazonaws.${var.region}.ecr.api"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private_app[*].id
  security_group_ids  = [aws_security_group.app.id]
  private_dns_enabled = true

  tags = merge(
    var.tags,
    {
      Name = "${var.environment}-ecr-api-endpoint"
      Environment = var.environment
    }
  )
}

# VPC Endpoint for ECR Docker Registry
resource "aws_vpc_endpoint" "ecr_dkr" {
  count               = var.create_ecr_endpoints ? 1 : 0
  vpc_id              = aws_vpc.this.id
  service_name        = "com.amazonaws.${var.region}.ecr.dkr"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private_app[*].id
  security_group_ids  = [aws_security_group.app.id]
  private_dns_enabled = true

  tags = merge(
    var.tags,
    {
      Name = "${var.environment}-ecr-dkr-endpoint"
      Environment = var.environment
    }
  )
}