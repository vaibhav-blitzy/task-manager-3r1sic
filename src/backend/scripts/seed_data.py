"""
Script to seed the MongoDB database with sample data for development, testing, and demonstration purposes.
Creates sample users, roles, projects, tasks, and relationships between them.
"""

import argparse  # latest
import random  # latest
import datetime  # latest
from typing import Dict, List

from faker import Faker  # v14.0.0
import pymongo  # v4.3.3
from tqdm import tqdm  # v4.64.1
from bson import ObjectId  # latest

from ..common.database.mongo.connection import get_mongo_connection
from ..services.auth.models.user import User, create_user
from ..services.auth.models.role import Role, create_default_roles
from ..services.task.models.task import Task
from ..services.project.models.project import Project
from ..services.project.models.member import ProjectMember
from ..common.utils.security import hash_password
from ..common.utils.datetime import get_utc_now
from ..common.config.base import Config

# Initialize Faker for generating realistic data
fake = Faker()

# Sample user data templates
SAMPLE_USERS = {
    "admin": {"email": "admin@example.com", "firstName": "System", "lastName": "Admin"},
    "manager": {"email": "manager@example.com", "firstName": "Project", "lastName": "Manager"},
    "user": {"email": "user@example.com", "firstName": "Regular", "lastName": "User"}
}

# Sample project data templates
SAMPLE_PROJECTS = {
    "Software Development": {"description": "Developing new software applications", "category": "Software"},
    "Marketing Campaign": {"description": "Launching a new marketing campaign", "category": "Marketing"},
    "Design Project": {"description": "Creating new designs for web and mobile", "category": "Design"}
}

# Sample task data templates
SAMPLE_TASKS = {
    "Develop API endpoints": {"priority": "high", "status": "in_progress"},
    "Design user interface": {"priority": "medium", "status": "in_review"},
    "Write user documentation": {"priority": "low", "status": "created"},
    "Test application": {"priority": "urgent", "status": "assigned"}
}

# Valid task status and priority options
STATUS_CHOICES = ["created", "assigned", "in_progress", "on_hold", "in_review", "completed", "cancelled"]
PRIORITY_CHOICES = ["low", "medium", "high", "urgent"]

# Default password for seeded users
DEFAULT_PASSWORD = "P@$$wOrd"


def create_users(count: int, db: pymongo.database.Database, verbose: bool) -> List[str]:
    """
    Creates sample users with different roles.

    Args:
        count: Number of users to create
        db: MongoDB database instance
        verbose: Whether to print progress messages

    Returns:
        List of created user IDs
    """
    # Initialize Faker library for generating realistic user data
    fake = Faker()

    # Create admin, manager, and regular user roles if they don't exist
    create_default_roles()

    # Create predefined users (admin@example.com, manager@example.com, user@example.com) with known passwords
    user_ids = []
    for role, user_data in SAMPLE_USERS.items():
        if verbose:
            print(f"Creating {role} user: {user_data['email']}")
        user = create_user({
            "email": user_data["email"],
            "password": DEFAULT_PASSWORD,
            "firstName": user_data["firstName"],
            "lastName": user_data["lastName"]
        })
        user_ids.append(str(user.get_id()))

    # Generate additional random users up to the specified count
    for i in tqdm(range(count - len(SAMPLE_USERS)), desc="Creating random users", disable=not verbose):
        email = fake.email()
        firstName = fake.first_name()
        lastName = fake.last_name()
        user = create_user({
            "email": email,
            "password": DEFAULT_PASSWORD,
            "firstName": firstName,
            "lastName": lastName
        })
        user_ids.append(str(user.get_id()))

    return user_ids


def create_projects(count: int, db: pymongo.database.Database, user_ids: List[str], verbose: bool) -> List[str]:
    """
    Creates sample projects and assigns members.

    Args:
        count: Number of projects to create
        db: MongoDB database instance
        user_ids: List of valid user IDs to assign as project members
        verbose: Whether to print progress messages

    Returns:
        List of created project IDs
    """
    # Initialize Faker library for generating realistic project data
    fake = Faker()

    # Generate sample projects with names, descriptions, and status
    project_ids = []
    for i in tqdm(range(count), desc="Creating projects", disable=not verbose):
        projectName = fake.catch_phrase()
        projectDescription = fake.paragraph()
        projectCategory = random.choice(list(SAMPLE_PROJECTS.keys()))
        owner_id = random.choice(user_ids)

        project = Project({
            "name": projectName,
            "description": projectDescription,
            "status": random.choice(["planning", "active", "on_hold"]),
            "category": projectCategory,
            "owner_id": ObjectId(owner_id)
        })
        project.save()
        project_id = str(project.get_id())
        project_ids.append(project_id)

    return project_ids


def create_tasks(count: int, db: pymongo.database.Database, user_ids: List[str], project_ids: List[str], verbose: bool) -> List[str]:
    """
    Creates sample tasks and assigns to users and projects.

    Args:
        count: Number of tasks to create
        db: MongoDB database instance
        user_ids: List of valid user IDs to assign tasks to
        project_ids: List of valid project IDs to assign tasks to
        verbose: Whether to print progress messages

    Returns:
        List of created task IDs
    """
    # Initialize Faker library for generating realistic task data
    fake = Faker()

    # Create tasks with titles, descriptions, status, priority, and due dates
    task_ids = []
    for i in tqdm(range(count), desc="Creating tasks", disable=not verbose):
        taskTitle = fake.sentence()
        taskDescription = fake.paragraph()
        taskStatus = random.choice(STATUS_CHOICES)
        taskPriority = random.choice(PRIORITY_CHOICES)
        taskDueDate = fake.future_datetime(end_date="+30d")
        created_by = random.choice(user_ids)
        assignee_id = random.choice(user_ids)
        project_id = random.choice(project_ids)

        task = Task({
            "title": taskTitle,
            "description": taskDescription,
            "status": taskStatus,
            "priority": taskPriority,
            "dueDate": taskDueDate,
            "createdBy": ObjectId(created_by),
            "assigneeId": ObjectId(assignee_id),
            "projectId": ObjectId(project_id)
        })
        task.save()
        task_ids.append(str(task.get_id()))

    return task_ids


def create_task_comments(task_ids: List[str], user_ids: List[str], db: pymongo.database.Database, verbose: bool) -> None:
    """
    Creates sample comments on tasks.

    Args:
        task_ids: List of valid task IDs to add comments to
        user_ids: List of valid user IDs to assign as comment authors
        db: MongoDB database instance
        verbose: Whether to print progress messages
    """
    # Randomly select tasks to receive comments (about 70% of tasks)
    tasks_with_comments = random.sample(task_ids, int(len(task_ids) * 0.7))

    # Generate between 0-5 comments per selected task
    for task_id in tqdm(tasks_with_comments, desc="Creating task comments", disable=not verbose):
        num_comments = random.randint(0, 5)
        for i in range(num_comments):
            commentContent = fake.paragraph()
            commentUserId = random.choice(user_ids)
            commentCreatedAt = fake.past_datetime()

            db.comments.insert_one({
                "taskId": ObjectId(task_id),
                "userId": ObjectId(commentUserId),
                "content": commentContent,
                "createdAt": commentCreatedAt
            })


def create_sample_data(args: argparse.Namespace) -> None:
    """
    Orchestrates the creation of all sample data types.

    Args:
        args: Parsed command line arguments
    """
    # Connect to MongoDB using connection string from Config
    db = get_mongo_connection()

    # Clear existing data if args.clear is True
    if args.clear:
        clear_collections(db, args.verbose)

    # Call create_users to generate sample users
    user_ids = create_users(args.users, db, args.verbose)

    # Call create_projects to generate sample projects
    project_ids = create_projects(args.projects, db, user_ids, args.verbose)

    # Call create_tasks to generate sample tasks
    task_ids = create_tasks(args.tasks, db, user_ids, project_ids, args.verbose)

    # Call create_task_comments to add comments to tasks
    create_task_comments(task_ids, user_ids, db, args.verbose)

    # Display summary of created data
    print("\nSample data creation complete:")
    print(f"  - Users: {len(user_ids)}")
    print(f"  - Projects: {len(project_ids)}")
    print(f"  - Tasks: {len(task_ids)}")


def clear_collections(db: pymongo.database.Database, verbose: bool) -> None:
    """
    Clears all collections in the database.

    Args:
        db: MongoDB database instance
        verbose: Whether to print progress messages
    """
    # Get list of all collections in the database
    collection_names = db.list_collection_names()

    # Iterate through collections and drop each one
    for collection_name in collection_names:
        # Skip system collections
        if collection_name.startswith("system."):
            continue

        # Drop the collection
        db.drop_collection(collection_name)
        if verbose:
            print(f"  - Dropped collection: {collection_name}")

    print("\nDatabase cleared.")


def setup_argparse() -> argparse.ArgumentParser:
    """
    Sets up command line argument parsing.

    Returns:
        Configured argument parser
    """
    # Create ArgumentParser instance with program description
    parser = argparse.ArgumentParser(description="Seed the MongoDB database with sample data.")

    # Add argument for user count (default: 20)
    parser.add_argument("--users", type=int, default=20, help="Number of users to create (default: 20)")

    # Add argument for project count (default: 5)
    parser.add_argument("--projects", type=int, default=5, help="Number of projects to create (default: 5)")

    # Add argument for task count (default: 50)
    parser.add_argument("--tasks", type=int, default=50, help="Number of tasks to create (default: 50)")

    # Add flag for clearing existing data (action: store_true)
    parser.add_argument("--clear", action="store_true", help="Clear existing data before seeding")

    # Add flag for verbose output (action: store_true)
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")

    return parser


def main() -> None:
    """
    Main entry point for the script.
    """
    try:
        # Set up argument parser
        parser = setup_argparse()

        # Parse command line arguments
        args = parser.parse_args()

        # Call create_sample_data with parsed arguments
        create_sample_data(args)

        print("\nDatabase seeding completed successfully!")

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()