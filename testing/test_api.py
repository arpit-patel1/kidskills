#!/usr/bin/env python3
"""
Test script for Kids Challenge Game API endpoints.
This script tests the backend API endpoints to ensure they're working correctly.
"""

import requests
import json
import sys
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

def test_players_api():
    """Test the players API endpoints."""
    print_header("Testing Players API")
    
    # Get all players
    print("\n1. Getting all players...")
    response = requests.get(f"{BASE_URL}/players")
    print_response(response)
    
    if response.status_code == 200:
        players = response.json()
        if players and len(players) > 0:
            # Get the first player for further testing
            return players[0]
    
    print("❌ No players found. Please ensure the database is populated.")
    return None

def test_question_generation(player):
    """Test the question generation API endpoint."""
    print_header("Testing Question Generation API")
    
    # Generate a question
    print("\n1. Generating a Math question (Easy difficulty)...")
    payload = {
        "player_id": player["id"],
        "subject": "math",
        "difficulty": "easy",
        "question_type": "multiple-choice"
    }
    
    response = requests.post(f"{BASE_URL}/challenges/generate", json=payload)
    print_response(response)
    
    if response.status_code == 200:
        question = response.json()
        print("✅ Question generated successfully!")
        return question
    
    print("❌ Failed to generate question.")
    return None

def test_answer_submission(player, question):
    """Test the answer submission API endpoint."""
    print_header("Testing Answer Submission API")
    
    if not question:
        print("❌ No question available for testing answer submission.")
        return
    
    # Get the correct answer (for testing purposes)
    correct_answer = question.get("answer", "")
    
    # Submit answer (correct answer)
    print("\n1. Submitting correct answer...")
    payload = {
        "player_id": player["id"],
        "question_id": question["id"],
        "answer": correct_answer
    }
    
    response = requests.post(f"{BASE_URL}/challenges/submit", json=payload)
    print_response(response)
    
    # Submit answer (incorrect answer)
    print("\n2. Submitting incorrect answer...")
    # Choose an incorrect answer
    choices = question.get("choices", [])
    incorrect_answer = next((c for c in choices if c != correct_answer), "wrong answer")
    
    payload = {
        "player_id": player["id"],
        "question_id": question["id"],
        "answer": incorrect_answer
    }
    
    response = requests.post(f"{BASE_URL}/challenges/submit", json=payload)
    print_response(response)

def main():
    """Run the API tests."""
    print_header("Kids Challenge Game API Test")
    
    # Check if the server is running
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code != 200:
            print("❌ API server is not responding correctly.")
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        print("❌ API server is not running. Please start the server at http://localhost:8000")
        sys.exit(1)
    
    # Test player API
    player = test_players_api()
    if not player:
        sys.exit(1)
    
    # Test question generation
    question = test_question_generation(player)
    
    # Test answer submission
    test_answer_submission(player, question)
    
    print_header("Test Complete")

if __name__ == "__main__":
    main() 