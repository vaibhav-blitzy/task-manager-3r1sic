# Terraform module that provisions comprehensive monitoring infrastructure for the Task Management System

provider "aws" {
  region = var.region
}

# Random provider for resource naming if needed
provider "random" {
}

# Local variables for naming convention and common tags
locals {
  name_prefix = "${var.resource_prefix}-${var.environment}"
  metric_namespace = "TaskManagementSystem"
  common_tags = merge(
    var.tags,
    {
      Environment = var.environment
      ManagedBy = "Terraform"
      Module = "monitoring"
    }
  )
}

# Create CloudWatch log groups for each service component
resource "aws_cloudwatch_log_group" "api_gateway" {
  name              = "${local.name_prefix}-api-gateway-logs"
  retention_in_days = var.cloudwatch_log_retention_days
  tags              = local.common_tags
}

resource "aws_cloudwatch_log_group" "auth_service" {
  name              = "${local.name_prefix}-auth-service-logs"
  retention_in_days = var.cloudwatch_log_retention_days
  tags              = local.common_tags
}

resource "aws_cloudwatch_log_group" "task_service" {
  name              = "${local.name_prefix}-task-service-logs"
  retention_in_days = var.cloudwatch_log_retention_days
  tags              = local.common_tags
}

resource "aws_cloudwatch_log_group" "project_service" {
  name              = "${local.name_prefix}-project-service-logs"
  retention_in_days = var.cloudwatch_log_retention_days
  tags              = local.common_tags
}

resource "aws_cloudwatch_log_group" "notification_service" {
  name              = "${local.name_prefix}-notification-service-logs"
  retention_in_days = var.cloudwatch_log_retention_days
  tags              = local.common_tags
}

resource "aws_cloudwatch_log_group" "file_service" {
  name              = "${local.name_prefix}-file-service-logs"
  retention_in_days = var.cloudwatch_log_retention_days
  tags              = local.common_tags
}

resource "aws_cloudwatch_log_group" "analytics_service" {
  name              = "${local.name_prefix}-analytics-service-logs"
  retention_in_days = var.cloudwatch_log_retention_days
  tags              = local.common_tags
}

resource "aws_cloudwatch_log_group" "realtime_service" {
  name              = "${local.name_prefix}-realtime-service-logs"
  retention_in_days = var.cloudwatch_log_retention_days
  tags              = local.common_tags
}

# Create SNS topic for CloudWatch alarm notifications
resource "aws_sns_topic" "alarm_notifications" {
  name = "${local.name_prefix}-alarm-notifications"
  tags = local.common_tags
}

# Create email subscription for alarm notifications if email is provided
resource "aws_sns_topic_subscription" "email_subscription" {
  count     = var.alarm_notification_email != "" ? 1 : 0
  topic_arn = aws_sns_topic.alarm_notifications.arn
  protocol  = "email"
  endpoint  = var.alarm_notification_email
}

# CloudWatch alarms for critical service metrics
resource "aws_cloudwatch_metric_alarm" "cpu_utilization_high" {
  alarm_name          = "${local.name_prefix}-high-cpu-utilization"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = 300
  statistic           = "Average"
  threshold           = var.cpu_utilization_threshold
  alarm_description   = "This metric monitors ECS service CPU utilization"
  alarm_actions       = [aws_sns_topic.alarm_notifications.arn]
  ok_actions          = [aws_sns_topic.alarm_notifications.arn]
  dimensions = {
    ClusterName = "${var.environment}-task-management-cluster"
  }
  tags = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "memory_utilization_high" {
  alarm_name          = "${local.name_prefix}-high-memory-utilization"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "MemoryUtilization"
  namespace           = "AWS/ECS"
  period              = 300
  statistic           = "Average"
  threshold           = var.memory_utilization_threshold
  alarm_description   = "This metric monitors ECS service memory utilization"
  alarm_actions       = [aws_sns_topic.alarm_notifications.arn]
  ok_actions          = [aws_sns_topic.alarm_notifications.arn]
  dimensions = {
    ClusterName = "${var.environment}-task-management-cluster"
  }
  tags = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "api_latency_high" {
  alarm_name          = "${local.name_prefix}-high-api-latency"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "Latency"
  namespace           = "AWS/ApplicationELB"
  period              = 300
  statistic           = "p95"
  threshold           = var.api_latency_threshold
  alarm_description   = "This metric monitors API gateway response latency"
  alarm_actions       = [aws_sns_topic.alarm_notifications.arn]
  ok_actions          = [aws_sns_topic.alarm_notifications.arn]
  dimensions = {
    LoadBalancer = "app/task-management-alb/${var.environment}"
  }
  tags = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "api_5xx_errors" {
  alarm_name          = "${local.name_prefix}-api-5xx-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "HTTPCode_ELB_5XX_Count"
  namespace           = "AWS/ApplicationELB"
  period              = 300
  statistic           = "Sum"
  threshold           = 10
  alarm_description   = "This metric monitors 5XX errors from the API gateway"
  alarm_actions       = [aws_sns_topic.alarm_notifications.arn]
  ok_actions          = [aws_sns_topic.alarm_notifications.arn]
  dimensions = {
    LoadBalancer = "app/task-management-alb/${var.environment}"
  }
  tags = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "database_connections_high" {
  alarm_name          = "${local.name_prefix}-high-db-connections"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "DatabaseConnections"
  namespace           = "AWS/DocDB"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "This metric monitors database connection count"
  alarm_actions       = [aws_sns_topic.alarm_notifications.arn]
  ok_actions          = [aws_sns_topic.alarm_notifications.arn]
  dimensions = {
    DBClusterIdentifier = "${var.environment}-task-management-db"
  }
  tags = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "cache_cpu_high" {
  alarm_name          = "${local.name_prefix}-high-cache-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ElastiCache"
  period              = 300
  statistic           = "Average"
  threshold           = 70
  alarm_description   = "This metric monitors cache CPU utilization"
  alarm_actions       = [aws_sns_topic.alarm_notifications.arn]
  ok_actions          = [aws_sns_topic.alarm_notifications.arn]
  dimensions = {
    CacheClusterId = "${var.environment}-task-management-redis"
  }
  tags = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "cache_memory_high" {
  alarm_name          = "${local.name_prefix}-high-cache-memory"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "FreeableMemory"
  namespace           = "AWS/ElastiCache"
  period              = 300
  statistic           = "Average"
  threshold           = 100 - var.memory_utilization_threshold
  alarm_description   = "This metric monitors cache freeable memory"
  alarm_actions       = [aws_sns_topic.alarm_notifications.arn]
  ok_actions          = [aws_sns_topic.alarm_notifications.arn]
  dimensions = {
    CacheClusterId = "${var.environment}-task-management-redis"
  }
  tags = local.common_tags
}

# CloudWatch dashboards for service and system monitoring
resource "aws_cloudwatch_dashboard" "services_dashboard" {
  dashboard_name = "${local.name_prefix}-services-dashboard"
  dashboard_body = <<EOF
{
  "widgets": [
    {
      "type": "metric",
      "x": 0,
      "y": 0,
      "width": 12,
      "height": 6,
      "properties": {
        "metrics": [
          [ "AWS/ECS", "CPUUtilization", "ServiceName", "api-gateway", "ClusterName", "${var.environment}-task-management-cluster" ],
          [ "AWS/ECS", "CPUUtilization", "ServiceName", "auth-service", "ClusterName", "${var.environment}-task-management-cluster" ],
          [ "AWS/ECS", "CPUUtilization", "ServiceName", "task-service", "ClusterName", "${var.environment}-task-management-cluster" ],
          [ "AWS/ECS", "CPUUtilization", "ServiceName", "project-service", "ClusterName", "${var.environment}-task-management-cluster" ],
          [ "AWS/ECS", "CPUUtilization", "ServiceName", "notification-service", "ClusterName", "${var.environment}-task-management-cluster" ],
          [ "AWS/ECS", "CPUUtilization", "ServiceName", "file-service", "ClusterName", "${var.environment}-task-management-cluster" ],
          [ "AWS/ECS", "CPUUtilization", "ServiceName", "analytics-service", "ClusterName", "${var.environment}-task-management-cluster" ],
          [ "AWS/ECS", "CPUUtilization", "ServiceName", "realtime-service", "ClusterName", "${var.environment}-task-management-cluster" ]
        ],
        "view": "timeSeries",
        "stacked": false,
        "region": "${var.region}",
        "title": "CPU Utilization by Service",
        "period": 300
      }
    },
    {
      "type": "metric",
      "x": 12,
      "y": 0,
      "width": 12,
      "height": 6,
      "properties": {
        "metrics": [
          [ "AWS/ECS", "MemoryUtilization", "ServiceName", "api-gateway", "ClusterName", "${var.environment}-task-management-cluster" ],
          [ "AWS/ECS", "MemoryUtilization", "ServiceName", "auth-service", "ClusterName", "${var.environment}-task-management-cluster" ],
          [ "AWS/ECS", "MemoryUtilization", "ServiceName", "task-service", "ClusterName", "${var.environment}-task-management-cluster" ],
          [ "AWS/ECS", "MemoryUtilization", "ServiceName", "project-service", "ClusterName", "${var.environment}-task-management-cluster" ],
          [ "AWS/ECS", "MemoryUtilization", "ServiceName", "notification-service", "ClusterName", "${var.environment}-task-management-cluster" ],
          [ "AWS/ECS", "MemoryUtilization", "ServiceName", "file-service", "ClusterName", "${var.environment}-task-management-cluster" ],
          [ "AWS/ECS", "MemoryUtilization", "ServiceName", "analytics-service", "ClusterName", "${var.environment}-task-management-cluster" ],
          [ "AWS/ECS", "MemoryUtilization", "ServiceName", "realtime-service", "ClusterName", "${var.environment}-task-management-cluster" ]
        ],
        "view": "timeSeries",
        "stacked": false,
        "region": "${var.region}",
        "title": "Memory Utilization by Service",
        "period": 300
      }
    },
    {
      "type": "metric",
      "x": 0,
      "y": 6,
      "width": 12,
      "height": 6,
      "properties": {
        "metrics": [
          [ "AWS/ApplicationELB", "RequestCount", "LoadBalancer", "app/task-management-alb/${var.environment}" ]
        ],
        "view": "timeSeries",
        "stacked": false,
        "region": "${var.region}",
        "title": "API Request Count",
        "period": 60
      }
    },
    {
      "type": "metric",
      "x": 12,
      "y": 6,
      "width": 12,
      "height": 6,
      "properties": {
        "metrics": [
          [ "AWS/ApplicationELB", "HTTPCode_Target_2XX_Count", "LoadBalancer", "app/task-management-alb/${var.environment}" ],
          [ "AWS/ApplicationELB", "HTTPCode_Target_4XX_Count", "LoadBalancer", "app/task-management-alb/${var.environment}" ],
          [ "AWS/ApplicationELB", "HTTPCode_Target_5XX_Count", "LoadBalancer", "app/task-management-alb/${var.environment}" ]
        ],
        "view": "timeSeries",
        "stacked": true,
        "region": "${var.region}",
        "title": "API Response Codes",
        "period": 60
      }
    },
    {
      "type": "metric",
      "x": 0,
      "y": 12,
      "width": 12,
      "height": 6,
      "properties": {
        "metrics": [
          [ "AWS/DocDB", "CPUUtilization", "DBClusterIdentifier", "${var.environment}-task-management-db" ],
          [ "AWS/ElastiCache", "CPUUtilization", "CacheClusterId", "${var.environment}-task-management-redis" ]
        ],
        "view": "timeSeries",
        "stacked": false,
        "region": "${var.region}",
        "title": "Database & Cache CPU",
        "period": 300
      }
    },
    {
      "type": "metric",
      "x": 12,
      "y": 12,
      "width": 12,
      "height": 6,
      "properties": {
        "metrics": [
          [ "AWS/ElastiCache", "CacheHits", "CacheClusterId", "${var.environment}-task-management-redis" ],
          [ "AWS/ElastiCache", "CacheMisses", "CacheClusterId", "${var.environment}-task-management-redis" ]
        ],
        "view": "timeSeries",
        "stacked": false,
        "region": "${var.region}",
        "title": "Cache Hit/Miss",
        "period": 300
      }
    }
  ]
}
EOF
  tags = local.common_tags
}

resource "aws_cloudwatch_dashboard" "system_dashboard" {
  dashboard_name = "${local.name_prefix}-system-dashboard"
  dashboard_body = <<EOF
{
  "widgets": [
    {
      "type": "metric",
      "x": 0,
      "y": 0,
      "width": 12,
      "height": 6,
      "properties": {
        "metrics": [
          [ "AWS/Usage", "ResourceCount", "Type", "Resource", "Resource", "AlarmName", "Service", "CloudWatch" ]
        ],
        "view": "timeSeries",
        "stacked": false,
        "region": "${var.region}",
        "title": "CloudWatch Alarms",
        "period": 300
      }
    },
    {
      "type": "metric",
      "x": 12,
      "y": 0,
      "width": 12,
      "height": 6,
      "properties": {
        "metrics": [
          [ "AWS/Logs", "IncomingBytes", "LogGroupName", "${aws_cloudwatch_log_group.api_gateway.name}" ],
          [ "AWS/Logs", "IncomingBytes", "LogGroupName", "${aws_cloudwatch_log_group.auth_service.name}" ],
          [ "AWS/Logs", "IncomingBytes", "LogGroupName", "${aws_cloudwatch_log_group.task_service.name}" ],
          [ "AWS/Logs", "IncomingBytes", "LogGroupName", "${aws_cloudwatch_log_group.project_service.name}" ],
          [ "AWS/Logs", "IncomingBytes", "LogGroupName", "${aws_cloudwatch_log_group.notification_service.name}" ],
          [ "AWS/Logs", "IncomingBytes", "LogGroupName", "${aws_cloudwatch_log_group.file_service.name}" ],
          [ "AWS/Logs", "IncomingBytes", "LogGroupName", "${aws_cloudwatch_log_group.analytics_service.name}" ],
          [ "AWS/Logs", "IncomingBytes", "LogGroupName", "${aws_cloudwatch_log_group.realtime_service.name}" ]
        ],
        "view": "timeSeries",
        "stacked": true,
        "region": "${var.region}",
        "title": "Log Volume by Service",
        "period": 300
      }
    },
    {
      "type": "metric",
      "x": 0,
      "y": 6,
      "width": 24,
      "height": 6,
      "properties": {
        "metrics": [
          [ "AWS/ECS", "RunningTaskCount", "ClusterName", "${var.environment}-task-management-cluster", "ServiceName", "api-gateway" ],
          [ "AWS/ECS", "RunningTaskCount", "ClusterName", "${var.environment}-task-management-cluster", "ServiceName", "auth-service" ],
          [ "AWS/ECS", "RunningTaskCount", "ClusterName", "${var.environment}-task-management-cluster", "ServiceName", "task-service" ],
          [ "AWS/ECS", "RunningTaskCount", "ClusterName", "${var.environment}-task-management-cluster", "ServiceName", "project-service" ],
          [ "AWS/ECS", "RunningTaskCount", "ClusterName", "${var.environment}-task-management-cluster", "ServiceName", "notification-service" ],
          [ "AWS/ECS", "RunningTaskCount", "ClusterName", "${var.environment}-task-management-cluster", "ServiceName", "file-service" ],
          [ "AWS/ECS", "RunningTaskCount", "ClusterName", "${var.environment}-task-management-cluster", "ServiceName", "analytics-service" ],
          [ "AWS/ECS", "RunningTaskCount", "ClusterName", "${var.environment}-task-management-cluster", "ServiceName", "realtime-service" ]
        ],
        "view": "timeSeries",
        "stacked": false,
        "region": "${var.region}",
        "title": "Running Task Count by Service",
        "period": 60
      }
    },
    {
      "type": "metric",
      "x": 0,
      "y": 12,
      "width": 12,
      "height": 6,
      "properties": {
        "metrics": [
          [ "AWS/S3", "BucketSizeBytes", "StorageType", "StandardStorage", "BucketName", "${var.environment}-task-management-files" ]
        ],
        "view": "timeSeries",
        "stacked": false,
        "region": "${var.region}",
        "title": "S3 Storage Used",
        "period": 86400
      }
    },
    {
      "type": "metric",
      "x": 12,
      "y": 12,
      "width": 12,
      "height": 6,
      "properties": {
        "metrics": [
          [ "AWS/S3", "AllRequests", "BucketName", "${var.environment}-task-management-files" ],
          [ "AWS/S3", "GetRequests", "BucketName", "${var.environment}-task-management-files" ],
          [ "AWS/S3", "PutRequests", "BucketName", "${var.environment}-task-management-files" ]
        ],
        "view": "timeSeries",
        "stacked": false,
        "region": "${var.region}",
        "title": "S3 Request Count",
        "period": 300
      }
    }
  ]
}
EOF
  tags = local.common_tags
}

# IAM role and policy for monitoring services
resource "aws_iam_role" "monitoring_role" {
  name = "${local.name_prefix}-monitoring-role"
  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "monitoring.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
  tags = local.common_tags
}

resource "aws_iam_policy" "monitoring_policy" {
  name = "${local.name_prefix}-monitoring-policy"
  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudwatch:*",
        "logs:*",
        "xray:*"
      ],
      "Resource": "*"
    }
  ]
}
EOF
  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "monitoring_attachment" {
  role       = aws_iam_role.monitoring_role.name
  policy_arn = aws_iam_policy.monitoring_policy.arn
}

# X-Ray sampling rules for tracing
resource "aws_xray_sampling_rule" "api_tracing" {
  count         = var.enable_x_ray ? 1 : 0
  rule_name     = "${local.name_prefix}-api-tracing"
  priority      = 10
  reservoir_size = 1
  fixed_rate    = 0.05
  url_path      = "/api/*"
  host          = "*"
  http_method   = "*"
  service_name  = "*"
  service_type  = "*"
  resource_arn  = "*"
  attributes = {
    environment = var.environment
  }
  tags = local.common_tags
}

# CloudWatch Log Metric Filters
resource "aws_cloudwatch_log_metric_filter" "api_errors" {
  name            = "${local.name_prefix}-api-errors"
  pattern         = "ERROR"
  log_group_name  = aws_cloudwatch_log_group.api_gateway.name

  metric_transformation {
    name          = "ApiErrorCount"
    namespace     = local.metric_namespace
    value         = "1"
    default_value = "0"
  }
}

resource "aws_cloudwatch_log_metric_filter" "auth_failures" {
  name            = "${local.name_prefix}-auth-failures"
  pattern         = "Authentication failed"
  log_group_name  = aws_cloudwatch_log_group.auth_service.name

  metric_transformation {
    name          = "AuthFailureCount"
    namespace     = local.metric_namespace
    value         = "1"
    default_value = "0"
  }
}

resource "aws_cloudwatch_log_metric_filter" "task_created" {
  name            = "${local.name_prefix}-task-created"
  pattern         = "Task created"
  log_group_name  = aws_cloudwatch_log_group.task_service.name

  metric_transformation {
    name          = "TaskCreatedCount"
    namespace     = local.metric_namespace
    value         = "1"
    default_value = "0"
  }
}

resource "aws_cloudwatch_log_metric_filter" "task_completed" {
  name            = "${local.name_prefix}-task-completed"
  pattern         = "Task status changed to Completed"
  log_group_name  = aws_cloudwatch_log_group.task_service.name

  metric_transformation {
    name          = "TaskCompletedCount"
    namespace     = local.metric_namespace
    value         = "1"
    default_value = "0"
  }
}

# Data source for Amazon Linux 2 AMI
data "aws_ami" "amazon_linux_2" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# Conditionally create Prometheus resources if enabled
resource "aws_iam_instance_profile" "prometheus_profile" {
  count = var.enable_prometheus ? 1 : 0
  name = "${local.name_prefix}-prometheus-profile"
  role = aws_iam_role.prometheus_role[0].name
}

resource "aws_iam_role" "prometheus_role" {
  count = var.enable_prometheus ? 1 : 0
  name = "${local.name_prefix}-prometheus-role"
  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "prometheus_cloudwatch" {
  count = var.enable_prometheus ? 1 : 0
  role = aws_iam_role.prometheus_role[0].name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchReadOnlyAccess"
}

resource "aws_instance" "prometheus" {
  count = var.enable_prometheus ? 1 : 0
  ami = data.aws_ami.amazon_linux_2.id
  instance_type = var.prometheus_instance_type
  subnet_id = var.subnet_ids[0]
  vpc_security_group_ids = var.monitoring_security_group_ids
  iam_instance_profile = aws_iam_instance_profile.prometheus_profile[0].name
  user_data = file("${path.module}/scripts/setup_prometheus.sh")
  
  root_block_device {
    volume_size = var.prometheus_storage_size
    volume_type = "gp3"
  }
  
  tags = merge(local.common_tags, {Name = "${local.name_prefix}-prometheus"})
}

# Conditionally create Grafana resources if enabled
resource "aws_iam_instance_profile" "grafana_profile" {
  count = var.enable_grafana ? 1 : 0
  name = "${local.name_prefix}-grafana-profile"
  role = aws_iam_role.grafana_role[0].name
}

resource "aws_iam_role" "grafana_role" {
  count = var.enable_grafana ? 1 : 0
  name = "${local.name_prefix}-grafana-role"
  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "grafana_cloudwatch" {
  count = var.enable_grafana ? 1 : 0
  role = aws_iam_role.grafana_role[0].name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchReadOnlyAccess"
}

resource "aws_instance" "grafana" {
  count = var.enable_grafana ? 1 : 0
  ami = data.aws_ami.amazon_linux_2.id
  instance_type = var.grafana_instance_type
  subnet_id = var.subnet_ids[0]
  vpc_security_group_ids = var.monitoring_security_group_ids
  iam_instance_profile = aws_iam_instance_profile.grafana_profile[0].name
  
  user_data = templatefile("${path.module}/scripts/setup_grafana.sh.tpl", {
    admin_password = var.grafana_admin_password
    prometheus_endpoint = var.enable_prometheus ? aws_instance.prometheus[0].private_ip : ""
  })
  
  tags = merge(local.common_tags, {Name = "${local.name_prefix}-grafana"})
}