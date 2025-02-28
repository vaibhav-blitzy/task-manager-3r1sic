import http from 'k6/http';
import { check, sleep, group } from 'k6';
import * as exec from 'k6/execution';
import { SharedArray } from 'k6/data';
import crypto from 'k6/crypto';

// API endpoints
const API_BASE_URL = 'http://localhost:5000/api/v1';
const AUTH_ENDPOINT = `${API_BASE_URL}/auth/login`;
const PROJECTS_ENDPOINT = `${API_BASE_URL}/projects`;

// Test users (shared between VUs)
const testUsers = new SharedArray('users', function() {
  return [
    { email: 'admin@example.com', password: 'securePassword123!' },
    { email: 'manager@example.com', password: 'securePassword123!' },
    { email: 'user@example.com', password: 'securePassword123!' }
  ];
});

// Load test configuration
export const options = {
  stages: [
    { duration: '30s', target: 50 },  // Ramp up to 50 users over 30 seconds
    { duration: '1m', target: 200 },  // Ramp up to 200 users over 1 minute
    { duration: '2m', target: 500 },  // Ramp up to 500 users over 2 minutes
    { duration: '5m', target: 500 },  // Stay at 500 users for 5 minutes
    { duration: '1m', target: 0 }     // Ramp down to 0 users over 1 minute
  ],
  thresholds: {
    // 95% of requests must complete below 1s
    'http_req_duration': ['p(95)<1000'],
    // 99% of requests must complete below 3s
    'http_req_duration{name:project-list}': ['p(99)<3000'],
    'http_req_duration{name:project-create}': ['p(99)<3000'],
    'http_req_duration{name:project-detail}': ['p(99)<3000'],
    'http_req_duration{name:project-update}': ['p(99)<3000'],
    // Success rate should be at least 95%
    'http_req_failed': ['rate<0.05']
  }
};

/**
 * Authenticates a user and returns the access token
 * @param {Object} credentials - User credentials with email and password
 * @returns {string} JWT access token
 */
function login(credentials) {
  const payload = JSON.stringify(credentials);
  const params = {
    headers: {
      'Content-Type': 'application/json'
    }
  };
  
  const response = http.post(AUTH_ENDPOINT, payload, params);
  
  const success = check(response, {
    'login status is 200': (r) => r.status === 200,
    'has access token': (r) => r.json('access.token') !== undefined
  });
  
  if (!success) {
    console.error(`Login failed: ${response.body}`);
    return null;
  }
  
  return response.json('access.token');
}

/**
 * Creates a new project with the given details
 * @param {string} token - Authentication token
 * @param {Object} projectData - Project details
 * @returns {Object} Project creation response with project ID
 */
function createProject(token, projectData) {
  const payload = JSON.stringify(projectData);
  const params = {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    tags: {
      name: 'project-create'
    }
  };
  
  return http.post(PROJECTS_ENDPOINT, payload, params);
}

/**
 * Retrieves a list of projects for the authenticated user
 * @param {string} token - Authentication token
 * @returns {Object} Response containing list of projects
 */
function getProjects(token) {
  const params = {
    headers: {
      'Authorization': `Bearer ${token}`
    },
    tags: {
      name: 'project-list'
    }
  };
  
  return http.get(PROJECTS_ENDPOINT, params);
}

/**
 * Retrieves a specific project by its ID
 * @param {string} token - Authentication token
 * @param {string} projectId - ID of the project to retrieve
 * @returns {Object} Response containing project details
 */
function getProjectById(token, projectId) {
  const params = {
    headers: {
      'Authorization': `Bearer ${token}`
    },
    tags: {
      name: 'project-detail'
    }
  };
  
  return http.get(`${PROJECTS_ENDPOINT}/${projectId}`, params);
}

/**
 * Updates an existing project with new data
 * @param {string} token - Authentication token
 * @param {string} projectId - ID of the project to update
 * @param {Object} updateData - New project data
 * @returns {Object} Response containing updated project details
 */
function updateProject(token, projectId, updateData) {
  const payload = JSON.stringify(updateData);
  const params = {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    tags: {
      name: 'project-update'
    }
  };
  
  return http.put(`${PROJECTS_ENDPOINT}/${projectId}`, payload, params);
}

/**
 * Deletes a project by its ID
 * @param {string} token - Authentication token
 * @param {string} projectId - ID of the project to delete
 * @returns {Object} Response confirming deletion
 */
function deleteProject(token, projectId) {
  const params = {
    headers: {
      'Authorization': `Bearer ${token}`
    },
    tags: {
      name: 'project-delete'
    }
  };
  
  return http.del(`${PROJECTS_ENDPOINT}/${projectId}`, null, params);
}

/**
 * Adds a member to a project
 * @param {string} token - Authentication token
 * @param {string} projectId - ID of the project
 * @param {Object} memberData - Member data to add
 * @returns {Object} Response confirming member addition
 */
function addProjectMember(token, projectId, memberData) {
  const payload = JSON.stringify(memberData);
  const params = {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    tags: {
      name: 'project-add-member'
    }
  };
  
  return http.post(`${PROJECTS_ENDPOINT}/${projectId}/members`, payload, params);
}

/**
 * Retrieves the list of members for a project
 * @param {string} token - Authentication token
 * @param {string} projectId - ID of the project
 * @returns {Object} Response containing list of project members
 */
function getProjectMembers(token, projectId) {
  const params = {
    headers: {
      'Authorization': `Bearer ${token}`
    },
    tags: {
      name: 'project-members'
    }
  };
  
  return http.get(`${PROJECTS_ENDPOINT}/${projectId}/members`, params);
}

/**
 * Generates random data for project creation
 * @returns {Object} Random project data object
 */
function generateRandomProjectData() {
  const randomId = crypto.md5(String(Date.now()) + String(Math.random()), 'hex').substring(0, 8);
  
  return {
    name: `Project ${randomId}`,
    description: `A test project created by load testing at ${new Date().toISOString()}`,
    status: 'active',
    category: ['Development', 'Marketing', 'Design', 'Operations'][Math.floor(Math.random() * 4)]
  };
}

/**
 * Main function executed by k6 for each virtual user
 */
export default function() {
  // Get a random user from the shared array
  const userIndex = exec.vu.idInTest % testUsers.length;
  const user = testUsers[userIndex];
  
  // Login to get the token
  const token = login(user);
  if (!token) {
    console.error(`Failed to log in with user ${user.email}`);
    return;
  }
  
  // Wait between 1-3 seconds after login
  sleep(Math.random() * 2 + 1);
  
  // Project lifecycle simulation with checks
  group('Project Operations', function() {
    // List existing projects
    let projectsResponse = getProjects(token);
    check(projectsResponse, {
      'get projects status is 200': (r) => r.status === 200,
      'projects data is an array': (r) => Array.isArray(r.json())
    });
    
    // Create a new project
    const projectData = generateRandomProjectData();
    let createResponse = createProject(token, projectData);
    check(createResponse, {
      'create project status is 201': (r) => r.status === 201,
      'create project returns id': (r) => r.json('id') !== undefined
    });
    
    // Skip further tests if project creation failed
    if (createResponse.status !== 201) {
      console.error(`Failed to create project: ${createResponse.body}`);
      return;
    }
    
    const projectId = createResponse.json('id');
    
    // Wait a bit to simulate user thinking time
    sleep(Math.random() * 2 + 1);
    
    // Get the project details
    let projectDetailResponse = getProjectById(token, projectId);
    check(projectDetailResponse, {
      'get project details status is 200': (r) => r.status === 200,
      'project name matches': (r) => r.json('name') === projectData.name
    });
    
    // Wait a bit to simulate user thinking time
    sleep(Math.random() * 2 + 1);
    
    // Update the project
    const updateData = {
      name: `${projectData.name} (Updated)`,
      status: 'on-hold'
    };
    let updateResponse = updateProject(token, projectId, updateData);
    check(updateResponse, {
      'update project status is 200': (r) => r.status === 200,
      'updated name is correct': (r) => r.json('name') === updateData.name,
      'updated status is correct': (r) => r.json('status') === updateData.status
    });
    
    // Wait a bit to simulate user thinking time
    sleep(Math.random() * 2 + 1);
    
    // Add a member to the project (using a random test user)
    const randomMemberIndex = (userIndex + 1) % testUsers.length;
    const memberData = {
      userId: `user-${randomMemberIndex}`, // Using a pseudo-ID based on index
      role: 'member'
    };
    
    let addMemberResponse = addProjectMember(token, projectId, memberData);
    check(addMemberResponse, {
      'add member status is 200 or 201': (r) => r.status === 200 || r.status === 201
    });
    
    // Wait a bit to simulate user thinking time
    sleep(Math.random() * 2 + 1);
    
    // Get project members
    let membersResponse = getProjectMembers(token, projectId);
    check(membersResponse, {
      'get members status is 200': (r) => r.status === 200,
      'members data is an array': (r) => Array.isArray(r.json())
    });
    
    // Wait a bit to simulate user thinking time
    sleep(Math.random() * 2 + 1);
    
    // Delete the project (only 50% of the time to avoid removing all test data)
    if (Math.random() > 0.5) {
      let deleteResponse = deleteProject(token, projectId);
      check(deleteResponse, {
        'delete project status is 200 or 204': (r) => r.status === 200 || r.status === 204
      });
    }
  });
  
  // Sleep between iterations to simulate user pause
  sleep(Math.random() * 5 + 5);
}