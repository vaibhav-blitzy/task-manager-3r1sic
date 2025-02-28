# Core infrastructure outputs
output "vpc_id" {
  description = "ID of the VPC created for the Task Management System"
  value       = module.vpc.vpc_id
}

output "public_subnet_ids" {
  description = "IDs of the public subnets where the load balancers are deployed"
  value       = module.vpc.public_subnets
}

output "private_subnet_ids" {
  description = "IDs of the private subnets where the application services are deployed"
  value       = module.vpc.private_subnets
}

output "private_data_subnet_ids" {
  description = "IDs of the private subnets where databases are deployed"
  value       = module.vpc.database_subnets
}

# Load balancer outputs
output "alb_dns_name" {
  description = "DNS name of the application load balancer"
  value       = module.alb.lb_dns_name
}

output "alb_zone_id" {
  description = "Route 53 zone ID of the application load balancer for DNS record creation"
  value       = module.alb.lb_zone_id
}

# CloudFront outputs
output "cloudfront_distribution_id" {
  description = "ID of the CloudFront distribution"
  value       = aws_cloudfront_distribution.main.id
}

output "cloudfront_domain_name" {
  description = "Domain name of the CloudFront distribution"
  value       = aws_cloudfront_distribution.main.domain_name
}

# ECS outputs
output "ecs_cluster_name" {
  description = "Name of the ECS cluster for the application services"
  value       = aws_ecs_cluster.main.name
}

output "ecs_cluster_arn" {
  description = "ARN of the ECS cluster for the application services"
  value       = aws_ecs_cluster.main.arn
}

# Database outputs
output "mongodb_endpoint" {
  description = "Endpoint URL for the MongoDB cluster (without credentials)"
  value       = module.mongodb.endpoint
}

output "redis_endpoint" {
  description = "Endpoint URL for the Redis cluster (without credentials)"
  value       = module.elasticache.redis_endpoint
}

# Storage outputs
output "s3_bucket_name" {
  description = "Name of the S3 bucket used for file storage"
  value       = aws_s3_bucket.file_storage.bucket
}

output "s3_bucket_arn" {
  description = "ARN of the S3 bucket used for file storage"
  value       = aws_s3_bucket.file_storage.arn
}

# Monitoring outputs
output "cloudwatch_dashboard_url" {
  description = "URL of the CloudWatch dashboard for monitoring the application"
  value       = "https://console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${aws_cloudwatch_dashboard.main.dashboard_name}"
}

# Container registry output
output "ecr_repository_url" {
  description = "URL of the ECR repository for storing container images"
  value       = aws_ecr_repository.main.repository_url
}

# API Gateway output
output "api_gateway_url" {
  description = "URL of the API Gateway for the Task Management System"
  value       = aws_api_gateway_deployment.main.invoke_url
}