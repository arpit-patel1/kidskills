# AI Kids Challenge Game

A web-based educational game that uses AI to generate math and English challenges tailored for kids based on their grade level and learning preferences.

## Features

- Player selection and customizable settings
- AI-powered question generation for Math and English
- Multiple choice questions with immediate feedback
- Visual effects for correct answers including confetti
- Score tracking and achievement streaks
- Responsive design for various devices

## System Requirements

- Python 3.9+ with pip
- Node.js 14+ with npm
- Internet connection (for AI-powered questions)

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd kids-challenge-game
   ```

2. Set up the backend:
   ```
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Add your OpenRouter API key to the `.env` file:
   ```
   OPENROUTER_API_KEY=your_api_key_here
   ```

4. Set up the frontend:
   ```
   cd ../frontend
   npm install
   ```

## Running the Game

Use the included shell script to start/stop the application:

```
# Start the application
./run_game.sh start

# Stop the application
./run_game.sh stop

# Check status
./run_game.sh status

# Restart services
./run_game.sh restart
```

When started, the game will be available at:
- Local access: http://localhost:3000
- Network access: http://<your-ip-address>:3000

## Usage Guide

1. **Player Selection**: Choose a player from the available list.
2. **Game Settings**: Configure subject (Math/English) and difficulty level.
3. **Game Play**: Answer questions and receive immediate feedback.
4. **Achievements**: Earn badges for answer streaks.
5. **Game Completion**: After 5 questions, view your final score and play again.

## Development

- Backend API runs on: http://localhost:8000
- Frontend development server: http://localhost:3000
- Testing scripts are available in the `testing` directory

## Credits

- Created for the AI Kids Challenge
- Uses OpenRouter for AI question generation