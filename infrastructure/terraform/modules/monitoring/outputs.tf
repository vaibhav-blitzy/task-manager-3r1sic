# Outputs for the monitoring module that exposes CloudWatch resources and monitoring endpoints

output "cloudwatch_dashboard_arns" {
  description = "The ARNs of the CloudWatch dashboards created for service and system monitoring"
  value       = aws_cloudwatch_dashboard.*.arn
}

output "cloudwatch_alarm_arns" {
  description = "The ARNs of the CloudWatch alarms created for critical service metrics"
  value       = aws_cloudwatch_metric_alarm.*.arn
}

output "log_group_names" {
  description = "The names of CloudWatch Log Groups created for application and service logs"
  value       = aws_cloudwatch_log_group.*.name
}

output "metrics_namespace" {
  description = "The namespace used for custom CloudWatch metrics"
  value       = var.metrics_namespace
}

output "monitoring_role_arn" {
  description = "The ARN of IAM role created for monitoring services"
  value       = aws_iam_role.monitoring.arn
}

output "alarm_topic_arn" {
  description = "The ARN of SNS topic used for CloudWatch alarm notifications"
  value       = aws_sns_topic.alarms.arn
}

output "prometheus_endpoint" {
  description = "The endpoint URL for Prometheus server if deployed"
  value       = var.enable_prometheus ? aws_prometheus_workspace.main[0].prometheus_endpoint : ""
}

output "grafana_endpoint" {
  description = "The endpoint URL for Grafana dashboard if deployed"
  value       = var.enable_grafana ? aws_grafana_workspace.main[0].endpoint : ""
}

output "xray_tracing_enabled" {
  description = "Flag indicating whether X-Ray tracing is enabled"
  value       = var.enable_xray_tracing
}

output "security_dashboard_url" {
  description = "URL for security monitoring dashboard"
  value       = var.enable_security_dashboard ? aws_cloudwatch_dashboard.security[0].dashboard_arn : ""
}