output "vpc_id" {
  description = "The ID of the VPC"
  value       = aws_vpc.this.id
}

output "vpc_cidr_block" {
  description = "The CIDR block of the VPC"
  value       = aws_vpc.this.cidr_block
}

output "public_subnet_ids" {
  description = "List of IDs of public subnets"
  value       = aws_subnet.public[*].id
}

output "private_app_subnet_ids" {
  description = "List of IDs of private application subnets"
  value       = aws_subnet.private_app[*].id
}

output "private_data_subnet_ids" {
  description = "List of IDs of private data subnets"
  value       = aws_subnet.private_data[*].id
}

output "nat_gateway_ids" {
  description = "List of NAT Gateway IDs"
  value       = aws_nat_gateway.this[*].id
}

output "internet_gateway_id" {
  description = "ID of the Internet Gateway"
  value       = aws_internet_gateway.this.id
}

output "load_balancer_security_group_id" {
  description = "ID of the security group for load balancers"
  value       = aws_security_group.alb.id
}

output "application_security_group_id" {
  description = "ID of the security group for application services"
  value       = aws_security_group.app.id
}

output "database_security_group_id" {
  description = "ID of the security group for database services"
  value       = aws_security_group.data.id
}

output "vpc_endpoint_s3_id" {
  description = "ID of the VPC endpoint for S3"
  value       = aws_vpc_endpoint.s3.id
}

output "availability_zones" {
  description = "List of availability zones used"
  value       = var.availability_zones
}

output "public_route_table_id" {
  description = "ID of the public route table"
  value       = aws_route_table.public.id
}

output "private_route_table_ids" {
  description = "List of IDs of private route tables"
  value       = aws_route_table.private[*].id
}

output "nat_gateway_public_ips" {
  description = "List of public IPs of the NAT Gateways"
  value       = aws_nat_gateway.this[*].public_ip
}