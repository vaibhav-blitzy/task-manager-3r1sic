# Task Management System Troubleshooting Guide

## Introduction

This troubleshooting guide provides comprehensive information for diagnosing and resolving common issues in the Task Management System. It is intended for system administrators, DevOps engineers, and support personnel responsible for maintaining system operations.

The guide covers all major components of the Task Management System, including:
- Microservices (Authentication, Task, Project, Notification, File, and Analytics services)
- Databases (MongoDB and Redis)
- Infrastructure (API Gateway, Containers, Networks)
- Performance and security concerns
- Logging and monitoring tools
- Recovery procedures for various failure scenarios

When troubleshooting issues, follow these general principles:
1. Identify symptoms precisely
2. Check recent changes or deployments
3. Consult monitoring dashboards and logs
4. Isolate the affected component
5. Apply the specific troubleshooting steps in this guide
6. Document the resolution for future reference

## Microservices Troubleshooting

### Authentication Service Issues

#### Login Failures

**Symptoms:**
- Users unable to log in despite correct credentials
- High rate of 401 Unauthorized responses
- Authentication service logs showing validation errors

**Diagnostic Steps:**
1. Check Authentication service logs at `/var/log/taskmanagement/auth-service.log`
2. Verify Auth0 service status in the monitoring dashboard
3. Examine JWT validation errors in logs
4. Check Redis connection for token storage

**Resolution:**
```bash
# Check Auth service health
curl -X GET https://api.taskmanagement.com/auth/health

# Restart Auth service if needed
aws ecs update-service --cluster task-management-prod --service auth-service --force-new-deployment

# Check Redis connectivity
redis-cli -h redis.taskmanagement.internal ping
```

**Prevention:**
- Monitor Auth0 rate limiting
- Set up alerts for authentication failure rate spikes
- Implement circuit breakers for downstream dependencies

#### Token Validation Errors

**Symptoms:**
- Users suddenly logged out
- API requests failing with 401 errors
- JWT verification errors in logs

**Diagnostic Steps:**
1. Check for expired or malformed JWTs in auth service logs
2. Verify public key configuration for JWT verification
3. Check for clock skew between services

**Resolution:**
```bash
# Verify JWT configuration
curl -X GET https://api.taskmanagement.com/auth/jwks

# Update authentication keys if needed
aws ssm put-parameter --name "/taskmanagement/prod/auth/jwt-public-key" --value "$(cat new-public-key.pem)" --type SecureString --overwrite
```

#### MFA Issues

**Symptoms:**
- Users unable to complete MFA verification
- Timeout errors during MFA process
- MFA delivery failures (SMS/email)

**Diagnostic Steps:**
1. Check MFA provider status (Auth0/Twilio)
2. Examine MFA delivery logs
3. Verify rate limiting status

**Resolution:**
```bash
# Temporarily disable MFA for specific user (emergency access)
curl -X PATCH https://api.taskmanagement.com/auth/users/{userId} \
  -H "Authorization: Bearer {admin-token}" \
  -d '{"mfaEnabled": false}'

# Reset MFA configuration
curl -X POST https://api.taskmanagement.com/auth/users/{userId}/reset-mfa \
  -H "Authorization: Bearer {admin-token}"
```

### Task & Project Service Issues

#### Task Creation Failures

**Symptoms:**
- "Failed to create task" errors in UI
- 500 error responses from Task API
- Error logs showing validation or persistence issues

**Diagnostic Steps:**
1. Check Task service logs at `/var/log/taskmanagement/task-service.log`
2. Verify MongoDB connection status
3. Check for validation errors in the request payload
4. Inspect associated project access permissions

**Resolution:**
```bash
# Check Task service health
curl -X GET https://api.taskmanagement.com/tasks/health

# Verify MongoDB connectivity
mongosh --host mongodb.taskmanagement.internal --eval "db.adminCommand('ping')"

# Restart Task service if needed
aws ecs update-service --cluster task-management-prod --service task-service --force-new-deployment
```

#### Project Access Problems

**Symptoms:**
- Users unable to access projects they should have permission for
- Missing projects in user's project list
- Permission denied errors when accessing project resources

**Diagnostic Steps:**
1. Check user's role assignments in auth database
2. Verify project membership records
3. Check for cached permission data in Redis

**Resolution:**
```bash
# Query user permissions
mongosh --host mongodb.taskmanagement.internal --eval "db.projectMembers.find({userId: 'user-id-here'})"

# Clear permissions cache for user
redis-cli -h redis.taskmanagement.internal DEL "permissions:user-id-here"

# Manually add user to project (if needed)
curl -X POST https://api.taskmanagement.com/projects/{projectId}/members \
  -H "Authorization: Bearer {admin-token}" \
  -d '{"userId": "user-id-here", "role": "member"}'
```

#### Data Consistency Issues

**Symptoms:**
- Task status inconsistent across views
- Missing subtasks or attachments
- Completed tasks reappearing as incomplete

**Diagnostic Steps:**
1. Check for failed event processing in logs
2. Verify synchronization between services
3. Look for database replication issues

**Resolution:**
```bash
# Force cache refresh for specific task
redis-cli -h redis.taskmanagement.internal DEL "task:task-id-here"

# Verify task state in database
mongosh --host mongodb.taskmanagement.internal --eval "db.tasks.findOne({_id: 'task-id-here'})"

# Trigger manual synchronization
curl -X POST https://api.taskmanagement.com/admin/synchronize \
  -H "Authorization: Bearer {admin-token}" \
  -d '{"entity": "task", "id": "task-id-here"}'
```

### Notification Service Issues

#### Email Delivery Failures

**Symptoms:**
- Users not receiving email notifications
- High failure rate in notification logs
- SendGrid API errors

**Diagnostic Steps:**
1. Check Notification service logs at `/var/log/taskmanagement/notification-service.log`
2. Verify SendGrid API status and quota
3. Look for malformed email addresses or content
4. Check email delivery logs in SendGrid dashboard

**Resolution:**
```bash
# Check email delivery queue status
redis-cli -h redis.taskmanagement.internal LLEN "queue:email"

# Force retry of failed notifications
curl -X POST https://api.taskmanagement.com/admin/notifications/retry \
  -H "Authorization: Bearer {admin-token}" \
  -d '{"type": "email", "minutes": 60}'

# Verify SendGrid API key
aws secretsmanager get-secret-value --secret-id taskmanagement/prod/sendgrid-api-key
```

**Prevention:**
- Monitor SendGrid quota and delivery rates
- Implement email validation before queuing
- Set up redundant email providers

#### Push Notification Problems

**Symptoms:**
- Mobile users not receiving push notifications
- Firebase/APNS errors in notification logs
- Device token registration issues

**Diagnostic Steps:**
1. Check push notification delivery logs
2. Verify Firebase/APNS connectivity
3. Inspect device token validity

**Resolution:**
```bash
# Check push notification queue
redis-cli -h redis.taskmanagement.internal LLEN "queue:push"

# Verify Firebase configuration
aws secretsmanager get-secret-value --secret-id taskmanagement/prod/firebase-config

# Clear invalid device tokens
curl -X POST https://api.taskmanagement.com/admin/notifications/cleanup-tokens \
  -H "Authorization: Bearer {admin-token}"
```

#### Notification Queue Backlog

**Symptoms:**
- Delayed notifications
- Growing queue size in monitoring
- High CPU usage in Notification service

**Diagnostic Steps:**
1. Check queue length metrics in CloudWatch
2. Monitor notification processing rate
3. Look for errors causing processing failures

**Resolution:**
```bash
# Check queue status
redis-cli -h redis.taskmanagement.internal INFO | grep list

# Increase notification worker capacity
aws ecs update-service --cluster task-management-prod --service notification-service --desired-count 6

# For critical backlog, consider selective purging of older items
redis-cli -h redis.taskmanagement.internal LREM "queue:email" -100 "*"
```

### File Service Issues

#### File Upload Failures

**Symptoms:**
- Unable to upload files in UI
- Timeout errors during upload
- S3 connectivity issues in logs

**Diagnostic Steps:**
1. Check File service logs at `/var/log/taskmanagement/file-service.log`
2. Verify S3 bucket permissions and connectivity
3. Check for file size or type restriction issues
4. Monitor upload bandwith and latency

**Resolution:**
```bash
# Check S3 connectivity
aws s3 ls s3://taskmanagement-files-prod/

# Verify IAM role permissions
aws iam get-role-policy --role-name TaskManagement-FileService-Role --policy-name S3Access

# Restart File service if needed
aws ecs update-service --cluster task-management-prod --service file-service --force-new-deployment
```

#### Download Failures

**Symptoms:**
- File download links not working
- Access denied errors when downloading
- Expired signed URLs

**Diagnostic Steps:**
1. Check for expired presigned URLs
2. Verify file exists in S3
3. Check file permissions for the user

**Resolution:**
```bash
# Verify file exists
aws s3 ls s3://taskmanagement-files-prod/files/file-id-here

# Generate new presigned URL
curl -X GET https://api.taskmanagement.com/files/{fileId}/download-url \
  -H "Authorization: Bearer {admin-token}"
```

#### Virus Scanning Issues

**Symptoms:**
- Files stuck in "scanning" status
- Scan service failures in logs
- False positive virus detections

**Diagnostic Steps:**
1. Check virus scanning service health
2. Verify ClamAV definitions are updated
3. Look for scanning timeout issues

**Resolution:**
```bash
# Check scanning service health
curl -X GET https://api.taskmanagement.com/files/scanning/health

# Manually trigger scan completion
curl -X POST https://api.taskmanagement.com/admin/files/{fileId}/scan-complete \
  -H "Authorization: Bearer {admin-token}" \
  -d '{"status": "clean"}'
```

### Real-time Service Issues

#### WebSocket Connection Problems

**Symptoms:**
- "Disconnected" alerts in UI
- Real-time updates not appearing
- High rate of WebSocket reconnection attempts

**Diagnostic Steps:**
1. Check Real-time service logs at `/var/log/taskmanagement/realtime-service.log`
2. Verify load balancer WebSocket configurations
3. Check Redis PubSub functionality
4. Monitor client connection errors

**Resolution:**
```bash
# Check WebSocket service health
curl -X GET https://api.taskmanagement.com/realtime/health

# Verify Redis PubSub connectivity
redis-cli -h redis.taskmanagement.internal PUBLISH test_channel "test message"

# Restart Realtime service if needed
aws ecs update-service --cluster task-management-prod --service realtime-service --force-new-deployment
```

#### Presence Tracking Errors

**Symptoms:**
- User online status incorrect
- Presence information out of sync
- Redis timeout errors

**Diagnostic Steps:**
1. Check presence data in Redis
2. Verify heartbeat message processing
3. Look for clock synchronization issues

**Resolution:**
```bash
# Check user presence data
redis-cli -h redis.taskmanagement.internal HGETALL "presence:user-id-here"

# Reset presence data
redis-cli -h redis.taskmanagement.internal DEL "presence:*"
```

#### Event Broadcast Failures

**Symptoms:**
- Real-time updates not propagating to clients
- Message queue growth in Redis
- Channel subscription errors

**Diagnostic Steps:**
1. Check event publication logs
2. Verify client subscription status
3. Monitor Redis PubSub health

**Resolution:**
```bash
# Check channel subscribers
redis-cli -h redis.taskmanagement.internal PUBSUB CHANNELS "task:*"

# Manually publish test event
redis-cli -h redis.taskmanagement.internal PUBLISH "task:update" "{\"id\":\"test\"}"

# Restart problem clients
curl -X POST https://api.taskmanagement.com/admin/realtime/disconnect-clients \
  -H "Authorization: Bearer {admin-token}" \
  -d '{"reason": "maintenance"}'
```

### Analytics Service Issues

#### Report Generation Failures

**Symptoms:**
- Reports failing to generate
- Timeout errors during report creation
- Incomplete or corrupted report data

**Diagnostic Steps:**
1. Check Analytics service logs at `/var/log/taskmanagement/analytics-service.log`
2. Monitor report generation queue
3. Check for database query timeouts
4. Verify data aggregation pipeline

**Resolution:**
```bash
# Check report generation queue
redis-cli -h redis.taskmanagement.internal LLEN "queue:reports"

# Cancel stuck report job
curl -X DELETE https://api.taskmanagement.com/admin/reports/jobs/{jobId} \
  -H "Authorization: Bearer {admin-token}"

# Restart Analytics service
aws ecs update-service --cluster task-management-prod --service analytics-service --force-new-deployment
```

#### Dashboard Rendering Problems

**Symptoms:**
- Dashboards not loading or partially loading
- Chart visualization errors
- Missing metrics data

**Diagnostic Steps:**
1. Check browser console errors
2. Verify metrics data availability
3. Check for dashboard configuration issues

**Resolution:**
```bash
# Verify metrics data exists
curl -X GET https://api.taskmanagement.com/analytics/metrics/task-completion \
  -H "Authorization: Bearer {admin-token}"

# Reset dashboard configuration
curl -X POST https://api.taskmanagement.com/admin/dashboards/{dashboardId}/reset \
  -H "Authorization: Bearer {admin-token}"
```

## Database Troubleshooting

### MongoDB Issues

#### Connectivity Problems

**Symptoms:**
- Services unable to connect to MongoDB
- Connection timeout errors
- High latency in database operations

**Diagnostic Steps:**
1. Check MongoDB server status
2. Verify network connectivity between services and database
3. Monitor connection pool utilization
4. Check for authentication issues

**Resolution:**
```bash
# Check MongoDB status
mongosh --host mongodb.taskmanagement.internal --eval "db.serverStatus()"

# Verify network connectivity
ping mongodb.taskmanagement.internal

# Check authentication configuration
aws secretsmanager get-secret-value --secret-id taskmanagement/prod/mongodb-auth
```

#### Replication Lag

**Symptoms:**
- Data inconsistency between read operations
- Secondary databases falling behind primary
- Replication errors in MongoDB logs

**Diagnostic Steps:**
1. Check replication status and lag
2. Monitor oplog size and growth
3. Check for network issues between replica nodes

**Resolution:**
```bash
# Check replication status
mongosh --host mongodb.taskmanagement.internal --eval "rs.status()"

# Check oplog size and window
mongosh --host mongodb.taskmanagement.internal --eval "db.printReplicationInfo()"

# Force resync of problematic secondary (last resort)
mongosh --host mongodb-secondary.taskmanagement.internal --eval "rs.resync()"
```

#### Query Performance Issues

**Symptoms:**
- Slow API responses
- High database CPU utilization
- Long-running queries in logs

**Diagnostic Steps:**
1. Check MongoDB logs for slow queries
2. Verify index usage on common queries
3. Check for collection scans in query plans

**Resolution:**
```bash
# View slow query log
mongosh --host mongodb.taskmanagement.internal --eval "db.setProfilingLevel(1, 200)"

# Create missing indexes
mongosh --host mongodb.taskmanagement.internal --eval "db.tasks.createIndex({assignedTo: 1, status: 1, dueDate: 1})"

# Kill long-running operations
mongosh --host mongodb.taskmanagement.internal --eval "db.currentOp({op: {$ne: 'none'}, secs_running: {$gt: 300}})" | grep opid
mongosh --host mongodb.taskmanagement.internal --eval "db.killOp(opid)"
```

### Redis Issues

#### Cache Consistency

**Symptoms:**
- Stale data served to users
- Cache miss ratio spikes
- Inconsistent UI state between users

**Diagnostic Steps:**
1. Monitor cache hit/miss rates
2. Check TTL settings for cached items
3. Verify cache invalidation events

**Resolution:**
```bash
# Check cache stats
redis-cli -h redis.taskmanagement.internal INFO stats

# Force cache invalidation for specific entity
redis-cli -h redis.taskmanagement.internal KEYS "task:*" | xargs redis-cli -h redis.taskmanagement.internal DEL

# Reset all application cache (emergency only)
redis-cli -h redis.taskmanagement.internal FLUSHDB
```

#### Connection Issues

**Symptoms:**
- Services unable to connect to Redis
- Connection timeout errors
- High latency in cache operations

**Diagnostic Steps:**
1. Check Redis server status
2. Verify network connectivity
3. Monitor connection count
4. Check for memory pressure

**Resolution:**
```bash
# Check Redis status
redis-cli -h redis.taskmanagement.internal PING

# Monitor connections
redis-cli -h redis.taskmanagement.internal CLIENT LIST | wc -l

# Reset client connections (emergency only)
redis-cli -h redis.taskmanagement.internal CLIENT KILL TYPE normal
```

#### Memory Issues

**Symptoms:**
- Redis OOM errors
- Eviction metrics increasing
- Slow Redis performance

**Diagnostic Steps:**
1. Check memory usage and limits
2. Monitor keyspace statistics
3. Identify large keys consuming memory

**Resolution:**
```bash
# Check memory usage
redis-cli -h redis.taskmanagement.internal INFO memory

# Find large keys
redis-cli -h redis.taskmanagement.internal --bigkeys

# Adjust maxmemory configuration (requires planning)
aws elasticache modify-cache-cluster --cache-cluster-id taskmanagement-redis-prod --cache-parameter-group-name redis-increased-memory
```

## Infrastructure Troubleshooting

### API Gateway Issues

#### Routing Problems

**Symptoms:**
- 404 errors for valid endpoints
- Requests routed to wrong services
- Inconsistent API behavior

**Diagnostic Steps:**
1. Check API Gateway configuration
2. Verify route mappings and service discovery
3. Inspect load balancer health checks

**Resolution:**
```bash
# Check API Gateway health
curl -X GET https://api.taskmanagement.com/health

# Verify specific route configuration
aws apigateway get-resource --rest-api-id abcd1234 --resource-id efgh5678

# Reset API Gateway cache
aws apigateway flush-stage-cache --rest-api-id abcd1234 --stage-name prod
```

#### Rate Limiting Issues

**Symptoms:**
- Users receiving 429 Too Many Requests errors
- Unexpected throttling of normal traffic
- Rate limit counters not resetting properly

**Diagnostic Steps:**
1. Check rate limit configuration
2. Monitor request volume by client/endpoint
3. Verify rate limit header values

**Resolution:**
```bash
# Check rate limit configuration
aws apigateway get-usage-plan --usage-plan-id plan-id-here

# Temporarily increase rate limits
aws apigateway update-usage-plan --usage-plan-id plan-id-here --throttle { "burstLimit": 100, "rateLimit": 50 }

# Reset rate limit for specific client
curl -X POST https://api.taskmanagement.com/admin/rate-limit/reset \
  -H "Authorization: Bearer {admin-token}" \
  -d '{"clientId": "client-id-here"}'
```

#### Authentication Failures

**Symptoms:**
- Valid API keys rejected
- Token validation inconsistency
- Authentication bypass for some routes

**Diagnostic Steps:**
1. Check API Gateway authorizer configuration
2. Verify JWT validation settings
3. Inspect token issuer configuration
4. Check for clock skew issues

**Resolution:**
```bash
# Verify authorizer configuration
aws apigateway get-authorizer --rest-api-id abcd1234 --authorizer-id auth123

# Update authorizer configuration if needed
aws apigateway update-authorizer --rest-api-id abcd1234 --authorizer-id auth123 --patch-operations op=replace,path=/authorizerUri,value=arn:aws:lambda:region:account:function:new-authorizer
```

### Container Orchestration Issues

#### Deployment Failures

**Symptoms:**
- Services failing to deploy or update
- Container startup failures
- Health check failures for new deployments

**Diagnostic Steps:**
1. Check ECS deployment logs
2. Verify container image exists and is accessible
3. Check for resource constraints
4. Inspect container logs for startup errors

**Resolution:**
```bash
# Check deployment status
aws ecs describe-services --cluster task-management-prod --services service-name-here

# Check container logs
aws logs get-log-events --log-group /ecs/task-management-prod --log-stream service-name/container-id

# Roll back to previous version
aws ecs update-service --cluster task-management-prod --service service-name --task-definition service-name:previous-version
```

#### Scaling Issues

**Symptoms:**
- Services not scaling up under load
- Delayed automatic scaling
- Containers terminating unexpectedly

**Diagnostic Steps:**
1. Check auto-scaling settings and history
2. Verify CloudWatch alarms for scaling
3. Monitor ECS service events
4. Check for service quota limits

**Resolution:**
```bash
# Check scaling settings
aws application-autoscaling describe-scaling-policies --service-namespace ecs --resource-id service/task-management-prod/service-name

# Manually scale service for immediate relief
aws ecs update-service --cluster task-management-prod --service service-name --desired-count 10

# Verify service quotas
aws service-quotas get-service-quota --service-code ecs --quota-code L-21C621EB
```

#### Health Check Failures

**Symptoms:**
- Services marked unhealthy despite being operational
- Containers being terminated and restarted frequently
- Inconsistent health status across instances

**Diagnostic Steps:**
1. Check health check configuration
2. Verify health check endpoint functionality
3. Monitor timing of health checks
4. Check for network issues affecting health checks

**Resolution:**
```bash
# Check current health status
aws ecs describe-tasks --cluster task-management-prod --tasks task-id-here

# Adjust health check settings
aws ecs update-service --cluster task-management-prod --service service-name --health-check-grace-period-seconds 120

# Verify health endpoint directly
curl -X GET http://container-ip:port/health
```

### Networking Issues

#### Connectivity Problems

**Symptoms:**
- Intermittent connection failures between services
- DNS resolution issues
- Timeouts when connecting to services

**Diagnostic Steps:**
1. Check DNS resolution
2. Verify security group rules
3. Test network connectivity between services
4. Check for network ACL issues

**Resolution:**
```bash
# Check DNS resolution
dig +short service-name.taskmanagement.internal

# Verify security group rules
aws ec2 describe-security-groups --group-ids sg-abcdef123456

# Test connectivity using network debugging container
kubectl run network-debug --image=nicolaka/netshoot --rm -it -- bash
```

#### DNS Resolution Issues

**Symptoms:**
- Service names not resolving
- Intermittent name resolution failures
- Slow DNS resolution

**Diagnostic Steps:**
1. Check DNS server functionality
2. Verify Route 53 resolver endpoints
3. Check for DNS cache poisoning
4. Monitor DNS query metrics

**Resolution:**
```bash
# Test DNS resolution
dig +short service-name.taskmanagement.internal

# Check Route 53 resolver status
aws route53resolver get-resolver-endpoint --resolver-endpoint-id endpoint-id-here

# Flush DNS cache on problematic hosts
sudo systemd-resolve --flush-caches
```

#### Load Balancer Issues

**Symptoms:**
- Uneven traffic distribution
- Services receiving no traffic despite being healthy
- Intermittent 502/504 errors

**Diagnostic Steps:**
1. Check load balancer health status
2. Verify target group registration
3. Monitor load balancer metrics
4. Check for connection draining issues

**Resolution:**
```bash
# Check target health
aws elbv2 describe-target-health --target-group-arn arn:aws:elasticloadbalancing:region:account:targetgroup/target-group-name/abcdef123456

# Deregister/register problematic target
aws elbv2 deregister-targets --target-group-arn arn:aws:elasticloadbalancing:region:account:targetgroup/target-group-name/abcdef123456 --targets Id=instance-id-here

# Verify load balancer logs
aws s3 ls s3://elb-logs-bucket/AWSLogs/account/elasticloadbalancing/region/yyyy/mm/dd/
```

## Performance Troubleshooting

### API Response Latency

#### Slow API Responses

**Symptoms:**
- API requests taking longer than expected
- Timeout errors from clients
- Increasing latency trends in monitoring

**Diagnostic Steps:**
1. Check API response time metrics in CloudWatch
2. Verify database query performance
3. Monitor CPU and memory utilization
4. Check for slow external dependencies
5. Analyze request patterns and potential bottlenecks

**Resolution:**
```bash
# Check service metrics
aws cloudwatch get-metric-statistics --namespace AWS/ECS --metric-name CPUUtilization --dimensions Name=ServiceName,Value=service-name Name=ClusterName,Value=task-management-prod --start-time $(date -u -d "1 hour ago" +%Y-%m-%dT%H:%M:%SZ) --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) --period 300 --statistics Average

# Identify slow API endpoints
curl -X GET https://api.taskmanagement.com/admin/metrics/slow-endpoints \
  -H "Authorization: Bearer {admin-token}"

# Increase service capacity for temporary relief
aws ecs update-service --cluster task-management-prod --service service-name --desired-count 8
```

#### Connection Pooling Problems

**Symptoms:**
- Database connection errors
- "Too many connections" errors
- Connection establishment latency

**Diagnostic Steps:**
1. Monitor connection pool utilization
2. Check for connection leaks
3. Verify connection pool configuration

**Resolution:**
```bash
# Check database connections
mongosh --host mongodb.taskmanagement.internal --eval "db.currentOp({op: 'query'})"

# Verify connection pool settings
aws ssm get-parameter --name "/taskmanagement/prod/database/max-pool-size"

# Restart service to reset connection pools (last resort)
aws ecs update-service --cluster task-management-prod --service service-name --force-new-deployment
```

#### Request Queueing

**Symptoms:**
- API requests processed in batches
- Request latency increasing under load
- Inconsistent response times

**Diagnostic Steps:**
1. Monitor request queue length
2. Check for threadpool saturation
3. Verify async processing configuration

**Resolution:**
```bash
# Check queue metrics
aws cloudwatch get-metric-statistics --namespace TaskManagement --metric-name RequestQueueLength --dimensions Name=ServiceName,Value=service-name --start-time $(date -u -d "1 hour ago" +%Y-%m-%dT%H:%M:%SZ) --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) --period 60 --statistics Maximum

# Adjust thread pool size
aws ssm put-parameter --name "/taskmanagement/prod/service-name/thread-pool-size" --value "24" --type String --overwrite
```

### Database Performance

#### Slow Queries

**Symptoms:**
- Specific operations becoming slower over time
- MongoDB logs showing slow query warnings
- Increasing database CPU utilization

**Diagnostic Steps:**
1. Enable profiling for slow queries
2. Analyze query patterns and execution plans
3. Check for missing or inefficient indexes
4. Monitor collection growth and fragmentation

**Resolution:**
```bash
# Enable profiling for queries slower than 100ms
mongosh --host mongodb.taskmanagement.internal --eval "db.setProfilingLevel(1, 100)"

# Check slow queries
mongosh --host mongodb.taskmanagement.internal --eval "db.system.profile.find({millis:{$gt:100}}).sort({ts:-1}).limit(10)"

# Analyze query plan
mongosh --host mongodb.taskmanagement.internal --eval "db.tasks.find({assignedTo:'user-id-here'}).explain('executionStats')"

# Add missing index
mongosh --host mongodb.taskmanagement.internal --eval "db.tasks.createIndex({assignedTo: 1, status: 1})"
```

#### Index Optimization

**Symptoms:**
- Query performance degrading over time
- Index size growing excessively
- High I/O on database server

**Diagnostic Steps:**
1. Analyze index usage statistics
2. Identify unused or duplicate indexes
3. Check index order and selectivity

**Resolution:**
```bash
# Check index usage
mongosh --host mongodb.taskmanagement.internal --eval "db.tasks.aggregate([{$indexStats:{}}])"

# Remove unused indexes
mongosh --host mongodb.taskmanagement.internal --eval "db.tasks.dropIndex('unused_index_name')"

# Create compound index for common queries
mongosh --host mongodb.taskmanagement.internal --eval "db.tasks.createIndex({projectId: 1, status: 1, dueDate: 1})"
```

#### Connection Saturation

**Symptoms:**
- "Too many connections" errors
- Connection timeouts
- Increasing wait time for database operations

**Diagnostic Steps:**
1. Monitor current connection count
2. Check connection pool settings across services
3. Look for connections not being released properly

**Resolution:**
```bash
# Check current connections
mongosh --host mongodb.taskmanagement.internal --eval "db.serverStatus().connections"

# Temporarily increase connection limit (emergency only)
mongosh --host mongodb.taskmanagement.internal --eval "db.adminCommand({setParameter: 1, maxConnections: 5000})"

# Restart problematic service to reset connections
aws ecs update-service --cluster task-management-prod --service service-name --force-new-deployment
```

### Resource Utilization

#### CPU Saturation

**Symptoms:**
- High CPU utilization alarms
- Services becoming unresponsive
- Increased response latency

**Diagnostic Steps:**
1. Identify processes consuming CPU
2. Check for runaway processing or infinite loops
3. Monitor CPU credits for burstable instances
4. Check for inefficient code patterns

**Resolution:**
```bash
# Check CPU utilization
aws cloudwatch get-metric-statistics --namespace AWS/ECS --metric-name CPUUtilization --dimensions Name=ServiceName,Value=service-name Name=ClusterName,Value=task-management-prod --start-time $(date -u -d "1 hour ago" +%Y-%m-%dT%H:%M:%SZ) --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) --period 60 --statistics Average

# Scale up service
aws ecs update-service --cluster task-management-prod --service service-name --desired-count 10

# Upgrade container resources
aws ecs update-service --cluster task-management-prod --service service-name --task-definition service-name:larger-resources
```

#### Memory Leaks

**Symptoms:**
- Increasing memory usage over time
- Container restarts due to OOM (Out of Memory)
- Degrading performance before restarts

**Diagnostic Steps:**
1. Monitor memory usage patterns
2. Check for gradual memory growth without release
3. Analyze heap dumps if available
4. Look for memory-intensive operations

**Resolution:**
```bash
# Check memory metrics
aws cloudwatch get-metric-statistics --namespace AWS/ECS --metric-name MemoryUtilization --dimensions Name=ServiceName,Value=service-name Name=ClusterName,Value=task-management-prod --start-time $(date -u -d "1 hour ago" +%Y-%m-%dT%H:%M:%SZ) --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) --period 60 --statistics Average

# Increase memory allocation (short-term)
aws ecs update-service --cluster task-management-prod --service service-name --task-definition service-name:more-memory

# Schedule regular restarts until resolved
aws events put-rule --name "RestartServiceDaily" --schedule-expression "cron(0 3 * * ? *)"
```

#### Disk Usage

**Symptoms:**
- "No space left on device" errors
- Failing writes or database operations
- Slow file system operations

**Diagnostic Steps:**
1. Identify volume with space issues
2. Find large files or directories
3. Check for log file growth
4. Monitor disk I/O metrics

**Resolution:**
```bash
# Check disk usage
df -h

# Find large files
find /var/log -type f -size +100M -exec ls -lh {} \;

# Clean up old log files
find /var/log/taskmanagement -name "*.log.*" -mtime +7 -delete

# Increase EBS volume size (if needed)
aws ec2 modify-volume --volume-id vol-abcdef123456 --size 100
```

## Security Issue Resolution

### Authentication Problems

#### Authentication Bypasses

**Symptoms:**
- Unexpected authentication successes in logs
- Access from unusual locations or devices
- Anomalous user behavior patterns

**Diagnostic Steps:**
1. Review authentication logs for patterns
2. Check for recent changes to auth configuration
3. Verify token validation is working correctly
4. Look for signs of token theft or replay

**Resolution:**
```bash
# Enable enhanced security logging
aws ssm put-parameter --name "/taskmanagement/prod/auth/enhanced-logging" --value "true" --type String --overwrite

# Force token invalidation for specific user
curl -X POST https://api.taskmanagement.com/admin/auth/invalidate-tokens \
  -H "Authorization: Bearer {admin-token}" \
  -d '{"userId": "user-id-here"}'

# Force system-wide token refresh (emergency only)
curl -X POST https://api.taskmanagement.com/admin/auth/rotate-keys \
  -H "Authorization: Bearer {admin-token}"
```

#### Brute Force Attempts

**Symptoms:**
- Multiple failed login attempts for same user
- Login attempts from unusual locations
- Distributed login attempts across users

**Diagnostic Steps:**
1. Monitor failed login attempt patterns
2. Check IP addresses of login attempts
3. Look for automated attack signatures

**Resolution:**
```bash
# Enable temporary IP blocking
aws ssm put-parameter --name "/taskmanagement/prod/auth/ip-blocking" --value "true" --type String --overwrite

# Block specific IP range
aws wafv2 update-ip-set --name TaskManagement-BlockList --scope REGIONAL --id abcdef123456 --addresses "192.0.2.0/24"

# Temporarily lock compromised accounts
curl -X POST https://api.taskmanagement.com/admin/users/lock \
  -H "Authorization: Bearer {admin-token}" \
  -d '{"userIds": ["user-id-1", "user-id-2"]}'
```

#### Suspicious Login Patterns

**Symptoms:**
- Logins from unusual geographic locations
- Multiple account access from same IP
- Login velocity exceeding human capabilities

**Diagnostic Steps:**
1. Analyze login patterns and anomalies
2. Check for credential stuffing patterns
3. Monitor session creation velocity

**Resolution:**
```bash
# Enable geographic restrictions
aws ssm put-parameter --name "/taskmanagement/prod/auth/geo-restrictions" --value "US,CA,UK" --type StringList --overwrite

# Force password reset for affected users
curl -X POST https://api.taskmanagement.com/admin/users/reset-password \
  -H "Authorization: Bearer {admin-token}" \
  -d '{"userIds": ["user-id-1", "user-id-2", "user-id-3"]}'

# Enable additional authentication factors
curl -X POST https://api.taskmanagement.com/admin/auth/enforce-mfa \
  -H "Authorization: Bearer {admin-token}" \
  -d '{"userRoles": ["admin", "manager"]}'
```

### Authorization Failures

#### Permission Issues

**Symptoms:**
- Users unable to access resources they should have permission for
- "Forbidden" errors for legitimate operations
- Inconsistent access across similar resources

**Diagnostic Steps:**
1. Check user role assignments
2. Verify permission mapping configuration
3. Look for caching issues with permissions
4. Monitor resource access patterns

**Resolution:**
```bash
# Check user permissions
curl -X GET https://api.taskmanagement.com/admin/users/{userId}/permissions \
  -H "Authorization: Bearer {admin-token}"

# Clear permission cache
redis-cli -h redis.taskmanagement.internal DEL "permissions:user-id-here"

# Manually grant permission (temporary fix)
curl -X POST https://api.taskmanagement.com/admin/permissions/grant \
  -H "Authorization: Bearer {admin-token}" \
  -d '{"userId": "user-id-here", "resource": "projects", "resourceId": "project-id-here", "actions": ["read", "update"]}'
```

#### Role Assignment Problems

**Symptoms:**
- Missing role assignments
- Incorrect role assignments
- Temporary role elevation not expiring

**Diagnostic Steps:**
1. Audit role assignments for affected users
2. Check recent role changes in audit logs
3. Verify role definition configuration

**Resolution:**
```bash
# Check user roles
curl -X GET https://api.taskmanagement.com/admin/users/{userId}/roles \
  -H "Authorization: Bearer {admin-token}"

# Assign correct role
curl -X PUT https://api.taskmanagement.com/admin/users/{userId}/roles \
  -H "Authorization: Bearer {admin-token}" \
  -d '{"roles": ["user", "project_manager"]}'

# Reset role hierarchy cache
redis-cli -h redis.taskmanagement.internal DEL "roles:hierarchy"
```

#### Access Control Bugs

**Symptoms:**
- Unauthorized access to resources
- Access control rules not being applied consistently
- Security boundaries being crossed

**Diagnostic Steps:**
1. Review access control logic implementation
2. Check for recent changes to authorization code
3. Verify security boundary enforcement

**Resolution:**
```bash
# Enable enhanced authorization logging
aws ssm put-parameter --name "/taskmanagement/prod/auth/verbose-authz-logging" --value "true" --type String --overwrite

# Force reload of access control rules
curl -X POST https://api.taskmanagement.com/admin/auth/reload-acl \
  -H "Authorization: Bearer {admin-token}"

# Apply security patch (after identifying issue)
aws ecs update-service --cluster task-management-prod --service auth-service --force-new-deployment --task-definition auth-service:security-patch
```

### Data Protection Issues

#### Encryption Problems

**Symptoms:**
- Failed decryption operations
- Garbled data returned to users
- Encryption key rotation failures

**Diagnostic Steps:**
1. Check encryption key status and validity
2. Verify encryption/decryption operations
3. Monitor key usage and access patterns

**Resolution:**
```bash
# Check key status
aws kms describe-key --key-id abcdef12-3456-7890-abcd-ef1234567890

# Test encryption service
curl -X POST https://api.taskmanagement.com/admin/encryption/test \
  -H "Authorization: Bearer {admin-token}"

# Rotate encryption keys (planned operation)
aws kms rotate-key-on-demand --key-id abcdef12-3456-7890-abcd-ef1234567890
```

#### Data Leakage

**Symptoms:**
- Sensitive data appearing in logs
- PII exposed in API responses
- Authentication credentials in error messages

**Diagnostic Steps:**
1. Scan logs for sensitive data patterns
2. Review API responses for data exposure
3. Check error handling for sensitive data leaks

**Resolution:**
```bash
# Enable data filtering in logs
aws ssm put-parameter --name "/taskmanagement/prod/logging/pii-filtering" --value "true" --type String --overwrite

# Update PII patterns for filtering
curl -X PUT https://api.taskmanagement.com/admin/security/pii-patterns \
  -H "Authorization: Bearer {admin-token}" \
  -d '{"patterns": ["credit-card", "ssn", "password"]}'

# Patch services with data leakage issues
aws ecs update-service --cluster task-management-prod --service affected-service --force-new-deployment --task-definition affected-service:data-leak-fix
```

#### Secure Transmission Issues

**Symptoms:**
- TLS certificate errors
- Mixed content warnings
- Insecure protocol usage

**Diagnostic Steps:**
1. Check TLS certificate validity and expiration
2. Verify security headers configuration
3. Monitor for insecure connection attempts

**Resolution:**
```bash
# Check TLS certificate status
openssl s_client -connect api.taskmanagement.com:443 -servername api.taskmanagement.com

# Enable strict transport security
aws ssm put-parameter --name "/taskmanagement/prod/security/hsts-enabled" --value "true" --type String --overwrite

# Update security headers configuration
curl -X PUT https://api.taskmanagement.com/admin/security/headers \
  -H "Authorization: Bearer {admin-token}" \
  -d '{"headers": {"Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload", "Content-Security-Policy": "default-src https:"}}'
```

## Logging and Monitoring

### Log Analysis Techniques

#### Correlation Across Services

**Approach:**
1. Use correlation IDs to track requests across services
2. Combine logs from multiple sources with timestamps
3. Build a timeline of events for complex issues

**Sample Commands:**
```bash
# Search for correlation ID across services
grep "correlation-id-here" /var/log/taskmanagement/*.log

# Extract timeline for specific user activity
grep "user-id-here" /var/log/taskmanagement/*.log | sort -k1,2

# Use CloudWatch Logs Insights for cross-service analysis
aws logs start-query --log-group-names "/aws/ecs/task-management-prod" --start-time $(date -d "1 hour ago" +%s) --end-time $(date +%s) --query-string "fields @timestamp, @message | filter @message like 'correlation-id-here' | sort @timestamp asc"
```

#### Pattern Recognition

**Approach:**
1. Look for recurring error patterns
2. Identify timing correlations between events
3. Use log aggregation to detect unusual patterns

**Sample Commands:**
```bash
# Count frequency of error types
grep ERROR /var/log/taskmanagement/service-name.log | cut -d: -f4 | sort | uniq -c | sort -nr

# Identify time periods with high error rates
grep ERROR /var/log/taskmanagement/service-name.log | cut -d' ' -f1,2 | uniq -c | sort -nr | head -10

# Use CloudWatch Logs Insights to analyze error patterns
aws logs start-query --log-group-names "/aws/ecs/task-management-prod" --start-time $(date -d "1 day ago" +%s) --end-time $(date +%s) --query-string "fields @timestamp, service, errorType | filter level = 'ERROR' | stats count(*) as errorCount by errorType, bin(30m) as timeSlot | sort errorCount desc"
```

#### Log Level Adjustment

**Approach:**
1. Temporarily increase log verbosity for detailed diagnosis
2. Target specific components for enhanced logging
3. Return to normal logging after diagnosis

**Sample Commands:**
```bash
# Change log level for specific service
curl -X PUT https://api.taskmanagement.com/admin/logging/{serviceName}/level \
  -H "Authorization: Bearer {admin-token}" \
  -d '{"level": "DEBUG", "duration": 30}'

# Enable trace logging for specific component
aws ssm put-parameter --name "/taskmanagement/prod/logging/components/auth/level" --value "TRACE" --type String --overwrite

# Reset all log levels to normal
curl -X POST https://api.taskmanagement.com/admin/logging/reset \
  -H "Authorization: Bearer {admin-token}"
```

### Using Monitoring Dashboards

#### Grafana Dashboards

**Key Dashboards:**
1. **System Overview**: High-level health of all components
2. **Service Performance**: Detailed metrics for individual services
3. **Database Performance**: MongoDB and Redis metrics
4. **User Activity**: User-focused metrics and patterns
5. **Error Tracking**: Aggregated error rates and patterns

**Usage Tips:**
- Use the time range selector to narrow investigations
- Correlate metrics across multiple panels
- Save and share dashboard snapshots for incident documentation
- Create temporary dashboards for specific investigations

**Sample Queries:**
```
# Grafana PromQL query for service latency
rate(http_request_duration_seconds_sum{service="task-service"}[5m]) / rate(http_request_duration_seconds_count{service="task-service"}[5m])

# Grafana PromQL query for error rate
sum(rate(http_requests_total{status=~"5.."}[5m])) by (service) / sum(rate(http_requests_total[5m])) by (service)
```

#### CloudWatch Dashboards

**Key Metrics to Monitor:**
1. ECS service CPU and memory utilization
2. API Gateway request counts and latencies
3. Database connections and query times
4. Custom application metrics
5. Error counts and rates

**Usage Tips:**
- Create composite alarms for related metrics
- Use CloudWatch Logs Insights for deep analysis
- Set up anomaly detection for key metrics
- Create dashboards for specific services or features

**Sample Commands:**
```bash
# Create a CloudWatch dashboard for a service
aws cloudwatch put-dashboard --dashboard-name TaskService-Performance --dashboard-body file://taskservice-dashboard.json

# Create an alarm for high error rates
aws cloudwatch put-metric-alarm --alarm-name TaskService-HighErrorRate --metric-name ErrorCount --namespace TaskManagement --statistic Sum --period 60 --evaluation-periods 3 --threshold 10 --comparison-operator GreaterThanThreshold --alarm-actions arn:aws:sns:region:account:TopicName
```

### Distributed Tracing

#### Using X-Ray

**Key Capabilities:**
1. End-to-end request tracing
2. Service map visualization
3. Latency breakdown by component
4. Error spotting and analysis

**Usage Tips:**
- Filter traces by user ID or correlation ID
- Look for anomalous latency patterns
- Identify services with high error rates
- Analyze service dependencies and bottlenecks

**Sample Commands:**
```bash
# Get recent traces for specific user
aws xray get-trace-summaries --start-time $(date -d "1 hour ago" +%s) --end-time $(date +%s) --filter-expression "service(\"task-service\") AND annotation.userId = \"user-id-here\""

# Get details for specific trace
aws xray batch-get-traces --trace-ids 1-abcdef123456789

# Enable sampling rule for increased capture
aws xray create-sampling-rule --sampling-rule '{"RuleName":"TaskServiceDebug","Priority":1,"FixedRate":1,"ReservoirSize":100,"ServiceName":"task-service","ServiceType":"*","Host":"*","HTTPMethod":"*","URLPath":"*","Version":1}'
```

#### Using OpenTelemetry

**Key Capabilities:**
1. Standardized tracing across services
2. Detailed context propagation
3. Integration with multiple backends
4. Custom attribute tagging

**Usage Tips:**
- Add business context as span attributes
- Use semantic conventions for consistency
- Create custom spans for critical operations
- Correlate traces with logs using trace IDs

**Sample Commands:**
```bash
# Check OpenTelemetry collector status
curl -X GET https://api.taskmanagement.com/admin/telemetry/status \
  -H "Authorization: Bearer {admin-token}"

# Temporarily increase sampling rate
curl -X PUT https://api.taskmanagement.com/admin/telemetry/sampling \
  -H "Authorization: Bearer {admin-token}" \
  -d '{"service": "task-service", "sampleRate": 1.0, "duration": 30}'

# Export trace data for analysis
curl -X GET https://api.taskmanagement.com/admin/telemetry/export \
  -H "Authorization: Bearer {admin-token}" \
  -d '{"traceId": "trace-id-here"}'
```

## Recovery Procedures

### Service Recovery

#### Failed Deployment Recovery

**Situation**: A service deployment has failed or introduced errors.

**Recovery Steps:**
1. Identify the failed deployment and issue
   ```bash
   aws ecs describe-services --cluster task-management-prod --services service-name
   ```

2. Roll back to the previous stable version
   ```bash
   aws ecs update-service --cluster task-management-prod --service service-name --task-definition service-name:previous-version
   ```

3. Verify the rollback was successful
   ```bash
   # Check service status
   aws ecs describe-services --cluster task-management-prod --services service-name
   
   # Verify functionality
   curl -X GET https://api.taskmanagement.com/service-endpoint/health
   ```

4. Document the issue for post-mortem analysis

#### Service Scaling Issues

**Situation**: Service is overwhelmed and needs immediate scale-up.

**Recovery Steps:**
1. Manually increase service capacity
   ```bash
   aws ecs update-service --cluster task-management-prod --service service-name --desired-count 20
   ```

2. Temporarily enable request throttling if needed
   ```bash
   curl -X PUT https://api.taskmanagement.com/admin/rate-limit/emergency \
     -H "Authorization: Bearer {admin-token}" \
     -d '{"enabled": true, "requestsPerMinute": 1000}'
   ```

3. Monitor performance metrics as capacity increases
   ```bash
   aws cloudwatch get-metric-statistics --namespace AWS/ECS --metric-name CPUUtilization --dimensions Name=ServiceName,Value=service-name Name=ClusterName,Value=task-management-prod --start-time $(date -u -d "1 hour ago" +%Y-%m-%dT%H:%M:%SZ) --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) --period 60 --statistics Average
   ```

4. Adjust auto-scaling configuration if needed
   ```bash
   aws application-autoscaling put-scaling-policy --service-namespace ecs --resource-id service/task-management-prod/service-name --policy-name cpu-tracking --policy-type TargetTrackingScaling --target-tracking-scaling-policy-configuration '{"TargetValue":70.0,"PredefinedMetricSpecification":{"PredefinedMetricType":"ECSServiceAverageCPUUtilization"}}'
   ```

#### Handling Service Dependencies

**Situation**: A critical service dependency is unavailable.

**Recovery Steps:**
1. Implement circuit breaker to prevent cascading failures
   ```bash
   curl -X PUT https://api.taskmanagement.com/admin/circuit-breaker/settings \
     -H "Authorization: Bearer {admin-token}" \
     -d '{"service": "dependency-name", "enabled": true, "failureThreshold": 50, "resetTimeout": 300}'
   ```

2. Enable fallback mechanisms for critical functionality
   ```bash
   curl -X PUT https://api.taskmanagement.com/admin/fallback/enable \
     -H "Authorization: Bearer {admin-token}" \
     -d '{"service": "service-name", "fallbackMode": "read-only"}'
   ```

3. Notify users of degraded functionality
   ```bash
   curl -X POST https://api.taskmanagement.com/admin/notifications/system \
     -H "Authorization: Bearer {admin-token}" \
     -d '{"message": "Some system features are temporarily unavailable. We are working to resolve the issue.", "level": "warning"}'
   ```

4. Monitor dependency status for recovery
   ```bash
   # Check health endpoint regularly
   watch -n 30 "curl -s https://dependency-service.example.com/health | jq '.status'"
   ```

### Database Recovery

#### MongoDB Failover

**Situation**: Primary MongoDB instance is unavailable or corrupted.

**Recovery Steps:**
1. Check replica set status to confirm the issue
   ```bash
   mongosh --host mongodb.taskmanagement.internal --eval "rs.status()"
   ```

2. If automated failover hasn't occurred, manually initiate failover
   ```bash
   # Connect to a secondary and force it to become primary
   mongosh --host mongodb-secondary.taskmanagement.internal --eval "rs.stepDown(300)"
   ```

3. Verify the new primary is functioning correctly
   ```bash
   mongosh --host mongodb.taskmanagement.internal --eval "db.serverStatus()"
   mongosh --host mongodb.taskmanagement.internal --eval "db.runCommand({ping: 1})"
   ```

4. Fix or replace the failed instance
   ```bash
   # If self-hosted, restart the failed MongoDB instance
   sudo systemctl restart mongod
   
   # If using Atlas, repair or replace the instance through the UI
   ```

#### Restore from Backup

**Situation**: Database data is corrupted or accidentally deleted.

**Recovery Steps:**
1. Identify the appropriate backup point
   ```bash
   # List available backups
   aws s3 ls s3://mongodb-backups-bucket/taskmanagement/
   ```

2. Stop write operations to the affected database
   ```bash
   # Enable maintenance mode
   curl -X POST https://api.taskmanagement.com/admin/maintenance \
     -H "Authorization: Bearer {admin-token}" \
     -d '{"enabled": true, "message": "System maintenance in progress"}'
   ```

3. Restore from backup
   ```bash
   # For self-hosted MongoDB
   mongorestore --host mongodb.taskmanagement.internal --gzip --archive=/path/to/backup.gz
   
   # For MongoDB Atlas
   # Use Atlas UI to initiate point-in-time recovery
   ```

4. Verify data integrity after restore
   ```bash
   mongosh --host mongodb.taskmanagement.internal --eval "db.tasks.count()"
   mongosh --host mongodb.taskmanagement.internal --eval "db.projects.count()"
   ```

5. Resume normal operations
   ```bash
   curl -X POST https://api.taskmanagement.com/admin/maintenance \
     -H "Authorization: Bearer {admin-token}" \
     -d '{"enabled": false}'
   ```

#### Redis Cache Recovery

**Situation**: Redis cache corruption or performance issues.

**Recovery Steps:**
1. Check Redis status
   ```bash
   redis-cli -h redis.taskmanagement.internal INFO
   ```

2. Flush the cache if necessary (warning: will clear all cached data)
   ```bash
   # Flush specific database
   redis-cli -h redis.taskmanagement.internal -n 0 FLUSHDB
   
   # Flush all databases (emergency only)
   redis-cli -h redis.taskmanagement.internal FLUSHALL
   ```

3. Restart Redis if necessary
   ```bash
   # For ElastiCache
   aws elasticache reboot-cache-cluster --cache-cluster-id taskmanagement-redis-prod --cache-node-ids-to-reboot 0001
   
   # For self-hosted Redis
   sudo systemctl restart redis
   ```

4. Verify functionality after recovery
   ```bash
   redis-cli -h redis.taskmanagement.internal PING
   ```

### Complete System Restoration

#### Regional Failover

**Situation**: Primary AWS region is experiencing an outage.

**Recovery Steps:**
1. Verify the outage and assess impact
   ```bash
   # Check AWS status page
   curl -s https://status.aws.amazon.com/
   
   # Check our services in the affected region
   aws --region us-east-1 cloudwatch get-metric-data --metric-data-queries file://check-metrics.json --start-time $(date -u -d "1 hour ago" +%Y-%m-%dT%H:%M:%SZ) --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ)
   ```

2. Initiate DNS failover to standby region
   ```bash
   aws route53 change-resource-record-sets --hosted-zone-id Z1234567890ABC --change-batch file://failover-to-secondary.json
   ```

3. Scale up resources in the secondary region
   ```bash
   aws --region us-west-2 ecs update-service --cluster task-management-dr --service auth-service --desired-count 6
   aws --region us-west-2 ecs update-service --cluster task-management-dr --service task-service --desired-count 8
   # Repeat for other services
   ```

4. Verify functionality in the new region
   ```bash
   # Check health endpoints
   curl -s https://dr.api.taskmanagement.com/health
   
   # Perform basic operations test
   ./test-scripts/basic-operations.sh dr.api.taskmanagement.com
   ```

5. Update status page and notify users
   ```bash
   curl -X POST https://api.statuspage.io/v1/pages/abc123/incidents \
     -H "Authorization: OAuth abc123" \
     -d "incident[name]=System Failover&incident[status]=investigating&incident[body]=We are currently experiencing a service disruption and have activated our backup systems. Most services should be available, but you may experience temporary delays."
   ```

#### Catastrophic Recovery

**Situation**: Complete system failure requiring full restoration.

**Recovery Steps:**
1. Assemble the emergency response team and establish communication channels
   ```bash
   # Send emergency notification to team
   aws sns publish --topic-arn arn:aws:sns:region:account:EmergencyResponse --message "CRITICAL: System-wide outage - Emergency response required. Join emergency call: https://meet.example.com/emergency"
   ```

2. Deploy core infrastructure using Terraform
   ```bash
   cd terraform/disaster-recovery
   terraform init
   terraform apply -var-file=dr-vars.tfvars
   ```

3. Restore databases from most recent backups
   ```bash
   # Restore MongoDB data
   aws s3 cp s3://taskmanagement-backups/latest/mongodb-backup.tar.gz /tmp/
   tar -xzf /tmp/mongodb-backup.tar.gz
   mongorestore --host new-mongodb.taskmanagement.internal --dir /tmp/mongodb-backup
   
   # Restore Redis if needed (usually not necessary)
   aws s3 cp s3://taskmanagement-backups/latest/redis-rdb.gz /tmp/
   gunzip /tmp/redis-rdb.gz
   # Copy to Redis data directory and restart
   ```

4. Deploy services using last known good configurations
   ```bash
   # Deploy core services first
   aws ecs create-service --cli-input-json file://auth-service-config.json
   aws ecs create-service --cli-input-json file://task-service-config.json
   aws ecs create-service --cli-input-json file://project-service-config.json
   
   # Then deploy supporting services
   aws ecs create-service --cli-input-json file://notification-service-config.json
   aws ecs create-service --cli-input-json file://file-service-config.json
   aws ecs create-service --cli-input-json file://analytics-service-config.json
   ```

5. Verify system functionality
   ```bash
   # Run comprehensive test suite
   ./test-scripts/system-verification.sh
   
   # Check critical business operations
   ./test-scripts/business-functions.sh
   ```

6. Update DNS and resume operations
   ```bash
   aws route53 change-resource-record-sets --hosted-zone-id Z1234567890ABC --change-batch file://restore-dns.json
   ```

7. Document the incident and conduct post-mortem analysis

## Common Error Codes

| Error Code | Description | Common Causes | Resolution |
|------------|-------------|--------------|------------|
| `AUTH-001` | Authentication failed | Invalid credentials, expired token | Verify credentials, refresh token or re-authenticate |
| `AUTH-002` | Token validation failed | Invalid JWT, expired token, wrong signature | Check token validity, refresh if expired |
| `AUTH-003` | MFA required | Account requires MFA, not provided | Complete MFA process |
| `PERM-001` | Insufficient permissions | User lacks required role or permission | Request appropriate access, verify user roles |
| `PERM-002` | Resource not found or access denied | Resource doesn't exist or user has no access | Verify resource exists and user has permission |
| `TASK-001` | Task creation failed | Validation errors, database issues | Check input data, verify database connectivity |
| `TASK-002` | Task update failed | Concurrency issues, validation errors | Refresh task data, check field values |
| `PROJ-001` | Project creation failed | Name conflict, validation errors | Choose unique name, check input data |
| `PROJ-002` | Project access denied | User not a member of project | Request project access |
| `FILE-001` | File upload failed | Size limit, storage issue, format issue | Check file size and type, verify storage |
| `FILE-002` | File download failed | File not found, permission issue | Verify file exists and user has access |
| `FILE-003` | Virus detected | Malware in uploaded file | Scan file locally, upload clean file |
| `NOTIF-001` | Notification delivery failed | Invalid email, delivery issues | Verify contact info, check notification settings |
| `DB-001` | Database connection failed | Network issue, credential problem | Check network, verify database credentials |
| `DB-002` | Query execution failed | Syntax error, timeout, resource limits | Review query, optimize if needed |
| `API-001` | Rate limit exceeded | Too many requests | Reduce request frequency, implement backoff |
| `API-002` | Invalid request | Malformed payload, validation error | Check request format and data |
| `SYS-001` | System maintenance | Scheduled downtime | Wait for maintenance completion |
| `SYS-002` | Service unavailable | Component failure, high load | Retry with backoff, report if persistent |

## Support Escalation

### Escalation Levels

1. **Level 1**: Initial troubleshooting using this guide
2. **Level 2**: DevOps team involvement for infrastructure or service issues
3. **Level 3**: Development team for application-specific problems
4. **Level 4**: Senior engineering and architecture team
5. **Level 5**: Executive leadership for critical business impact

### When to Escalate

| Criteria | Description | Escalation Level |
|----------|-------------|------------------|
| Issue Duration | Problem persists more than 1 hour despite troubleshooting | Level 2 |
| Service Impact | Multiple users or critical functionality affected | Level 2-3 |
| Data Integrity | Potential data loss or corruption | Level 3-4 |
| Security Breach | Suspected or confirmed security incident | Level 3-5 |
| System-wide Outage | Multiple services or entire system unavailable | Level 4-5 |

### Required Information for Escalation

1. **Issue Summary**:
   - Clear description of the problem
   - First occurrence timestamp
   - Affected components
   - Impact severity (users affected, functionality impaired)

2. **Diagnostic Data**:
   - Relevant log excerpts (with timestamps and correlation IDs)
   - Error messages and codes
   - Screenshots of monitoring dashboards
   - Affected user IDs or request details

3. **Troubleshooting Steps**:
   - Actions already taken
   - Results of those actions
   - Temporary workarounds implemented
   - Configuration changes made

4. **Contact Information**:
   - Person reporting the issue
   - Users experiencing the problem
   - Stakeholders who need to be informed

### Escalation Contacts

| Escalation Level | Contact Method | Response Time |
|------------------|----------------|---------------|
| Level 2 | Slack #devops-support, On-call phone | 15 minutes |
| Level 3 | Slack #dev-oncall, PagerDuty | 30 minutes |
| Level 4 | Slack #senior-engineering, PagerDuty P2 | 1 hour |
| Level 5 | PagerDuty P1, Emergency contact list | 2 hours |

**Note**: Maintain updated contact information in the emergency response document at `/docs/operations/emergency-contacts.md`.