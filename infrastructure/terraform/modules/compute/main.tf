# Terraform module for AWS ECS compute resources to host the Task Management System microservices.

# Required providers
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.16"
    }
  }
}

# Input variables
variable "environment" {
  description = "Environment name (e.g., dev, staging, production)"
  type        = string
}

variable "vpc_id" {
  description = "ID of the VPC where resources will be created"
  type        = string
}

variable "private_subnet_ids" {
  description = "List of private subnet IDs for ECS tasks"
  type        = list(string)
}

variable "public_subnet_ids" {
  description = "List of public subnet IDs for load balancer"
  type        = list(string)
}

variable "certificate_arn" {
  description = "ARN of the ACM certificate for HTTPS listener"
  type        = string
  default     = ""
}

variable "namespace" {
  description = "Namespace for service discovery"
  type        = string
  default     = "taskms"
}

variable "domain_name" {
  description = "Base domain name for the application"
  type        = string
  default     = ""
}

variable "tags" {
  description = "Tags to be applied to resources"
  type        = map(string)
  default     = {}
}

variable "enable_https" {
  description = "Enable HTTPS listener on load balancer"
  type        = bool
  default     = true
}

variable "fargate_platform_version" {
  description = "Fargate platform version"
  type        = string
  default     = "LATEST"
}

variable "log_retention_in_days" {
  description = "Number of days to retain CloudWatch logs"
  type        = number
  default     = 30
}

# Local variables
locals {
  name_prefix = "taskms-${var.environment}"
  
  # Service configurations - defining each microservice
  services = {
    authentication = {
      name               = "authentication"
      container_port     = 8000
      host_port          = 8000
      cpu                = 1024  # 1 vCPU
      memory             = 2048  # 2 GB
      desired_count      = var.environment == "production" ? 4 : 2
      path_patterns      = ["/api/v1/auth/*", "/api/v1/users/*"]
      health_check_path  = "/api/v1/health"
      auto_scaling       = {
        min_capacity     = var.environment == "production" ? 4 : 2
        max_capacity     = var.environment == "production" ? 12 : 4
        cpu_threshold    = 70
        memory_threshold = 80
      }
      service_discovery = true
      public_service    = true
      spot_enabled      = false  # Critical service runs on regular Fargate
    },
    task = {
      name               = "task"
      container_port     = 8000
      host_port          = 8000
      cpu                = 2048  # 2 vCPU
      memory             = 4096  # 4 GB
      desired_count      = var.environment == "production" ? 6 : 2
      path_patterns      = ["/api/v1/tasks/*"]
      health_check_path  = "/api/v1/health"
      auto_scaling       = {
        min_capacity     = var.environment == "production" ? 6 : 2
        max_capacity     = var.environment == "production" ? 20 : 6
        cpu_threshold    = 70
        memory_threshold = 80
      }
      service_discovery = true
      public_service    = true
      spot_enabled      = false  # Critical service runs on regular Fargate
    },
    project = {
      name               = "project"
      container_port     = 8000
      host_port          = 8000
      cpu                = 1024  # 1 vCPU
      memory             = 2048  # 2 GB
      desired_count      = var.environment == "production" ? 4 : 2
      path_patterns      = ["/api/v1/projects/*"]
      health_check_path  = "/api/v1/health"
      auto_scaling       = {
        min_capacity     = var.environment == "production" ? 4 : 2
        max_capacity     = var.environment == "production" ? 12 : 4
        cpu_threshold    = 65
        memory_threshold = 75
      }
      service_discovery = true
      public_service    = true
      spot_enabled      = false  # Critical service runs on regular Fargate
    },
    notification = {
      name               = "notification"
      container_port     = 8000
      host_port          = 8000
      cpu                = 512   # 0.5 vCPU
      memory             = 1024  # 1 GB
      desired_count      = var.environment == "production" ? 3 : 2
      path_patterns      = ["/api/v1/notifications/*"]
      health_check_path  = "/api/v1/health"
      auto_scaling       = {
        min_capacity     = var.environment == "production" ? 3 : 2
        max_capacity     = var.environment == "production" ? 10 : 4
        cpu_threshold    = 70
        memory_threshold = 80
      }
      service_discovery = true
      public_service    = true
      spot_enabled      = true  # Non-critical service can use Fargate Spot
    },
    file = {
      name               = "file"
      container_port     = 8000
      host_port          = 8000
      cpu                = 2048  # 2 vCPU
      memory             = 4096  # 4 GB
      desired_count      = var.environment == "production" ? 4 : 2
      path_patterns      = ["/api/v1/files/*"]
      health_check_path  = "/api/v1/health"
      auto_scaling       = {
        min_capacity     = var.environment == "production" ? 4 : 2
        max_capacity     = var.environment == "production" ? 12 : 4
        cpu_threshold    = 60
        memory_threshold = 70
      }
      service_discovery = true
      public_service    = true
      spot_enabled      = false  # File operations are critical
    },
    analytics = {
      name               = "analytics"
      container_port     = 8000
      host_port          = 8000
      cpu                = 2048  # 2 vCPU
      memory             = 8192  # 8 GB
      desired_count      = var.environment == "production" ? 2 : 1
      path_patterns      = ["/api/v1/analytics/*", "/api/v1/reports/*"]
      health_check_path  = "/api/v1/health"
      auto_scaling       = {
        min_capacity     = var.environment == "production" ? 2 : 1
        max_capacity     = var.environment == "production" ? 6 : 3
        cpu_threshold    = 75
        memory_threshold = 85
      }
      service_discovery = true
      public_service    = true
      spot_enabled      = true  # Analytics can use Fargate Spot for cost savings
    },
    realtime = {
      name               = "realtime"
      container_port     = 8000
      host_port          = 8000
      cpu                = 1024  # 1 vCPU
      memory             = 2048  # 2 GB
      desired_count      = var.environment == "production" ? 3 : 2
      path_patterns      = ["/api/v1/realtime/*", "/api/v1/websocket/*"]
      health_check_path  = "/api/v1/health"
      auto_scaling       = {
        min_capacity     = var.environment == "production" ? 3 : 2
        max_capacity     = var.environment == "production" ? 10 : 4
        cpu_threshold    = 70
        memory_threshold = 80
      }
      service_discovery = true
      public_service    = true
      spot_enabled      = false  # Real-time services are critical
    }
  }
  
  # Common tags
  common_tags = merge(
    var.tags,
    {
      Environment = var.environment
      Terraform   = "true"
      Application = "TaskManagementSystem"
    }
  )
}

# Resources

# 1. ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "${local.name_prefix}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = local.common_tags
}

# 2. ECS Cluster Capacity Providers
resource "aws_ecs_cluster_capacity_providers" "main" {
  cluster_name = aws_ecs_cluster.main.name

  capacity_providers = ["FARGATE", "FARGATE_SPOT"]

  default_capacity_provider_strategy {
    capacity_provider = "FARGATE"
    weight            = 1
    base              = 1
  }
}

# 3. IAM Roles for ECS Tasks
# ECS Task Execution Role - used by ECS to pull images, write logs, etc.
resource "aws_iam_role" "ecs_task_execution_role" {
  name = "${local.name_prefix}-ecs-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

# Attach required policies to the task execution role
resource "aws_iam_role_policy_attachment" "ecs_task_execution_role_policy" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# ECS Task Role - used by the application code running inside the container
resource "aws_iam_role" "ecs_task_role" {
  name = "${local.name_prefix}-ecs-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

# Policy for task role to access required AWS services
resource "aws_iam_role_policy" "ecs_task_role_policy" {
  name = "${local.name_prefix}-ecs-task-policy"
  role = aws_iam_role.ecs_task_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::taskms-${var.environment}-*",
          "arn:aws:s3:::taskms-${var.environment}-*/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = [
          "arn:aws:secretsmanager:*:*:secret:taskms-${var.environment}-*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameters",
          "ssm:GetParameter"
        ]
        Resource = [
          "arn:aws:ssm:*:*:parameter/taskms/${var.environment}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "xray:PutTraceSegments",
          "xray:PutTelemetryRecords"
        ]
        Resource = "*"
      }
    ]
  })
}

# 4. Security Groups
# Security group for the ALB
resource "aws_security_group" "alb" {
  name        = "${local.name_prefix}-alb-sg"
  description = "Security group for the application load balancer"
  vpc_id      = var.vpc_id

  ingress {
    description = "HTTP from internet"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  dynamic "ingress" {
    for_each = var.enable_https ? [1] : []
    content {
      description = "HTTPS from internet"
      from_port   = 443
      to_port     = 443
      protocol    = "tcp"
      cidr_blocks = ["0.0.0.0/0"]
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
      Name = "${local.name_prefix}-alb-sg"
    }
  )
}

# Security group for ECS tasks
resource "aws_security_group" "ecs_tasks" {
  name        = "${local.name_prefix}-ecs-tasks-sg"
  description = "Security group for the ECS tasks"
  vpc_id      = var.vpc_id

  # Allow inbound traffic from ALB
  ingress {
    description     = "Traffic from ALB"
    from_port       = 0
    to_port         = 65535
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  # Allow inbound traffic from other ECS tasks
  ingress {
    description = "Intra-service communication"
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    self        = true
  }

  # Allow all outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-ecs-tasks-sg"
    }
  )
}

# 5. Application Load Balancer (ALB)
resource "aws_lb" "main" {
  name               = "${local.name_prefix}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = var.public_subnet_ids

  enable_deletion_protection = var.environment == "production" ? true : false

  tags = local.common_tags
}

# HTTP Listener - either the main listener or redirect to HTTPS
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = var.enable_https && var.certificate_arn != "" ? "redirect" : "fixed-response"

    dynamic "redirect" {
      for_each = var.enable_https && var.certificate_arn != "" ? [1] : []
      content {
        port        = "443"
        protocol    = "HTTPS"
        status_code = "HTTP_301"
      }
    }

    dynamic "fixed_response" {
      for_each = !var.enable_https || var.certificate_arn == "" ? [1] : []
      content {
        content_type = "text/plain"
        message_body = "Not Found"
        status_code  = "404"
      }
    }
  }
}

# HTTPS Listener (if enabled)
resource "aws_lb_listener" "https" {
  count = var.enable_https && var.certificate_arn != "" ? 1 : 0

  load_balancer_arn = aws_lb.main.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS-1-2-2017-01"
  certificate_arn   = var.certificate_arn

  default_action {
    type = "fixed-response"

    fixed_response {
      content_type = "text/plain"
      message_body = "Not Found"
      status_code  = "404"
    }
  }
}

# 6. CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "ecs_logs" {
  for_each = local.services

  name              = "/ecs/${var.environment}/${each.value.name}"
  retention_in_days = var.log_retention_in_days

  tags = local.common_tags
}

# 7. Service Discovery
resource "aws_service_discovery_private_dns_namespace" "main" {
  name        = "${var.namespace}.${var.environment}.local"
  description = "Service discovery namespace for the Task Management System"
  vpc         = var.vpc_id
  
  tags = local.common_tags
}

# Create service discovery resources for each service
resource "aws_service_discovery_service" "services" {
  for_each = {
    for k, v in local.services : k => v
    if v.service_discovery
  }

  name = each.value.name

  dns_config {
    namespace_id = aws_service_discovery_private_dns_namespace.main.id
    
    dns_records {
      ttl  = 10
      type = "A"
    }

    routing_policy = "MULTIVALUE"
  }

  health_check_custom_config {
    failure_threshold = 1
  }

  tags = local.common_tags
}

# 8. Target Groups and Listener Rules for public services
resource "aws_lb_target_group" "services" {
  for_each = {
    for k, v in local.services : k => v
    if v.public_service
  }

  name        = "${local.name_prefix}-${each.value.name}-tg"
  port        = each.value.container_port
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"
  
  health_check {
    healthy_threshold   = 3
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    path                = each.value.health_check_path
    port                = "traffic-port"
    matcher             = "200"
  }

  tags = local.common_tags

  lifecycle {
    create_before_destroy = true
  }
}

# ALB Listener Rules for each public service
resource "aws_lb_listener_rule" "services_http" {
  for_each = {
    for k, v in local.services : k => v
    if v.public_service && (!var.enable_https || var.certificate_arn == "")
  }

  listener_arn = aws_lb_listener.http.arn
  priority     = 100 + index(keys({
    for k, v in local.services : k => v
    if v.public_service
  }), each.key)

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.services[each.key].arn
  }

  condition {
    path_pattern {
      values = each.value.path_patterns
    }
  }
}

resource "aws_lb_listener_rule" "services_https" {
  for_each = {
    for k, v in local.services : k => v
    if v.public_service && var.enable_https && var.certificate_arn != ""
  }

  listener_arn = aws_lb_listener.https[0].arn
  priority     = 100 + index(keys({
    for k, v in local.services : k => v
    if v.public_service
  }), each.key)

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.services[each.key].arn
  }

  condition {
    path_pattern {
      values = each.value.path_patterns
    }
  }
}

# 9. ECS Services
resource "aws_ecs_service" "services" {
  for_each = local.services

  name                               = "${local.name_prefix}-${each.value.name}"
  cluster                            = aws_ecs_cluster.main.id
  task_definition                    = each.value.name # This will be overridden by the deployment
  desired_count                      = each.value.desired_count
  launch_type                        = each.value.spot_enabled ? null : "FARGATE"
  platform_version                   = var.fargate_platform_version
  health_check_grace_period_seconds  = each.value.public_service ? 60 : null
  propagate_tags                     = "SERVICE"
  enable_execute_command             = true # Allow exec into containers for debugging
  
  dynamic "capacity_provider_strategy" {
    for_each = each.value.spot_enabled ? [1] : []
    content {
      capacity_provider = "FARGATE_SPOT"
      weight            = 1
    }
  }

  dynamic "capacity_provider_strategy" {
    for_each = each.value.spot_enabled ? [] : [1]
    content {
      capacity_provider = "FARGATE"
      weight            = 1
    }
  }

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = false
  }

  dynamic "load_balancer" {
    for_each = each.value.public_service ? [1] : []
    content {
      target_group_arn = aws_lb_target_group.services[each.key].arn
      container_name   = each.value.name
      container_port   = each.value.container_port
    }
  }

  dynamic "service_registries" {
    for_each = each.value.service_discovery ? [1] : []
    content {
      registry_arn = aws_service_discovery_service.services[each.key].arn
    }
  }
  
  # Required placeholder task definition - will be overridden by deployments
  # We're creating a dummy placeholder as Terraform requires a valid task definition
  # but in practice, this will be managed by the CI/CD pipeline
  lifecycle {
    ignore_changes = [
      task_definition,
      desired_count,
      load_balancer
    ]
  }

  tags = local.common_tags
}

# 10. Auto Scaling
resource "aws_appautoscaling_target" "services" {
  for_each = {
    for k, v in local.services : k => v
    if v.auto_scaling != null
  }

  max_capacity       = each.value.auto_scaling.max_capacity
  min_capacity       = each.value.auto_scaling.min_capacity
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.services[each.key].name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

# CPU-based auto scaling
resource "aws_appautoscaling_policy" "cpu" {
  for_each = {
    for k, v in local.services : k => v
    if v.auto_scaling != null
  }

  name               = "${local.name_prefix}-${each.value.name}-cpu-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.services[each.key].resource_id
  scalable_dimension = aws_appautoscaling_target.services[each.key].scalable_dimension
  service_namespace  = aws_appautoscaling_target.services[each.key].service_namespace

  target_tracking_scaling_policy_configuration {
    target_value       = each.value.auto_scaling.cpu_threshold
    scale_in_cooldown  = 300
    scale_out_cooldown = 60

    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
  }
}

# Memory-based auto scaling
resource "aws_appautoscaling_policy" "memory" {
  for_each = {
    for k, v in local.services : k => v
    if v.auto_scaling != null
  }

  name               = "${local.name_prefix}-${each.value.name}-memory-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.services[each.key].resource_id
  scalable_dimension = aws_appautoscaling_target.services[each.key].scalable_dimension
  service_namespace  = aws_appautoscaling_target.services[each.key].service_namespace

  target_tracking_scaling_policy_configuration {
    target_value       = each.value.auto_scaling.memory_threshold
    scale_in_cooldown  = 300
    scale_out_cooldown = 60

    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageMemoryUtilization"
    }
  }
}

# Request count based auto scaling for services with load balancers
resource "aws_appautoscaling_policy" "request_count" {
  for_each = {
    for k, v in local.services : k => v
    if v.auto_scaling != null && v.public_service
  }

  name               = "${local.name_prefix}-${each.value.name}-request-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.services[each.key].resource_id
  scalable_dimension = aws_appautoscaling_target.services[each.key].scalable_dimension
  service_namespace  = aws_appautoscaling_target.services[each.key].service_namespace

  target_tracking_scaling_policy_configuration {
    target_value       = 100 # Target 100 requests per target per minute
    scale_in_cooldown  = 300
    scale_out_cooldown = 60

    predefined_metric_specification {
      predefined_metric_type = "ALBRequestCountPerTarget"
      resource_label         = "${aws_lb.main.arn_suffix}/${aws_lb_target_group.services[each.key].arn_suffix}"
    }
  }
}

# Output values
output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = aws_ecs_cluster.main.name
}

output "ecs_cluster_arn" {
  description = "ARN of the ECS cluster"
  value       = aws_ecs_cluster.main.arn
}

output "ecs_task_execution_role_arn" {
  description = "ARN of the ECS task execution role"
  value       = aws_iam_role.ecs_task_execution_role.arn
}

output "ecs_task_role_arn" {
  description = "ARN of the ECS task role"
  value       = aws_iam_role.ecs_task_role.arn
}

output "alb_dns_name" {
  description = "DNS name of the load balancer"
  value       = aws_lb.main.dns_name
}

output "alb_zone_id" {
  description = "Zone ID of the load balancer"
  value       = aws_lb.main.zone_id
}

output "alb_arn" {
  description = "ARN of the load balancer"
  value       = aws_lb.main.arn
}

output "service_discovery_namespace_id" {
  description = "ID of the service discovery namespace"
  value       = aws_service_discovery_private_dns_namespace.main.id
}

output "service_discovery_namespace_name" {
  description = "Name of the service discovery namespace"
  value       = aws_service_discovery_private_dns_namespace.main.name
}

output "service_security_group_id" {
  description = "ID of the security group for ECS tasks"
  value       = aws_security_group.ecs_tasks.id
}

output "services" {
  description = "Map of ECS service details"
  value = {
    for k, v in aws_ecs_service.services : k => {
      name       = v.name
      arn        = v.id
      cluster    = v.cluster
      service_discovery_id = try(aws_service_discovery_service.services[k].id, null)
      target_group_arn = try(aws_lb_target_group.services[k].arn, null)
    }
  }
}