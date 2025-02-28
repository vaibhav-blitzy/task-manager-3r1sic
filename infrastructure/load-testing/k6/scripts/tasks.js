import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Counter, Trend } from 'k6/metrics';

// Configuration variables
const BASE_URL = process.env.API_BASE_URL || 'http://localhost:8000/api/v1';
const TASKS_ENDPOINT = `${BASE_URL}/tasks`;
const THINK_TIME_MIN = 1; // Minimum think time in seconds
const THINK_TIME_MAX = 3; // Maximum think time in seconds

// Custom metrics
const taskCreationTrend = new Trend('task_creation_time');
const taskUpdateTrend = new Trend('task_update_time');
const taskListTrend = new Trend('task_list_time');
const taskDetailTrend = new Trend('task_detail_time');
const createdTasks = new Counter('created_tasks');
const updatedTasks = new Counter('updated_tasks');

// Test configuration
export const options = {
  stages: [
    { duration: '1m', target: 10 },   // Ramp up to 10 users over 1 minute
    { duration: '3m', target: 10 },   // Stay at 10 users for 3 minutes
    { duration: '1m', target: 20 },   // Ramp up to 20 users over 1 minute
    { duration: '3m', target: 20 },   // Stay at 20 users for 3 minutes
    { duration: '1m', target: 0 },    // Ramp down to 0 users over 1 minute
  ],
  thresholds: {
    'task_creation_time': ['p95<1000'], // 95% of task creations should be under 1000ms
    'task_update_time': ['p95<1000'],   // 95% of task updates should be under 1000ms
    'task_list_time': ['p95<500'],      // 95% of task listings should be under 500ms
    'task_detail_time': ['p95<200'],    // 95% of task detail views should be under 200ms
    'http_req_duration': ['p95<1000'],  // 95% of requests should be under 1000ms
    'http_req_failed': ['rate<0.01'],   // Less than 1% of requests should fail
  },
};

// Setup function runs once before all tests
export function setup() {
  // Login to get authentication token
  const loginPayload = JSON.stringify({
    email: 'test@example.com',
    password: 'password123'
  });
  
  const loginParams = {
    headers: {
      'Content-Type': 'application/json',
    },
  };
  
  const loginResponse = http.post(`${BASE_URL}/auth/login`, loginPayload, loginParams);
  
  check(loginResponse, {
    'login successful': (r) => r.status === 200,
    'has auth token': (r) => r.json('access.token') !== '',
  });
  
  const authToken = loginResponse.json('access.token');
  const userId = loginResponse.json('user.id');
  
  // Create a test project to use in task tests
  const projectPayload = JSON.stringify({
    name: `Load Test Project ${new Date().toISOString()}`,
    description: 'Project created for load testing',
    status: 'active'
  });
  
  const projectParams = {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${authToken}`
    },
  };
  
  const projectResponse = http.post(`${BASE_URL}/projects`, projectPayload, projectParams);
  
  check(projectResponse, {
    'project creation successful': (r) => r.status === 201,
    'has project id': (r) => r.json('id') !== '',
  });
  
  const projectId = projectResponse.json('id');
  
  // Return data for test use
  return {
    authToken,
    userId,
    projectId,
    createdTaskIds: [] // Will be populated during tests
  };
}

// Generate random task data
function generateTaskData(projectId) {
  const priorities = ['low', 'medium', 'high', 'urgent'];
  const statuses = ['not_started', 'in_progress', 'in_review', 'completed'];
  
  // Set due date to 1-14 days in the future
  const dueDate = new Date();
  dueDate.setDate(dueDate.getDate() + Math.floor(Math.random() * 14) + 1);
  
  return {
    title: `Load Test Task ${Date.now()}`,
    description: 'This is a task created during load testing',
    priority: priorities[Math.floor(Math.random() * priorities.length)],
    status: statuses[Math.floor(Math.random() * statuses.length)],
    dueDate: dueDate.toISOString().split('T')[0], // Format as YYYY-MM-DD
    projectId: projectId
  };
}

// Create a new task
function createTask(authToken, projectId) {
  const taskData = generateTaskData(projectId);
  
  const params = {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${authToken}`
    },
  };
  
  const startTime = new Date();
  const response = http.post(TASKS_ENDPOINT, JSON.stringify(taskData), params);
  const endTime = new Date();
  
  taskCreationTrend.add(endTime - startTime);
  createdTasks.add(1);
  
  return response;
}

// Get tasks list with optional filters
function getTasks(authToken, params = {}) {
  const headers = {
    'Authorization': `Bearer ${authToken}`
  };
  
  // Build query string from params
  let queryString = '';
  if (Object.keys(params).length > 0) {
    queryString = '?' + Object.entries(params)
      .map(([key, value]) => `${key}=${encodeURIComponent(value)}`)
      .join('&');
  }
  
  const startTime = new Date();
  const response = http.get(`${TASKS_ENDPOINT}${queryString}`, { headers });
  const endTime = new Date();
  
  taskListTrend.add(endTime - startTime);
  
  return response;
}

// Get a specific task by ID
function getTaskById(authToken, taskId) {
  const headers = {
    'Authorization': `Bearer ${authToken}`
  };
  
  const startTime = new Date();
  const response = http.get(`${TASKS_ENDPOINT}/${taskId}`, { headers });
  const endTime = new Date();
  
  taskDetailTrend.add(endTime - startTime);
  
  return response;
}

// Update a task
function updateTask(authToken, taskId, updateData) {
  const params = {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${authToken}`
    },
  };
  
  const startTime = new Date();
  const response = http.put(`${TASKS_ENDPOINT}/${taskId}`, JSON.stringify(updateData), params);
  const endTime = new Date();
  
  taskUpdateTrend.add(endTime - startTime);
  updatedTasks.add(1);
  
  return response;
}

// Delete a task
function deleteTask(authToken, taskId) {
  const params = {
    headers: {
      'Authorization': `Bearer ${authToken}`
    },
  };
  
  return http.del(`${TASKS_ENDPOINT}/${taskId}`, null, params);
}

// Simulate user think time
function simulateThinkTime() {
  sleep(THINK_TIME_MIN + Math.random() * (THINK_TIME_MAX - THINK_TIME_MIN));
}

// Main test function
export default function(data) {
  const authToken = data.authToken;
  const userId = data.userId;
  const projectId = data.projectId;
  let createdTaskIds = data.createdTaskIds || [];
  
  // Task creation group
  group('Task Creation', () => {
    // Create 1-3 tasks
    const tasksToCreate = Math.floor(Math.random() * 3) + 1;
    
    for (let i = 0; i < tasksToCreate; i++) {
      const response = createTask(authToken, projectId);
      
      check(response, {
        'task created successfully': (r) => r.status === 201,
        'has task id': (r) => r.json('id') !== '',
      });
      
      if (response.status === 201) {
        createdTaskIds.push(response.json('id'));
        data.createdTaskIds = createdTaskIds; // Update shared data
      }
      
      simulateThinkTime();
    }
  });
  
  simulateThinkTime();
  
  // Task listing group
  group('Task Listing', () => {
    // Get all tasks
    let response = getTasks(authToken);
    check(response, {
      'get all tasks successful': (r) => r.status === 200,
      'tasks returned as array': (r) => Array.isArray(r.json()),
    });
    
    simulateThinkTime();
    
    // Get tasks by project
    response = getTasks(authToken, { projectId: projectId });
    check(response, {
      'get tasks by project successful': (r) => r.status === 200,
      'filtered tasks returned': (r) => Array.isArray(r.json()),
    });
    
    simulateThinkTime();
    
    // Get tasks by status
    response = getTasks(authToken, { status: 'in_progress' });
    check(response, {
      'get tasks by status successful': (r) => r.status === 200,
      'status filtered tasks returned': (r) => Array.isArray(r.json()),
    });
  });
  
  simulateThinkTime();
  
  // Task detail group
  group('Task Detail', () => {
    if (createdTaskIds.length > 0) {
      // Get random task from created tasks
      const randomIndex = Math.floor(Math.random() * createdTaskIds.length);
      const taskId = createdTaskIds[randomIndex];
      
      const response = getTaskById(authToken, taskId);
      
      check(response, {
        'get task detail successful': (r) => r.status === 200,
        'correct task returned': (r) => r.json('id') === taskId,
      });
    }
  });
  
  simulateThinkTime();
  
  // Task update group
  group('Task Update', () => {
    if (createdTaskIds.length > 0) {
      // Update random task from created tasks
      const randomIndex = Math.floor(Math.random() * createdTaskIds.length);
      const taskId = createdTaskIds[randomIndex];
      
      const updateData = {
        title: `Updated Task ${Date.now()}`,
        status: 'in_progress',
        priority: 'high'
      };
      
      const response = updateTask(authToken, taskId, updateData);
      
      check(response, {
        'task update successful': (r) => r.status === 200,
        'task was updated': (r) => r.json('title') === updateData.title,
      });
    }
  });
  
  simulateThinkTime();
  
  // Task deletion group (only in some iterations to avoid deleting all tasks)
  if (Math.random() < 0.3 && createdTaskIds.length > 0) {
    group('Task Deletion', () => {
      // Delete a random task from created tasks
      const randomIndex = Math.floor(Math.random() * createdTaskIds.length);
      const taskId = createdTaskIds[randomIndex];
      
      const response = deleteTask(authToken, taskId);
      
      check(response, {
        'task deletion successful': (r) => r.status === 204 || r.status === 200,
      });
      
      // Remove from tracking array
      createdTaskIds.splice(randomIndex, 1);
      data.createdTaskIds = createdTaskIds; // Update shared data
    });
  }
}