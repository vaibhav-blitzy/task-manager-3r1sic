# Output variables for the compute module that provisions ECS Fargate resources
# for the Task Management System's containerized microservices architecture.

output "cluster_id" {
  description = "The ID of the ECS cluster created for the Task Management System"
  value       = aws_ecs_cluster.main.id
}

output "cluster_arn" {
  description = "The ARN of the ECS cluster for use in resource policies and service definitions"
  value       = aws_ecs_cluster.main.arn
}

output "cluster_name" {
  description = "The name of the ECS cluster for use in service definitions and operational commands"
  value       = aws_ecs_cluster.main.name
}

output "service_security_group_id" {
  description = "The ID of the security group attached to the ECS services for network access control"
  value       = aws_security_group.ecs_tasks.id
}

output "task_execution_role_arn" {
  description = "The ARN of the IAM role used for ECS task execution (pulling container images, writing logs)"
  value       = aws_iam_role.task_execution_role.arn
}

output "task_role_arn" {
  description = "The ARN of the IAM role used by tasks during runtime for accessing AWS resources"
  value       = aws_iam_role.task_role.arn
}

output "alb_dns_name" {
  description = "The DNS name of the application load balancer for accessing the Task Management System"
  value       = aws_lb.main.dns_name
}

output "alb_arn" {
  description = "The ARN of the application load balancer for use in DNS configurations and certificates"
  value       = aws_lb.main.arn
}

output "alb_listener_https_arn" {
  description = "The ARN of the HTTPS listener on the application load balancer for rule attachments"
  value       = aws_lb_listener.https.arn
}

output "service_discovery_namespace_id" {
  description = "The ID of the service discovery namespace for internal microservice communication"
  value       = aws_service_discovery_private_dns_namespace.main.id
}

output "log_group_name" {
  description = "The name of the CloudWatch log group for container logs and monitoring"
  value       = aws_cloudwatch_log_group.ecs_logs.name
}

output "service_arns" {
  description = "A map of service names to their ARNs for service discovery and dependencies"
  value       = { for k, v in aws_ecs_service.service : k => v.id }
}

output "service_names" {
  description = "A map of service identifiers to their names for operational commands and monitoring"
  value       = { for k, v in aws_ecs_service.service : k => v.name }
}

output "target_group_arns" {
  description = "A map of service names to their target group ARNs for load balancer configurations"
  value       = { for k, v in aws_lb_target_group.service : k => v.arn }
}