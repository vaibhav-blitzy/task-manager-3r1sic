#!/bin/bash
# verify-restore.sh - Validates the integrity and completeness of restored MongoDB database backups
# Version: 1.0.0
# 
# This script performs comprehensive checks on MongoDB database contents after restoration
# to ensure data consistency, structural integrity, and referential validity.
#
# Usage: ./verify-restore.sh [--backup-id ID] [--host HOST] [--port PORT] [--verbose]

# Script version
SCRIPT_VERSION="1.0.0"

# Default values
LOG_FILE="/var/log/task-management/backup/verify-restore.log"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-27017}"
DB_USER="${DB_USER:-}"
DB_PASSWORD="${DB_PASSWORD:-}"
BACKUP_ID="${BACKUP_ID:-$(date +%Y%m%d%H%M%S)}"
NOTIFICATION_TOPIC_ARN="${NOTIFICATION_TOPIC_ARN:-}"
RESULTS_BUCKET="${RESULTS_BUCKET:-task-management-backup-reports}"
VERBOSE=false
TEMP_DIR=$(mktemp -d)

# MongoDB collections to verify
EXPECTED_COLLECTIONS=(
    "users"
    "tasks"
    "projects"
    "comments"
    "attachments"
    "task_history"
    "notifications"
    "tags"
)

# Log message to console and file
log_message() {
    local message="$1"
    local level="${2:-INFO}"
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    local formatted_message="[$timestamp] [$level] $message"
    
    echo "$formatted_message"
    
    # Ensure log directory exists
    mkdir -p "$(dirname "$LOG_FILE")"
    echo "$formatted_message" >> "$LOG_FILE"
}

# Check for required tools and environment variables
check_prerequisites() {
    log_message "Checking prerequisites..." "INFO"
    
    # Check required commands
    local required_commands=("mongosh" "aws" "jq")
    local missing_commands=()
    
    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            missing_commands+=("$cmd")
        fi
    done
    
    if [ ${#missing_commands[@]} -ne 0 ]; then
        log_message "Missing required commands: ${missing_commands[*]}" "ERROR"
        return 1
    fi
    
    # Check required environment variables
    local required_vars=(
        "DB_HOST"
        "DB_PORT"
    )
    
    local missing_vars=()
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -ne 0 ]; then
        log_message "Missing required environment variables: ${missing_vars[*]}" "ERROR"
        return 1
    fi
    
    # If authentication is required, check for credentials
    if [ -n "$DB_USER" ]; then
        if [ -z "$DB_PASSWORD" ]; then
            log_message "DB_USER is set but DB_PASSWORD is missing" "ERROR"
            return 1
        fi
    fi
    
    log_message "All prerequisites satisfied" "INFO"
    return 0
}

# Connect to MongoDB and verify connection
connect_to_mongodb() {
    log_message "Connecting to MongoDB at ${DB_HOST}:${DB_PORT}..." "INFO"
    
    local connection_string="mongodb://"
    
    # Add authentication if provided
    if [ -n "$DB_USER" ] && [ -n "$DB_PASSWORD" ]; then
        connection_string="${connection_string}${DB_USER}:${DB_PASSWORD}@"
    fi
    
    # Add host and port
    connection_string="${connection_string}${DB_HOST}:${DB_PORT}/admin"
    
    # Test connection with a simple command
    # Write a simple MongoDB JavaScript that returns a success message if connection works
    local mongo_script=$(cat <<EOF
        try {
            db.adminCommand({ ping: 1 });
            print("CONNECTION_SUCCESSFUL");
            quit();
        } catch (err) {
            print("CONNECTION_FAILED: " + err.message);
            quit(1);
        }
EOF
    )
    
    local result=$(mongosh "$connection_string" --quiet --eval "$mongo_script")
    
    if [[ "$result" == *"CONNECTION_SUCCESSFUL"* ]]; then
        log_message "Successfully connected to MongoDB" "INFO"
        return 0
    else
        log_message "Failed to connect to MongoDB: ${result}" "ERROR"
        return 1
    fi
}

# Verify collections exist and have appropriate counts
verify_collections() {
    log_message "Verifying collections..." "INFO"
    
    local connection_string="mongodb://"
    
    # Add authentication if provided
    if [ -n "$DB_USER" ] && [ -n "$DB_PASSWORD" ]; then
        connection_string="${connection_string}${DB_USER}:${DB_PASSWORD}@"
    fi
    
    # Add host and port
    connection_string="${connection_string}${DB_HOST}:${DB_PORT}/task_management"
    
    # MongoDB script to verify collections
    local mongo_script=$(cat <<EOF
        let results = {
            status: "success",
            collections: {},
            missing: [],
            total_documents: 0
        };
        
        // Expected collections
        const expectedCollections = [
            "users",
            "tasks",
            "projects",
            "comments",
            "attachments",
            "task_history",
            "notifications",
            "tags"
        ];
        
        // Get list of actual collections
        const actualCollections = db.getCollectionNames();
        
        // Check each expected collection
        for (const coll of expectedCollections) {
            if (actualCollections.includes(coll)) {
                const count = db[coll].countDocuments({});
                results.collections[coll] = {
                    exists: true,
                    count: count
                };
                results.total_documents += count;
            } else {
                results.missing.push(coll);
                results.collections[coll] = {
                    exists: false,
                    count: 0
                };
                results.status = "failed";
            }
        }
        
        // Set minimum expected counts for critical collections
        const minExpected = {
            "users": 1,        // At least one admin user should exist
            "tasks": 0,        // Tasks may be empty in a new system
            "projects": 0,     // Projects may be empty in a new system
        };
        
        // Check if collections meet minimum counts
        for (const [coll, min] of Object.entries(minExpected)) {
            if (results.collections[coll] && results.collections[coll].exists) {
                if (results.collections[coll].count < min) {
                    results.collections[coll].belowMinimum = true;
                    results.status = "failed";
                } else {
                    results.collections[coll].belowMinimum = false;
                }
            }
        }
        
        // Output results as JSON
        JSON.stringify(results);
EOF
    )
    
    local result=$(mongosh "$connection_string" --quiet --eval "$mongo_script")
    
    # Write the result to a temporary file for later processing
    echo "$result" > "${TEMP_DIR}/collection_results.json"
    
    # Check if verification passed
    local status=$(echo "$result" | jq -r '.status')
    if [ "$status" == "success" ]; then
        log_message "Collection verification passed" "INFO"
        if [ "$VERBOSE" == "true" ]; then
            log_message "$(echo "$result" | jq -r '.collections | to_entries | map("\(.key): \(.value.count) documents") | join(", ")')" "INFO"
        fi
    else
        log_message "Collection verification failed" "ERROR"
        log_message "Missing collections: $(echo "$result" | jq -r '.missing | join(", ")')" "ERROR"
        
        # Log collections with below minimum counts
        for coll in $(echo "$result" | jq -r '.collections | to_entries | map(select(.value.belowMinimum == true)) | map(.key) | join(" ")'); do
            local count=$(echo "$result" | jq -r ".collections.\"$coll\".count")
            local min=$(echo "$minExpected" | jq -r ".\"$coll\"")
            log_message "Collection '$coll' has $count documents (minimum expected: $min)" "ERROR"
        done
    fi
    
    echo "$result"
}

# Verify indexes exist on collections
verify_indexes() {
    log_message "Verifying indexes..." "INFO"
    
    local connection_string="mongodb://"
    
    # Add authentication if provided
    if [ -n "$DB_USER" ] && [ -n "$DB_PASSWORD" ]; then
        connection_string="${connection_string}${DB_USER}:${DB_PASSWORD}@"
    fi
    
    # Add host and port
    connection_string="${connection_string}${DB_HOST}:${DB_PORT}/task_management"
    
    # MongoDB script to verify indexes
    local mongo_script=$(cat <<EOF
        let results = {
            status: "success",
            indexes: {},
            missing_indexes: {}
        };
        
        // Expected indexes for each collection
        const expectedIndexes = {
            "users": ["email_1", "_id_"],
            "tasks": ["assigneeId_1_status_1", "projectId_1_status_1", "dueDate_1", "createdBy_1", "_id_"],
            "projects": ["ownerId_1", "members.user_1", "_id_"],
            "comments": ["taskId_1", "userId_1", "_id_"],
            "task_history": ["taskId_1", "_id_"],
            "notifications": ["recipient_1", "_id_"],
            "attachments": ["taskId_1", "projectId_1", "_id_"]
        };
        
        // Check each collection for expected indexes
        for (const [coll, expectedIdxs] of Object.entries(expectedIndexes)) {
            if (!db.getCollectionNames().includes(coll)) {
                continue; // Skip collections that don't exist
            }
            
            results.indexes[coll] = {
                expected: expectedIdxs,
                actual: [],
                missing: []
            };
            
            // Get actual indexes
            const actualIndexes = db[coll].getIndexes().map(idx => idx.name);
            results.indexes[coll].actual = actualIndexes;
            
            // Find missing indexes
            const missing = expectedIdxs.filter(idx => !actualIndexes.includes(idx));
            results.indexes[coll].missing = missing;
            
            if (missing.length > 0) {
                results.status = "failed";
                results.missing_indexes[coll] = missing;
            }
        }
        
        // Output results as JSON
        JSON.stringify(results);
EOF
    )
    
    local result=$(mongosh "$connection_string" --quiet --eval "$mongo_script")
    
    # Write the result to a temporary file for later processing
    echo "$result" > "${TEMP_DIR}/index_results.json"
    
    # Check if verification passed
    local status=$(echo "$result" | jq -r '.status')
    if [ "$status" == "success" ]; then
        log_message "Index verification passed" "INFO"
    else
        log_message "Index verification failed" "ERROR"
        for coll in $(echo "$result" | jq -r '.missing_indexes | keys[]'); do
            log_message "Collection '$coll' missing indexes: $(echo "$result" | jq -r ".missing_indexes.\"$coll\" | join(\", \")")" "ERROR"
        done
    fi
    
    echo "$result"
}

# Verify data integrity across collections
verify_data_integrity() {
    log_message "Verifying data integrity..." "INFO"
    
    local connection_string="mongodb://"
    
    # Add authentication if provided
    if [ -n "$DB_USER" ] && [ -n "$DB_PASSWORD" ]; then
        connection_string="${connection_string}${DB_USER}:${DB_PASSWORD}@"
    fi
    
    # Add host and port
    connection_string="${connection_string}${DB_HOST}:${DB_PORT}/task_management"
    
    # MongoDB script to verify data integrity
    local mongo_script=$(cat <<EOF
        let results = {
            status: "success",
            integrity_checks: {},
            issues: []
        };
        
        // Function to add an issue
        function addIssue(check, description, details) {
            results.issues.push({
                check: check,
                description: description,
                details: details
            });
            results.status = "failed";
            results.integrity_checks[check] = false;
        }
        
        try {
            // 1. Check User References in Tasks
            const taskCount = db.tasks.countDocuments();
            const tasksWithInvalidAssignee = db.tasks.countDocuments({
                assigneeId: { $ne: null },
                $expr: {
                    $eq: [
                        { $cond: [{ $isObjectId: "$assigneeId" }, 1, 0] },
                        { $cond: [
                            { $gt: [{ $size: { $objectToArray: { $ifNull: [ "$assigneeId", {} ] } } }, 0] },
                            { $cond: [
                                { $gt: [db.users.countDocuments({ _id: "$assigneeId" }), 0] },
                                1,
                                0
                            ]},
                            1
                        ]}
                    ]
                }
            });
            
            results.integrity_checks["task_assignee_references"] = tasksWithInvalidAssignee === 0;
            if (tasksWithInvalidAssignee > 0) {
                addIssue(
                    "task_assignee_references",
                    "Tasks with invalid assignee references",
                    { count: tasksWithInvalidAssignee, total: taskCount }
                );
            }
            
            // 2. Check Project References in Tasks
            const tasksWithInvalidProject = db.tasks.countDocuments({
                projectId: { $ne: null },
                $expr: {
                    $eq: [
                        { $cond: [{ $isObjectId: "$projectId" }, 1, 0] },
                        { $cond: [
                            { $gt: [{ $size: { $objectToArray: { $ifNull: [ "$projectId", {} ] } } }, 0] },
                            { $cond: [
                                { $gt: [db.projects.countDocuments({ _id: "$projectId" }), 0] },
                                1,
                                0
                            ]},
                            1
                        ]}
                    ]
                }
            });
            
            results.integrity_checks["task_project_references"] = tasksWithInvalidProject === 0;
            if (tasksWithInvalidProject > 0) {
                addIssue(
                    "task_project_references",
                    "Tasks with invalid project references",
                    { count: tasksWithInvalidProject, total: taskCount }
                );
            }
            
            // 3. Check Task References in Comments
            const commentCount = db.comments.countDocuments();
            const commentsWithInvalidTask = db.comments.countDocuments({
                $expr: {
                    $eq: [
                        { $cond: [{ $isObjectId: "$taskId" }, 1, 0] },
                        { $cond: [
                            { $gt: [db.tasks.countDocuments({ _id: "$taskId" }), 0] },
                            1,
                            0
                        ]}
                    ]
                }
            });
            
            results.integrity_checks["comment_task_references"] = commentsWithInvalidTask === 0;
            if (commentsWithInvalidTask > 0) {
                addIssue(
                    "comment_task_references",
                    "Comments with invalid task references",
                    { count: commentsWithInvalidTask, total: commentCount }
                );
            }
            
            // 4. Check Task History Integrity
            const taskHistoryCount = db.task_history.countDocuments();
            const taskHistoryWithInvalidTask = db.task_history.countDocuments({
                $expr: {
                    $eq: [
                        { $cond: [{ $isObjectId: "$taskId" }, 1, 0] },
                        { $cond: [
                            { $gt: [db.tasks.countDocuments({ _id: "$taskId" }), 0] },
                            1,
                            0
                        ]}
                    ]
                }
            });
            
            results.integrity_checks["task_history_references"] = taskHistoryWithInvalidTask === 0;
            if (taskHistoryWithInvalidTask > 0) {
                addIssue(
                    "task_history_references",
                    "Task history entries with invalid task references",
                    { count: taskHistoryWithInvalidTask, total: taskHistoryCount }
                );
            }
            
            // 5. Check User References in Projects
            const projectCount = db.projects.countDocuments();
            const projectsWithInvalidOwner = db.projects.countDocuments({
                $expr: {
                    $eq: [
                        { $cond: [{ $isObjectId: "$ownerId" }, 1, 0] },
                        { $cond: [
                            { $gt: [db.users.countDocuments({ _id: "$ownerId" }), 0] },
                            1,
                            0
                        ]}
                    ]
                }
            });
            
            results.integrity_checks["project_owner_references"] = projectsWithInvalidOwner === 0;
            if (projectsWithInvalidOwner > 0) {
                addIssue(
                    "project_owner_references",
                    "Projects with invalid owner references",
                    { count: projectsWithInvalidOwner, total: projectCount }
                );
            }
            
            // 6. Check Task Status Validity
            const validStatuses = ["created", "assigned", "in-progress", "on-hold", "in-review", "completed", "cancelled"];
            const tasksWithInvalidStatus = db.tasks.countDocuments({
                status: { $nin: validStatuses }
            });
            
            results.integrity_checks["task_status_validity"] = tasksWithInvalidStatus === 0;
            if (tasksWithInvalidStatus > 0) {
                addIssue(
                    "task_status_validity",
                    "Tasks with invalid status values",
                    { count: tasksWithInvalidStatus, total: taskCount }
                );
            }
            
            // If no issues were found, mark all checks as passed
            if (results.issues.length === 0) {
                results.integrity_checks = {
                    "task_assignee_references": true,
                    "task_project_references": true,
                    "comment_task_references": true,
                    "task_history_references": true,
                    "project_owner_references": true,
                    "task_status_validity": true
                };
            }
        } catch (err) {
            results.status = "error";
            results.error = err.message;
        }
        
        // Output results as JSON
        JSON.stringify(results);
EOF
    )
    
    local result=$(mongosh "$connection_string" --quiet --eval "$mongo_script")
    
    # Write the result to a temporary file for later processing
    echo "$result" > "${TEMP_DIR}/integrity_results.json"
    
    # Check if verification passed
    local status=$(echo "$result" | jq -r '.status')
    if [ "$status" == "success" ]; then
        log_message "Data integrity verification passed" "INFO"
    elif [ "$status" == "error" ]; then
        log_message "Data integrity verification encountered an error: $(echo "$result" | jq -r '.error')" "ERROR"
    else
        log_message "Data integrity verification failed" "ERROR"
        for issue in $(echo "$result" | jq -c '.issues[]'); do
            local check=$(echo "$issue" | jq -r '.check')
            local description=$(echo "$issue" | jq -r '.description')
            local details=$(echo "$issue" | jq -r '.details | to_entries | map("\(.key): \(.value)") | join(", ")')
            log_message "Integrity issue: $description ($details)" "ERROR"
        done
    fi
    
    echo "$result"
}

# Generate comprehensive verification report
generate_report() {
    local collection_results="$1"
    local index_results="$2"
    local integrity_results="$3"
    
    log_message "Generating verification report..." "INFO"
    
    # Get MongoDB version
    local connection_string="mongodb://"
    
    # Add authentication if provided
    if [ -n "$DB_USER" ] && [ -n "$DB_PASSWORD" ]; then
        connection_string="${connection_string}${DB_USER}:${DB_PASSWORD}@"
    fi
    
    # Add host and port
    connection_string="${connection_string}${DB_HOST}:${DB_PORT}/admin"
    
    # Get MongoDB version
    local mongo_version=$(mongosh "$connection_string" --quiet --eval "db.version()")
    
    # Create the report
    local report=$(cat <<EOF
{
    "report_type": "database_restore_verification",
    "backup_id": "$BACKUP_ID",
    "verification_time": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
    "environment": {
        "hostname": "$(hostname)",
        "script_version": "$SCRIPT_VERSION",
        "mongodb_version": "$mongo_version"
    },
    "collection_verification": $collection_results,
    "index_verification": $index_results,
    "data_integrity": $integrity_results,
    "overall_status": "$(
        if [[ $(echo "$collection_results" | jq -r '.status') == "success" && 
              $(echo "$index_results" | jq -r '.status') == "success" && 
              $(echo "$integrity_results" | jq -r '.status') == "success" ]]; then
            echo "success"
        else
            echo "failed"
        fi
    )"
}
EOF
    )
    
    # Format with jq for consistent output
    echo "$report" | jq '.'
}

# Save verification report to S3 and local filesystem
save_report() {
    local report="$1"
    local timestamp=$(date +"%Y%m%d%H%M%S")
    local filename="verify-restore-${BACKUP_ID}-${timestamp}.json"
    local local_path="/var/log/task-management/backup/reports/${filename}"
    
    log_message "Saving verification report..." "INFO"
    
    # Ensure directory exists
    mkdir -p "$(dirname "$local_path")"
    
    # Save locally
    echo "$report" > "$local_path"
    log_message "Report saved locally to $local_path" "INFO"
    
    # Save to S3 if bucket is configured
    if [ -n "$RESULTS_BUCKET" ]; then
        if aws s3 cp "$local_path" "s3://${RESULTS_BUCKET}/${filename}"; then
            log_message "Report uploaded to s3://${RESULTS_BUCKET}/${filename}" "INFO"
            return 0
        else
            log_message "Failed to upload report to S3" "ERROR"
            return 1
        fi
    else
        log_message "S3 bucket not configured, report not uploaded to S3" "WARN"
        return 0
    fi
}

# Send notification with verification results
send_notification() {
    local report="$1"
    local success="$2"
    
    # Skip if notification topic not configured
    if [ -z "$NOTIFICATION_TOPIC_ARN" ]; then
        log_message "Notification topic not configured, skipping notification" "WARN"
        return 0
    fi
    
    log_message "Sending notification..." "INFO"
    
    local status_text=$([ "$success" == "true" ] && echo "PASSED" || echo "FAILED")
    local subject="Backup Verification ${status_text}: ${BACKUP_ID}"
    
    # Create a summary message
    local collection_status=$(echo "$report" | jq -r '.collection_verification.status')
    local index_status=$(echo "$report" | jq -r '.index_verification.status')
    local integrity_status=$(echo "$report" | jq -r '.data_integrity.status')
    local total_documents=$(echo "$report" | jq -r '.collection_verification.total_documents')
    
    local message=$(cat <<EOF
Backup Verification Report: ${status_text}

Backup ID: ${BACKUP_ID}
Verification Time: $(date)
Environment: $(hostname)

Summary:
- Collection Verification: ${collection_status}
- Index Verification: ${index_status}
- Data Integrity: ${integrity_status}
- Total Documents: ${total_documents}

For detailed results, see the full report in:
s3://${RESULTS_BUCKET}/verify-restore-${BACKUP_ID}-$(date +"%Y%m%d%H%M%S").json
EOF
    )
    
    # Send via SNS
    if aws sns publish --topic-arn "$NOTIFICATION_TOPIC_ARN" --subject "$subject" --message "$message"; then
        log_message "Notification sent successfully" "INFO"
        return 0
    else
        log_message "Failed to send notification" "ERROR"
        return 1
    fi
}

# Cleanup temporary files and resources
cleanup() {
    log_message "Performing cleanup..." "INFO"
    
    # Remove temporary directory
    if [ -d "$TEMP_DIR" ]; then
        rm -rf "$TEMP_DIR"
    fi
    
    log_message "Cleanup completed" "INFO"
}

# Main function
main() {
    # Parse command line options
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --backup-id)
                BACKUP_ID="$2"
                shift 2
                ;;
            --host)
                DB_HOST="$2"
                shift 2
                ;;
            --port)
                DB_PORT="$2"
                shift 2
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            --help)
                echo "Usage: $0 [--backup-id ID] [--host HOST] [--port PORT] [--verbose]"
                echo ""
                echo "Options:"
                echo "  --backup-id ID    Specify the backup ID being verified"
                echo "  --host HOST       MongoDB host (default: \$DB_HOST or localhost)"
                echo "  --port PORT       MongoDB port (default: \$DB_PORT or 27017)"
                echo "  --verbose         Enable verbose output"
                echo "  --help            Display this help message"
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done
    
    # Setup trap to ensure cleanup on exit
    trap cleanup EXIT
    
    # Initialize with banner
    log_message "=== MongoDB Backup Verification v${SCRIPT_VERSION} ===" "INFO"
    log_message "Backup ID: ${BACKUP_ID}" "INFO"
    log_message "Target: ${DB_HOST}:${DB_PORT}" "INFO"
    
    # Check prerequisites
    if ! check_prerequisites; then
        log_message "Prerequisite check failed, aborting" "ERROR"
        return 1
    fi
    
    # Connect to MongoDB
    if ! connect_to_mongodb; then
        log_message "MongoDB connection failed, aborting" "ERROR"
        return 1
    fi
    
    # Perform verifications
    local collection_results=$(verify_collections)
    local index_results=$(verify_indexes)
    local integrity_results=$(verify_data_integrity)
    
    # Generate and save report
    local report=$(generate_report "$collection_results" "$index_results" "$integrity_results")
    save_report "$report"
    
    # Determine overall status
    local overall_status=$(echo "$report" | jq -r '.overall_status')
    local success=$([ "$overall_status" == "success" ] && echo "true" || echo "false")
    
    # Send notification
    send_notification "$report" "$success"
    
    # Output final status
    if [ "$success" == "true" ]; then
        log_message "Verification completed successfully!" "INFO"
        return 0
    else
        log_message "Verification completed with failures" "ERROR"
        return 1
    fi
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
    exit $?
fi