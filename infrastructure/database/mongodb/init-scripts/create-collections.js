/**
 * MongoDB Initialization Script for Task Management System
 * Version: 1.0.0
 * 
 * This script creates all necessary collections with validation schemas for the 
 * Task Management System database as specified in the technical requirements.
 * 
 * mongodb: ^4.17.1
 */

// Database connection parameters (can be overridden by environment variables)
var MONGODB_URI = (typeof process !== 'undefined' && process.env.MONGODB_URI) || 'mongodb://localhost:27017/taskmanagement';
var DB_NAME = (typeof process !== 'undefined' && process.env.DB_NAME) || 'taskmanagement';

/**
 * Creates the users collection with validation schema
 * @param {Object} db - MongoDB database instance
 * @returns {Promise} Resolves when collection is created
 */
function createUsersCollection(db) {
  print("Creating users collection...");
  
  // Check if collection already exists
  if (db.getCollectionNames().indexOf("users") !== -1) {
    print("Users collection already exists");
    return;
  }
  
  // User schema validation
  db.createCollection("users", {
    validator: {
      $jsonSchema: {
        bsonType: "object",
        required: ["email", "passwordHash", "firstName", "lastName", "roles", "status", "createdAt"],
        properties: {
          _id: {
            bsonType: "objectId",
            description: "Required and must be an ObjectId"
          },
          email: {
            bsonType: "string",
            pattern: "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$",
            description: "Must be a valid email address"
          },
          passwordHash: {
            bsonType: "string",
            description: "Required and must be a string"
          },
          firstName: {
            bsonType: "string",
            description: "Required and must be a string"
          },
          lastName: {
            bsonType: "string",
            description: "Required and must be a string"
          },
          roles: {
            bsonType: "array",
            minItems: 1,
            items: {
              bsonType: "string"
            },
            description: "Required and must be an array of strings"
          },
          organizations: {
            bsonType: "array",
            items: {
              bsonType: "object",
              required: ["orgId", "role"],
              properties: {
                orgId: {
                  bsonType: "objectId",
                  description: "Must be an ObjectId"
                },
                role: {
                  bsonType: "string",
                  description: "Must be a string"
                }
              }
            },
            description: "Must be an array of organization memberships"
          },
          settings: {
            bsonType: "object",
            properties: {
              language: {
                bsonType: "string",
                description: "Must be a string"
              },
              theme: {
                bsonType: "string",
                description: "Must be a string"
              },
              notifications: {
                bsonType: "object",
                properties: {
                  email: {
                    bsonType: "bool",
                    description: "Must be a boolean"
                  },
                  push: {
                    bsonType: "bool",
                    description: "Must be a boolean"
                  },
                  inApp: {
                    bsonType: "bool",
                    description: "Must be a boolean"
                  }
                }
              }
            },
            description: "User preferences and settings"
          },
          security: {
            bsonType: "object",
            properties: {
              mfaEnabled: {
                bsonType: "bool",
                description: "Must be a boolean"
              },
              mfaMethod: {
                bsonType: "string",
                enum: ["app", "sms", "email"],
                description: "Must be one of the allowed MFA methods"
              },
              lastLogin: {
                bsonType: "date",
                description: "Must be a date"
              },
              passwordLastChanged: {
                bsonType: "date",
                description: "Must be a date"
              },
              failedAttempts: {
                bsonType: "int",
                description: "Must be an integer"
              }
            },
            description: "Security settings and information"
          },
          status: {
            bsonType: "string",
            enum: ["active", "suspended", "inactive"],
            description: "Required and must be one of the allowed values"
          },
          createdAt: {
            bsonType: "date",
            description: "Required and must be a date"
          },
          updatedAt: {
            bsonType: "date",
            description: "Must be a date"
          }
        }
      }
    },
    validationLevel: "moderate",
    validationAction: "error"
  });
  
  print("Users collection created with validation schema");
  
  // Create unique index on email
  db.users.createIndex({ email: 1 }, { unique: true });
  print("Unique index created on users.email");
  
  // Create index on organizations.orgId
  db.users.createIndex({ "organizations.orgId": 1 });
  print("Index created on users.organizations.orgId");
}

/**
 * Creates the tasks collection with validation schema
 * @param {Object} db - MongoDB database instance
 * @returns {Promise} Resolves when collection is created
 */
function createTasksCollection(db) {
  print("Creating tasks collection...");
  
  // Check if collection already exists
  if (db.getCollectionNames().indexOf("tasks") !== -1) {
    print("Tasks collection already exists");
    return;
  }
  
  // Task schema validation
  db.createCollection("tasks", {
    validator: {
      $jsonSchema: {
        bsonType: "object",
        required: ["title", "status", "createdBy", "metadata.createdAt"],
        properties: {
          _id: {
            bsonType: "objectId",
            description: "Required and must be an ObjectId"
          },
          title: {
            bsonType: "string",
            minLength: 1,
            description: "Required and must be a non-empty string"
          },
          description: {
            bsonType: "string",
            description: "Must be a string"
          },
          status: {
            bsonType: "string",
            enum: ["created", "assigned", "in-progress", "on-hold", "in-review", "completed", "cancelled"],
            description: "Required and must be one of the allowed values"
          },
          priority: {
            bsonType: "string",
            enum: ["low", "medium", "high", "urgent"],
            description: "Must be one of the allowed values"
          },
          dueDate: {
            bsonType: "date",
            description: "Must be a date"
          },
          createdBy: {
            bsonType: "objectId",
            description: "Required and must be an ObjectId"
          },
          assigneeId: {
            bsonType: ["objectId", "null"],
            description: "Must be an ObjectId or null"
          },
          projectId: {
            bsonType: ["objectId", "null"],
            description: "Must be an ObjectId or null"
          },
          tags: {
            bsonType: "array",
            items: {
              bsonType: "string"
            },
            description: "Must be an array of strings"
          },
          subtasks: {
            bsonType: "array",
            items: {
              bsonType: "object",
              required: ["title", "completed"],
              properties: {
                _id: {
                  bsonType: "objectId",
                  description: "Must be an ObjectId"
                },
                title: {
                  bsonType: "string",
                  description: "Required and must be a string"
                },
                completed: {
                  bsonType: "bool",
                  description: "Required and must be a boolean"
                },
                assigneeId: {
                  bsonType: ["objectId", "null"],
                  description: "Must be an ObjectId or null"
                }
              }
            },
            description: "Must be an array of subtask objects"
          },
          dependencies: {
            bsonType: "array",
            items: {
              bsonType: "object",
              required: ["taskId", "type"],
              properties: {
                taskId: {
                  bsonType: "objectId",
                  description: "Required and must be an ObjectId"
                },
                type: {
                  bsonType: "string",
                  enum: ["blocks", "blocked-by"],
                  description: "Required and must be one of the allowed values"
                }
              }
            },
            description: "Must be an array of dependency objects"
          },
          metadata: {
            bsonType: "object",
            required: ["createdAt"],
            properties: {
              createdAt: {
                bsonType: "date",
                description: "Required and must be a date"
              },
              updatedAt: {
                bsonType: "date",
                description: "Must be a date"
              },
              completedAt: {
                bsonType: ["date", "null"],
                description: "Must be a date or null"
              },
              timeEstimate: {
                bsonType: ["int", "null"],
                description: "Must be an integer or null representing minutes"
              },
              timeSpent: {
                bsonType: ["int", "null"],
                description: "Must be an integer or null representing minutes"
              }
            },
            description: "Metadata for the task"
          }
        }
      }
    },
    validationLevel: "moderate",
    validationAction: "error"
  });
  
  print("Tasks collection created with validation schema");
  
  // Create indexes
  db.tasks.createIndex({ assigneeId: 1, status: 1 });
  print("Index created on tasks.assigneeId and tasks.status");
  
  db.tasks.createIndex({ projectId: 1, status: 1 });
  print("Index created on tasks.projectId and tasks.status");
  
  db.tasks.createIndex({ dueDate: 1 });
  print("Index created on tasks.dueDate");
  
  db.tasks.createIndex({ createdBy: 1 });
  print("Index created on tasks.createdBy");
  
  // Create text index for search
  db.tasks.createIndex({ title: "text", description: "text" });
  print("Text index created on tasks.title and tasks.description");
}

/**
 * Creates the projects collection with validation schema
 * @param {Object} db - MongoDB database instance
 * @returns {Promise} Resolves when collection is created
 */
function createProjectsCollection(db) {
  print("Creating projects collection...");
  
  // Check if collection already exists
  if (db.getCollectionNames().indexOf("projects") !== -1) {
    print("Projects collection already exists");
    return;
  }
  
  // Project schema validation
  db.createCollection("projects", {
    validator: {
      $jsonSchema: {
        bsonType: "object",
        required: ["name", "status", "owner", "metadata.created"],
        properties: {
          _id: {
            bsonType: "objectId",
            description: "Required and must be an ObjectId"
          },
          name: {
            bsonType: "string",
            minLength: 1,
            description: "Required and must be a non-empty string"
          },
          description: {
            bsonType: "string",
            description: "Must be a string"
          },
          status: {
            bsonType: "string",
            enum: ["planning", "active", "on-hold", "completed", "archived", "cancelled"],
            description: "Required and must be one of the allowed values"
          },
          category: {
            bsonType: "string",
            description: "Must be a string"
          },
          owner: {
            bsonType: "objectId",
            description: "Required and must be an ObjectId"
          },
          members: {
            bsonType: "array",
            items: {
              bsonType: "object",
              required: ["user", "role", "joinedAt"],
              properties: {
                user: {
                  bsonType: "objectId",
                  description: "Required and must be an ObjectId"
                },
                role: {
                  bsonType: "string",
                  enum: ["admin", "manager", "member", "viewer"],
                  description: "Required and must be one of the allowed values"
                },
                joinedAt: {
                  bsonType: "date",
                  description: "Required and must be a date"
                }
              }
            },
            description: "Must be an array of member objects"
          },
          settings: {
            bsonType: "object",
            properties: {
              workflow: {
                bsonType: "object",
                properties: {
                  enableReview: {
                    bsonType: "bool",
                    description: "Must be a boolean"
                  },
                  allowSubtasks: {
                    bsonType: "bool",
                    description: "Must be a boolean"
                  },
                  defaultTaskStatus: {
                    bsonType: "string",
                    description: "Must be a string"
                  }
                }
              },
              permissions: {
                bsonType: "object",
                properties: {
                  memberInvite: {
                    bsonType: "string",
                    description: "Must be a string"
                  },
                  taskCreate: {
                    bsonType: "string",
                    description: "Must be a string"
                  },
                  commentCreate: {
                    bsonType: "string",
                    description: "Must be a string"
                  }
                }
              },
              notifications: {
                bsonType: "object",
                properties: {
                  taskCreate: {
                    bsonType: "bool",
                    description: "Must be a boolean"
                  },
                  taskComplete: {
                    bsonType: "bool",
                    description: "Must be a boolean"
                  },
                  commentAdd: {
                    bsonType: "bool",
                    description: "Must be a boolean"
                  }
                }
              }
            },
            description: "Project settings"
          },
          taskLists: {
            bsonType: "array",
            items: {
              bsonType: "object",
              required: ["name", "sortOrder"],
              properties: {
                _id: {
                  bsonType: "objectId",
                  description: "Must be an ObjectId"
                },
                name: {
                  bsonType: "string",
                  description: "Required and must be a string"
                },
                description: {
                  bsonType: "string",
                  description: "Must be a string"
                },
                sortOrder: {
                  bsonType: "int",
                  description: "Required and must be an integer"
                }
              }
            },
            description: "Must be an array of task list objects"
          },
          metadata: {
            bsonType: "object",
            required: ["created"],
            properties: {
              created: {
                bsonType: "date",
                description: "Required and must be a date"
              },
              lastUpdated: {
                bsonType: "date",
                description: "Must be a date"
              },
              completedAt: {
                bsonType: ["date", "null"],
                description: "Must be a date or null"
              },
              taskCount: {
                bsonType: "int",
                description: "Must be an integer"
              },
              completedTaskCount: {
                bsonType: "int",
                description: "Must be an integer"
              }
            },
            description: "Metadata for the project"
          },
          tags: {
            bsonType: "array",
            items: {
              bsonType: "string"
            },
            description: "Must be an array of strings"
          },
          customFields: {
            bsonType: "array",
            items: {
              bsonType: "object",
              required: ["name", "type"],
              properties: {
                name: {
                  bsonType: "string",
                  description: "Required and must be a string"
                },
                type: {
                  bsonType: "string",
                  enum: ["text", "number", "date", "select"],
                  description: "Required and must be one of the allowed values"
                },
                options: {
                  bsonType: "array",
                  items: {
                    bsonType: "string"
                  },
                  description: "Must be an array of strings for select type"
                }
              }
            },
            description: "Must be an array of custom field objects"
          }
        }
      }
    },
    validationLevel: "moderate",
    validationAction: "error"
  });
  
  print("Projects collection created with validation schema");
  
  // Create indexes
  db.projects.createIndex({ owner: 1 });
  print("Index created on projects.owner");
  
  db.projects.createIndex({ "members.user": 1 });
  print("Index created on projects.members.user");
  
  db.projects.createIndex({ name: 1, owner: 1 }, { unique: true });
  print("Unique index created on projects.name and projects.owner");
  
  // Create text index for search
  db.projects.createIndex({ name: "text", description: "text" });
  print("Text index created on projects.name and projects.description");
}

/**
 * Creates the comments collection with validation schema
 * @param {Object} db - MongoDB database instance
 * @returns {Promise} Resolves when collection is created
 */
function createCommentsCollection(db) {
  print("Creating comments collection...");
  
  // Check if collection already exists
  if (db.getCollectionNames().indexOf("comments") !== -1) {
    print("Comments collection already exists");
    return;
  }
  
  // Comment schema validation
  db.createCollection("comments", {
    validator: {
      $jsonSchema: {
        bsonType: "object",
        required: ["content", "taskId", "createdBy", "createdAt"],
        properties: {
          _id: {
            bsonType: "objectId",
            description: "Required and must be an ObjectId"
          },
          content: {
            bsonType: "string",
            minLength: 1,
            description: "Required and must be a non-empty string"
          },
          taskId: {
            bsonType: "objectId",
            description: "Required and must be an ObjectId"
          },
          createdBy: {
            bsonType: "objectId",
            description: "Required and must be an ObjectId"
          },
          createdAt: {
            bsonType: "date",
            description: "Required and must be a date"
          },
          updatedAt: {
            bsonType: ["date", "null"],
            description: "Must be a date or null"
          }
        }
      }
    },
    validationLevel: "moderate",
    validationAction: "error"
  });
  
  print("Comments collection created with validation schema");
  
  // Create indexes
  db.comments.createIndex({ taskId: 1 });
  print("Index created on comments.taskId");
  
  db.comments.createIndex({ createdBy: 1 });
  print("Index created on comments.createdBy");
  
  db.comments.createIndex({ createdAt: 1 });
  print("Index created on comments.createdAt");
}

/**
 * Creates the notifications collection with validation schema
 * @param {Object} db - MongoDB database instance
 * @returns {Promise} Resolves when collection is created
 */
function createNotificationsCollection(db) {
  print("Creating notifications collection...");
  
  // Check if collection already exists
  if (db.getCollectionNames().indexOf("notifications") !== -1) {
    print("Notifications collection already exists");
    return;
  }
  
  // Notification schema validation
  db.createCollection("notifications", {
    validator: {
      $jsonSchema: {
        bsonType: "object",
        required: ["recipient", "type", "title", "metadata.created"],
        properties: {
          _id: {
            bsonType: "objectId",
            description: "Required and must be an ObjectId"
          },
          recipient: {
            bsonType: "objectId",
            description: "Required and must be an ObjectId"
          },
          type: {
            bsonType: "string",
            enum: [
              "TASK_ASSIGNED", "TASK_DUE_SOON", "TASK_OVERDUE", 
              "COMMENT_ADDED", "MENTION", "PROJECT_INVITATION", 
              "STATUS_CHANGE"
            ],
            description: "Required and must be one of the allowed values"
          },
          title: {
            bsonType: "string",
            description: "Required and must be a string"
          },
          content: {
            bsonType: "string",
            description: "Must be a string"
          },
          priority: {
            bsonType: "string",
            enum: ["low", "normal", "high", "urgent"],
            description: "Must be one of the allowed values"
          },
          read: {
            bsonType: "bool",
            description: "Must be a boolean"
          },
          actionUrl: {
            bsonType: "string",
            description: "Must be a string"
          },
          metadata: {
            bsonType: "object",
            required: ["created"],
            properties: {
              created: {
                bsonType: "date",
                description: "Required and must be a date"
              },
              readAt: {
                bsonType: ["date", "null"],
                description: "Must be a date or null"
              },
              deliveryStatus: {
                bsonType: "object",
                properties: {
                  inApp: {
                    bsonType: "string",
                    enum: ["delivered", "failed", "pending"],
                    description: "Must be one of the allowed values"
                  },
                  email: {
                    bsonType: "string",
                    enum: ["delivered", "failed", "pending", "disabled"],
                    description: "Must be one of the allowed values"
                  },
                  push: {
                    bsonType: "string",
                    enum: ["delivered", "failed", "pending", "disabled"],
                    description: "Must be one of the allowed values"
                  }
                }
              },
              sourceEvent: {
                bsonType: "object",
                properties: {
                  type: {
                    bsonType: "string",
                    description: "Must be a string"
                  },
                  objectId: {
                    bsonType: "string",
                    description: "Must be a string"
                  },
                  objectType: {
                    bsonType: "string",
                    description: "Must be a string"
                  }
                }
              }
            },
            description: "Metadata for the notification"
          }
        }
      }
    },
    validationLevel: "moderate",
    validationAction: "error"
  });
  
  print("Notifications collection created with validation schema");
  
  // Create indexes
  db.notifications.createIndex({ recipient: 1 });
  print("Index created on notifications.recipient");
  
  db.notifications.createIndex({ "metadata.created": 1 });
  print("Index created on notifications.metadata.created");
  
  db.notifications.createIndex({ read: 1 });
  print("Index created on notifications.read");
  
  // Create TTL index for automatic deletion of old notifications
  db.notifications.createIndex({ "metadata.created": 1 }, { expireAfterSeconds: 7776000 }); // 90 days
  print("TTL index created on notifications.metadata.created (90 days)");
}

/**
 * Creates the files collection with validation schema
 * @param {Object} db - MongoDB database instance
 * @returns {Promise} Resolves when collection is created
 */
function createFilesCollection(db) {
  print("Creating files collection...");
  
  // Check if collection already exists
  if (db.getCollectionNames().indexOf("files") !== -1) {
    print("Files collection already exists");
    return;
  }
  
  // File schema validation
  db.createCollection("files", {
    validator: {
      $jsonSchema: {
        bsonType: "object",
        required: ["name", "size", "type", "storageKey", "metadata.uploadedBy", "metadata.uploadedAt"],
        properties: {
          _id: {
            bsonType: "objectId",
            description: "Required and must be an ObjectId"
          },
          name: {
            bsonType: "string",
            description: "Required and must be a string"
          },
          size: {
            bsonType: "int",
            description: "Required and must be an integer (bytes)"
          },
          type: {
            bsonType: "string",
            description: "Required and must be a string (MIME type)"
          },
          extension: {
            bsonType: "string",
            description: "Must be a string"
          },
          storageKey: {
            bsonType: "string",
            description: "Required and must be a string"
          },
          url: {
            bsonType: "string",
            description: "Must be a string"
          },
          preview: {
            bsonType: "object",
            properties: {
              thumbnail: {
                bsonType: "string",
                description: "Must be a string"
              },
              previewAvailable: {
                bsonType: "bool",
                description: "Must be a boolean"
              },
              previewType: {
                bsonType: "string",
                enum: ["image", "pdf", "document", "none"],
                description: "Must be one of the allowed values"
              }
            }
          },
          metadata: {
            bsonType: "object",
            required: ["uploadedBy", "uploadedAt"],
            properties: {
              uploadedBy: {
                bsonType: "objectId",
                description: "Required and must be an ObjectId"
              },
              uploadedAt: {
                bsonType: "date",
                description: "Required and must be a date"
              },
              lastAccessed: {
                bsonType: "date",
                description: "Must be a date"
              },
              accessCount: {
                bsonType: "int",
                description: "Must be an integer"
              },
              md5Hash: {
                bsonType: "string",
                description: "Must be a string"
              }
            }
          },
          security: {
            bsonType: "object",
            properties: {
              accessLevel: {
                bsonType: "string",
                enum: ["public", "private", "shared"],
                description: "Must be one of the allowed values"
              },
              encryptionType: {
                bsonType: "string",
                description: "Must be a string"
              },
              scanStatus: {
                bsonType: "string",
                enum: ["pending", "clean", "infected", "unknown"],
                description: "Must be one of the allowed values"
              }
            }
          },
          associations: {
            bsonType: "object",
            properties: {
              taskId: {
                bsonType: ["objectId", "null"],
                description: "Must be an ObjectId or null"
              },
              projectId: {
                bsonType: ["objectId", "null"],
                description: "Must be an ObjectId or null"
              },
              commentId: {
                bsonType: ["objectId", "null"],
                description: "Must be an ObjectId or null"
              }
            }
          },
          versions: {
            bsonType: "array",
            items: {
              bsonType: "object",
              required: ["storageKey", "size", "uploadedBy", "uploadedAt"],
              properties: {
                _id: {
                  bsonType: "objectId",
                  description: "Must be an ObjectId"
                },
                storageKey: {
                  bsonType: "string",
                  description: "Required and must be a string"
                },
                size: {
                  bsonType: "int",
                  description: "Required and must be an integer"
                },
                uploadedBy: {
                  bsonType: "objectId",
                  description: "Required and must be an ObjectId"
                },
                uploadedAt: {
                  bsonType: "date",
                  description: "Required and must be a date"
                },
                changeNotes: {
                  bsonType: "string",
                  description: "Must be a string"
                }
              }
            }
          }
        }
      }
    },
    validationLevel: "moderate",
    validationAction: "error"
  });
  
  print("Files collection created with validation schema");
  
  // Create indexes
  db.files.createIndex({ "metadata.uploadedBy": 1 });
  print("Index created on files.metadata.uploadedBy");
  
  db.files.createIndex({ "associations.taskId": 1 });
  print("Index created on files.associations.taskId");
  
  db.files.createIndex({ "associations.projectId": 1 });
  print("Index created on files.associations.projectId");
  
  db.files.createIndex({ type: 1 });
  print("Index created on files.type");
}

/**
 * Creates the dashboards collection with validation schema
 * @param {Object} db - MongoDB database instance
 * @returns {Promise} Resolves when collection is created
 */
function createDashboardsCollection(db) {
  print("Creating dashboards collection...");
  
  // Check if collection already exists
  if (db.getCollectionNames().indexOf("dashboards") !== -1) {
    print("Dashboards collection already exists");
    return;
  }
  
  // Dashboard schema validation
  db.createCollection("dashboards", {
    validator: {
      $jsonSchema: {
        bsonType: "object",
        required: ["name", "owner", "type", "metadata.created"],
        properties: {
          _id: {
            bsonType: "objectId",
            description: "Required and must be an ObjectId"
          },
          name: {
            bsonType: "string",
            description: "Required and must be a string"
          },
          owner: {
            bsonType: "objectId",
            description: "Required and must be an ObjectId"
          },
          type: {
            bsonType: "string",
            enum: ["personal", "project", "team", "organization"],
            description: "Required and must be one of the allowed values"
          },
          scope: {
            bsonType: "object",
            properties: {
              projects: {
                bsonType: "array",
                items: {
                  bsonType: "objectId"
                },
                description: "Must be an array of ObjectIds"
              },
              users: {
                bsonType: "array",
                items: {
                  bsonType: "objectId"
                },
                description: "Must be an array of ObjectIds"
              },
              dateRange: {
                bsonType: "object",
                properties: {
                  start: {
                    bsonType: ["date", "null"],
                    description: "Must be a date or null"
                  },
                  end: {
                    bsonType: ["date", "null"],
                    description: "Must be a date or null"
                  },
                  preset: {
                    bsonType: "string",
                    enum: ["today", "week", "month", "quarter", "year"],
                    description: "Must be one of the allowed values"
                  }
                }
              }
            }
          },
          layout: {
            bsonType: "object",
            properties: {
              columns: {
                bsonType: "int",
                description: "Must be an integer"
              },
              widgets: {
                bsonType: "array",
                items: {
                  bsonType: "object",
                  required: ["type", "position"],
                  properties: {
                    _id: {
                      bsonType: "objectId",
                      description: "Must be an ObjectId"
                    },
                    type: {
                      bsonType: "string",
                      description: "Required and must be a string"
                    },
                    position: {
                      bsonType: "object",
                      required: ["x", "y", "width", "height"],
                      properties: {
                        x: {
                          bsonType: "int",
                          description: "Required and must be an integer"
                        },
                        y: {
                          bsonType: "int",
                          description: "Required and must be an integer"
                        },
                        width: {
                          bsonType: "int",
                          description: "Required and must be an integer"
                        },
                        height: {
                          bsonType: "int",
                          description: "Required and must be an integer"
                        }
                      }
                    },
                    config: {
                      bsonType: "object",
                      properties: {
                        title: {
                          bsonType: "string",
                          description: "Must be a string"
                        },
                        dataSource: {
                          bsonType: "string",
                          description: "Must be a string"
                        },
                        refreshInterval: {
                          bsonType: "int",
                          description: "Must be an integer"
                        },
                        visualizationType: {
                          bsonType: "string",
                          description: "Must be a string"
                        },
                        filters: {
                          bsonType: "object",
                          description: "Must be an object with filter criteria"
                        },
                        drilldownEnabled: {
                          bsonType: "bool",
                          description: "Must be a boolean"
                        }
                      }
                    }
                  }
                }
              }
            }
          },
          sharing: {
            bsonType: "object",
            properties: {
              public: {
                bsonType: "bool",
                description: "Must be a boolean"
              },
              sharedWith: {
                bsonType: "array",
                items: {
                  bsonType: "objectId"
                },
                description: "Must be an array of ObjectIds"
              }
            }
          },
          metadata: {
            bsonType: "object",
            required: ["created"],
            properties: {
              created: {
                bsonType: "date",
                description: "Required and must be a date"
              },
              lastUpdated: {
                bsonType: "date",
                description: "Must be a date"
              },
              lastViewed: {
                bsonType: "date",
                description: "Must be a date"
              }
            }
          }
        }
      }
    },
    validationLevel: "moderate",
    validationAction: "error"
  });
  
  print("Dashboards collection created with validation schema");
  
  // Create indexes
  db.dashboards.createIndex({ owner: 1 });
  print("Index created on dashboards.owner");
  
  db.dashboards.createIndex({ "sharing.sharedWith": 1 });
  print("Index created on dashboards.sharing.sharedWith");
  
  db.dashboards.createIndex({ "scope.projects": 1 });
  print("Index created on dashboards.scope.projects");
}

/**
 * Creates the reports collection with validation schema
 * @param {Object} db - MongoDB database instance
 * @returns {Promise} Resolves when collection is created
 */
function createReportsCollection(db) {
  print("Creating reports collection...");
  
  // Check if collection already exists
  if (db.getCollectionNames().indexOf("reports") !== -1) {
    print("Reports collection already exists");
    return;
  }
  
  // Report schema validation
  db.createCollection("reports", {
    validator: {
      $jsonSchema: {
        bsonType: "object",
        required: ["name", "owner", "type"],
        properties: {
          _id: {
            bsonType: "objectId",
            description: "Required and must be an ObjectId"
          },
          name: {
            bsonType: "string",
            description: "Required and must be a string"
          },
          owner: {
            bsonType: "objectId",
            description: "Required and must be an ObjectId"
          },
          type: {
            bsonType: "string",
            enum: ["task-status", "project-progress", "user-performance", "time-tracking", "custom"],
            description: "Required and must be one of the allowed values"
          },
          description: {
            bsonType: "string",
            description: "Must be a string"
          },
          parameters: {
            bsonType: "object",
            properties: {
              projects: {
                bsonType: "array",
                items: {
                  bsonType: "objectId"
                },
                description: "Must be an array of ObjectIds"
              },
              users: {
                bsonType: "array",
                items: {
                  bsonType: "objectId"
                },
                description: "Must be an array of ObjectIds"
              },
              dateRange: {
                bsonType: "object",
                properties: {
                  start: {
                    bsonType: "date",
                    description: "Must be a date"
                  },
                  end: {
                    bsonType: "date",
                    description: "Must be a date"
                  }
                }
              },
              filters: {
                bsonType: "object",
                description: "Must be an object with filter criteria"
              },
              groupBy: {
                bsonType: "string",
                description: "Must be a string"
              },
              sortBy: {
                bsonType: "string",
                description: "Must be a string"
              }
            }
          },
          schedule: {
            bsonType: "object",
            properties: {
              frequency: {
                bsonType: "string",
                enum: ["daily", "weekly", "monthly", "quarterly"],
                description: "Must be one of the allowed values"
              },
              day: {
                bsonType: "int",
                description: "Must be an integer"
              },
              time: {
                bsonType: "string",
                description: "Must be a string in HH:MM format"
              },
              recipients: {
                bsonType: "array",
                items: {
                  bsonType: "string"
                },
                description: "Must be an array of email strings"
              },
              enabled: {
                bsonType: "bool",
                description: "Must be a boolean"
              },
              lastRun: {
                bsonType: "date",
                description: "Must be a date"
              },
              nextRun: {
                bsonType: "date",
                description: "Must be a date"
              }
            }
          },
          format: {
            bsonType: "string",
            enum: ["pdf", "csv", "excel", "html"],
            description: "Must be one of the allowed values"
          },
          createdAt: {
            bsonType: "date",
            description: "Must be a date"
          },
          updatedAt: {
            bsonType: "date",
            description: "Must be a date"
          }
        }
      }
    },
    validationLevel: "moderate",
    validationAction: "error"
  });
  
  print("Reports collection created with validation schema");
  
  // Create indexes
  db.reports.createIndex({ owner: 1 });
  print("Index created on reports.owner");
  
  db.reports.createIndex({ type: 1 });
  print("Index created on reports.type");
  
  db.reports.createIndex({ "schedule.nextRun": 1 });
  print("Index created on reports.schedule.nextRun");
}

/**
 * Creates the roles collection with validation schema
 * @param {Object} db - MongoDB database instance
 * @returns {Promise} Resolves when collection is created
 */
function createRolesCollection(db) {
  print("Creating roles collection...");
  
  // Check if collection already exists
  if (db.getCollectionNames().indexOf("roles") !== -1) {
    print("Roles collection already exists");
    return;
  }
  
  // Role schema validation
  db.createCollection("roles", {
    validator: {
      $jsonSchema: {
        bsonType: "object",
        required: ["name", "permissions"],
        properties: {
          _id: {
            bsonType: "objectId",
            description: "Required and must be an ObjectId"
          },
          name: {
            bsonType: "string",
            description: "Required and must be a string"
          },
          description: {
            bsonType: "string",
            description: "Must be a string"
          },
          permissions: {
            bsonType: "array",
            minItems: 1,
            items: {
              bsonType: "object",
              required: ["resource", "action"],
              properties: {
                resource: {
                  bsonType: "string",
                  description: "Required and must be a string"
                },
                action: {
                  bsonType: "string",
                  description: "Required and must be a string"
                },
                conditions: {
                  bsonType: "array",
                  items: {
                    bsonType: "object"
                  },
                  description: "Must be an array of condition objects"
                }
              }
            },
            description: "Required and must be an array of permission objects"
          },
          createdAt: {
            bsonType: "date",
            description: "Must be a date"
          },
          updatedAt: {
            bsonType: "date",
            description: "Must be a date"
          },
          isSystem: {
            bsonType: "bool",
            description: "Must be a boolean indicating if this is a system-defined role"
          }
        }
      }
    },
    validationLevel: "moderate",
    validationAction: "error"
  });
  
  print("Roles collection created with validation schema");
  
  // Create indexes
  db.roles.createIndex({ name: 1 }, { unique: true });
  print("Unique index created on roles.name");
}

/**
 * Creates the notification preferences collection with validation schema
 * @param {Object} db - MongoDB database instance
 * @returns {Promise} Resolves when collection is created
 */
function createNotificationPreferencesCollection(db) {
  print("Creating notification preferences collection...");
  
  // Check if collection already exists
  if (db.getCollectionNames().indexOf("notificationPreferences") !== -1) {
    print("Notification preferences collection already exists");
    return;
  }
  
  // Notification preferences schema validation
  db.createCollection("notificationPreferences", {
    validator: {
      $jsonSchema: {
        bsonType: "object",
        required: ["userId", "globalSettings"],
        properties: {
          _id: {
            bsonType: "objectId",
            description: "Required and must be an ObjectId"
          },
          userId: {
            bsonType: "objectId",
            description: "Required and must be an ObjectId"
          },
          globalSettings: {
            bsonType: "object",
            required: ["inApp", "email"],
            properties: {
              inApp: {
                bsonType: "bool",
                description: "Required and must be a boolean"
              },
              email: {
                bsonType: "bool",
                description: "Required and must be a boolean"
              },
              push: {
                bsonType: "bool",
                description: "Must be a boolean"
              },
              digest: {
                bsonType: "object",
                properties: {
                  enabled: {
                    bsonType: "bool",
                    description: "Must be a boolean"
                  },
                  frequency: {
                    bsonType: "string",
                    enum: ["daily", "weekly"],
                    description: "Must be one of the allowed values"
                  }
                }
              }
            }
          },
          typeSettings: {
            bsonType: "object",
            description: "Must be an object with notification type preferences"
          },
          projectSettings: {
            bsonType: "object",
            description: "Must be an object with project-specific preferences"
          },
          quietHours: {
            bsonType: "object",
            properties: {
              enabled: {
                bsonType: "bool",
                description: "Must be a boolean"
              },
              start: {
                bsonType: "string",
                description: "Must be a string in HH:MM format"
              },
              end: {
                bsonType: "string",
                description: "Must be a string in HH:MM format"
              },
              timezone: {
                bsonType: "string",
                description: "Must be a string"
              },
              excludeUrgent: {
                bsonType: "bool",
                description: "Must be a boolean"
              }
            }
          },
          updatedAt: {
            bsonType: "date",
            description: "Must be a date"
          }
        }
      }
    },
    validationLevel: "moderate",
    validationAction: "error"
  });
  
  print("Notification preferences collection created with validation schema");
  
  // Create indexes
  db.notificationPreferences.createIndex({ userId: 1 }, { unique: true });
  print("Unique index created on notificationPreferences.userId");
}

/**
 * Main function that connects to MongoDB and creates all necessary collections
 * @returns {Promise} Resolves when all collections are created
 */
function main() {
  print("Starting collection creation for Task Management System database");
  
  try {
    // Get database reference
    var db = db.getSiblingDB(DB_NAME);
    print(`Using database: ${DB_NAME}`);
    
    // Create all collections
    createUsersCollection(db);
    createTasksCollection(db);
    createProjectsCollection(db);
    createCommentsCollection(db);
    createNotificationsCollection(db);
    createFilesCollection(db);
    createDashboardsCollection(db);
    createReportsCollection(db);
    createRolesCollection(db);
    createNotificationPreferencesCollection(db);
    
    print("All collections created successfully for Task Management System");
  } catch (err) {
    print("Error creating collections: " + err.message);
    throw err;
  }
}

// Run the script directly or export for importing
if (typeof process !== 'undefined' && process.argv.length > 1) {
  main();
}

// Export main function for potential import by other scripts
if (typeof module !== 'undefined') {
  module.exports = main;
}