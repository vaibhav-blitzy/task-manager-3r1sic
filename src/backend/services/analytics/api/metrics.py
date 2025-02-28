"""
Analytics metrics API endpoints module.

Implements REST API endpoints for analytics metrics, providing access to various
performance indicators, task statistics, project progress metrics, and user
productivity data for dashboards and reports.
"""

import typing
from datetime import datetime
from flask import Blueprint, request, jsonify

from ...common.auth.decorators import token_required, roles_required, get_current_user
from ...common.exceptions.api_exceptions import BadRequestError
from ...common.logging.logger import get_logger
from ..services.metrics_service import (
    get_task_completion_rate,
    get_on_time_completion_rate,
    get_average_task_age,
    get_cycle_time,
    get_lead_time,
    get_workload_distribution,
    identify_bottlenecks,
    get_burndown_data,
    get_task_status_distribution,
    get_task_priority_distribution,
    get_project_progress,
    get_user_productivity,
    get_task_completion_trend,
    get_overdue_tasks_count,
    get_upcoming_due_tasks,
    calculate_project_completion_percentage,
    get_metrics_summary,
    MetricsCache
)

# Create Blueprint for metrics API routes
metrics_blueprint = Blueprint('metrics', __name__, url_prefix='/metrics')

# Initialize metrics cache
metrics_cache = MetricsCache()

# Configure logger
logger = get_logger(__name__)


@metrics_blueprint.route('/task-completion-rate', methods=['GET'])
@token_required
def get_task_completion_rate_endpoint():
    """
    API endpoint to retrieve task completion rate.
    
    Returns:
        JSON response with task completion rate data
    """
    try:
        # Extract filter parameters from request
        filters = _extract_filters_from_request()
        
        # Extract time period (default to month)
        time_period = request.args.get('time_period', 'month')
        
        # Generate cache key and check cache
        cache_key = metrics_cache.get_cache_key('task_completion_rate', filters=filters, time_period=time_period)
        cached_result = metrics_cache.get(cache_key)
        
        if cached_result:
            logger.debug(f"Returning cached task completion rate for filters: {filters}, time_period: {time_period}")
            return jsonify(cached_result)
        
        # Calculate task completion rate
        result = get_task_completion_rate(filters=filters, time_period=time_period)
        
        # Cache the result
        metrics_cache.set(cache_key, result)
        
        logger.info(f"Calculated task completion rate for filters: {filters}, time_period: {time_period}")
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error retrieving task completion rate: {str(e)}")
        raise


@metrics_blueprint.route('/on-time-completion-rate', methods=['GET'])
@token_required
def get_on_time_completion_rate_endpoint():
    """
    API endpoint to retrieve on-time task completion rate.
    
    Returns:
        JSON response with on-time completion rate data
    """
    try:
        # Extract filter parameters from request
        filters = _extract_filters_from_request()
        
        # Extract time period (default to month)
        time_period = request.args.get('time_period', 'month')
        
        # Generate cache key and check cache
        cache_key = metrics_cache.get_cache_key('on_time_completion_rate', filters=filters, time_period=time_period)
        cached_result = metrics_cache.get(cache_key)
        
        if cached_result:
            logger.debug(f"Returning cached on-time completion rate for filters: {filters}, time_period: {time_period}")
            return jsonify(cached_result)
        
        # Calculate on-time completion rate
        result = get_on_time_completion_rate(filters=filters, time_period=time_period)
        
        # Cache the result
        metrics_cache.set(cache_key, result)
        
        logger.info(f"Calculated on-time completion rate for filters: {filters}, time_period: {time_period}")
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error retrieving on-time completion rate: {str(e)}")
        raise


@metrics_blueprint.route('/average-task-age', methods=['GET'])
@token_required
def get_average_task_age_endpoint():
    """
    API endpoint to retrieve average task age.
    
    Returns:
        JSON response with average task age data
    """
    try:
        # Extract filter parameters from request
        filters = _extract_filters_from_request()
        
        # Extract status parameter if provided
        status = request.args.get('status')
        
        # Generate cache key and check cache
        cache_key = metrics_cache.get_cache_key('average_task_age', filters=filters, status=status)
        cached_result = metrics_cache.get(cache_key)
        
        if cached_result:
            logger.debug(f"Returning cached average task age for filters: {filters}, status: {status}")
            return jsonify(cached_result)
        
        # Calculate average task age
        result = get_average_task_age(filters=filters, status=status)
        
        # Cache the result
        metrics_cache.set(cache_key, result)
        
        logger.info(f"Calculated average task age for filters: {filters}, status: {status}")
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error retrieving average task age: {str(e)}")
        raise


@metrics_blueprint.route('/cycle-time', methods=['GET'])
@token_required
def get_cycle_time_endpoint():
    """
    API endpoint to retrieve average cycle time from task creation to completion.
    
    Returns:
        JSON response with cycle time data
    """
    try:
        # Extract filter parameters from request
        filters = _extract_filters_from_request()
        
        # Extract time period (default to month)
        time_period = request.args.get('time_period', 'month')
        
        # Generate cache key and check cache
        cache_key = metrics_cache.get_cache_key('cycle_time', filters=filters, time_period=time_period)
        cached_result = metrics_cache.get(cache_key)
        
        if cached_result:
            logger.debug(f"Returning cached cycle time for filters: {filters}, time_period: {time_period}")
            return jsonify(cached_result)
        
        # Calculate cycle time
        result = get_cycle_time(filters=filters, time_period=time_period)
        
        # Cache the result
        metrics_cache.set(cache_key, result)
        
        logger.info(f"Calculated cycle time for filters: {filters}, time_period: {time_period}")
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error retrieving cycle time: {str(e)}")
        raise


@metrics_blueprint.route('/lead-time', methods=['GET'])
@token_required
def get_lead_time_endpoint():
    """
    API endpoint to retrieve average lead time from task creation to delivery.
    
    Returns:
        JSON response with lead time data
    """
    try:
        # Extract filter parameters from request
        filters = _extract_filters_from_request()
        
        # Extract time period (default to month)
        time_period = request.args.get('time_period', 'month')
        
        # Generate cache key and check cache
        cache_key = metrics_cache.get_cache_key('lead_time', filters=filters, time_period=time_period)
        cached_result = metrics_cache.get(cache_key)
        
        if cached_result:
            logger.debug(f"Returning cached lead time for filters: {filters}, time_period: {time_period}")
            return jsonify(cached_result)
        
        # Calculate lead time
        result = get_lead_time(filters=filters, time_period=time_period)
        
        # Cache the result
        metrics_cache.set(cache_key, result)
        
        logger.info(f"Calculated lead time for filters: {filters}, time_period: {time_period}")
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error retrieving lead time: {str(e)}")
        raise


@metrics_blueprint.route('/workload-distribution', methods=['GET'])
@token_required
def get_workload_distribution_endpoint():
    """
    API endpoint to retrieve workload distribution among users.
    
    Returns:
        JSON response with workload distribution data
    """
    try:
        # Extract filter parameters from request
        filters = _extract_filters_from_request()
        
        # Generate cache key and check cache
        cache_key = metrics_cache.get_cache_key('workload_distribution', filters=filters)
        cached_result = metrics_cache.get(cache_key)
        
        if cached_result:
            logger.debug(f"Returning cached workload distribution for filters: {filters}")
            return jsonify(cached_result)
        
        # Calculate workload distribution
        result = get_workload_distribution(filters=filters)
        
        # Cache the result
        metrics_cache.set(cache_key, result)
        
        logger.info(f"Calculated workload distribution for filters: {filters}")
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error retrieving workload distribution: {str(e)}")
        raise


@metrics_blueprint.route('/bottlenecks', methods=['GET'])
@token_required
def identify_bottlenecks_endpoint():
    """
    API endpoint to identify process bottlenecks in task workflow.
    
    Returns:
        JSON response with bottleneck analysis data
    """
    try:
        # Extract filter parameters from request
        filters = _extract_filters_from_request()
        
        # Extract time period (default to month)
        time_period = request.args.get('time_period', 'month')
        
        # Generate cache key and check cache
        cache_key = metrics_cache.get_cache_key('bottlenecks', filters=filters, time_period=time_period)
        cached_result = metrics_cache.get(cache_key)
        
        if cached_result:
            logger.debug(f"Returning cached bottleneck analysis for filters: {filters}, time_period: {time_period}")
            return jsonify(cached_result)
        
        # Identify bottlenecks
        result = identify_bottlenecks(filters=filters, time_period=time_period)
        
        # Cache the result
        metrics_cache.set(cache_key, result)
        
        logger.info(f"Identified bottlenecks for filters: {filters}, time_period: {time_period}")
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error identifying bottlenecks: {str(e)}")
        raise


@metrics_blueprint.route('/burndown', methods=['GET'])
@token_required
def get_burndown_data_endpoint():
    """
    API endpoint to retrieve burndown chart data for project tracking.
    
    Returns:
        JSON response with burndown chart data
    """
    try:
        # Extract required parameters
        project_id = request.args.get('project_id')
        if not project_id:
            raise BadRequestError("Project ID is required for burndown chart data")
        
        # Extract date range parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Generate cache key and check cache
        cache_key = metrics_cache.get_cache_key('burndown', project_id=project_id, 
                                              start_date=start_date, end_date=end_date)
        cached_result = metrics_cache.get(cache_key)
        
        if cached_result:
            logger.debug(f"Returning cached burndown data for project_id: {project_id}")
            return jsonify(cached_result)
        
        # Get burndown data
        result = get_burndown_data(project_id=project_id, start_date=start_date, end_date=end_date)
        
        # Cache the result
        metrics_cache.set(cache_key, result)
        
        logger.info(f"Generated burndown chart data for project_id: {project_id}")
        return jsonify(result)
    
    except BadRequestError as e:
        logger.warning(f"Bad request for burndown data: {str(e)}")
        raise
        
    except Exception as e:
        logger.error(f"Error retrieving burndown data: {str(e)}")
        raise


@metrics_blueprint.route('/task-status-distribution', methods=['GET'])
@token_required
def get_task_status_distribution_endpoint():
    """
    API endpoint to retrieve distribution of tasks by status.
    
    Returns:
        JSON response with task status distribution data
    """
    try:
        # Extract filter parameters from request
        filters = _extract_filters_from_request()
        
        # Generate cache key and check cache
        cache_key = metrics_cache.get_cache_key('task_status_distribution', filters=filters)
        cached_result = metrics_cache.get(cache_key)
        
        if cached_result:
            logger.debug(f"Returning cached task status distribution for filters: {filters}")
            return jsonify(cached_result)
        
        # Calculate task status distribution
        result = get_task_status_distribution(filters=filters)
        
        # Cache the result
        metrics_cache.set(cache_key, result)
        
        logger.info(f"Calculated task status distribution for filters: {filters}")
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error retrieving task status distribution: {str(e)}")
        raise


@metrics_blueprint.route('/task-priority-distribution', methods=['GET'])
@token_required
def get_task_priority_distribution_endpoint():
    """
    API endpoint to retrieve distribution of tasks by priority.
    
    Returns:
        JSON response with task priority distribution data
    """
    try:
        # Extract filter parameters from request
        filters = _extract_filters_from_request()
        
        # Generate cache key and check cache
        cache_key = metrics_cache.get_cache_key('task_priority_distribution', filters=filters)
        cached_result = metrics_cache.get(cache_key)
        
        if cached_result:
            logger.debug(f"Returning cached task priority distribution for filters: {filters}")
            return jsonify(cached_result)
        
        # Calculate task priority distribution
        result = get_task_priority_distribution(filters=filters)
        
        # Cache the result
        metrics_cache.set(cache_key, result)
        
        logger.info(f"Calculated task priority distribution for filters: {filters}")
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error retrieving task priority distribution: {str(e)}")
        raise


@metrics_blueprint.route('/project-progress', methods=['GET'])
@token_required
def get_project_progress_endpoint():
    """
    API endpoint to retrieve progress information for projects.
    
    Returns:
        JSON response with project progress data
    """
    try:
        # Extract project IDs from query parameters (comma-separated list)
        project_ids_param = request.args.get('project_ids')
        project_ids = _parse_comma_separated_list(project_ids_param)
        
        # Generate cache key and check cache
        cache_key = metrics_cache.get_cache_key('project_progress', project_ids=project_ids)
        cached_result = metrics_cache.get(cache_key)
        
        if cached_result:
            logger.debug(f"Returning cached project progress for project_ids: {project_ids}")
            return jsonify(cached_result)
        
        # Get project progress
        result = get_project_progress(project_ids=project_ids)
        
        # Cache the result
        metrics_cache.set(cache_key, result)
        
        logger.info(f"Retrieved project progress for project_ids: {project_ids}")
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error retrieving project progress: {str(e)}")
        raise


@metrics_blueprint.route('/user-productivity', methods=['GET'])
@token_required
@roles_required(['admin', 'manager'])
def get_user_productivity_endpoint():
    """
    API endpoint to retrieve productivity metrics for users.
    
    Returns:
        JSON response with user productivity data
    """
    try:
        # Extract user IDs from query parameters (comma-separated list)
        user_ids_param = request.args.get('user_ids')
        user_ids = _parse_comma_separated_list(user_ids_param)
        
        # Extract time period (default to month)
        time_period = request.args.get('time_period', 'month')
        
        # Generate cache key and check cache
        cache_key = metrics_cache.get_cache_key('user_productivity', user_ids=user_ids, time_period=time_period)
        cached_result = metrics_cache.get(cache_key)
        
        if cached_result:
            logger.debug(f"Returning cached user productivity for user_ids: {user_ids}, time_period: {time_period}")
            return jsonify(cached_result)
        
        # Get user productivity metrics
        result = get_user_productivity(user_ids=user_ids, time_period=time_period)
        
        # Cache the result
        metrics_cache.set(cache_key, result)
        
        logger.info(f"Retrieved user productivity for user_ids: {user_ids}, time_period: {time_period}")
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error retrieving user productivity: {str(e)}")
        raise


@metrics_blueprint.route('/task-completion-trend', methods=['GET'])
@token_required
def get_task_completion_trend_endpoint():
    """
    API endpoint to retrieve time-series data of task completions.
    
    Returns:
        JSON response with task completion trend data
    """
    try:
        # Extract filter parameters from request
        filters = _extract_filters_from_request()
        
        # Extract time period (default to month)
        time_period = request.args.get('time_period', 'month')
        
        # Extract interval (default to day)
        interval = request.args.get('interval', 'day')
        
        # Generate cache key and check cache
        cache_key = metrics_cache.get_cache_key('task_completion_trend', 
                                              filters=filters, 
                                              time_period=time_period,
                                              interval=interval)
        cached_result = metrics_cache.get(cache_key)
        
        if cached_result:
            logger.debug(f"Returning cached task completion trend for filters: {filters}")
            return jsonify(cached_result)
        
        # Get task completion trend data
        result = get_task_completion_trend(filters=filters, time_period=time_period, interval=interval)
        
        # Cache the result
        metrics_cache.set(cache_key, result)
        
        logger.info(f"Retrieved task completion trend for filters: {filters}")
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error retrieving task completion trend: {str(e)}")
        raise


@metrics_blueprint.route('/overdue-tasks-count', methods=['GET'])
@token_required
def get_overdue_tasks_count_endpoint():
    """
    API endpoint to retrieve count of overdue tasks.
    
    Returns:
        JSON response with overdue tasks count
    """
    try:
        # Extract filter parameters from request
        filters = _extract_filters_from_request()
        
        # Generate cache key and check cache
        cache_key = metrics_cache.get_cache_key('overdue_tasks_count', filters=filters)
        cached_result = metrics_cache.get(cache_key)
        
        if cached_result:
            logger.debug(f"Returning cached overdue tasks count for filters: {filters}")
            return jsonify(cached_result)
        
        # Get overdue tasks count
        result = get_overdue_tasks_count(filters=filters)
        
        # Cache the result
        metrics_cache.set(cache_key, result)
        
        logger.info(f"Retrieved overdue tasks count for filters: {filters}")
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error retrieving overdue tasks count: {str(e)}")
        raise


@metrics_blueprint.route('/upcoming-due-tasks', methods=['GET'])
@token_required
def get_upcoming_due_tasks_endpoint():
    """
    API endpoint to retrieve tasks approaching their due dates.
    
    Returns:
        JSON response with upcoming due tasks data
    """
    try:
        # Extract number of days parameter (default to 7)
        days = int(request.args.get('days', 7))
        
        # Extract filter parameters from request
        filters = _extract_filters_from_request()
        
        # Generate cache key and check cache
        cache_key = metrics_cache.get_cache_key('upcoming_due_tasks', days=days, filters=filters)
        cached_result = metrics_cache.get(cache_key)
        
        if cached_result:
            logger.debug(f"Returning cached upcoming due tasks for days: {days}, filters: {filters}")
            return jsonify(cached_result)
        
        # Get upcoming due tasks
        result = get_upcoming_due_tasks(days=days, filters=filters)
        
        # Cache the result
        metrics_cache.set(cache_key, result)
        
        logger.info(f"Retrieved upcoming due tasks for days: {days}, filters: {filters}")
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error retrieving upcoming due tasks: {str(e)}")
        raise


@metrics_blueprint.route('/project-completion-percentage/<project_id>', methods=['GET'])
@token_required
def calculate_project_completion_percentage_endpoint(project_id):
    """
    API endpoint to retrieve completion percentage for a project.
    
    Returns:
        JSON response with project completion percentage data
    """
    try:
        # Generate cache key and check cache
        cache_key = metrics_cache.get_cache_key('project_completion_percentage', project_id=project_id)
        cached_result = metrics_cache.get(cache_key)
        
        if cached_result:
            logger.debug(f"Returning cached project completion percentage for project_id: {project_id}")
            return jsonify(cached_result)
        
        # Calculate project completion percentage
        result = calculate_project_completion_percentage(project_id=project_id)
        
        # Cache the result
        metrics_cache.set(cache_key, result)
        
        logger.info(f"Calculated project completion percentage for project_id: {project_id}")
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error calculating project completion percentage: {str(e)}")
        raise


@metrics_blueprint.route('/summary', methods=['GET'])
@token_required
def get_metrics_summary_endpoint():
    """
    API endpoint to retrieve a comprehensive summary of key metrics.
    
    Returns:
        JSON response with comprehensive metrics summary
    """
    try:
        # Extract filter parameters from request
        filters = _extract_filters_from_request()
        
        # Extract time period (default to month)
        time_period = request.args.get('time_period', 'month')
        
        # Generate cache key and check cache
        cache_key = metrics_cache.get_cache_key('metrics_summary', filters=filters, time_period=time_period)
        cached_result = metrics_cache.get(cache_key)
        
        if cached_result:
            logger.debug(f"Returning cached metrics summary for filters: {filters}, time_period: {time_period}")
            return jsonify(cached_result)
        
        # Get metrics summary
        result = get_metrics_summary(filters=filters, time_period=time_period)
        
        # Cache the result
        metrics_cache.set(cache_key, result)
        
        logger.info(f"Retrieved metrics summary for filters: {filters}, time_period: {time_period}")
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error retrieving metrics summary: {str(e)}")
        raise


def _extract_filters_from_request():
    """
    Helper function to extract filter parameters from request query string.
    
    Returns:
        dict: Dictionary of filter parameters
    """
    filters = {}
    
    # Extract common filter parameters
    if request.args.get('project_id'):
        filters['project_id'] = request.args.get('project_id')
    
    if request.args.get('user_id'):
        filters['user_id'] = request.args.get('user_id')
    
    if request.args.get('status'):
        filters['status'] = request.args.get('status')
    
    if request.args.get('priority'):
        filters['priority'] = request.args.get('priority')
    
    if request.args.get('organization_id'):
        filters['organization_id'] = request.args.get('organization_id')
    
    return filters


def _parse_comma_separated_list(value):
    """
    Helper function to parse comma-separated parameter into a list.
    
    Args:
        value (str): Comma-separated string value
        
    Returns:
        list: List of values from comma-separated string
    """
    if not value:
        return []
    
    return [item.strip() for item in value.split(',') if item.strip()]