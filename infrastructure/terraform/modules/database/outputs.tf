# MongoDB/DocumentDB Outputs
output "mongodb_connection_string" {
  description = "MongoDB/DocumentDB connection string for application use"
  value       = "mongodb://${var.mongodb_username}:${var.mongodb_password}@${aws_docdb_cluster.mongodb_cluster.endpoint}:${aws_docdb_cluster.mongodb_cluster.port}/${var.mongodb_database}?tls=true&replicaSet=rs0&readPreference=secondaryPreferred&retryWrites=false"
  sensitive   = true
}

output "mongodb_endpoint" {
  description = "MongoDB/DocumentDB cluster endpoint"
  value       = aws_docdb_cluster.mongodb_cluster.endpoint
}

output "mongodb_port" {
  description = "MongoDB/DocumentDB cluster port"
  value       = aws_docdb_cluster.mongodb_cluster.port
}

output "mongodb_cluster_id" {
  description = "MongoDB/DocumentDB cluster identifier"
  value       = aws_docdb_cluster.mongodb_cluster.id
}

output "mongodb_security_group_id" {
  description = "Security group ID for MongoDB/DocumentDB cluster"
  value       = aws_security_group.mongodb_sg.id
}

# Redis ElastiCache Outputs
output "redis_primary_endpoint" {
  description = "Primary endpoint address of the Redis ElastiCache cluster"
  value       = aws_elasticache_replication_group.redis_cluster.primary_endpoint_address
}

output "redis_reader_endpoint" {
  description = "Reader endpoint address of the Redis ElastiCache cluster"
  value       = aws_elasticache_replication_group.redis_cluster.reader_endpoint_address
}

output "redis_port" {
  description = "Port number for the Redis ElastiCache cluster"
  value       = aws_elasticache_replication_group.redis_cluster.port
}

output "redis_connection_string" {
  description = "Redis connection string for application use"
  value       = "redis://${aws_elasticache_replication_group.redis_cluster.primary_endpoint_address}:${aws_elasticache_replication_group.redis_cluster.port}"
  sensitive   = true
}

output "redis_cluster_id" {
  description = "Redis ElastiCache cluster identifier"
  value       = aws_elasticache_replication_group.redis_cluster.id
}

output "redis_security_group_id" {
  description = "Security group ID for Redis ElastiCache cluster"
  value       = aws_security_group.redis_sg.id
}

# Secrets Manager Output
output "database_secrets_arn" {
  description = "ARN of the AWS Secrets Manager secret containing database credentials"
  value       = aws_secretsmanager_secret.database_credentials.arn
}