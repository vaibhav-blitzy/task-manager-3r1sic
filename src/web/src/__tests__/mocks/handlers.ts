/**
 * Mock Service Worker (MSW) handlers for API mocking during tests
 * 
 * This file defines request handlers that intercept and respond to API requests made during tests.
 * It provides consistent, predictable responses that match the expected API contract,
 * allowing frontend components to be tested in isolation without actual backend dependencies.
 * 
 * @version 1.0.0
 */

import { rest, PathParams } from 'msw';
import {
  AUTH_ENDPOINTS,
  TASK_ENDPOINTS,
  PROJECT_ENDPOINTS,
  NOTIFICATION_ENDPOINTS,
  FILE_ENDPOINTS,
  ANALYTICS_ENDPOINTS,
  USER_ENDPOINTS,
  REALTIME_ENDPOINTS
} from '../../api/endpoints';
import { Role, MfaType } from '../../types/auth';
import { TaskStatus, TaskPriority } from '../../types/task';

/**
 * Generates a mock user object with specified or default properties
 */
const generateMockUser = (overrides = {}) => {
  const defaultUser = {
    id: '1',
    email: 'john.doe@example.com',
    firstName: 'John',
    lastName: 'Doe',
    roles: [Role.USER],
    status: 'active',
    organizations: [
      {
        orgId: 'org1',
        name: 'Acme Corp',
        role: 'member',
        joinedAt: '2023-01-15T00:00:00.000Z'
      }
    ],
    settings: {
      language: 'en',
      theme: 'light',
      notifications: {
        email: true,
        push: true,
        inApp: true,
        digest: {
          enabled: true,
          frequency: 'daily'
        }
      },
      defaultView: 'tasks'
    },
    security: {
      mfaEnabled: false,
      mfaMethod: '',
      lastLogin: '2023-04-15T10:30:00.000Z',
      lastPasswordChange: '2023-03-10T08:15:00.000Z',
      emailVerified: true
    },
    createdAt: '2023-01-01T00:00:00.000Z',
    updatedAt: '2023-04-15T10:30:00.000Z'
  };

  return { ...defaultUser, ...overrides };
};

/**
 * Generates a mock task object with specified or default properties
 */
const generateMockTask = (overrides = {}) => {
  const now = new Date();
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  
  const creator = generateMockUser();
  const assignee = generateMockUser({
    id: '2',
    email: 'jane.smith@example.com',
    firstName: 'Jane',
    lastName: 'Smith'
  });

  const defaultTask = {
    id: '101',
    title: 'Complete project documentation',
    description: 'Write comprehensive documentation for the new feature including API specs and usage examples.',
    status: TaskStatus.IN_PROGRESS,
    priority: TaskPriority.MEDIUM,
    dueDate: tomorrow.toISOString(),
    createdBy: creator,
    assignee: assignee,
    project: {
      id: '201',
      name: 'Website Redesign',
      description: 'Redesign company website for better user experience',
      status: 'active'
    },
    tags: ['documentation', 'api'],
    attachments: [],
    subtasks: [
      {
        id: '1001',
        title: 'Create API documentation',
        completed: true,
        assigneeId: '1'
      },
      {
        id: '1002',
        title: 'Write usage examples',
        completed: false,
        assigneeId: '2'
      }
    ],
    dependencies: [],
    comments: [],
    activity: [
      {
        type: 'status-change',
        user: creator,
        timestamp: now.toISOString(),
        details: {
          oldStatus: TaskStatus.CREATED,
          newStatus: TaskStatus.IN_PROGRESS
        }
      }
    ],
    metadata: {
      created: new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000).toISOString(), // 7 days ago
      lastUpdated: now.toISOString(),
      completedAt: null,
      timeEstimate: 120, // 2 hours
      timeSpent: 45 // 45 minutes
    }
  };

  return { ...defaultTask, ...overrides };
};

/**
 * Generates a mock project object with specified or default properties
 */
const generateMockProject = (overrides = {}) => {
  const owner = generateMockUser();
  const member = generateMockUser({
    id: '2',
    email: 'jane.smith@example.com',
    firstName: 'Jane',
    lastName: 'Smith'
  });

  const defaultProject = {
    id: '201',
    name: 'Website Redesign',
    description: 'Redesign company website for better user experience and modern look',
    status: 'active',
    category: 'development',
    owner: owner,
    ownerId: owner.id,
    members: [
      {
        userId: owner.id,
        user: owner,
        role: 'admin',
        joinedAt: '2023-01-01T00:00:00.000Z',
        isActive: true
      },
      {
        userId: member.id,
        user: member,
        role: 'member',
        joinedAt: '2023-01-05T00:00:00.000Z',
        isActive: true
      }
    ],
    settings: {
      workflow: {
        enableReview: true,
        allowSubtasks: true,
        defaultTaskStatus: 'created'
      },
      permissions: {
        memberInvite: 'admin',
        taskCreate: 'member',
        commentCreate: 'member'
      },
      notifications: {
        taskCreate: true,
        taskComplete: true,
        commentAdd: true
      }
    },
    taskLists: [
      {
        id: '301',
        name: 'Backlog',
        description: 'Tasks to be prioritized',
        sortOrder: 0,
        createdAt: '2023-01-01T00:00:00.000Z'
      },
      {
        id: '302',
        name: 'In Progress',
        description: 'Tasks currently being worked on',
        sortOrder: 1,
        createdAt: '2023-01-01T00:00:00.000Z'
      }
    ],
    metadata: {
      created: '2023-01-01T00:00:00.000Z',
      lastUpdated: '2023-04-15T10:30:00.000Z',
      completedAt: null,
      taskCount: 15,
      completedTaskCount: 8
    },
    tags: ['website', 'design', 'development'],
    customFields: [
      {
        id: '401',
        name: 'Client Approval',
        type: 'select',
        options: ['Pending', 'Approved', 'Rejected']
      }
    ]
  };

  return { ...defaultProject, ...overrides };
};

/**
 * Generates a mock authentication response with user and token information
 */
const generateAuthResponse = (userOverrides = {}, mfaRequired = false) => {
  const user = generateMockUser(userOverrides);
  
  return {
    user,
    tokens: {
      accessToken: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNjE2MjM5MDIyfQ.XbPfbIHMI6arZ3Y922BhjWgQzWXcXNrz0ogtVhfEd2o',
      refreshToken: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiaWF0IjoxNjE2MjM5MDIyLCJ0eXBlIjoicmVmcmVzaCJ9.13VC6fdPPuLA8g1MZhEGHJDhVKYAIVXDtFEYA0xkPnM',
      expiresAt: new Date(Date.now() + 15 * 60 * 1000).getTime() // 15 minutes from now
    },
    mfaRequired
  };
};

/**
 * Generates a paginated response with the provided items
 */
const generatePaginatedResponse = (items, page = 1, pageSize = 20, total = null) => {
  const totalItems = total !== null ? total : items.length;
  const totalPages = Math.ceil(totalItems / pageSize);
  
  return {
    items,
    pagination: {
      page,
      pageSize,
      total: totalItems,
      totalPages
    }
  };
};

// Authentication Handlers
const authHandlers = [
  // Login handler
  rest.post(AUTH_ENDPOINTS.LOGIN, (req, res, ctx) => {
    const { email, password } = req.body as { email: string, password: string };
    
    // Simulate authentication failure for specific credentials
    if (email === 'invalid@example.com' || password === 'wrongpassword') {
      return res(
        ctx.status(401),
        ctx.json({
          error: 'InvalidCredentials',
          message: 'The email or password you entered is incorrect.'
        })
      );
    }
    
    // Simulate MFA requirement for specific email
    if (email === 'mfa@example.com') {
      return res(
        ctx.status(200),
        ctx.json({
          mfaRequired: true,
          user: {
            id: '3',
            email: 'mfa@example.com',
            firstName: 'MFA',
            lastName: 'User',
          },
          methods: [MfaType.APP, MfaType.EMAIL]
        })
      );
    }
    
    // Default success response
    return res(
      ctx.status(200),
      ctx.json(generateAuthResponse())
    );
  }),
  
  // Registration handler
  rest.post(AUTH_ENDPOINTS.REGISTER, (req, res, ctx) => {
    const { email } = req.body as { email: string };
    
    // Simulate registration failure for existing email
    if (email === 'existing@example.com') {
      return res(
        ctx.status(400),
        ctx.json({
          error: 'ValidationError',
          message: 'A user with this email already exists.'
        })
      );
    }
    
    // Default success response
    return res(
      ctx.status(201),
      ctx.json(generateAuthResponse({
        email: email,
        createdAt: new Date().toISOString()
      }))
    );
  }),
  
  // Refresh token handler
  rest.post(AUTH_ENDPOINTS.REFRESH_TOKEN, (req, res, ctx) => {
    const { refreshToken } = req.body as { refreshToken: string };
    
    // Simulate expired or invalid refresh token
    if (refreshToken === 'expired' || refreshToken === 'invalid') {
      return res(
        ctx.status(401),
        ctx.json({
          error: 'InvalidToken',
          message: 'The refresh token is invalid or expired.'
        })
      );
    }
    
    // Default success response with new tokens
    return res(
      ctx.status(200),
      ctx.json({
        accessToken: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNjE2MjM5MDIyfQ.NEW_TOKEN',
        refreshToken: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiaWF0IjoxNjE2MjM5MDIyLCJ0eXBlIjoicmVmcmVzaCJ9.NEW_REFRESH',
        expiresAt: new Date(Date.now() + 15 * 60 * 1000).getTime() // 15 minutes from now
      })
    );
  }),
  
  // Logout handler
  rest.post(AUTH_ENDPOINTS.LOGOUT, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        success: true,
        message: 'Successfully logged out'
      })
    );
  }),
  
  // MFA verification handler
  rest.post(AUTH_ENDPOINTS.VERIFY_MFA, (req, res, ctx) => {
    const { code } = req.body as { code: string };
    
    // Simulate invalid MFA code
    if (code === '000000' || code === '999999') {
      return res(
        ctx.status(401),
        ctx.json({
          error: 'InvalidCode',
          message: 'The verification code is invalid or expired.'
        })
      );
    }
    
    // Default success response
    return res(
      ctx.status(200),
      ctx.json(generateAuthResponse({
        security: {
          mfaEnabled: true,
          mfaMethod: MfaType.APP,
          lastLogin: new Date().toISOString(),
          lastPasswordChange: '2023-03-10T08:15:00.000Z',
          emailVerified: true
        }
      }))
    );
  }),
  
  // Auth status check handler
  rest.get(AUTH_ENDPOINTS.STATUS, (req, res, ctx) => {
    // Check for auth header
    const authHeader = req.headers.get('Authorization');
    
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return res(
        ctx.status(401),
        ctx.json({
          error: 'Unauthorized',
          message: 'Authentication required'
        })
      );
    }
    
    // Default success response
    return res(
      ctx.status(200),
      ctx.json({
        isAuthenticated: true,
        user: generateMockUser()
      })
    );
  })
];

// Task Handlers
const taskHandlers = [
  // Get tasks (with pagination)
  rest.get(TASK_ENDPOINTS.BASE, (req, res, ctx) => {
    // Get query parameters for filtering and pagination
    const page = parseInt(req.url.searchParams.get('page') || '1');
    const pageSize = parseInt(req.url.searchParams.get('pageSize') || '20');
    const status = req.url.searchParams.get('status');
    const priority = req.url.searchParams.get('priority');
    const assigneeId = req.url.searchParams.get('assigneeId');
    const projectId = req.url.searchParams.get('projectId');
    
    // Generate mock tasks
    const tasks = Array(pageSize).fill(null).map((_, index) => {
      const id = (100 + index).toString();
      return generateMockTask({ 
        id,
        // Apply filters if provided
        ...(status && { status }),
        ...(priority && { priority }),
        ...(assigneeId && { assignee: generateMockUser({ id: assigneeId }) }),
        ...(projectId && { project: { ...generateMockProject({ id: projectId }), id: projectId } })
      });
    });
    
    return res(
      ctx.status(200),
      ctx.json(generatePaginatedResponse(tasks, page, pageSize, 100))
    );
  }),
  
  // Get single task
  rest.get(TASK_ENDPOINTS.GET_TASK(':id'), (req, res, ctx) => {
    const { id } = req.params as PathParams;
    
    // Simulate task not found
    if (id === '999') {
      return res(
        ctx.status(404),
        ctx.json({
          error: 'NotFound',
          message: 'Task not found'
        })
      );
    }
    
    return res(
      ctx.status(200),
      ctx.json(generateMockTask({ id }))
    );
  }),
  
  // Create task
  rest.post(TASK_ENDPOINTS.BASE, (req, res, ctx) => {
    const taskData = req.body as any;
    
    return res(
      ctx.status(201),
      ctx.json(generateMockTask({
        ...taskData,
        id: Math.floor(Math.random() * 1000).toString(),
        metadata: {
          ...generateMockTask().metadata,
          created: new Date().toISOString(),
          lastUpdated: new Date().toISOString()
        }
      }))
    );
  }),
  
  // Update task
  rest.put(TASK_ENDPOINTS.UPDATE_TASK(':id'), (req, res, ctx) => {
    const { id } = req.params as PathParams;
    const taskData = req.body as any;
    
    // Simulate task not found
    if (id === '999') {
      return res(
        ctx.status(404),
        ctx.json({
          error: 'NotFound',
          message: 'Task not found'
        })
      );
    }
    
    return res(
      ctx.status(200),
      ctx.json(generateMockTask({
        ...taskData,
        id,
        metadata: {
          ...generateMockTask().metadata,
          lastUpdated: new Date().toISOString()
        }
      }))
    );
  }),
  
  // Delete task
  rest.delete(TASK_ENDPOINTS.DELETE_TASK(':id'), (req, res, ctx) => {
    const { id } = req.params as PathParams;
    
    // Simulate task not found
    if (id === '999') {
      return res(
        ctx.status(404),
        ctx.json({
          error: 'NotFound',
          message: 'Task not found'
        })
      );
    }
    
    return res(
      ctx.status(200),
      ctx.json({
        success: true,
        message: 'Task deleted successfully'
      })
    );
  }),
  
  // Update task status
  rest.patch(TASK_ENDPOINTS.UPDATE_STATUS(':id'), (req, res, ctx) => {
    const { id } = req.params as PathParams;
    const { status } = req.body as { status: TaskStatus };
    
    // Simulate task not found
    if (id === '999') {
      return res(
        ctx.status(404),
        ctx.json({
          error: 'NotFound',
          message: 'Task not found'
        })
      );
    }
    
    return res(
      ctx.status(200),
      ctx.json(generateMockTask({
        id,
        status,
        metadata: {
          ...generateMockTask().metadata,
          lastUpdated: new Date().toISOString(),
          ...((status === TaskStatus.COMPLETED) && { completedAt: new Date().toISOString() })
        }
      }))
    );
  }),
  
  // Assign task
  rest.patch(TASK_ENDPOINTS.ASSIGN_TASK(':id'), (req, res, ctx) => {
    const { id } = req.params as PathParams;
    const { assigneeId } = req.body as { assigneeId: string | null };
    
    // Simulate task not found
    if (id === '999') {
      return res(
        ctx.status(404),
        ctx.json({
          error: 'NotFound',
          message: 'Task not found'
        })
      );
    }
    
    // Handle unassignment
    if (assigneeId === null) {
      return res(
        ctx.status(200),
        ctx.json(generateMockTask({
          id,
          assignee: null,
          metadata: {
            ...generateMockTask().metadata,
            lastUpdated: new Date().toISOString()
          }
        }))
      );
    }
    
    // Handle assignment
    return res(
      ctx.status(200),
      ctx.json(generateMockTask({
        id,
        assignee: generateMockUser({ id: assigneeId }),
        metadata: {
          ...generateMockTask().metadata,
          lastUpdated: new Date().toISOString()
        }
      }))
    );
  }),
  
  // Get task comments
  rest.get(TASK_ENDPOINTS.COMMENTS(':id'), (req, res, ctx) => {
    const { id } = req.params as PathParams;
    
    // Simulate task not found
    if (id === '999') {
      return res(
        ctx.status(404),
        ctx.json({
          error: 'NotFound',
          message: 'Task not found'
        })
      );
    }
    
    const comments = [
      {
        id: '1',
        content: 'This is a sample comment on the task.',
        createdBy: generateMockUser(),
        createdAt: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(), // 1 day ago
        updatedAt: null
      },
      {
        id: '2',
        content: 'Here is another comment with an update.',
        createdBy: generateMockUser({
          id: '2',
          firstName: 'Jane',
          lastName: 'Smith'
        }),
        createdAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(), // 2 hours ago
        updatedAt: null
      }
    ];
    
    return res(
      ctx.status(200),
      ctx.json(comments)
    );
  }),
  
  // Add comment to task
  rest.post(TASK_ENDPOINTS.COMMENTS(':id'), (req, res, ctx) => {
    const { id } = req.params as PathParams;
    const { content } = req.body as { content: string };
    
    // Simulate task not found
    if (id === '999') {
      return res(
        ctx.status(404),
        ctx.json({
          error: 'NotFound',
          message: 'Task not found'
        })
      );
    }
    
    const newComment = {
      id: Math.floor(Math.random() * 1000).toString(),
      content,
      createdBy: generateMockUser(),
      createdAt: new Date().toISOString(),
      updatedAt: null
    };
    
    return res(
      ctx.status(201),
      ctx.json(newComment)
    );
  }),
  
  // Get task subtasks
  rest.get(TASK_ENDPOINTS.SUBTASKS(':id'), (req, res, ctx) => {
    const { id } = req.params as PathParams;
    
    // Simulate task not found
    if (id === '999') {
      return res(
        ctx.status(404),
        ctx.json({
          error: 'NotFound',
          message: 'Task not found'
        })
      );
    }
    
    const subtasks = [
      {
        id: '1001',
        title: 'Research existing dashboard patterns',
        completed: true,
        assigneeId: '1'
      },
      {
        id: '1002',
        title: 'Create initial sketches',
        completed: false,
        assigneeId: '1'
      },
      {
        id: '1003',
        title: 'Get feedback from team',
        completed: false,
        assigneeId: '2'
      }
    ];
    
    return res(
      ctx.status(200),
      ctx.json(subtasks)
    );
  })
];

// Project Handlers
const projectHandlers = [
  // Get projects (with pagination)
  rest.get(PROJECT_ENDPOINTS.BASE, (req, res, ctx) => {
    // Get query parameters for filtering and pagination
    const page = parseInt(req.url.searchParams.get('page') || '1');
    const pageSize = parseInt(req.url.searchParams.get('pageSize') || '20');
    const status = req.url.searchParams.get('status');
    const category = req.url.searchParams.get('category');
    
    // Generate mock projects
    const projects = Array(Math.min(pageSize, 5)).fill(null).map((_, index) => {
      const id = (200 + index).toString();
      return generateMockProject({ 
        id,
        // Apply filters if provided
        ...(status && { status }),
        ...(category && { category })
      });
    });
    
    return res(
      ctx.status(200),
      ctx.json(generatePaginatedResponse(projects, page, pageSize, 15))
    );
  }),
  
  // Get single project
  rest.get(PROJECT_ENDPOINTS.GET_PROJECT(':id'), (req, res, ctx) => {
    const { id } = req.params as PathParams;
    
    // Simulate project not found
    if (id === '999') {
      return res(
        ctx.status(404),
        ctx.json({
          error: 'NotFound',
          message: 'Project not found'
        })
      );
    }
    
    return res(
      ctx.status(200),
      ctx.json(generateMockProject({ id }))
    );
  }),
  
  // Create project
  rest.post(PROJECT_ENDPOINTS.BASE, (req, res, ctx) => {
    const projectData = req.body as any;
    
    return res(
      ctx.status(201),
      ctx.json(generateMockProject({
        ...projectData,
        id: Math.floor(Math.random() * 1000).toString(),
        metadata: {
          ...generateMockProject().metadata,
          created: new Date().toISOString(),
          lastUpdated: new Date().toISOString()
        }
      }))
    );
  }),
  
  // Update project
  rest.put(PROJECT_ENDPOINTS.UPDATE_PROJECT(':id'), (req, res, ctx) => {
    const { id } = req.params as PathParams;
    const projectData = req.body as any;
    
    // Simulate project not found
    if (id === '999') {
      return res(
        ctx.status(404),
        ctx.json({
          error: 'NotFound',
          message: 'Project not found'
        })
      );
    }
    
    return res(
      ctx.status(200),
      ctx.json(generateMockProject({
        ...projectData,
        id,
        metadata: {
          ...generateMockProject().metadata,
          lastUpdated: new Date().toISOString()
        }
      }))
    );
  }),
  
  // Delete project
  rest.delete(PROJECT_ENDPOINTS.DELETE_PROJECT(':id'), (req, res, ctx) => {
    const { id } = req.params as PathParams;
    
    // Simulate project not found
    if (id === '999') {
      return res(
        ctx.status(404),
        ctx.json({
          error: 'NotFound',
          message: 'Project not found'
        })
      );
    }
    
    return res(
      ctx.status(200),
      ctx.json({
        success: true,
        message: 'Project deleted successfully'
      })
    );
  }),
  
  // Get project members
  rest.get(PROJECT_ENDPOINTS.MEMBERS(':id'), (req, res, ctx) => {
    const { id } = req.params as PathParams;
    
    // Simulate project not found
    if (id === '999') {
      return res(
        ctx.status(404),
        ctx.json({
          error: 'NotFound',
          message: 'Project not found'
        })
      );
    }
    
    const owner = generateMockUser();
    const members = [
      {
        userId: owner.id,
        user: owner,
        role: 'admin',
        joinedAt: '2023-01-01T00:00:00.000Z',
        isActive: true
      },
      {
        userId: '2',
        user: generateMockUser({
          id: '2',
          email: 'jane.smith@example.com',
          firstName: 'Jane',
          lastName: 'Smith'
        }),
        role: 'member',
        joinedAt: '2023-01-05T00:00:00.000Z',
        isActive: true
      },
      {
        userId: '3',
        user: generateMockUser({
          id: '3',
          email: 'bob.johnson@example.com',
          firstName: 'Bob',
          lastName: 'Johnson'
        }),
        role: 'viewer',
        joinedAt: '2023-02-10T00:00:00.000Z',
        isActive: true
      }
    ];
    
    return res(
      ctx.status(200),
      ctx.json(members)
    );
  })
];

// Notification Handlers
const notificationHandlers = [
  // Get notifications
  rest.get(NOTIFICATION_ENDPOINTS.BASE, (req, res, ctx) => {
    // Get query parameters for filtering and pagination
    const page = parseInt(req.url.searchParams.get('page') || '1');
    const pageSize = parseInt(req.url.searchParams.get('pageSize') || '20');
    const read = req.url.searchParams.get('read');
    
    // Generate mock notifications
    const notifications = Array(Math.min(pageSize, 10)).fill(null).map((_, index) => {
      const id = (300 + index).toString();
      const createdAt = new Date(Date.now() - index * 3600 * 1000); // Staggered times
      
      return {
        id,
        recipient: generateMockUser().id,
        type: index % 3 === 0 ? 'task-assigned' : index % 3 === 1 ? 'comment-added' : 'due-soon',
        title: index % 3 === 0 
          ? 'Task assigned to you' 
          : index % 3 === 1 
            ? 'New comment on your task' 
            : 'Task due soon',
        content: index % 3 === 0 
          ? 'You have been assigned to "Complete project documentation"' 
          : index % 3 === 1 
            ? 'John Doe commented on "Website redesign"' 
            : '"API Integration" is due in 2 days',
        priority: index % 4 === 0 ? 'high' : 'normal',
        read: read === 'true' ? true : index > 3,
        actionUrl: `/tasks/${100 + index}`,
        metadata: {
          created: createdAt.toISOString(),
          readAt: index > 3 ? new Date(createdAt.getTime() + 1800 * 1000).toISOString() : null,
          deliveryStatus: {
            inApp: 'delivered',
            email: index < 5 ? 'delivered' : 'disabled',
            push: 'disabled'
          },
          sourceEvent: {
            type: index % 3 === 0 ? 'task.assigned' : index % 3 === 1 ? 'task.comment.added' : 'task.due_soon',
            objectId: (100 + index).toString(),
            objectType: 'task'
          }
        }
      };
    });
    
    return res(
      ctx.status(200),
      ctx.json(generatePaginatedResponse(notifications, page, pageSize, 25))
    );
  }),
  
  // Mark notification as read
  rest.patch(NOTIFICATION_ENDPOINTS.MARK_READ(':id'), (req, res, ctx) => {
    const { id } = req.params as PathParams;
    
    // Simulate notification not found
    if (id === '999') {
      return res(
        ctx.status(404),
        ctx.json({
          error: 'NotFound',
          message: 'Notification not found'
        })
      );
    }
    
    return res(
      ctx.status(200),
      ctx.json({
        id,
        read: true,
        metadata: {
          readAt: new Date().toISOString()
        }
      })
    );
  }),
  
  // Get unread notification count
  rest.get(NOTIFICATION_ENDPOINTS.UNREAD_COUNT, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        count: 5,
        byType: {
          'task-assigned': 2,
          'comment-added': 1,
          'due-soon': 2
        }
      })
    );
  })
];

// File Handlers
const fileHandlers = [
  // Request file upload URL
  rest.post(FILE_ENDPOINTS.UPLOAD, (req, res, ctx) => {
    const { name, size, type } = req.body as { name: string, size: number, type: string };
    
    // Simulate file size limit exceeded
    if (size > 25 * 1024 * 1024) { // 25MB
      return res(
        ctx.status(400),
        ctx.json({
          error: 'FileTooLarge',
          message: 'File exceeds the maximum allowed size of 25MB'
        })
      );
    }
    
    // Simulate unsupported file type
    const supportedTypes = [
      'image/jpeg', 'image/png', 'image/gif', 'application/pdf', 
      'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'text/plain', 'text/csv'
    ];
    
    if (!supportedTypes.includes(type)) {
      return res(
        ctx.status(400),
        ctx.json({
          error: 'UnsupportedFileType',
          message: 'This file type is not supported'
        })
      );
    }
    
    const fileId = Math.floor(Math.random() * 1000).toString();
    
    return res(
      ctx.status(200),
      ctx.json({
        uploadUrl: `https://mock-upload-url.example.com/${fileId}`,
        fileId,
        expiresAt: new Date(Date.now() + 15 * 60 * 1000).toISOString() // 15 minutes from now
      })
    );
  }),
  
  // Get file metadata
  rest.get(FILE_ENDPOINTS.GET_FILE(':id'), (req, res, ctx) => {
    const { id } = req.params as PathParams;
    
    // Simulate file not found
    if (id === '999') {
      return res(
        ctx.status(404),
        ctx.json({
          error: 'NotFound',
          message: 'File not found'
        })
      );
    }
    
    return res(
      ctx.status(200),
      ctx.json({
        id,
        name: 'document.pdf',
        size: 1024 * 1024 * 2, // 2MB
        type: 'application/pdf',
        extension: 'pdf',
        storageKey: `files/${id}/document.pdf`,
        url: `https://mock-file-url.example.com/${id}`,
        preview: {
          thumbnail: `https://mock-thumbnail-url.example.com/${id}`,
          previewAvailable: true,
          previewType: 'pdf'
        },
        metadata: {
          uploadedBy: '1',
          uploadedAt: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(), // 1 day ago
          lastAccessed: new Date().toISOString(),
          accessCount: 5,
          md5Hash: 'a1b2c3d4e5f6g7h8i9j0'
        },
        security: {
          accessLevel: 'shared',
          encryptionType: 'AES-256',
          scanStatus: 'clean'
        },
        associations: {
          taskId: '101',
          projectId: null,
          commentId: null
        },
        versions: [
          {
            id: 'v1',
            storageKey: `files/${id}/versions/v1/document.pdf`,
            size: 1024 * 1024 * 1.8, // 1.8MB
            uploadedBy: '1',
            uploadedAt: new Date(Date.now() - 48 * 60 * 60 * 1000).toISOString(), // 2 days ago
            changeNotes: 'Initial version'
          },
          {
            id: 'v2',
            storageKey: `files/${id}/versions/v2/document.pdf`,
            size: 1024 * 1024 * 2, // 2MB
            uploadedBy: '1',
            uploadedAt: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(), // 1 day ago
            changeNotes: 'Updated with feedback'
          }
        ]
      })
    );
  }),
  
  // Get file download URL
  rest.get(FILE_ENDPOINTS.DOWNLOAD(':id'), (req, res, ctx) => {
    const { id } = req.params as PathParams;
    
    // Simulate file not found
    if (id === '999') {
      return res(
        ctx.status(404),
        ctx.json({
          error: 'NotFound',
          message: 'File not found'
        })
      );
    }
    
    return res(
      ctx.status(200),
      ctx.json({
        downloadUrl: `https://mock-download-url.example.com/${id}`,
        expiresAt: new Date(Date.now() + 15 * 60 * 1000).toISOString() // 15 minutes from now
      })
    );
  })
];

// Analytics Handlers
const analyticsHandlers = [
  // Get analytics metrics
  rest.get(ANALYTICS_ENDPOINTS.METRICS, (req, res, ctx) => {
    const metricType = req.url.searchParams.get('metric') || 'taskCompletion';
    const period = req.url.searchParams.get('period') || 'week';
    const projectId = req.url.searchParams.get('projectId');
    
    let data;
    
    // Different mock data based on metric type
    switch (metricType) {
      case 'taskCompletion':
        data = {
          labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
          datasets: [
            {
              label: 'Completed Tasks',
              data: [3, 7, 4, 8, 5, 2, 1]
            }
          ],
          total: 30
        };
        break;
      case 'tasksByStatus':
        data = {
          labels: ['Not Started', 'In Progress', 'On Hold', 'In Review', 'Completed'],
          datasets: [
            {
              label: 'Tasks',
              data: [12, 8, 3, 4, 15]
            }
          ],
          total: 42
        };
        break;
      case 'tasksByAssignee':
        data = {
          labels: ['John Doe', 'Jane Smith', 'Bob Johnson', 'Unassigned'],
          datasets: [
            {
              label: 'Tasks',
              data: [15, 12, 8, 5]
            }
          ],
          total: 40
        };
        break;
      default:
        data = {
          labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
          datasets: [
            {
              label: 'Activity',
              data: [10, 15, 8, 12, 18, 5, 7]
            }
          ],
          total: 75
        };
    }
    
    return res(
      ctx.status(200),
      ctx.json({
        type: metricType,
        period,
        projectId: projectId || null,
        timestamp: new Date().toISOString(),
        data
      })
    );
  }),
  
  // Get dashboard configurations
  rest.get(ANALYTICS_ENDPOINTS.DASHBOARDS, (req, res, ctx) => {
    const dashboards = [
      {
        id: '501',
        name: 'Project Overview',
        owner: generateMockUser(),
        type: 'project',
        scope: {
          projects: ['201'],
          users: [],
          dateRange: {
            preset: 'month'
          }
        },
        layout: {
          columns: 2,
          widgets: [
            {
              id: 'w1',
              type: 'task-status',
              position: { x: 0, y: 0, width: 1, height: 1 },
              config: {
                title: 'Task Status',
                dataSource: 'tasksByStatus',
                refreshInterval: 300,
                visualizationType: 'pie',
                drilldownEnabled: true
              }
            },
            {
              id: 'w2',
              type: 'task-completion',
              position: { x: 1, y: 0, width: 1, height: 1 },
              config: {
                title: 'Task Completion',
                dataSource: 'taskCompletion',
                refreshInterval: 300,
                visualizationType: 'line',
                drilldownEnabled: false
              }
            }
          ]
        },
        sharing: {
          public: false,
          sharedWith: ['2', '3']
        },
        metadata: {
          created: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
          lastUpdated: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
          lastViewed: new Date().toISOString()
        }
      },
      {
        id: '502',
        name: 'Personal Dashboard',
        owner: generateMockUser(),
        type: 'personal',
        scope: {
          projects: [],
          users: ['1'],
          dateRange: {
            preset: 'week'
          }
        },
        layout: {
          columns: 2,
          widgets: [
            {
              id: 'w1',
              type: 'upcoming-tasks',
              position: { x: 0, y: 0, width: 1, height: 1 },
              config: {
                title: 'Upcoming Tasks',
                dataSource: 'myTasks',
                refreshInterval: 300,
                visualizationType: 'list',
                drilldownEnabled: true
              }
            },
            {
              id: 'w2',
              type: 'productivity',
              position: { x: 1, y: 0, width: 1, height: 1 },
              config: {
                title: 'My Productivity',
                dataSource: 'productivity',
                refreshInterval: 300,
                visualizationType: 'bar',
                drilldownEnabled: false
              }
            }
          ]
        },
        sharing: {
          public: false,
          sharedWith: []
        },
        metadata: {
          created: new Date(Date.now() - 60 * 24 * 60 * 60 * 1000).toISOString(),
          lastUpdated: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
          lastViewed: new Date().toISOString()
        }
      }
    ];
    
    return res(
      ctx.status(200),
      ctx.json(dashboards)
    );
  })
];

// User Handlers
const userHandlers = [
  // Get user profile
  rest.get(USER_ENDPOINTS.PROFILE, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json(generateMockUser())
    );
  }),
  
  // Update user profile
  rest.patch(USER_ENDPOINTS.UPDATE_PROFILE, (req, res, ctx) => {
    const profileData = req.body as any;
    
    return res(
      ctx.status(200),
      ctx.json(generateMockUser({
        ...profileData,
        updatedAt: new Date().toISOString()
      }))
    );
  }),
  
  // Search users
  rest.get(USER_ENDPOINTS.SEARCH, (req, res, ctx) => {
    const query = req.url.searchParams.get('q') || '';
    
    // Always return a fixed set of users for testing purposes
    const users = [
      generateMockUser(),
      generateMockUser({
        id: '2',
        email: 'jane.smith@example.com',
        firstName: 'Jane',
        lastName: 'Smith'
      }),
      generateMockUser({
        id: '3',
        email: 'bob.johnson@example.com',
        firstName: 'Bob',
        lastName: 'Johnson'
      })
    ];
    
    // Filter users if query is provided
    const filteredUsers = query ? 
      users.filter(user => 
        user.firstName.toLowerCase().includes(query.toLowerCase()) || 
        user.lastName.toLowerCase().includes(query.toLowerCase()) ||
        user.email.toLowerCase().includes(query.toLowerCase())
      ) : 
      users;
    
    return res(
      ctx.status(200),
      ctx.json(filteredUsers)
    );
  })
];

// Combine all handlers
const handlers = [
  ...authHandlers,
  ...taskHandlers,
  ...projectHandlers,
  ...notificationHandlers,
  ...fileHandlers,
  ...analyticsHandlers,
  ...userHandlers
];

export default handlers;