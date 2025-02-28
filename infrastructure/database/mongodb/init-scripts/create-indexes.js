/**
 * MongoDB Initialization Script - Index Creation
 * 
 * This script creates optimized indexes for all collections in the Task Management System
 * to improve query performance according to the indexing strategy specified in the 
 * technical documentation.
 * 
 * @version 1.0.0
 */

// MongoDB connection parameters
const MONGODB_URI = process.env.MONGODB_URI || 'mongodb://localhost:27017/taskmanagement';
const DB_NAME = process.env.DB_NAME || 'taskmanagement';

// MongoDB driver - version 4.17.1
const { MongoClient } = require('mongodb');

/**
 * Creates indexes for the users collection
 * @param {object} db - MongoDB database reference
 * @returns {Promise} Resolves when indexes are created
 */
async function createUserIndexes(db) {
  const users = db.collection('users');
  
  console.log('Creating indexes for users collection...');
  
  // Create a unique index on email field for fast lookup and to ensure uniqueness
  await users.createIndex({ email: 1 }, { unique: true });
  
  // Create an index on organizations.orgId field for organization membership queries
  await users.createIndex({ 'organizations.orgId': 1 });
  
  // Create an index on roles field for authorization queries
  await users.createIndex({ roles: 1 });
  
  // Create an index on status field for filtering active/inactive users
  await users.createIndex({ status: 1 });
  
  console.log('User indexes created successfully');
}

/**
 * Creates indexes for the tasks collection
 * @param {object} db - MongoDB database reference
 * @returns {Promise} Resolves when indexes are created
 */
async function createTaskIndexes(db) {
  const tasks = db.collection('tasks');
  
  console.log('Creating indexes for tasks collection...');
  
  // Create compound index on assigneeId and status fields for task list by assignee and status
  await tasks.createIndex({ assigneeId: 1, status: 1 });
  
  // Create compound index on projectId and status fields for project task lists by status
  await tasks.createIndex({ projectId: 1, status: 1 });
  
  // Create index on dueDate field for due date sorting and filtering
  await tasks.createIndex({ dueDate: 1 });
  
  // Create index on createdBy field for tasks created by user
  await tasks.createIndex({ createdBy: 1 });
  
  // Create index on priority field for task prioritization queries
  await tasks.createIndex({ priority: 1 });
  
  // Create text index on title and description for search functionality
  await tasks.createIndex(
    { title: "text", description: "text" }, 
    { weights: { title: 10, description: 5 } }
  );
  
  console.log('Task indexes created successfully');
}

/**
 * Creates indexes for the projects collection
 * @param {object} db - MongoDB database reference
 * @returns {Promise} Resolves when indexes are created
 */
async function createProjectIndexes(db) {
  const projects = db.collection('projects');
  
  console.log('Creating indexes for projects collection...');
  
  // Create index on ownerId field for project ownership queries
  await projects.createIndex({ ownerId: 1 });
  
  // Create index on members.userId field for project membership queries
  await projects.createIndex({ 'members.userId': 1 });
  
  // Create index on status field for filtering by project status
  await projects.createIndex({ status: 1 });
  
  // Create index on category field for project categorization
  await projects.createIndex({ category: 1 });
  
  console.log('Project indexes created successfully');
}

/**
 * Creates indexes for the comments collection
 * @param {object} db - MongoDB database reference
 * @returns {Promise} Resolves when indexes are created
 */
async function createCommentIndexes(db) {
  const comments = db.collection('comments');
  
  console.log('Creating indexes for comments collection...');
  
  // Create index on taskId field for retrieving comments for a specific task
  await comments.createIndex({ taskId: 1 });
  
  // Create index on createdBy field for user's comments
  await comments.createIndex({ createdBy: 1 });
  
  // Create index on createdAt field for chronological sorting
  await comments.createIndex({ createdAt: 1 });
  
  console.log('Comment indexes created successfully');
}

/**
 * Creates indexes for the notifications collection
 * @param {object} db - MongoDB database reference
 * @returns {Promise} Resolves when indexes are created
 */
async function createNotificationIndexes(db) {
  const notifications = db.collection('notifications');
  
  console.log('Creating indexes for notifications collection...');
  
  // Create index on recipient field for user notifications
  await notifications.createIndex({ recipient: 1 });
  
  // Create index on read field for filtering read/unread notifications
  await notifications.createIndex({ read: 1 });
  
  // Create index on priority field for prioritizing notifications
  await notifications.createIndex({ priority: 1 });
  
  // Create TTL index on metadata.created field for automatic expiration of old notifications
  await notifications.createIndex(
    { 'metadata.created': 1 }, 
    { expireAfterSeconds: 30 * 24 * 60 * 60 } // 30 days TTL
  );
  
  console.log('Notification indexes created successfully');
}

/**
 * Creates indexes for the files collection
 * @param {object} db - MongoDB database reference
 * @returns {Promise} Resolves when indexes are created
 */
async function createFileIndexes(db) {
  const files = db.collection('files');
  
  console.log('Creating indexes for files collection...');
  
  // Create index on associations.taskId field for task attachments
  await files.createIndex({ 'associations.taskId': 1 });
  
  // Create index on associations.projectId field for project attachments
  await files.createIndex({ 'associations.projectId': 1 });
  
  // Create index on metadata.uploadedBy field for user uploads
  await files.createIndex({ 'metadata.uploadedBy': 1 });
  
  // Create index on security.accessLevel field for access control
  await files.createIndex({ 'security.accessLevel': 1 });
  
  console.log('File indexes created successfully');
}

/**
 * Creates indexes for the analytics collections
 * @param {object} db - MongoDB database reference
 * @returns {Promise} Resolves when indexes are created
 */
async function createAnalyticsIndexes(db) {
  console.log('Creating indexes for analytics collections...');
  
  // Dashboard collection indexes
  const dashboards = db.collection('dashboards');
  
  // Create index on owner field for user's dashboards
  await dashboards.createIndex({ owner: 1 });
  
  // Report collection indexes
  const reports = db.collection('reports');
  
  // Create index on owner field for user's reports
  await reports.createIndex({ owner: 1 });
  
  // Create index on metadata.created field for report date filtering
  await reports.createIndex({ 'metadata.created': 1 });
  
  console.log('Analytics indexes created successfully');
}

/**
 * Main function that connects to MongoDB and creates all necessary indexes
 * @returns {Promise} Resolves when all indexes are created
 */
async function main() {
  let client;
  
  try {
    // Connect to MongoDB
    console.log(`Connecting to MongoDB at ${MONGODB_URI}...`);
    client = new MongoClient(MONGODB_URI);
    await client.connect();
    console.log('Connected to MongoDB successfully');
    
    // Get database reference
    const db = client.db(DB_NAME);
    console.log(`Using database: ${DB_NAME}`);
    
    // Create indexes for all collections
    await createUserIndexes(db);
    await createTaskIndexes(db);
    await createProjectIndexes(db);
    await createCommentIndexes(db);
    await createNotificationIndexes(db);
    await createFileIndexes(db);
    await createAnalyticsIndexes(db);
    
    console.log('All indexes created successfully');
  } catch (err) {
    console.error('Error creating indexes:', err);
    throw err;
  } finally {
    // Close the connection
    if (client) {
      await client.close();
      console.log('MongoDB connection closed');
    }
  }
}

// Execute the script directly if run from command line
if (require.main === module) {
  main()
    .then(() => console.log('Index creation completed successfully'))
    .catch((err) => {
      console.error('Failed to create indexes:', err);
      process.exit(1);
    });
}

// Export the main function for importing in other scripts
module.exports = main;