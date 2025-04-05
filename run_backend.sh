#!/bin/bash

# AI Kids Challenge Game - Backend Server Manager
# Script to start, stop, and restart the backend API

# Colors for better output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKEND_PORT=8000

# Print header
print_header() {
  echo -e "\n${BLUE}=========================================${NC}"
  echo -e "${BLUE}   AI Kids Challenge Game - Backend - $1${NC}"
  echo -e "${BLUE}=========================================${NC}\n"
}

# Check if a port is in use
is_port_in_use() {
  local port=$1
  if command -v lsof >/dev/null 2>&1; then
    # Only consider connections in LISTEN state
    lsof -i:"$port" -sTCP:LISTEN >/dev/null 2>&1
    return $?
  else
    # Alternative check if lsof is not available
    netstat -tuln | grep -q ":$port "
    return $?
  fi
}

# Free up a port if it's in use
free_port() {
  local port=$1
  echo -e "${YELLOW}Checking if port $port is in use...${NC}"
  
  if is_port_in_use "$port"; then
    echo -e "${YELLOW}Port $port is in use. Attempting to free it...${NC}"
    
    if command -v lsof >/dev/null 2>&1; then
      local pid=$(lsof -t -i:"$port")
      if [ -n "$pid" ]; then
        echo -e "${YELLOW}Killing process $pid using port $port${NC}"
        kill -9 "$pid" 2>/dev/null
        sleep 1
      fi
    else
      # More aggressive approach if lsof is not available
      echo -e "${YELLOW}Using general process termination for port $port${NC}"
      pkill -f "uvicorn.*--port $port" 2>/dev/null
      pkill -f "uvicorn.*:$port" 2>/dev/null
      sleep 1
    fi
    
    if is_port_in_use "$port"; then
      echo -e "${RED}Warning: Port $port is still in use. You may need to manually terminate the process.${NC}"
    else
      echo -e "${GREEN}Port $port is now free.${NC}"
    fi
  else
    echo -e "${GREEN}Port $port is available.${NC}"
  fi
}

# Start backend service
start_backend() {
  print_header "Starting Service"
  
  # Starting from project root directory
  PROJECT_ROOT=$(pwd)
  
  # Free up the port if it's in use
  free_port $BACKEND_PORT
  
  # Start the backend
  echo -e "${YELLOW}Starting backend server...${NC}"
  if [ -d "$PROJECT_ROOT/backend" ]; then
    cd "$PROJECT_ROOT/backend" 
    
    # Check for virtual environment and activate it
    if [ -d "venv" ]; then
      echo -e "${YELLOW}Activating virtual environment...${NC}"
      source venv/bin/activate
      
      # Start the server with the virtual environment's Python (foreground)
      echo -e "${GREEN}Server starting in foreground. Press CTRL+C to stop.${NC}"
      python -m uvicorn main:app --host 0.0.0.0 --port $BACKEND_PORT
    else
      echo -e "${YELLOW}Virtual environment not found, trying with system Python...${NC}"
      echo -e "${GREEN}Server starting in foreground. Press CTRL+C to stop.${NC}"
      python -m uvicorn main:app --host 0.0.0.0 --port $BACKEND_PORT
    fi
  else
    echo -e "${RED}Error: Backend directory not found at $PROJECT_ROOT/backend${NC}"
    return 1
  fi
}

# Stop backend service
stop_backend() {
  print_header "Stopping Service"
  
  # Check if backend PID file exists
  if [ -f backend_pid ]; then
    backend_pid=$(cat backend_pid)
    echo -e "${YELLOW}Stopping backend (PID: $backend_pid)...${NC}"
    kill $backend_pid 2>/dev/null || pkill -f "uvicorn main:app"
    rm backend_pid
    echo -e "${GREEN}Backend stopped.${NC}"
  else
    echo -e "${YELLOW}Stopping backend servers...${NC}"
    pkill -f "uvicorn main:app"
    echo -e "${GREEN}Backend stopped.${NC}"
  fi
}

# Check status of backend service
check_backend_status() {
  print_header "Service Status"
  
  # Check backend
  if curl -s http://localhost:$BACKEND_PORT/api/players >/dev/null; then
    echo -e "Backend: ${GREEN}Running${NC} at http://localhost:$BACKEND_PORT"
  else
    echo -e "Backend: ${RED}Not running${NC}"
  fi
}

# Print usage information
print_usage() {
  echo -e "Usage: $0 {start|stop|restart|status}"
  echo -e "  start   - Start backend service"
  echo -e "  stop    - Stop backend service"
  echo -e "  restart - Restart backend service"
  echo -e "  status  - Check if backend service is running"
}

# Main script logic
case "$1" in
  start)
    start_backend
    ;;
  stop)
    stop_backend
    ;;
  restart)
    stop_backend
    sleep 2
    start_backend
    ;;
  status)
    check_backend_status
    ;;
  *)
    print_header "Welcome"
    print_usage
    exit 1
esac

exit 0 