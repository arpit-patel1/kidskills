#!/bin/bash

# AI Kids Challenge Game - Frontend Server Manager
# Script to start, stop, and restart the frontend application

# Colors for better output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
FRONTEND_PORT=3000
# Get host IP address - fallback to localhost if not available
HOST_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
if [ -z "$HOST_IP" ]; then
  HOST_IP="localhost"
fi

# Print header
print_header() {
  echo -e "\n${BLUE}=========================================${NC}"
  echo -e "${BLUE}   AI Kids Challenge Game - Frontend - $1${NC}"
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
      pkill -f "node.*start" 2>/dev/null
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

# Start frontend service
start_frontend() {
  print_header "Starting Service"
  
  # Starting from project root directory
  PROJECT_ROOT=$(pwd)
  
  # Free up the port if it's in use
  free_port $FRONTEND_PORT
  
  # Start the frontend
  echo -e "${YELLOW}Starting frontend server...${NC}"
  if [ -d "$PROJECT_ROOT/frontend" ]; then
    cd "$PROJECT_ROOT/frontend" 
    echo -e "${GREEN}Server starting in foreground. Press CTRL+C to stop.${NC}"
    npm start
  else
    echo -e "${RED}Error: Frontend directory not found at $PROJECT_ROOT/frontend${NC}"
    return 1
  fi
}

# Stop frontend service
stop_frontend() {
  print_header "Stopping Service"
  
  # Check if frontend PID file exists
  if [ -f frontend_pid ]; then
    frontend_pid=$(cat frontend_pid)
    echo -e "${YELLOW}Stopping frontend (PID: $frontend_pid)...${NC}"
    kill $frontend_pid 2>/dev/null || pkill -f "node.*start"
    rm frontend_pid
    echo -e "${GREEN}Frontend stopped.${NC}"
  else
    echo -e "${YELLOW}Stopping frontend servers...${NC}"
    pkill -f "node.*start"
    echo -e "${GREEN}Frontend stopped.${NC}"
  fi
}

# Check status of frontend service
check_frontend_status() {
  print_header "Service Status"
  
  # Check frontend
  if curl -s http://localhost:$FRONTEND_PORT >/dev/null; then
    echo -e "Frontend: ${GREEN}Running${NC} at http://localhost:$FRONTEND_PORT"
  else
    echo -e "Frontend: ${RED}Not running${NC}"
  fi
}

# Print usage information
print_usage() {
  echo -e "Usage: $0 {start|stop|restart|status}"
  echo -e "  start   - Start frontend service"
  echo -e "  stop    - Stop frontend service"
  echo -e "  restart - Restart frontend service"
  echo -e "  status  - Check if frontend service is running"
}

# Main script logic
case "$1" in
  start)
    start_frontend
    ;;
  stop)
    stop_frontend
    ;;
  restart)
    stop_frontend
    sleep 2
    start_frontend
    ;;
  status)
    check_frontend_status
    ;;
  *)
    print_header "Welcome"
    print_usage
    exit 1
esac

exit 0 