#!/bin/bash

# Integration Hub Management Script
# Provides utilities for managing integration connections and data processing

set -e

# Configuration
API_BASE_URL="http://localhost:5001/api"
CONFIG_DIR="config"
DATA_DIR="data"
LOGS_DIR="logs"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Create required directories
create_dirs() {
    mkdir -p "$CONFIG_DIR" "$DATA_DIR" "$LOGS_DIR"
}

# Logging functions
log_info() {
    echo -e "${CYAN}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOGS_DIR/integration.log"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOGS_DIR/integration.log"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOGS_DIR/integration.log"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOGS_DIR/integration.log"
}

log_debug() {
    if [[ "${DEBUG:-false}" == "true" ]]; then
        echo -e "${PURPLE}[DEBUG]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOGS_DIR/integration.log"
    fi
}

# Check if required tools are installed
check_dependencies() {
    local deps=("curl" "jq")
    local missing=()
    
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            missing+=("$dep")
        fi
    done
    
    if [[ ${#missing[@]} -gt 0 ]]; then
        log_error "Missing required dependencies: ${missing[*]}"
        log_info "Please install: sudo apt-get install ${missing[*]}"
        exit 1
    fi
}

# API helper function
api_call() {
    local method="$1"
    local endpoint="$2"
    local data="$3"
    local response_file="$LOGS_DIR/api_response.json"
    
    log_debug "Making $method request to $API_BASE_URL$endpoint"
    
    if [[ -n "$data" ]]; then
        curl -s -X "$method" \
             -H "Content-Type: application/json" \
             -d "$data" \
             "$API_BASE_URL$endpoint" > "$response_file"
    else
        curl -s -X "$method" \
             -H "Content-Type: application/json" \
             "$API_BASE_URL$endpoint" > "$response_file"
    fi
    
    local status_code=$(curl -s -o /dev/null -w "%{http_code}" -X "$method" \
                        -H "Content-Type: application/json" \
                        ${data:+-d "$data"} \
                        "$API_BASE_URL$endpoint")
    
    if [[ "$status_code" -ge 200 && "$status_code" -lt 300 ]]; then
        log_debug "API call successful (HTTP $status_code)"
        cat "$response_file"
    else
        log_error "API call failed with status $status_code"
        cat "$response_file"
        return 1
    fi
}

# List all integrations
list_integrations() {
    log_info "Fetching integration list..."
    
    if response=$(api_call "GET" "/integrations"); then
        echo "$response" | jq -r '.[] | "ID: \(.id) | Name: \(.name) | Status: \(.status) | Type: \(.type)"'
        log_success "Integration list retrieved successfully"
    else
        log_error "Failed to retrieve integration list"
        return 1
    fi
}

# Get integration status
get_integration_status() {
    local integration_id="$1"
    
    if [[ -z "$integration_id" ]]; then
        log_error "Integration ID is required"
        return 1
    fi
    
    log_info "Getting status for integration: $integration_id"
    
    if response=$(api_call "GET" "/integrations/$integration_id/status"); then
        echo "$response" | jq '.'
        log_success "Status retrieved for integration $integration_id"
    else
        log_error "Failed to get status for integration $integration_id"
        return 1
    fi
}

# Start integration
start_integration() {
    local integration_id="$1"
    
    if [[ -z "$integration_id" ]]; then
        log_error "Integration ID is required"
        return 1
    fi
    
    log_info "Starting integration: $integration_id"
    
    if response=$(api_call "POST" "/integrations/$integration_id/start"); then
        log_success "Integration $integration_id started successfully"
        echo "$response" | jq '.'
    else
        log_error "Failed to start integration $integration_id"
        return 1
    fi
}

# Stop integration
stop_integration() {
    local integration_id="$1"
    
    if [[ -z "$integration_id" ]]; then
        log_error "Integration ID is required"
        return 1
    fi
    
    log_info "Stopping integration: $integration_id"
    
    if response=$(api_call "POST" "/integrations/$integration_id/stop"); then
        log_success "Integration $integration_id stopped successfully"
        echo "$response" | jq '.'
    else
        log_error "Failed to stop integration $integration_id"
        return 1
    fi
}

# Create new integration
create_integration() {
    local config_file="$1"
    
    if [[ -z "$config_file" ]]; then
        log_error "Configuration file is required"
        return 1
    fi
    
    if [[ ! -f "$config_file" ]]; then
        log_error "Configuration file not found: $config_file"
        return 1
    fi
    
    log_info "Creating new integration from config: $config_file"
    
    local config_data=$(cat "$config_file")
    
    if response=$(api_call "POST" "/integrations" "$config_data"); then
        local integration_id=$(echo "$response" | jq -r '.id')
        log_success "Integration created successfully with ID: $integration_id"
        echo "$response" | jq '.'
    else
        log_error "Failed to create integration"
        return 1
    fi
}

# Delete integration
delete_integration() {
    local integration_id="$1"
    
    if [[ -z "$integration_id" ]]; then
        log_error "Integration ID is required"
        return 1
    fi
    
    log_warning "Deleting integration: $integration_id"
    read -p "Are you sure you want to delete integration $integration_id? (y/N): " confirm
    
    if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
        log_info "Delete operation cancelled"
        return 0
    fi
    
    if response=$(api_call "DELETE" "/integrations/$integration_id"); then
        log_success "Integration $integration_id deleted successfully"
    else
        log_error "Failed to delete integration $integration_id"
        return 1
    fi
}

# Process data for integration
process_data() {
    local integration_id="$1"
    local data_file="$2"
    
    if [[ -z "$integration_id" || -z "$data_file" ]]; then
        log_error "Integration ID and data file are required"
        return 1
    fi
    
    if [[ ! -f "$data_file" ]]; then
        log_error "Data file not found: $data_file"
        return 1
    fi
    
    log_info "Processing data file $data_file for integration $integration_id"
    
    local data=$(cat "$data_file")
    
    if response=$(api_call "POST" "/integrations/$integration_id/process" "$data"); then
        log_success "Data processed successfully for integration $integration_id"
        echo "$response" | jq '.'
    else
        log_error "Failed to process data for integration $integration_id"
        return 1
    fi
}

# Monitor integration health
monitor_health() {
    log_info "Checking system health..."
    
    if response=$(api_call "GET" "/health"); then
        local status=$(echo "$response" | jq -r '.status')
        local uptime=$(echo "$response" | jq -r '.uptime')
        local active_integrations=$(echo "$response" | jq -r '.active_integrations')
        
        if [[ "$status" == "healthy" ]]; then
            log_success "System is healthy - Uptime: $uptime, Active Integrations: $active_integrations"
        else
            log_warning "System status: $status"
        fi
        
        echo "$response" | jq '.'
    else
        log_error "Failed to check system health"
        return 1
    fi
}

# Generate sample configuration
generate_sample_config() {
    local config_file="$CONFIG_DIR/sample_integration.json"
    
    log_info "Generating sample configuration file: $config_file"
    
    cat > "$config_file" << EOF
{
  "name": "Sample Integration",
  "type": "api",
  "description": "Sample integration configuration",
  "config": {
    "endpoint": "https://api.example.com/v1",
    "auth_type": "bearer_token",
    "token": "your_api_token_here",
    "poll_interval": 300,
    "retry_attempts": 3
  },
  "data_mapping": {
    "input_format": "json",
    "output_format": "json",
    "transformations": []
  },
  "triggers": {
    "schedule": "*/5 * * * *",
    "webhook": false
  }
}
EOF
    
    log_success "Sample configuration generated: $config_file"
}

# Show usage information
show_usage() {
    cat << EOF
${BLUE}Integration Hub Management Script${NC}

Usage: $0 [command] [options]

Commands:
  ${GREEN}list${NC}                          List all integrations
  ${GREEN}status${NC} <integration_id>       Get integration status
  ${GREEN}start${NC} <integration_id>        Start an integration
  ${GREEN}stop${NC} <integration_id>         Stop an integration
  ${GREEN}create${NC} <config_file>          Create new integration from config
  ${GREEN}delete${NC} <integration_id>       Delete an integration
  ${GREEN}process${NC} <id> <data_file>      Process data for integration
  ${GREEN}health${NC}                        Check system health
  ${GREEN}sample-config${NC}                Generate sample configuration
  ${GREEN}help${NC}                          Show this usage information

Options:
  ${YELLOW}--debug${NC}                      Enable debug logging
  ${YELLOW}--api-url${NC} <url>             Override API base URL

Examples:
  $0 list
  $0 status my-integration-001
  $0 create config/my_integration.json
  $0 process my-integration-001 data/input.json
  $0 --debug health

Configuration files should be placed in the '$CONFIG_DIR' directory.
Data files should be placed in the '$DATA_DIR' directory.
Logs are written to the '$LOGS_DIR' directory.
EOF
}

# Main script logic
main() {
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --debug)
                export DEBUG=true
                shift
                ;;
            --api-url)
                API_BASE_URL="$2"
                shift 2
                ;;
            *)
                break
                ;;
        esac
    done
    
    local command="$1"
    
    # Create required directories
    create_dirs
    
    # Check dependencies
    check_dependencies
    
    log_info "Starting Integration Hub Management Script"
    log_debug "API Base URL: $API_BASE_URL"
    
    case "$command" in
        list)
            list_integrations
            ;;
        status)
            get_integration_status "$2"
            ;;
        start)
            start_integration "$2"
            ;;
        stop)
            stop_integration "$2"
            ;;
        create)
            create_integration "$2"
            ;;
        delete)
            delete_integration "$2"
            ;;
        process)
            process_data "$2" "$3"
            ;;
        health)
            monitor_health
            ;;
        sample-config)
            generate_sample_config
            ;;
        help|--help|-h)
            show_usage
            ;;
        "")
            log_error "No command specified"
            show_usage
            exit 1
            ;;
        *)
            log_error "Unknown command: $command"
            show_usage
            exit 1
            ;;
    esac
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi