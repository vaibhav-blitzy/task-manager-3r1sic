import http from 'k6/http';
import { sleep, check } from 'k6';
import { Counter, Rate } from 'k6/metrics';
import { SharedArray } from 'k6/data';
import { randomIntBetween } from 'https://jslib.k6.io/k6-utils/1.1.0/index.js';

// Custom metrics for tracking test results
const requests = new Counter('http_reqs');
const failRate = new Rate('failed_requests');
const authSuccessRate = new Rate('successful_auth');

// Configuration constants
const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const THINK_TIME_MIN = 1;
const THINK_TIME_MAX = 5;

// Load test users from data file
const users = new SharedArray('users', function() { 
  return JSON.parse(open('./data/users.json')); 
});

// Track users registered during this test run
let registeredUsers = [];

/**
 * Authenticates a user with email and password
 * @param {Object} credentials - User credentials containing email and password
 * @returns {Object|null} Response data containing tokens or null if authentication fails
 */
function login(credentials) {
  const payload = JSON.stringify({
    email: credentials.email,
    password: credentials.password
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
    },
  };

  const response = http.post(`${BASE_URL}/api/v1/auth/login`, payload, params);
  requests.add(1);
  
  const success = check(response, {
    'login status is 200': (r) => r.status === 200,
    'login response has tokens': (r) => r.json('access_token') !== undefined,
  });

  if (success) {
    authSuccessRate.add(1);
    return response.json();
  } else {
    failRate.add(1);
    console.log(`Login failed: ${response.status} - ${response.body}`);
    return null;
  }
}

/**
 * Registers a new user with unique credentials
 * @returns {Object|null} Response data containing user info or null if registration fails
 */
function register() {
  // Generate unique email with timestamp and random string
  const timestamp = new Date().getTime();
  const randomStr = Math.random().toString(36).substring(2, 8);
  const email = `test_${timestamp}_${randomStr}@example.com`;
  
  const payload = JSON.stringify({
    email: email,
    password: 'Password123!',
    first_name: 'Test',
    last_name: 'User'
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
    },
  };

  const response = http.post(`${BASE_URL}/api/v1/auth/register`, payload, params);
  requests.add(1);
  
  const success = check(response, {
    'register status is 201': (r) => r.status === 201,
    'register response has user data': (r) => r.json('id') !== undefined,
  });

  if (success) {
    // Store registered user for potential later use
    const credentials = {
      email: email,
      password: 'Password123!'
    };
    registeredUsers.push(credentials);
    return response.json();
  } else {
    failRate.add(1);
    console.log(`Registration failed: ${response.status} - ${response.body}`);
    return null;
  }
}

/**
 * Refreshes an access token using a refresh token
 * @param {string} refreshToken - The refresh token to use
 * @returns {Object|null} Response data containing new tokens or null if refresh fails
 */
function refreshToken(refreshToken) {
  const params = {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${refreshToken}`
    },
  };

  const response = http.post(`${BASE_URL}/api/v1/auth/refresh`, {}, params);
  requests.add(1);
  
  const success = check(response, {
    'refresh token status is 200': (r) => r.status === 200,
    'refresh response has new access token': (r) => r.json('access_token') !== undefined,
  });

  if (success) {
    return response.json();
  } else {
    failRate.add(1);
    console.log(`Token refresh failed: ${response.status} - ${response.body}`);
    return null;
  }
}

/**
 * Retrieves the authenticated user's profile
 * @param {string} accessToken - The access token for authorization
 * @returns {Object|null} User profile data or null if request fails
 */
function getUserProfile(accessToken) {
  const params = {
    headers: {
      'Authorization': `Bearer ${accessToken}`
    },
  };

  const response = http.get(`${BASE_URL}/api/v1/auth/me`, params);
  requests.add(1);
  
  const success = check(response, {
    'get profile status is 200': (r) => r.status === 200,
    'profile response has user data': (r) => r.json('id') !== undefined,
  });

  if (success) {
    return response.json();
  } else {
    failRate.add(1);
    console.log(`Get profile failed: ${response.status} - ${response.body}`);
    return null;
  }
}

/**
 * Logs out a user by invalidating their token server-side
 * @param {string} accessToken - The access token to invalidate
 * @returns {boolean} True if logout was successful, false otherwise
 */
function logout(accessToken) {
  const params = {
    headers: {
      'Authorization': `Bearer ${accessToken}`
    },
  };

  const response = http.post(`${BASE_URL}/api/v1/auth/logout`, {}, params);
  requests.add(1);
  
  const success = check(response, {
    'logout status is 200': (r) => r.status === 200,
  });

  if (success) {
    return true;
  } else {
    failRate.add(1);
    console.log(`Logout failed: ${response.status} - ${response.body}`);
    return false;
  }
}

/**
 * Simulates authentication flow for existing users including:
 * login, profile retrieval, token refresh, and logout
 * @param {number} userIndex - Index of the user in the test data array
 */
function simulateExistingUserFlow(userIndex) {
  // Get user credentials from shared test data
  const user = users[userIndex % users.length];
  
  // Login
  const loginResponse = login(user);
  if (!loginResponse) return;
  
  // Get user profile
  const profile = getUserProfile(loginResponse.access_token);
  
  // Simulate user think time
  sleep(randomIntBetween(THINK_TIME_MIN, THINK_TIME_MAX));
  
  // Refresh token
  const refreshResponse = refreshToken(loginResponse.refresh_token);
  
  // Simulate user think time
  sleep(randomIntBetween(THINK_TIME_MIN, THINK_TIME_MAX));
  
  // Logout
  if (refreshResponse) {
    logout(refreshResponse.access_token);
  } else {
    logout(loginResponse.access_token);
  }
  
  // Track completed request
  requests.add(1, { type: 'completed_flow' });
}

/**
 * Simulates authentication flow for new users including:
 * registration, login, profile retrieval, and logout
 */
function simulateNewUserFlow() {
  // Register new user
  const registerResponse = register();
  if (!registerResponse) return;
  
  // Simulate user think time
  sleep(randomIntBetween(THINK_TIME_MIN, THINK_TIME_MAX));
  
  // Login with newly registered credentials
  const credentials = {
    email: registerResponse.email,
    password: 'Password123!'
  };
  const loginResponse = login(credentials);
  
  // Simulate user think time
  sleep(randomIntBetween(THINK_TIME_MIN, THINK_TIME_MAX));
  
  // Get user profile if login was successful
  if (loginResponse) {
    const profile = getUserProfile(loginResponse.access_token);
    
    // Simulate user think time
    sleep(randomIntBetween(THINK_TIME_MIN, THINK_TIME_MAX));
    
    // Logout
    logout(loginResponse.access_token);
  }
  
  // Track completed request
  requests.add(1, { type: 'completed_flow' });
}

// Test configuration options
export const options = {
  scenarios: {
    // Standard load test: 500 concurrent users as per requirements
    moderate_load: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '30s', target: 500 },  // Ramp up to 500 users over 30 seconds
        { duration: '2m', target: 500 },   // Stay at 500 users for 2 minutes
        { duration: '30s', target: 0 },    // Ramp down over 30 seconds
      ],
      gracefulRampDown: '30s',
      exec: 'default',
    },
    // Stress test: Up to 2000 users to test system limits
    stress_test: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '1m', target: 1000 },  // Ramp up to 1000 users
        { duration: '2m', target: 2000 },  // Continue to 2000 users
        { duration: '1m', target: 0 },     // Ramp down
      ],
      gracefulRampDown: '30s',
      exec: 'default',
      tags: { test_type: 'stress' },
      // Disabled by default, enable when explicitly running stress tests
      startTime: '10m',  // Will run after moderate load test completes
    },
  },
  thresholds: {
    // 95% of requests should be below 300ms for standard load (per Authentication Service SLA)
    'http_req_duration{scenario:moderate_load}': ['p(95)<300'],
    // Allow higher latency during stress testing
    'http_req_duration{scenario:stress_test}': ['p(95)<1000'],
    // Less than 1% failure rate for standard load
    'failed_requests{scenario:moderate_load}': ['rate<0.01'],
    // Less than 5% failure rate during stress test
    'failed_requests{scenario:stress_test}': ['rate<0.05'],
    // 99% authentication success rate per SLA requirements
    'successful_auth{scenario:moderate_load}': ['rate>0.99'],
    // Ensure we make enough requests to be statistically significant
    'http_reqs': ['count>100'],
  },
};

// Main test function
export default function() {
  // 80% of traffic simulates existing users, 20% new registrations
  if (Math.random() < 0.8) {
    const userIndex = Math.floor(Math.random() * users.length);
    simulateExistingUserFlow(userIndex);
  } else {
    simulateNewUserFlow();
  }
}