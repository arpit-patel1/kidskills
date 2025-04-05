#!/bin/bash

# Colors for better output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Print header
print_header() {
  echo -e "\n${YELLOW}=================================${NC}"
  echo -e "${YELLOW} $1 ${NC}"
  echo -e "${YELLOW}=================================${NC}\n"
}

# Check if dependencies are installed
check_dependencies() {
  print_header "Checking Dependencies"
  
  # Check Python
  if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is not installed. Please install it to run the tests.${NC}"
    exit 1
  fi
  
  # Check if requests module is installed
  if ! python3 -c "import requests" &> /dev/null; then
    echo -e "${YELLOW}Python requests module not found. Installing...${NC}"
    pip install requests
  fi
  
  echo -e "${GREEN}All dependencies are installed.${NC}"
}

# Test if servers are running
check_servers() {
  print_header "Checking Servers"
  
  # Check if backend is running
  if ! curl -s http://localhost:8000/api/health &> /dev/null; then
    echo -e "${RED}Backend server is not running. Please start it at http://localhost:8000${NC}"
    return 1
  else
    echo -e "${GREEN}Backend server is running.${NC}"
  fi
  
  # Check if frontend is running
  if ! curl -s http://localhost:3000 &> /dev/null; then
    echo -e "${RED}Frontend server is not running. Please start it at http://localhost:3000${NC}"
    return 1
  else
    echo -e "${GREEN}Frontend server is running.${NC}"
  fi
  
  return 0
}

# Run API tests
run_api_tests() {
  print_header "Running API Tests"
  python3 test_api.py
  if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}API tests completed successfully.${NC}"
  else
    echo -e "\n${RED}API tests failed.${NC}"
  fi
}

# Run fallback tests
run_fallback_tests() {
  print_header "Running Fallback Tests"
  python3 test_fallbacks.py
  if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}Fallback tests completed successfully.${NC}"
  else
    echo -e "\n${RED}Fallback tests failed.${NC}"
  fi
}

# Print completion message with next steps
print_test_completion() {
  print_header "Testing Completed"
  echo -e "Next steps:"
  echo -e "1. Review the test results"
  echo -e "2. Update the integration_test_plan.md with your findings"
  echo -e "3. Fix any issues identified"
  echo -e "4. Manually test the UI for proper responsiveness"
}

# Main function
main() {
  # Change to the script directory
  cd "$(dirname "$0")"
  
  print_header "Kids Challenge Game Integration Tests"
  
  # Check dependencies
  check_dependencies
  
  # Check if servers are running
  check_servers
  if [ $? -ne 0 ]; then
    echo -e "\n${RED}Servers are not running. Please start both servers and try again.${NC}"
    exit 1
  fi
  
  # Run tests
  run_api_tests
  run_fallback_tests
  
  # Print completion message
  print_test_completion
}

# Run the main function
main 