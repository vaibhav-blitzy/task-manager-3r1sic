# MongoDB Database Migrations

This document provides comprehensive guidance on managing database migrations for the Task Management System. It covers the principles, processes, and best practices for creating, testing, and deploying MongoDB schema and data migrations safely and efficiently.

## Table of Contents

1. [Introduction](#introduction)
2. [Migration Strategy Principles](#migration-strategy-principles)
3. [Migration File Organization](#migration-file-organization)
4. [Creating Migrations](#creating-migrations)
5. [Running Migrations](#running-migrations)
6. [Testing Migrations](#testing-migrations)
7. [Production Deployment](#production-deployment)
8. [Rollback Procedures](#rollback-procedures)
9. [Migration Examples](#migration-examples)
10. [Troubleshooting](#troubleshooting)
11. [References](#references)

## Introduction

Database schema and data migrations are necessary to evolve the database structure while preserving existing data as the application grows and requirements change. This document outlines the approach for MongoDB migrations in the Task Management System.

MongoDB, as a schema-flexible document database, offers different challenges and advantages for migrations compared to relational databases. While MongoDB doesn't enforce strict schemas by default, we use schema validation and follow consistent document structures, making migrations necessary when these structures change.

## Migration Strategy Principles

Our migration strategy follows these core principles:

1. **Schema Versioning**: Each database schema version corresponds to a specific application version, with clear tracking of applied migrations.

2. **Automated Scripts**: Migrations are handled by versioned scripts that can be executed as part of deployment or manually by administrators.

3. **Backward Compatibility**: New schema changes maintain compatibility with the previous application version whenever possible, enabling zero-downtime deployments.

4. **Rollback Capability**: Each migration has a corresponding rollback script to revert changes if issues arise after deployment.

5. **Testing**: All migrations are thoroughly tested against production-like data volumes before being applied to production environments.

## Migration File Organization

Migrations are organized in the following directory structure:

```
infrastructure/database/mongodb/migrations/
├── scripts/                       # Migration scripts
│   ├── YYYYMMDD_HHMMSS_name/      # Each migration in its own directory
│   │   ├── up.js                  # Migration script
│   │   ├── down.js                # Rollback script
│   │   └── metadata.json          # Migration metadata
│   └── ...
├── templates/                     # Migration templates
├── config.js                      # Migration configuration
├── runner.js                      # Migration runner script
└── README.md                      # This documentation
```

Each migration is contained in its own directory, named with a timestamp and descriptive name for easy identification and chronological ordering.

## Creating Migrations

### Step 1: Generate Migration Skeleton

Use the migration generator script to create a new migration:

```bash
npm run migration:create -- --name "add_due_date_index_to_tasks"
```

This creates a new migration directory with the necessary files:

- `up.js`: The migration to apply
- `down.js`: The rollback script
- `metadata.json`: Information about the migration including description, dependencies, and version compatibility

### Step 2: Implement the Migration

Edit the `up.js` file to implement your migration logic. Here's an example for adding an index:

```javascript
module.exports = async function up(db, client) {
  // Get the tasks collection
  const tasksCollection = db.collection('tasks');
  
  // Create index on dueDate field
  await tasksCollection.createIndex(
    { dueDate: 1 },
    { 
      name: 'tasks_dueDate_idx',
      background: true,
      // Add expireAfterSeconds if this should be a TTL index
    }
  );
  
  console.log('Created index tasks_dueDate_idx on tasks collection');
};
```

### Step 3: Implement the Rollback

Edit the `down.js` file to implement rollback logic:

```javascript
module.exports = async function down(db, client) {
  // Get the tasks collection
  const tasksCollection = db.collection('tasks');
  
  // Drop the index
  await tasksCollection.dropIndex('tasks_dueDate_idx');
  
  console.log('Dropped index tasks_dueDate_idx from tasks collection');
};
```

### Step 4: Update Metadata

Edit `metadata.json` to provide detailed information about the migration:

```json
{
  "name": "add_due_date_index_to_tasks",
  "description": "Adds an index on the dueDate field to improve query performance for task due date filtering",
  "createdBy": "developer_name",
  "createdAt": "2023-09-18T14:30:00Z",
  "dependencies": [],
  "minAppVersion": "1.2.0",
  "estimatedExecutionTime": "30s",
  "impact": "low",
  "requiresDowntime": false
}
```

## Running Migrations

### Development Environment

To run all pending migrations in the development environment:

```bash
npm run migration:up
```

To run migrations up to a specific version:

```bash
npm run migration:up -- --to YYYYMMDD_HHMMSS
```

To rollback the most recent migration:

```bash
npm run migration:down
```

To rollback to a specific version:

```bash
npm run migration:down -- --to YYYYMMDD_HHMMSS
```

### Viewing Migration Status

To check which migrations have been applied and which are pending:

```bash
npm run migration:status
```

This will display information about all migrations, including:
- Migration ID
- Name and description
- Status (applied/pending)
- Applied timestamp (for completed migrations)
- Execution time

## Testing Migrations

All migrations must be thoroughly tested before being deployed to production:

1. **Isolated Testing**: Test each migration on a copy of production data in an isolated environment.

2. **Volume Testing**: Verify performance with realistic data volumes to identify potential issues with large collections.

3. **Integration Testing**: Test the migration with the application version it's designed for to ensure compatibility.

4. **Rollback Testing**: Verify that the rollback script successfully reverts all changes.

### Testing Checklist

- [ ] Migration successfully applies to current database schema
- [ ] Application works correctly with the migrated schema
- [ ] Migration performance is acceptable with production-like data volume
- [ ] Rollback script successfully reverts all changes
- [ ] Migration and rollback scripts are idempotent (can be run multiple times safely)
- [ ] Migration maintains backward compatibility where required

## Production Deployment

The migration process for production follows these steps:

```
┌─────────────┐     ┌────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ Development │────>│ Create Snapshot │────>│ Apply Migration │────>│ Verify Success  │
└─────────────┘     └────────────────┘     └─────────────────┘     └─────────────────┘
                                                   │                          │
                                                   │                          │
                                                   ▼                          ▼
                                           ┌─────────────┐           ┌─────────────────┐
                                           │   Issues?   │──Yes────>│ Execute Rollback │
                                           └─────────────┘           └─────────────────┘
                                                   │                          │
                                                   No                         │
                                                   │                          │
                                                   ▼                          ▼
                                           ┌─────────────────┐       ┌─────────────────┐
                                           │ Update App Code │       │ Restore Snapshot│
                                           └─────────────────┘       └─────────────────┘
```

### Pre-Migration Steps

1. **Schedule Maintenance Window**: For migrations that require downtime
2. **Notify Users**: If service disruption is expected
3. **Create Database Snapshot**: For rollback capability
4. **Verify Backup**: Ensure the backup is valid and accessible

### Migration Execution

1. Execute migrations using the migration runner:

```bash
NODE_ENV=production npm run migration:up
```

2. Monitor the migration process closely, watching for errors or performance issues

### Post-Migration Verification

1. Verify database integrity and application functionality
2. Run health checks and monitoring for at least 24 hours
3. Keep backup snapshot for at least 7 days

## Rollback Procedures

If issues are detected after migration:

1. **Assess Impact**: Determine the severity and scope of the issue
2. **Attempt Targeted Fix**: For minor issues, deploy a targeted fix
3. **Execute Rollback**: For significant issues, use the rollback script:

```bash
NODE_ENV=production npm run migration:down
```

4. **Last Resort**: Restore from pre-migration snapshot if rollback scripts fail

### Rollback Decision Matrix

| Issue Type | Example | Action |
|------------|---------|--------|
| Minor | Slow queries, non-critical features affected | Monitor, fix forward |
| Moderate | Some features broken, performance degraded | Fix forward or selective rollback |
| Severe | System unstable, critical features broken | Full rollback |
| Critical | Data corruption, system unusable | Restore from snapshot |

## Migration Examples

### Example 1: Adding a Field with Default Value

```javascript
// up.js
module.exports = async function up(db, client) {
  await db.collection('tasks').updateMany(
    { priority: { $exists: false } },
    { $set: { priority: "medium" } }
  );
};

// down.js
module.exports = async function down(db, client) {
  await db.collection('tasks').updateMany(
    {},
    { $unset: { priority: "" } }
  );
};
```

### Example 2: Renaming a Field

```javascript
// up.js
module.exports = async function up(db, client) {
  await db.collection('users').updateMany(
    {},
    { $rename: { "name": "fullName" } }
  );
};

// down.js
module.exports = async function down(db, client) {
  await db.collection('users').updateMany(
    {},
    { $rename: { "fullName": "name" } }
  );
};
```

### Example 3: Creating a Collection with Validation

```javascript
// up.js
module.exports = async function up(db, client) {
  await db.createCollection("comments", {
    validator: {
      $jsonSchema: {
        bsonType: "object",
        required: ["taskId", "userId", "content", "createdAt"],
        properties: {
          taskId: { bsonType: "objectId" },
          userId: { bsonType: "objectId" },
          content: { bsonType: "string" },
          createdAt: { bsonType: "date" }
        }
      }
    },
    validationLevel: "strict"
  });
  
  // Create indexes
  await db.collection("comments").createIndex(
    { taskId: 1 },
    { name: "comments_taskId_idx" }
  );
};

// down.js
module.exports = async function down(db, client) {
  await db.collection("comments").drop();
};
```

## Troubleshooting

### Common Issues and Solutions

| Issue | Possible Causes | Solutions |
|-------|----------------|-----------|
| Migration timeout | Large data volume, inefficient queries | Add indexing, batch operations, increase timeout |
| Lock contention | Concurrent operations, long-running write operations | Schedule during low traffic, batch operations |
| Migration failure | Script errors, unexpected data | Test with production data copy, add error handling |
| Slow migration | Missing indexes, complex operations | Create temporary indexes, optimize operations |
| Data inconsistency | Partial migration completion | Ensure transactions or idempotent scripts |

### Monitoring During Migrations

Monitor these key metrics during migration execution:

- Database CPU and memory usage
- Lock percentage and queue length
- Operation time and throughput
- Error rates and types
- Disk I/O and storage usage

### Log Analysis

Migration logs should be analyzed for patterns of issues:

```
migration-logs/
├── YYYYMMDD_HHMMSS_migration_name.log
└── ...
```

Use log analysis tools to identify warnings, errors, and performance issues.

## References

- [MongoDB Data Migration Best Practices](https://www.mongodb.com/blog/post/building-with-patterns-the-schema-versioning-pattern)
- [MongoDB Schema Design Patterns](https://www.mongodb.com/blog/post/building-with-patterns-a-summary)
- [MongoDB Index Creation](https://docs.mongodb.com/manual/reference/method/db.collection.createIndex/)
- Internal Task Management System Architecture Documentation

---

**Note**: This migration system is designed specifically for the Task Management System and may need adjustments for other projects or specific requirements. Always consult with the database administration team before executing migrations in production environments.