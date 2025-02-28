#!/usr/bin/env bash
#
# wait-for-it.sh - Wait for a host and port to become available before executing a command
#
# This script is useful in Docker environments to ensure services start in the correct order
# by verifying that dependencies are available before starting dependent services.
#
# Usage: ./wait-for-it.sh host:port [-s] [-t timeout] [-q] [-- command args]
#
# bash 4.0+ required

# Global variables
SCRIPTNAME=$(basename "$0")
TIMEOUT=15
QUIET=false
STRICT=false
CHILD=0
START_TS=$(date +%s)

# Display usage information
usage() {
    cat << USAGE >&2
Usage:
    $SCRIPTNAME host:port [-s] [-t timeout] [-q] [-- command args]
    -h HOST | --host=HOST       Host or IP to wait for
    -p PORT | --port=PORT       Port to wait for
    -s | --strict               Only execute command if connection succeeds
    -q | --quiet                Don't output any status messages
    -t TIMEOUT | --timeout=TIMEOUT
                                Timeout in seconds, zero for no timeout
    -- COMMAND ARGS             Command with args to execute after wait

Examples:
    $SCRIPTNAME example.com:8080 -t 30
    $SCRIPTNAME example.com:8080 -t 30 -s -- echo "Service is up!"
    $SCRIPTNAME db:5432 -s -- ./start-app.sh
USAGE
    exit 1
}

# Attempt to connect to a specified host and port
# Returns 0 if successful, 1 if connection fails
wait_for() {
    local host="$1"
    local port="$2"
    
    # Try to establish a TCP connection to the host:port
    (</dev/tcp/$host/$port) >/dev/null 2>&1
    
    # Return the result of the connection attempt
    return $?
}

# Handle timeout logic around the wait_for function
# Repeatedly tries to connect until success or timeout
wait_for_wrapper() {
    local host="$1"
    local port="$2"
    local timeout="$3"
    local quiet="$4"
    local start_ts="$(date +%s)"
    local end_ts=$((start_ts + timeout))
    
    if [[ $quiet == "false" ]]; then
        echo "Waiting for $host:$port for up to $timeout seconds..."
    fi
    
    # If timeout is 0, wait indefinitely
    if [[ $timeout -eq 0 ]]; then
        if [[ $quiet == "false" ]]; then
            echo "Waiting indefinitely for $host:$port"
        fi
        
        wait_for "$host" "$port"
        local result=$?
        
        if [[ $result -eq 0 ]]; then
            if [[ $quiet == "false" ]]; then
                echo "$host:$port is available"
            fi
            return 0
        else
            if [[ $quiet == "false" ]]; then
                echo "$host:$port is unavailable"
            fi
            return 1
        fi
    fi
    
    # Try until timeout
    while [[ $(date +%s) -lt $end_ts ]]; do
        wait_for "$host" "$port"
        local result=$?
        
        if [[ $result -eq 0 ]]; then
            if [[ $quiet == "false" ]]; then
                local elapsed=$(($(date +%s) - start_ts))
                echo "$host:$port is available after $elapsed seconds"
            fi
            return 0
        fi
        
        # Sleep before retrying
        sleep 1
    done
    
    if [[ $quiet == "false" ]]; then
        echo "Operation timed out after $timeout seconds waiting for $host:$port"
    fi
    return 1
}

# Parse command line arguments and control execution
main() {
    local hostport=""
    local host=""
    local port=""
    local command=""
    
    # Parse command line options
    while [[ $# -gt 0 ]]; do
        case "$1" in
            *:* )
                hostport="$1"
                shift 1
                ;;
            -q | --quiet)
                QUIET=true
                shift 1
                ;;
            -s | --strict)
                STRICT=true
                shift 1
                ;;
            -t)
                TIMEOUT="$2"
                if [[ $TIMEOUT == "" ]]; then
                    usage
                fi
                shift 2
                ;;
            --timeout=*)
                TIMEOUT="${1#*=}"
                shift 1
                ;;
            --)
                shift
                command="$@"
                break
                ;;
            -h | --help)
                usage
                ;;
            *)
                echo "Unknown argument: $1"
                usage
                ;;
        esac
    done
    
    # Extract host and port from hostport
    if [[ $hostport != "" ]]; then
        host="${hostport%:*}"
        port="${hostport#*:}"
    fi
    
    # Validate required parameters
    if [[ $host == "" || $port == "" ]]; then
        echo "Error: You need to provide a host and port to test."
        usage
    fi
    
    # Wait for service to be available
    wait_for_wrapper "$host" "$port" "$TIMEOUT" "$QUIET"
    local result=$?
    
    # Handle command execution based on result and strict mode
    if [[ $STRICT == "true" && $result -ne 0 ]]; then
        if [[ $QUIET == "false" ]]; then
            echo "Strict mode, refusing to execute command since $host:$port is unavailable"
        fi
        exit $result
    fi
    
    # Execute command if provided
    if [[ -n $command ]]; then
        if [[ $QUIET == "false" ]]; then
            echo "Executing command: $command"
        fi
        exec $command
    else
        exit $result
    fi
}

# Execute main with all arguments
main "$@"