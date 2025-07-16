#!/bin/bash
# File: database_testing.sh
# Path: Scripts/Testing/database_testing.sh
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-07-12
# Last Modified: 2025-07-12  06:36PM
# Description: Shell wrapper for automated SQLite ↔ MySQL round-trip testing

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Default values
MYSQL_HOST="localhost"
MYSQL_PORT="3306"
RESULTS_DIR="$PROJECT_ROOT/Results/Testing"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

function print_usage() {
    echo "Usage: $0 <command> [options]"
    echo
    echo "Commands:"
    echo "  roundtrip           Run round-trip test on database"
    echo "  report             Show test results"
    echo "  cleanup            Clean up test artifacts"
    echo "  verify-mysql       Verify MySQL connection"
    echo
    echo "Round-trip options:"
    echo "  --sqlite-db PATH         SQLite database to test (required)"
    echo "  --mysql-user USER        MySQL username (required)"
    echo "  --mysql-password PASS    MySQL password (required)"
    echo "  --mysql-host HOST        MySQL host (default: localhost)"
    echo "  --mysql-port PORT        MySQL port (default: 3306)"
    echo "  --test-name NAME         Test name (default: Round Trip Test)"
    echo "  --output FILE            Save results to JSON file"
    echo
    echo "Report options:"
    echo "  --test-id ID             Show specific test results"
    echo "  --latest                 Show latest test results"
    echo
    echo "Examples:"
    echo "  $0 roundtrip --sqlite-db Data/Databases/MyLibrary.db --mysql-user root --mysql-password secret"
    echo "  $0 report --latest"
    echo "  $0 verify-mysql --mysql-user root --mysql-password secret"
}

function log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

function log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

function log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

function log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

function verify_mysql() {
    local user="$1"
    local password="$2"
    local host="${3:-localhost}"
    local port="${4:-3306}"
    
    log_info "Verifying MySQL connection..."
    
    if command -v mysql >/dev/null 2>&1; then
        # Try with sudo mysql (auth_socket) first for root user
        if [[ "$user" == "root" ]]; then
            if sudo mysql -e "SELECT 1;" >/dev/null 2>&1; then
                log_success "MySQL connection successful (using sudo)"
                sudo mysql -e "SELECT VERSION();"
                return 0
            fi
        fi
        
        # Try with password
        if mysql -h"$host" -P"$port" -u"$user" -p"$password" -e "SELECT 1;" >/dev/null 2>&1; then
            log_success "MySQL connection successful"
            mysql -h"$host" -P"$port" -u"$user" -p"$password" -e "SELECT VERSION();"
            return 0
        else
            log_error "MySQL connection failed"
            return 1
        fi
    else
        log_error "MySQL client not found"
        return 1
    fi
}

function setup_results_dir() {
    mkdir -p "$RESULTS_DIR"
    log_info "Results directory: $RESULTS_DIR"
}

function run_roundtrip_test() {
    local sqlite_db=""
    local mysql_user=""
    local mysql_password=""
    local mysql_host="$MYSQL_HOST"
    local mysql_port="$MYSQL_PORT"
    local test_name="Round Trip Test"
    local output_file=""
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --sqlite-db)
                sqlite_db="$2"
                shift 2
                ;;
            --mysql-user)
                mysql_user="$2"
                shift 2
                ;;
            --mysql-password)
                mysql_password="$2"
                shift 2
                ;;
            --mysql-host)
                mysql_host="$2"
                shift 2
                ;;
            --mysql-port)
                mysql_port="$2"
                shift 2
                ;;
            --test-name)
                test_name="$2"
                shift 2
                ;;
            --output)
                output_file="$2"
                shift 2
                ;;
            *)
                log_error "Unknown option: $1"
                return 1
                ;;
        esac
    done
    
    # Validate required arguments
    if [[ -z "$sqlite_db" || -z "$mysql_user" || -z "$mysql_password" ]]; then
        log_error "Missing required arguments"
        print_usage
        return 1
    fi
    
    # Convert relative path to absolute
    if [[ ! "$sqlite_db" = /* ]]; then
        sqlite_db="$PROJECT_ROOT/$sqlite_db"
    fi
    
    # Check if SQLite database exists
    if [[ ! -f "$sqlite_db" ]]; then
        log_error "SQLite database not found: $sqlite_db"
        return 1
    fi
    
    # Setup results directory
    setup_results_dir
    
    # Generate output file if not specified
    if [[ -z "$output_file" ]]; then
        timestamp=$(date +"%Y%m%d_%H%M%S")
        output_file="$RESULTS_DIR/roundtrip_test_$timestamp.json"
    fi
    
    # Convert relative output path to absolute
    if [[ ! "$output_file" = /* ]]; then
        output_file="$PROJECT_ROOT/$output_file"
    fi
    
    log_info "Starting round-trip test..."
    log_info "SQLite database: $sqlite_db"
    log_info "MySQL connection: $mysql_user@$mysql_host:$mysql_port"
    log_info "Test name: $test_name"
    log_info "Output file: $output_file"
    
    # Verify MySQL connection first
    if ! verify_mysql "$mysql_user" "$mysql_password" "$mysql_host" "$mysql_port"; then
        return 1
    fi
    
    # Add sudo flag for root user
    sudo_flag=""
    if [[ "$mysql_user" == "root" ]]; then
        sudo_flag="--use-sudo --sudo-password 5790"
    fi
    
    # Run the Python test script
    python3 "$SCRIPT_DIR/RoundTripTester.py" \
        "$sqlite_db" \
        --mysql-user "$mysql_user" \
        --mysql-password "$mysql_password" \
        --mysql-host "$mysql_host" \
        --mysql-port "$mysql_port" \
        --test-name "$test_name" \
        --output "$output_file" \
        $sudo_flag
    
    if [[ $? -eq 0 ]]; then
        log_success "Round-trip test completed successfully"
        log_info "Results saved to: $output_file"
        
        # Show summary
        show_test_summary "$output_file"
    else
        log_error "Round-trip test failed"
        return 1
    fi
}

function show_test_summary() {
    local results_file="$1"
    
    if [[ ! -f "$results_file" ]]; then
        log_error "Results file not found: $results_file"
        return 1
    fi
    
    log_info "Test Summary:"
    
    # Extract key metrics using Python
    python3 -c "
import json
import sys

with open('$results_file', 'r') as f:
    data = json.load(f)

print(f\"Test Name: {data.get('test_name', 'Unknown')}\")
print(f\"Test ID: {data.get('test_id', 'Unknown')}\")
print(f\"Timestamp: {data.get('timestamp', 'Unknown')}\")

integrity = data.get('data_integrity', {})
print(f\"Row Count Integrity: {integrity.get('row_count_integrity_percent', 0):.1f}%\")
print(f\"Hash Integrity: {integrity.get('hash_integrity_percent', 0):.1f}%\")

original_counts = integrity.get('original_row_counts', {})
converted_counts = integrity.get('converted_row_counts', {})
total_original = sum(original_counts.values())
total_converted = sum(converted_counts.values())
print(f\"Total Rows: {total_original} → {total_converted}\")

performance = data.get('performance_metrics', {})
total_time = performance.get('total_test_seconds', 0)
print(f\"Total Test Time: {total_time:.1f} seconds\")

errors = data.get('errors', [])
if errors:
    print(f\"Errors: {len(errors)}\")
    for error in errors:
        print(f\"  - {error}\")
else:
    print(\"Errors: None\")
"
}

function show_report() {
    local test_id=""
    local show_latest=false
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --test-id)
                test_id="$2"
                shift 2
                ;;
            --latest)
                show_latest=true
                shift
                ;;
            *)
                log_error "Unknown option: $1"
                return 1
                ;;
        esac
    done
    
    setup_results_dir
    
    if [[ "$show_latest" == true ]]; then
        # Find latest test results
        latest_file=$(find "$RESULTS_DIR" -name "roundtrip_test_*.json" -type f -printf '%T@ %p\n' | sort -n | tail -1 | cut -d' ' -f2-)
        
        if [[ -n "$latest_file" ]]; then
            log_info "Latest test results:"
            show_test_summary "$latest_file"
        else
            log_warning "No test results found in $RESULTS_DIR"
        fi
    elif [[ -n "$test_id" ]]; then
        # Find specific test results
        results_file=$(find "$RESULTS_DIR" -name "*$test_id*.json" -type f | head -1)
        
        if [[ -n "$results_file" ]]; then
            log_info "Test results for ID $test_id:"
            show_test_summary "$results_file"
        else
            log_error "No test results found for ID: $test_id"
            return 1
        fi
    else
        # List all available tests
        log_info "Available test results:"
        find "$RESULTS_DIR" -name "roundtrip_test_*.json" -type f -printf '%T@ %f\n' | sort -n | while read timestamp filename; do
            echo "  - $filename"
        done
    fi
}

function cleanup() {
    log_info "Cleaning up test artifacts..."
    
    # Clean up MySQL test databases
    read -p "MySQL username: " mysql_user
    read -s -p "MySQL password: " mysql_password
    echo
    
    if verify_mysql "$mysql_user" "$mysql_password"; then
        mysql -u"$mysql_user" -p"$mysql_password" -e "SHOW DATABASES LIKE 'roundtrip_test_%';" | grep roundtrip_test | while read db; do
            log_info "Dropping database: $db"
            mysql -u"$mysql_user" -p"$mysql_password" -e "DROP DATABASE $db;"
        done
    fi
    
    # Clean up temporary SQLite files
    find /tmp -name "roundtrip_test_*.db" -type f -delete 2>/dev/null || true
    
    log_success "Cleanup completed"
}

# Main script logic
case "${1:-}" in
    roundtrip)
        shift
        run_roundtrip_test "$@"
        ;;
    report)
        shift
        show_report "$@"
        ;;
    cleanup)
        cleanup
        ;;
    verify-mysql)
        shift
        verify_mysql "$@"
        ;;
    *)
        print_usage
        exit 1
        ;;
esac