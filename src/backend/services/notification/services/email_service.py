"""
Email service for the Task Management System.

This module provides functionality for sending email notifications
using SendGrid API. It includes methods for different notification types,
retry logic, and template formatting.
"""

import os
import time
import json
from typing import Dict, Any, Optional

from sendgrid import SendGridAPIClient  # sendgrid v6.9.x
from sendgrid.helpers.mail import Mail  # sendgrid v6.9.x

from ..config import SENDGRID_API_KEY, EMAIL_SENDER, EMAIL_TEMPLATES
from ...common.logging.logger import logger
from ...common.exceptions.api_exceptions import APIException
from ...common.utils.datetime import format_datetime


class EmailService:
    """Service for sending email notifications using SendGrid."""
    
    def __init__(self):
        """Initialize the email service with SendGrid API credentials."""
        self._sendgrid_client = SendGridAPIClient(api_key=SENDGRID_API_KEY)
        self._sender_email = EMAIL_SENDER
        self._templates = EMAIL_TEMPLATES
        self._max_retries = 3
    
    def send_email(self, to_email: str, subject: str, content: str, is_html: bool = True) -> bool:
        """
        Send an email to a recipient.
        
        Args:
            to_email: Recipient email address
            subject: Email subject line
            content: Email content (HTML or plain text)
            is_html: Whether the content is HTML (default: True)
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        try:
            message = Mail(
                from_email=self._sender_email,
                to_emails=to_email,
                subject=subject
            )
            
            # Set content type based on is_html parameter
            content_type = "text/html" if is_html else "text/plain"
            message.add_content(content_type, content)
            
            logger.info(f"Attempting to send email to {to_email} with subject: {subject}")
            return self._send_with_retry(message)
            
        except Exception as e:
            logger.error(f"Failed to prepare email to {to_email}: {str(e)}")
            return False
    
    def send_task_assigned_notification(self, to_email: str, recipient_name: str, 
                                       assigner_name: str, task_title: str, 
                                       task_id: str, due_date: str) -> bool:
        """
        Send email notification when a task is assigned to a user.
        
        Args:
            to_email: Recipient email address
            recipient_name: Name of the recipient
            assigner_name: Name of the person who assigned the task
            task_title: Title of the assigned task
            task_id: ID of the task
            due_date: Due date of the task
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        formatted_due_date = format_datetime(due_date, "long_date") if due_date else "No due date"
        task_url = self._generate_url("task", task_id)
        
        template_data = {
            "recipient_name": recipient_name,
            "assigner_name": assigner_name,
            "task_title": task_title,
            "due_date": formatted_due_date,
            "task_url": task_url
        }
        
        subject = f"Task Assigned: {task_title}"
        content = self._load_template("task_assigned", template_data)
        
        return self.send_email(to_email, subject, content, is_html=True)
    
    def send_task_due_soon_notification(self, to_email: str, recipient_name: str, 
                                       task_title: str, task_id: str, 
                                       due_date: str, time_remaining: str) -> bool:
        """
        Send email notification when a task is due soon.
        
        Args:
            to_email: Recipient email address
            recipient_name: Name of the recipient
            task_title: Title of the task
            task_id: ID of the task
            due_date: Due date of the task
            time_remaining: Human-readable time remaining until due date
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        formatted_due_date = format_datetime(due_date, "long_date") if due_date else "Unknown"
        task_url = self._generate_url("task", task_id)
        
        template_data = {
            "recipient_name": recipient_name,
            "task_title": task_title,
            "due_date": formatted_due_date,
            "time_remaining": time_remaining,
            "task_url": task_url
        }
        
        subject = f"Task Due Soon: {task_title}"
        content = self._load_template("task_due_soon", template_data)
        
        return self.send_email(to_email, subject, content, is_html=True)
    
    def send_task_overdue_notification(self, to_email: str, recipient_name: str, 
                                      task_title: str, task_id: str, 
                                      due_date: str, days_overdue: str) -> bool:
        """
        Send email notification when a task is overdue.
        
        Args:
            to_email: Recipient email address
            recipient_name: Name of the recipient
            task_title: Title of the task
            task_id: ID of the task
            due_date: Due date of the task
            days_overdue: Number of days the task is overdue
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        formatted_due_date = format_datetime(due_date, "long_date") if due_date else "Unknown"
        task_url = self._generate_url("task", task_id)
        
        template_data = {
            "recipient_name": recipient_name,
            "task_title": task_title,
            "due_date": formatted_due_date,
            "days_overdue": days_overdue,
            "task_url": task_url
        }
        
        subject = f"Task Overdue: {task_title}"
        content = self._load_template("task_overdue", template_data)
        
        return self.send_email(to_email, subject, content, is_html=True)
    
    def send_comment_notification(self, to_email: str, recipient_name: str, 
                                 commenter_name: str, task_title: str, 
                                 task_id: str, comment_snippet: str) -> bool:
        """
        Send email notification when someone comments on a task.
        
        Args:
            to_email: Recipient email address
            recipient_name: Name of the recipient
            commenter_name: Name of the person who commented
            task_title: Title of the task
            task_id: ID of the task
            comment_snippet: Preview of the comment content
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        task_url = self._generate_url("task", task_id)
        
        template_data = {
            "recipient_name": recipient_name,
            "commenter_name": commenter_name,
            "task_title": task_title,
            "comment_snippet": comment_snippet,
            "task_url": task_url
        }
        
        subject = f"New Comment on Task: {task_title}"
        content = self._load_template("comment_added", template_data)
        
        return self.send_email(to_email, subject, content, is_html=True)
    
    def send_project_invitation(self, to_email: str, recipient_name: str, 
                               inviter_name: str, project_name: str, 
                               project_id: str) -> bool:
        """
        Send email notification for project invitation.
        
        Args:
            to_email: Recipient email address
            recipient_name: Name of the recipient
            inviter_name: Name of the person sending the invitation
            project_name: Name of the project
            project_id: ID of the project
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        project_url = self._generate_url("project", project_id)
        
        template_data = {
            "recipient_name": recipient_name,
            "inviter_name": inviter_name,
            "project_name": project_name,
            "project_url": project_url
        }
        
        subject = f"Invitation to Project: {project_name}"
        content = self._load_template("project_invitation", template_data)
        
        return self.send_email(to_email, subject, content, is_html=True)
    
    def send_status_change_notification(self, to_email: str, recipient_name: str, 
                                       updater_name: str, task_title: str, 
                                       task_id: str, old_status: str, 
                                       new_status: str) -> bool:
        """
        Send email notification when a task status changes.
        
        Args:
            to_email: Recipient email address
            recipient_name: Name of the recipient
            updater_name: Name of the person who updated the status
            task_title: Title of the task
            task_id: ID of the task
            old_status: Previous task status
            new_status: New task status
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        task_url = self._generate_url("task", task_id)
        
        template_data = {
            "recipient_name": recipient_name,
            "updater_name": updater_name,
            "task_title": task_title,
            "old_status": old_status,
            "new_status": new_status,
            "task_url": task_url
        }
        
        subject = f"Task Status Changed: {task_title}"
        content = self._load_template("status_change", template_data)
        
        return self.send_email(to_email, subject, content, is_html=True)
    
    def _send_with_retry(self, message: Mail) -> bool:
        """
        Private method to send email with retry logic for transient failures.
        
        Args:
            message: SendGrid Mail object to send
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        retry_count = 0
        
        while retry_count <= self._max_retries:
            try:
                response = self._sendgrid_client.send(message)
                
                # Check if the request was successful (2xx status code)
                if 200 <= response.status_code < 300:
                    logger.info(f"Email sent successfully with status code {response.status_code}")
                    return True
                
                # Handle permanent errors (4xx status codes except for specific retryable ones)
                if 400 <= response.status_code < 500 and response.status_code not in [408, 429]:
                    logger.error(f"Permanent error sending email: Status code {response.status_code}")
                    return False
                
                # For other errors, retry with exponential backoff
                retry_count += 1
                if retry_count <= self._max_retries:
                    backoff_time = 2 ** retry_count  # Exponential backoff: 2, 4, 8 seconds
                    logger.warning(f"Temporary error sending email. Retrying in {backoff_time} seconds...")
                    time.sleep(backoff_time)
                
            except Exception as e:
                retry_count += 1
                if retry_count <= self._max_retries:
                    backoff_time = 2 ** retry_count
                    logger.warning(f"Error sending email: {str(e)}. Retrying in {backoff_time} seconds...")
                    time.sleep(backoff_time)
                else:
                    logger.error(f"Failed to send email after {self._max_retries} retries: {str(e)}")
                    return False
        
        logger.error(f"Failed to send email after {self._max_retries} retries")
        return False
    
    def _load_template(self, template_type: str, template_data: Dict[str, Any]) -> str:
        """
        Private method to load an email template by type and format with data.
        
        Args:
            template_type: Type of template to load
            template_data: Dictionary of data to populate the template
            
        Returns:
            str: Formatted HTML content for the email
        """
        try:
            template = self._templates.get(template_type)
            if not template:
                logger.warning(f"Template not found for type: {template_type}")
                # Fallback to a basic template
                return f"""
                <html>
                <body>
                    <h2>{template_data.get('subject', 'Notification')}</h2>
                    <p>This is an automated notification from the Task Management System.</p>
                    <dl>
                        {' '.join([f'<dt>{k}</dt><dd>{v}</dd>' for k, v in template_data.items() if not k.endswith('_url')])}
                    </dl>
                    <p><a href="{next((v for k, v in template_data.items() if k.endswith('_url')), '#')}">View Details</a></p>
                </body>
                </html>
                """
            
            # Replace placeholders in the template with actual data
            formatted_template = template
            for key, value in template_data.items():
                placeholder = f"{{{{{key}}}}}"
                formatted_template = formatted_template.replace(placeholder, str(value))
            
            return formatted_template
            
        except Exception as e:
            logger.error(f"Error loading template {template_type}: {str(e)}")
            # Fallback to very basic template
            return f"""
            <html>
            <body>
                <h2>Notification</h2>
                <p>There was an error formatting this email. Please check the system.</p>
            </body>
            </html>
            """
    
    def _generate_url(self, resource_type: str, resource_id: str) -> str:
        """
        Private method to generate a URL for a task or project in the application.
        
        Args:
            resource_type: Type of resource (task, project, etc.)
            resource_id: ID of the resource
            
        Returns:
            str: Full URL to the resource in the application
        """
        base_url = os.environ.get("APP_BASE_URL", "https://taskmanagement.example.com")
        
        if resource_type == "task":
            return f"{base_url}/tasks/{resource_id}"
        elif resource_type == "project":
            return f"{base_url}/projects/{resource_id}"
        else:
            return f"{base_url}"