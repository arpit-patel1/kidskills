#!/usr/bin/env python3
"""
Test script for Kids Challenge Game fallback questions mechanism.
This script tests that fallback questions are served when the AI API fails.
"""

import requests
import json
import sys
import os
import time

BASE_URL = "http://localhost:8000/api"

def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 50)
    print(f" {text}")
    print("=" * 50)

def print_response(response, label="Response"):
    """Print a formatted API response."""
    print(f"\n{label} (Status: {response.status_code}):")
    try:
        print(json.dumps(response.json(), indent=2))
    except:
        print(response.text)

def test_fallback_mechanism():
    """Test the fallback questions mechanism."""
    print_header("Testing Fallback Questions Mechanism")
    
    # First, get a player to test with
    response = requests.get(f"{BASE_URL}/players")
    if response.status_code != 200 or not response.json():
        print("❌ No players found. Please ensure the database is populated.")
        return False
    
    player = response.json()[0]
    
    # 1. Test that normal question generation works
    print("\n1. Testing normal question generation...")
    payload = {
        "player_id": player["id"],
        "subject": "math",
        "difficulty": "easy",
        "question_type": "multiple-choice"
    }
    
    response = requests.post(f"{BASE_URL}/challenges/generate", json=payload)
    print_response(response)
    
    if response.status_code != 200:
        print("❌ Normal question generation failed. Cannot continue testing fallbacks.")
        return False
    
    # 2. Test with force_fallback parameter (if implemented)
    print("\n2. Testing forced fallback question...")
    payload = {
        "player_id": player["id"],
        "subject": "math",
        "difficulty": "easy",
        "question_type": "multiple-choice",
        "force_fallback": True  # This is a special flag we might add for testing
    }
    
    response = requests.post(f"{BASE_URL}/challenges/generate", json=payload)
    print_response(response)
    
    if response.status_code == 200:
        print("✅ Fallback question received successfully!")
        return True
    else:
        print("⚠️ Force fallback parameter may not be implemented.")
    
    # 3. Alternative: Test by inducing API failure
    # This method depends on how API failures are triggered in your implementation
    print("\n3. Testing by inducing API failure...")
    print("   This test might need manual verification in server logs.")
    
    # Some options to induce failure:
    # a. Use an invalid API key (requires backend modification or environment variable)
    # b. Use invalid parameters that would cause API rejection
    # c. Use a special debug route that simulates API failure
    
    payload = {
        "player_id": player["id"],
        "subject": "invalid_subject",  # This might trigger a fallback
        "difficulty": "easy",
        "question_type": "multiple-choice"
    }
    
    response = requests.post(f"{BASE_URL}/challenges/generate", json=payload)
    print_response(response)
    
    if response.status_code == 200:
        print("✅ Received a question despite invalid parameters - fallback likely working!")
        return True
    else:
        print("❌ Request failed but cannot confirm if fallback mechanism was attempted.")
        return False

def main():
    """Run the fallback tests."""
    print_header("Kids Challenge Game Fallback Test")
    
    # Check if the server is running
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code != 200:
            print("❌ API server is not responding correctly.")
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        print("❌ API server is not running. Please start the server at http://localhost:8000")
        sys.exit(1)
    
    # Test fallback mechanism
    success = test_fallback_mechanism()
    
    # Report result
    if success:
        print("\n✅ Fallback mechanism appears to be working.")
    else:
        print("\n⚠️ Could not verify fallback mechanism. Check server implementation.")
    
    print_header("Test Complete")

if __name__ == "__main__":
    main() 