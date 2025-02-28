from locust import HttpUser, task, tag, between
import json
import random
import time
from datetime import datetime, timedelta

# Base URL for API endpoints
API_BASE_URL = '/api/v1'

def generate_random_user():
    """
    Generate random user data for testing
    
    Returns:
        dict: Random user data with email, password, first_name, last_name
    """
    timestamp = int(time.time())
    email = f"testuser_{timestamp}_{random.randint(1000, 9999)}@example.com"
    password = "Test123456!"  # Use a standard password for testing
    first_name = f"Test{random.randint(100, 999)}"
    last_name = f"User{random.randint(100, 999)}"
    
    return {
        "email": email,
        "password": password,
        "first_name": first_name,
        "last_name": last_name
    }

def generate_random_task(project_id=None):
    """
    Generate random task data for testing
    
    Args:
        project_id (str): Optional project ID to associate with task
        
    Returns:
        dict: Random task data with title, description, status, priority, due_date
    """
    timestamp = int(time.time())
    statuses = ["created", "assigned", "in-progress", "on-hold", "in-review", "completed"]
    priorities = ["low", "medium", "high", "urgent"]
    
    task_data = {
        "title": f"Test Task {timestamp}_{random.randint(1000, 9999)}",
        "description": f"This is a test task created for performance testing at {datetime.now().isoformat()}",
        "status": random.choice(statuses),
        "priority": random.choice(priorities),
        "due_date": (datetime.now() + timedelta(days=random.randint(1, 30))).strftime("%Y-%m-%d")
    }
    
    if project_id:
        task_data["project_id"] = project_id
        
    return task_data

def generate_random_project():
    """
    Generate random project data for testing
    
    Returns:
        dict: Random project data with name, description, status
    """
    timestamp = int(time.time())
    statuses = ["planning", "active", "on-hold", "completed"]
    
    return {
        "name": f"Test Project {timestamp}_{random.randint(1000, 9999)}",
        "description": f"This is a test project created for performance testing at {datetime.now().isoformat()}",
        "status": random.choice(statuses)
    }

class BaseUser(HttpUser):
    """
    Base user class with common functionality for all user types
    """
    
    def __init__(self, *args, **kwargs):
        """
        Initialize the base user with default wait time and host
        """
        super().__init__(*args, **kwargs)
        self.auth_token = None
        self.user_data = {}
    
    def login(self, credentials):
        """
        Authenticate user and store JWT token
        
        Args:
            credentials (dict): User credentials with email and password
            
        Returns:
            dict: Response from login endpoint
        """
        response = self.client.post(
            f"{API_BASE_URL}/auth/login",
            json=credentials,
            name="Login"
        )
        
        if response.status_code == 200:
            data = response.json()
            if "token" in data:
                self.auth_token = data["token"]
                self.client.headers.update({"Authorization": f"Bearer {self.auth_token}"})
        
        return response
    
    def register(self, user_data=None):
        """
        Register a new user
        
        Args:
            user_data (dict): Optional user data. If not provided, generates random data
            
        Returns:
            dict: Response from register endpoint
        """
        if not user_data:
            user_data = generate_random_user()
            
        response = self.client.post(
            f"{API_BASE_URL}/auth/register",
            json=user_data,
            name="Register New User"
        )
        
        return response, user_data
    
    def on_start(self):
        """
        Actions to perform when user starts
        """
        # Generate user data and register
        self.user_data = generate_random_user()
        register_response, _ = self.register(self.user_data)
        
        # Login with the created user
        self.login({
            "email": self.user_data["email"],
            "password": self.user_data["password"]
        })

class TaskUser(BaseUser):
    """
    User that performs task-related operations
    """
    
    def __init__(self, *args, **kwargs):
        """
        Initialize the task user
        """
        super().__init__(*args, **kwargs)
        self.task_ids = []
    
    def on_start(self):
        """
        Actions to perform when user starts
        """
        super().on_start()
        self.task_ids = []
    
    @task(3)
    @tag('task')
    def create_task(self):
        """
        Create a new task
        
        Returns:
            dict: Created task data
        """
        task_data = generate_random_task()
        
        response = self.client.post(
            f"{API_BASE_URL}/tasks",
            json=task_data,
            name="Create Task"
        )
        
        if response.status_code == 201:
            task_id = response.json().get("id")
            if task_id:
                self.task_ids.append(task_id)
        
        return response
    
    @task(10)
    @tag('task')
    def get_tasks(self):
        """
        Get list of tasks
        
        Returns:
            dict: Task list data
        """
        response = self.client.get(
            f"{API_BASE_URL}/tasks",
            name="Get Task List"
        )
        
        return response
    
    @task(2)
    @tag('task')
    def update_task(self):
        """
        Update an existing task
        
        Returns:
            dict: Updated task data
        """
        if not self.task_ids:
            return None
            
        task_id = random.choice(self.task_ids)
        statuses = ["in-progress", "on-hold", "in-review", "completed"]
        priorities = ["low", "medium", "high", "urgent"]
        
        update_data = {
            "status": random.choice(statuses),
            "priority": random.choice(priorities)
        }
        
        response = self.client.put(
            f"{API_BASE_URL}/tasks/{task_id}",
            json=update_data,
            name="Update Task"
        )
        
        return response
    
    @task(5)
    @tag('task')
    def get_task_detail(self):
        """
        Get details of a specific task
        
        Returns:
            dict: Task detail data
        """
        if not self.task_ids:
            return None
            
        task_id = random.choice(self.task_ids)
        
        response = self.client.get(
            f"{API_BASE_URL}/tasks/{task_id}",
            name="Get Task Detail"
        )
        
        return response

class ProjectUser(BaseUser):
    """
    User that performs project-related operations
    """
    
    def __init__(self, *args, **kwargs):
        """
        Initialize the project user
        """
        super().__init__(*args, **kwargs)
        self.project_ids = []
    
    def on_start(self):
        """
        Actions to perform when user starts
        """
        super().on_start()
        self.project_ids = []
    
    @task(3)
    @tag('project')
    def create_project(self):
        """
        Create a new project
        
        Returns:
            dict: Created project data
        """
        project_data = generate_random_project()
        
        response = self.client.post(
            f"{API_BASE_URL}/projects",
            json=project_data,
            name="Create Project"
        )
        
        if response.status_code == 201:
            project_id = response.json().get("id")
            if project_id:
                self.project_ids.append(project_id)
        
        return response
    
    @task(10)
    @tag('project')
    def get_projects(self):
        """
        Get list of projects
        
        Returns:
            dict: Project list data
        """
        response = self.client.get(
            f"{API_BASE_URL}/projects",
            name="Get Project List"
        )
        
        return response
    
    @task(2)
    @tag('project')
    def update_project(self):
        """
        Update an existing project
        
        Returns:
            dict: Updated project data
        """
        if not self.project_ids:
            return None
            
        project_id = random.choice(self.project_ids)
        statuses = ["planning", "active", "on-hold", "completed"]
        
        update_data = {
            "name": f"Updated Project {int(time.time())}_{random.randint(1000, 9999)}",
            "status": random.choice(statuses)
        }
        
        response = self.client.put(
            f"{API_BASE_URL}/projects/{project_id}",
            json=update_data,
            name="Update Project"
        )
        
        return response
    
    @task(5)
    @tag('project')
    def get_project_detail(self):
        """
        Get details of a specific project
        
        Returns:
            dict: Project detail data
        """
        if not self.project_ids:
            return None
            
        project_id = random.choice(self.project_ids)
        
        response = self.client.get(
            f"{API_BASE_URL}/projects/{project_id}",
            name="Get Project Detail"
        )
        
        return response

class CombinedUser(BaseUser):
    """
    User that performs operations across multiple services to simulate realistic workflows
    """
    wait_time = between(1, 5)  # Wait between 1 and 5 seconds between tasks
    
    def __init__(self, *args, **kwargs):
        """
        Initialize the combined user
        """
        super().__init__(*args, **kwargs)
        self.task_ids = []
        self.project_ids = []
    
    def on_start(self):
        """
        Actions to perform when user starts
        """
        super().on_start()
        self.task_ids = []
        self.project_ids = []
    
    @task(2)
    @tag('combined')
    def create_project_and_tasks(self):
        """
        Create a project and associate tasks with it
        
        Returns:
            dict: Project and tasks data
        """
        # Create project
        project_data = generate_random_project()
        project_response = self.client.post(
            f"{API_BASE_URL}/projects",
            json=project_data,
            name="Create Project with Tasks - Project Creation"
        )
        
        result = {"project": project_response.json() if project_response.status_code == 201 else None}
        task_results = []
        
        if project_response.status_code == 201:
            project_id = project_response.json().get("id")
            if project_id:
                self.project_ids.append(project_id)
                
                # Create 3-5 tasks for this project
                num_tasks = random.randint(3, 5)
                for _ in range(num_tasks):
                    task_data = generate_random_task(project_id)
                    task_response = self.client.post(
                        f"{API_BASE_URL}/tasks",
                        json=task_data,
                        name="Create Project with Tasks - Task Creation"
                    )
                    
                    if task_response.status_code == 201:
                        task_id = task_response.json().get("id")
                        if task_id:
                            self.task_ids.append(task_id)
                            task_results.append(task_response.json())
        
        result["tasks"] = task_results
        return result
    
    @task(8)
    @tag('combined')
    def get_dashboard_data(self):
        """
        Get user dashboard data with tasks and projects
        
        Returns:
            dict: Dashboard data
        """
        response = self.client.get(
            f"{API_BASE_URL}/dashboard",
            name="Get Dashboard Data"
        )
        
        return response
    
    @task(1)
    @tag('combined')
    def complete_task_flow(self):
        """
        Complete flow from task creation to completion
        
        Returns:
            dict: Task completion data
        """
        # Create a new task
        task_data = generate_random_task()
        task_response = self.client.post(
            f"{API_BASE_URL}/tasks",
            json=task_data,
            name="Complete Task Flow - Task Creation"
        )
        
        result = {"creation": task_response.json() if task_response.status_code == 201 else None}
        
        if task_response.status_code == 201:
            task_id = task_response.json().get("id")
            if task_id:
                self.task_ids.append(task_id)
                
                # Update to in-progress
                progress_update = {
                    "status": "in-progress"
                }
                progress_response = self.client.put(
                    f"{API_BASE_URL}/tasks/{task_id}",
                    json=progress_update,
                    name="Complete Task Flow - Set In Progress"
                )
                result["in_progress"] = progress_response.json() if progress_response.status_code == 200 else None
                
                # Wait for a short time to simulate work
                time.sleep(random.uniform(1, 2))
                
                # Update to completed
                completion_update = {
                    "status": "completed"
                }
                completion_response = self.client.put(
                    f"{API_BASE_URL}/tasks/{task_id}",
                    json=completion_update,
                    name="Complete Task Flow - Set Completed"
                )
                result["completed"] = completion_response.json() if completion_response.status_code == 200 else None
                
                # Verify task status
                verification_response = self.client.get(
                    f"{API_BASE_URL}/tasks/{task_id}",
                    name="Complete Task Flow - Verify Completion"
                )
                result["verification"] = verification_response.json() if verification_response.status_code == 200 else None
        
        return result