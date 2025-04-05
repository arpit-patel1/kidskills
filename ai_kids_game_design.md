# AI Kids Challenge Game: Design Document

## 🎯 Overview

A web-based educational game that uses AI to generate math and English challenges tailored for kids based on their grade level and learning preferences. The platform will have both a frontend and a backend, with AI-powered question generation, and basic progress tracking.

**Weekend MVP Goal:** Create a playable version within 2 days for Grades 2 & 3 (Math/English) on a home network. Focus on core question generation and play loop.

---

## 🧱 System Architecture

### Frontend (Client)
- Built with: React
- Layout Structure:
  - **Sidebar Layout:** Implement a responsive sidebar for player selection and settings.
  - **Main Content Area:** Dedicated area for displaying questions and handling gameplay.
  - **Components:** Modular components for different functionalities (sidebar, player selection, game area, etc.).
- Responsibilities:
  - Allow user to select player (e.g., Kid 1 / Kid 2) and update settings (Grade 2/3, Math/English, Easy/Medium/Hard).
  - Fetch challenges from backend.
  - Display questions and accept answers.
  - Show feedback (incorporating UI/UX enhancements below).
  - Display session score.
- UI/UX Enhancements:
  - **Theme:** Powder blue color palette with complementary pastel colors, creating a calm, friendly environment suitable for all children. The theme includes light blues, mint greens, and soft peach accents.
  - **Sidebar Design:** 
    - Fixed width (250-300px) with proper padding (15-20px)
    - Contained dropdowns that fit within sidebar width
    - Use Bootstrap icons for visual hierarchy
    - Compact player selection cards
    - Responsive behavior (push content in landscape, overlay in portrait)
  - **Answer Selection:** 
    - Clickable answer cards that visually highlight when selected
    - Submit button to confirm selection
    - Color-coded feedback: green for correct answers, red for incorrect answers
  - **Feedback:** Use emojis alongside text (e.g., "Correct! Great job! 🎉", "Incorrect. Keep trying! 🤔").
  - **Correct Answer Celebration:** Trigger a full-screen confetti effect using the `react-confetti` library with pink and blue colors. Confetti displays for 5 seconds upon correct answers.
  - **Incorrect Answer Feedback:** Highlight the correct answer in green, while the incorrect selection remains red. Show text indicating the correct answer.
  - **Question Progression:** Automatic advancement to the next question after 6 seconds, with a countdown timer showing the remaining time.
  - **Session Score:** Display a simple running score for the current session (e.g., "Score: 5 / 8") prominently on the page with animated achievement badges for streaks.
  - **Layout:** Clean, organized interface with a header subtitle and branded footer, consistent spacing, and responsive design for different screen sizes.

### Backend (Server)
- Built with: FastAPI
- Responsibilities:
  - Manage *simple* player settings (perhaps keyed by name in DB or passed from client).
  - Generate AI prompts based on selected settings (Grade, Subject, Difficulty) and send to OpenRouter.
  - Record basic progress (questions, answers).
  - Provide APIs for frontend:
    - `/challenge/get`: fetch new question based on settings.
    - `/challenge/submit`: submit answer and get feedback.

### Database
- SQLite3 (with SQLAlchemy ORM)
- Tables:
  - `players`: Store basic player info (name, grade) and selected settings.
  - `progress`: Log user answers, questions, timestamps for basic tracking.
- Advantages:
  - File-based (no separate database server needed)
  - Zero configuration required
  - Python standard library support
  - Perfect for small applications and home use

### SQLite Schema
```python
# SQLAlchemy models

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

Base = declarative_base()

class Player(Base):
    __tablename__ = "players"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    grade = Column(Integer)  # 2 or 3
    created_at = Column(DateTime, default=func.now())
    
    # Default settings
    preferred_subject = Column(String, default="Math")  # "Math" or "English"
    preferred_sub_activity = Column(String, default="Addition/Subtraction")  # Changes based on subject
    preferred_difficulty = Column(String, default="Easy")  # "Easy", "Medium", "Hard"
    
    # Relationship
    progress = relationship("Progress", back_populates="player")


class Progress(Base):
    __tablename__ = "progress"
    
    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id"))
    
    # Question details
    question_text = Column(Text)
    question_type = Column(String)  # "multiple-choice", "direct-answer", "reading-comprehension"
    subject = Column(String)  # "Math" or "English"
    sub_activity = Column(String)  # e.g., "Addition/Subtraction", "Opposites/Antonyms"
    difficulty = Column(String)  # "Easy", "Medium", "Hard"
    
    # Answer details
    user_answer = Column(Text)
    correct_answer = Column(Text)
    is_correct = Column(Boolean)
    
    # Metadata
    timestamp = Column(DateTime, default=func.now())
    
    # Relationship
    player = relationship("Player", back_populates="progress")
```

---

## 🔐 Player Selection (Simplified)
- No formal login/signup.
- Player Selection: Simple dropdown/buttons on the frontend to choose between pre-defined players (e.g., "Kid 1 - Grade 3", "Kid 2 - Grade 2"). Settings are loaded/saved based on the selected player name.

---

## ⚙️ Game Settings

Settings a user can configure (on the main page):
- Player: Kid 1 (Grade 3) / Kid 2 (Grade 2)
- Subject: Math / English
- Sub-Activity: 
  - For Math: Addition/Subtraction, Multiplication/Division, Word Problems
  - For English: Opposites/Antonyms, Reading Comprehension, Nouns/Pronouns
- Difficulty: Easy, Medium, Hard

Note: All activities are continuous by design, with questions automatically advancing after each answer.

---

## 📚 Challenge Types & Subjects (Focus for MVP)

### Math (Grade 2 & 3 Focus)
Sub-activities available:
1. **Addition/Subtraction** (Multiple Choice)
   - Basic operations with numbers appropriate for grade level
   - Visual representation questions (e.g., "How many apples are left?")

2. **Multiplication/Division** (Multiple Choice)
   - Basic operations with numbers appropriate for grade level
   - Visual representation questions with groups

3. **Word Problems** (Reading Comprehension + Multiple Choice)
   - Simple real-world scenarios requiring mathematical operations
   - Problems involving money, time, or measurement appropriate to grade level

### English (Grade 2 & 3 Focus)
Sub-activities available:
1. **Opposites/Antonyms** (Multiple Choice)
   - Word pairs with opposite meanings
   - Grade-appropriate vocabulary challenges

2. **Reading Comprehension** (Reading Passage + Multiple Choice Questions)
   - Short passages appropriate for grade level
   - Questions about the main idea, details, and inferences

3. **Nouns/Pronouns** (Fill-in-the-blank Multiple Choice)
   - Sentences with missing words to be filled with the correct noun or pronoun
   - Identifying parts of speech in sentences

---

## 🧠 AI Question Generation

- Powered by OpenRouter API (e.g., Mistral, Claude, GPT)
- Prompts constructed dynamically based on:
  - Selected Player's Grade (2 or 3)
  - Subject (Math/English)
  - Sub-Activity (e.g., Addition/Subtraction, Opposites/Antonyms, etc.)
  - Difficulty (Easy/Medium/Hard)
- Returned format (Example):
```json
{
  "question": "What is 12 + 9?",
  "choices": ["20", "21", "22", "23"], // For multiple-choice questions
  "answer": "21",
  "type": "multiple-choice" // Or "direct-answer" or "reading-comprehension"
}
```

---

## 🎲 RANDOMNESS MANAGEMENT IN AI-GENERATED QUESTIONS (Simplified for MVP)

Focus on basic prompt randomization and inherent AI variety.

### Prompt Engineering: Controlled Randomness

Prompts are dynamically constructed with:
- **Fixed Parameters** (from user selection):
  - Subject (Math / English)
  - Sub-Activity (e.g., Addition/Subtraction, Reading Comprehension)
  - Grade level (2 or 3)
  - Difficulty
- **Randomized Elements** (implicitly via AI or basic prompt structure):
  - Numbers (math)
  - Word choices / names (English)

**Sample Prompt (Math - Addition/Subtraction - Grade 2 Easy)**:
```
Generate an easy 2nd-grade level math question about addition/subtraction involving two-digit addition where no carrying is required. Provide the question text and 4 multiple choice options with the correct answer.
```

**Sample Prompt (English - Opposites/Antonyms - Grade 3 Medium)**:
```
Generate a medium difficulty 3rd-grade level English question about opposites/antonyms. Provide a word and ask for its opposite with 4 multiple choice options.
```

---

### AI Creativity Parameters

Use OpenRouter's AI temperature and top-p controls (Keep default or slightly lower temperature for consistency):
| Parameter      | Purpose                          | Recommended Value |
|----------------|----------------------------------|-------------------|
| `temperature`  | Controls creativity randomness   | 0.4 – 0.6         |
| `top_p`        | Narrows focus on token pool      | 0.8 – 0.9         |

These help keep questions reasonably diverse yet appropriate.

---

### Conceptual Architecture (Simplified)

```
+----------------------------+
|     Player Settings        | (Grade, Subject, Sub-Activity, Diff)
+-------------+-------------+
              |
              v
+----------------------------+
|  AI Prompt Constructor     |  <-- Basic structured template
+-------------+-------------+
              |
              v
+----------------------------+
|     AI Model (OpenRouter)  |
+-------------+-------------+
              |
              v
+----------------------------+
|     Game Interface         | (Display Q, Get A, Show Feedback)
+----------------------------+
```

---

## 📋 Question Types and Handling

The game will support three main question types, each with specific UI components and answer validation approaches:

### 1. Multiple Choice Questions
- **Format**: Question with 3-4 possible answers to choose from
- **UI Implementation**: 
  - Clickable answer cards that highlight when selected
  - Submit button to confirm selection and check answer
  - Visual feedback: Correct answers turn green, incorrect answers turn red with the correct answer highlighted in green
- **Example**: 
  - Math: "What is 7 + 8?" with options [13, 14, 15, 16]
  - English: "Which word means 'happy'?" with options [sad, glad, mad, bad]
- **Answer Validation**: Direct comparison of selected option with correct answer
- **Feedback Flow**:
  1. Player selects an answer choice
  2. Player clicks the Submit button
  3. If correct: 
     - Selected answer turns green
     - Pink and blue confetti rains down for 5 seconds
     - Game automatically advances to next question after 6 seconds
  4. If incorrect:
     - Selected answer gets red border
     - Correct answer gets green border
     - Text displays showing the correct answer
     - Game automatically advances to next question after 6 seconds
- **AI Prompt Example**: 
  ```
  Generate a 3rd-grade multiple choice math question with exactly 4 options.
  Return as JSON with "question", "choices" (array of 4 options), and "answer" (the correct option).
  ```

### 2. Direct Answer Questions
- **Format**: Question requiring a text/number input from the student
- **UI Implementation**: Text input field with submit button
- **Example**: 
  - Math: "What is 25 + 17?"
  - English: "Spell the word: [audio would say 'together']"
- **Answer Validation**: 
  - For math: Numerical comparison
  - For spelling/text: Case-insensitive string comparison, possibly with tolerance for minor typos
- **AI Prompt Example**:
  ```
  Generate a 2nd-grade spelling question. Return as JSON with "question" (use "Spell the word: [word]"), 
  and "answer" (the correct spelling).
  ```

### 3. Reading Comprehension / Word Problems
- **Format**: Short passage or story followed by a question about the content
- **UI Implementation**: Text passage displayed above question, which could be multiple choice or direct answer
- **Example**:
  - English: "Sarah has 3 red apples and 2 green apples. How many apples does she have in total?"
  - English: A short story followed by "What did the main character learn?"
- **Answer Validation**: Depends on sub-type (multiple choice or direct answer)
- **AI Prompt Example**:
  ```
  Generate a short 2nd-grade reading passage (2-3 sentences) followed by a question about it.
  Return as JSON with "passage", "question", and "answer".
  ```

### Frontend Implementation
For each question type, the frontend will:
1. Detect the question type from the `type` field in the API response
2. Render the appropriate UI component (choice selector, text input, or reading passage + question)
3. Apply the correct validation logic when checking answers
4. Show appropriate feedback and trigger confetti on correct answers

### Backend Implementation
The backend will:
1. Include the question type in the prompt to the AI
2. Parse and validate the AI's response to ensure it matches the expected format
3. Send the structured question data to the frontend
4. Receive and validate answers according to the question type

This approach allows for variety in question formats while maintaining a consistent gameplay experience.

---

## 🎯 Additional Features

### Error Handling
- Implement basic retry mechanism for OpenRouter API calls (max 2 attempts)
- Have 3-5 "fallback" questions per grade/subject in case the API is unavailable
- Show user-friendly error messages for kids ("Oops! Let's try another question!")

### Visual Feedback and Celebration
- Selected answers highlight in a distinct color before submission
- Correct answers trigger pink and blue confetti for 5 seconds
- Incorrect answers show what the correct answer would have been
- Countdown timer shows seconds until the next question (6 seconds) 

### Small Badges or Stars for Correct Answers
- Display small badges or stars for 3, 5, 10 correct answers in a row
- Bigger/special confetti for milestone achievements

### Automatic Question Progression
- Questions automatically progress after 6 seconds following an answer
- No manual "Next Question" button required
- Provides a steady rhythm to the game experience

### Stretch Goal: Direct Answer Questions
- Add Direct Answer questions as a stretch goal

### Stretch Goal: Reading Comprehension
- Defer Reading Comprehension to post-MVP

### API Contract
- GET /challenge/get
- Request: 
```json
{
  "player": "Kid 1",
  "grade": 3,
  "subject": "Math",
  "sub_activity": "Addition/Subtraction",
  "difficulty": "Easy",
  "type": "multiple-choice"
}
```
- Response:
```json
{
  "id": "q123",
  "question": "What is 7 + 8?",
  "choices": ["13", "14", "15", "16"],
  "answer": "15",
  "type": "multiple-choice",
  "subject": "Math",
  "sub_activity": "Addition/Subtraction",
  "difficulty": "Easy"
}
```

---

## 🏠 Home Deployment

### Shell Script Automation
- Create a simple shell script (`run_game.sh`) to manage both frontend and backend services:
  ```bash
  #!/bin/bash
  
  # Start services
  start_services() {
    echo "Starting Kids Game services..."
    cd backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000 &
    cd frontend && npm start &
    echo "Services started! Access the game at http://localhost:3000"
  }
  
  # Stop services
  stop_services() {
    echo "Stopping Kids Game services..."
    pkill -f "uvicorn main:app"
    pkill -f "node.*start"
    echo "Services stopped!"
  }
  
  # Script usage
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
    *)
      echo "Usage: $0 {start|stop|restart}"
      exit 1
  esac
  ```

### Running the Game
- Start: `./run_game.sh start`
- Stop: `./run_game.sh stop`
- Restart: `./run_game.sh restart`

### Home Network Access
- Access from the host machine: http://localhost:3000
- Access from other devices on home network: http://[HOST_IP]:3000
- No internet exposure or complex deployment needed

---

## 🔧 Technical Implementation Notes

### CORS Configuration
To enable communication between the React frontend (port 3000) and FastAPI backend (port 8000), CORS needs to be configured:

```python
# In main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React development server
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Add routes below...
```

For home network access, you may need to add the IP-based URL to `allow_origins` as well:
```python
allow_origins=["http://localhost:3000", "http://192.168.1.X:3000"]
```

### Dependencies

#### Backend (Python)
Create a `requirements.txt` with these key dependencies:
```
fastapi==0.110.0
uvicorn==0.29.0
sqlalchemy==2.0.29
httpx==0.27.0  # For making API calls to OpenRouter
python-dotenv==1.0.1  # For handling environment variables (API keys)
pydantic==2.6.4
```

#### Frontend (Node.js/React)
Key npm packages to install:
```bash
# Core packages
npm install react-router-dom axios

# UI/UX enhancements
npm install react-confetti  # For celebration animations
npm install react-icons     # For emoji icons and UI elements
npm install bootstrap       # Bootstrap for responsive layout and components
npm install react-bootstrap # React components for Bootstrap
npm install bootstrap-icons # Icons for the UI elements

# No longer needed as we're using Bootstrap
# npm install @chakra-ui/react @emotion/react @emotion/styled framer-motion
```

#### OpenRouter API Integration
Store your API key in a `.env` file:
```
OPENROUTER_API_KEY=your_api_key_here
```

Backend API call example:
```python
import httpx
import os
from dotenv import load_dotenv

load_dotenv()  # Load API key from .env file

async def generate_question(grade, subject, sub_activity, difficulty, question_type):
    """Generate a question using OpenRouter API."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Construct the prompt based on settings
    prompt = f"Generate a {difficulty} {grade}-grade level {subject} question about {sub_activity} of type {question_type}."
    
    # Example API call to Claude or similar model via OpenRouter
    payload = {
        "model": "anthropic/claude-3-haiku-20240307",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.5,
        "top_p": 0.8
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            # Handle API errors - use fallback questions
            return {"error": f"API Error: {response.status_code}"}
```

### Sidebar Implementation
For the sidebar implementation, use React Bootstrap's offcanvas component in larger screens and ensure proper styling:

```jsx
// Example sidebar component structure
import { Offcanvas, Form } from 'react-bootstrap';
import { useState, useEffect } from 'react';

function Sidebar({ show, handleClose, settings, onSettingsChange, ...props }) {
  const [subActivities, setSubActivities] = useState([]);
  
  // Update sub-activities when subject changes
  useEffect(() => {
    if (settings.subject === 'Math') {
      setSubActivities([
        'Addition/Subtraction',
        'Multiplication/Division',
        'Word Problems'
      ]);
    } else if (settings.subject === 'English') {
      setSubActivities([
        'Opposites/Antonyms',
        'Reading Comprehension',
        'Nouns/Pronouns'
      ]);
    }
    
    // Update sub-activity to first option when subject changes
    if (subActivities.length > 0) {
      onSettingsChange({
        ...settings,
        sub_activity: subActivities[0]
      });
    }
  }, [settings.subject]);

  return (
    <Offcanvas show={show} onHide={handleClose} responsive="lg" className="sidebar-container">
      <Offcanvas.Header closeButton>
        <Offcanvas.Title>Game Settings</Offcanvas.Title>
      </Offcanvas.Header>
      <Offcanvas.Body>
        {/* Player Selection */}
        <div className="player-selection">
          {/* Player cards here */}
        </div>
        
        {/* Form Controls - note the custom classes to constrain width */}
        <Form className="sidebar-form">
          <Form.Group className="mb-3 sidebar-form-group">
            <Form.Label>Subject</Form.Label>
            <Form.Select 
              className="sidebar-select" 
              value={settings.subject}
              onChange={(e) => onSettingsChange({...settings, subject: e.target.value})}
            >
              <option>Math</option>
              <option>English</option>
            </Form.Select>
          </Form.Group>
          
          <Form.Group className="mb-3 sidebar-form-group">
            <Form.Label>Sub-Activity</Form.Label>
            <Form.Select 
              className="sidebar-select"
              value={settings.sub_activity}
              onChange={(e) => onSettingsChange({...settings, sub_activity: e.target.value})}
            >
              {subActivities.map(activity => (
                <option key={activity}>{activity}</option>
              ))}
            </Form.Select>
          </Form.Group>
          
          <Form.Group className="mb-3 sidebar-form-group">
            <Form.Label>Difficulty</Form.Label>
            <Form.Select
              className="sidebar-select"
              value={settings.difficulty}
              onChange={(e) => onSettingsChange({...settings, difficulty: e.target.value})}
            >
              <option>Easy</option>
              <option>Medium</option>
              <option>Hard</option>
            </Form.Select>
          </Form.Group>
        </Form>
      </Offcanvas.Body>
    </Offcanvas>
  );
}
```

Add these custom styles to ensure dropdowns stay within the sidebar:

```css
/* Custom styles for sidebar */
.sidebar-container {
  max-width: 280px;
}

.sidebar-form {
  width: 100%;
}

.sidebar-form-group {
  width: 100%;
}

.sidebar-select {
  width: 100%;
  max-width: 240px; /* Ensure it fits within sidebar with padding */
}
```

---

## 📋 Implementation Checklist

### Day 1: Setup & Backend Development

#### 1. Project Setup (1 hour)
- [x] Create project directories (`frontend` and `backend`)
- [x] Initialize Git repository (optional)
- [x] Set up backend Python environment
  - [x] Create virtual environment: `python -m venv venv`
  - [x] Create `requirements.txt` with dependencies
  - [x] Install dependencies: `pip install -r requirements.txt`
- [x] Set up frontend React project
  - [x] Create React app: `npx create-react-app frontend`
  - [x] Install frontend dependencies
- [x] Create folder structure for React components
- [x] Create shell script for starting/stopping services

#### 2. Backend Development - Database (1-2 hours)
- [x] Create SQLite database connection
  - [x] Implement SQLAlchemy models (copy from design document)
  - [x] Create database initialization script
  - [x] Add DB session management
- [x] Add test entries for your kids
  - [x] Create `Player` entries for each child

#### 3. Backend Development - API & AI Integration (2-3 hours)
- [x] Set up FastAPI skeleton with CORS
- [x] Create OpenRouter API integration
  - [x] Create `.env` file with API key
  - [x] Implement question generation function
  - [x] Add error handling and fallback logic
- [x] Implement `/challenge/get` endpoint
  - [x] Accept player settings (including sub-activity)
  - [x] Call OpenRouter API
  - [x] Parse and validate AI response
  - [x] Return formatted question
- [x] Implement `/challenge/submit` endpoint
  - [x] Validate answers
  - [x] Record progress in database
  - [x] Return feedback
- [x] Create 3-5 fallback questions per category
- [x] Test APIs with tools like Postman or Thunder Client

### Day 2: Frontend Development & Integration

#### 4. Frontend - Core Components (2-3 hours)
- [x] Set up project structure
- [x] Create API service layer
  - [x] Implement axios calls to backend
  - [x] Add error handling
- [x] Create main components:
  - [x] Player selection
  - [x] Game settings (subject, sub-activity, difficulty)
  - [x] Dynamic sub-activity options based on selected subject
  - [x] Question display
  - [x] Answer input (multiple choice for MVP)
  - [x] Score display
- [x] Implement responsive sidebar layout
  - [x] Create sidebar component with Bootstrap Offcanvas
  - [x] Add constrained form controls within sidebar
  - [x] Implement player selection cards in sidebar
  - [x] Add toggle button in header
  - [x] Ensure proper responsive behavior

#### 5. Frontend - Game Logic (2 hours)
- [x] Implement game state management
  - [x] Track current player
  - [x] Track score
  - [x] Track question history
- [x] Implement question flow
  - [x] Fetch questions based on settings
  - [x] Handle answer submission
  - [x] Process feedback
- [x] Add basic styling and layout

#### 6. Frontend - UI Enhancements (2 hours)
- [x] Add visual effects
  - [x] Confetti effect for correct answers
  - [x] Emoji feedback
  - [x] Streak/badge logic
- [x] Improve CSS styling
  - [x] Add animations for elements
  - [x] Improve responsive design
  - [x] Create consistent theme
- [x] Implement game completion screen
  - [x] Show final score
  - [x] Congratulate player
  - [x] Add replay option

#### 7. Integration & Testing (1-2 hours)
- [x] Test end-to-end flow
  - [x] Player selection
  - [x] Question fetching
  - [x] Answer submission
  - [x] Score tracking
- [x] Fix any integration issues
- [x] Test fallback questions

#### 8. Deployment (30 mins)
- [x] Create start/stop shell script
- [x] Test on home network
- [x] Document any manual steps

### Sub-Activity Implementation Tasks

#### Backend Tasks
1. **Database Model Updates**
   - [x] Add `preferred_sub_activity` column to `Player` model in `models.py`
   - [x] Add `sub_activity` column to `Progress` model in `models.py`
   - [x] Create a database migration script to update existing tables

2. **API Schema Updates**
   - [x] Update `GetQuestionRequest` schema to include `sub_activity` field
   - [x] Update `QuestionResponse` schema to include `sub_activity` field
   - [x] Update `PlayerResponse` schema to include `preferred_sub_activity` field

3. **API Routes Updates**
   - [x] Modify `/challenges/generate` endpoint to accept and pass the sub_activity parameter
   - [x] Update player creation to include default sub_activity

4. **OpenRouter Service Updates**
   - [x] Update `generate_question()` function to accept `sub_activity` parameter
   - [x] Enhance prompt construction to include sub-activity context
   - [x] Create sub-activity-specific fallback questions

#### Frontend Tasks
1. **State Management Updates**
   - [x] Update `settings` state in `useGameState.js` to include `sub_activity` field
   - [x] Implement logic to update available sub-activities when subject changes

2. **API Service Updates**
   - [x] Update `getQuestion()` function in `api.js` to pass `sub_activity` to the backend

3. **Component Updates**
   - [x] Update `GameSettings.js` to add a new dropdown for sub-activity selection
   - [x] Implement dynamic options based on selected subject
   - [x] Update `ActivitySidebar.js` to display the current sub-activity
   - [x] Add event handlers for sub-activity changes

4. **UI Updates**
   - [x] Add styling for the new sub-activity dropdown in CSS files
   - [x] Update activity badges to include sub-activity information

5. **Testing**
   - [x] Test database migrations
   - [x] Test API functionality with the new parameter
   - [x] Test UI flows for selecting different sub-activities
   - [x] Verify questions match the selected sub-activity

### Stretch Goals (if time permits)
- [ ] Implement Direct Answer questions
- [ ] Add basic stats (% correct, topics mastered)
- [ ] Improve error handling and recovery
- [ ] Enhance visual design

### Recommended Development Sequence
1. Focus on getting the backend API working first
2. Create a minimal frontend that can fetch and display questions
3. Add answer validation and scoring
4. Enhance the UI and user experience
5. Add more question types (if time permits)

This implementation approach ensures you have a functional product even if you don't complete all features within the weekend.