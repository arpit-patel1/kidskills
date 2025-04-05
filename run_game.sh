#!/bin/bash

# Kids Challenge Game Launcher
# Script to start, stop, and restart both backend and frontend services

# Colors for better output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKEND_SCRIPT="./run_backend.sh"
FRONTEND_SCRIPT="./run_frontend.sh"

# Print header
print_header() {
  echo -e "\n${BLUE}=========================================${NC}"
  echo -e "${BLUE}   AI Kids Challenge Game - $1${NC}"
  echo -e "${BLUE}=========================================${NC}\n"
}

# Make scripts executable if they aren't already
ensure_executables() {
  if [ ! -x "$BACKEND_SCRIPT" ]; then
    chmod +x "$BACKEND_SCRIPT"
  fi
  
  if [ ! -x "$FRONTEND_SCRIPT" ]; then
    chmod +x "$FRONTEND_SCRIPT"
  fi
}

# Start both services
start_services() {
  print_header "Starting Services"
  
  # Ensure scripts are executable
  ensure_executables
  
  # Start backend
  echo -e "${YELLOW}Starting backend service...${NC}"
  $BACKEND_SCRIPT start
  
  # Start frontend
  echo -e "\n${YELLOW}Starting frontend service...${NC}"
  $FRONTEND_SCRIPT start
  
  print_header "All Services Started"
  echo -e "Both backend and frontend services are now running."
  echo -e "Use '$0 stop' to stop all services."
}

# Stop both services
stop_services() {
  print_header "Stopping Services"
  
  # Ensure scripts are executable
  ensure_executables
  
  # Stop frontend first (depends on backend)
  echo -e "${YELLOW}Stopping frontend service...${NC}"
  $FRONTEND_SCRIPT stop
  
  # Then stop backend
  echo -e "\n${YELLOW}Stopping backend service...${NC}"
  $BACKEND_SCRIPT stop
  
  print_header "All Services Stopped"
  echo -e "Both backend and frontend services have been stopped."
}

# Check status of both services
check_status() {
  print_header "Service Status"
  
  # Check backend status
  echo -e "${YELLOW}Checking backend status...${NC}"
  $BACKEND_SCRIPT status
  
  # Check frontend status
  echo -e "\n${YELLOW}Checking frontend status...${NC}"
  $FRONTEND_SCRIPT status
}

# Print usage information
print_usage() {
  echo -e "Usage: $0 {start|stop|restart|status}"
  echo -e "  start   - Start both backend and frontend services"
  echo -e "  stop    - Stop all services"
  echo -e "  restart - Restart all services"
  echo -e "  status  - Check status of all services"
  echo -e "\nTo manage services individually, use:"
  echo -e "  ${YELLOW}$BACKEND_SCRIPT${NC} or ${YELLOW}$FRONTEND_SCRIPT${NC} directly."
}

# Main script logic
case "$1" in
  start)
    start_services
    ;;
  stop)
    stop_services
    ;;
  restart)
    stop_services
    sleep 2
    start_services
    ;;
  status)
    check_status
    ;;
  *)
    print_header "Welcome"
    print_usage
    exit 1
esac

exit 0
