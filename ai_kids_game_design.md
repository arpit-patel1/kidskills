# AI Kids Challenge Game: Design Document

## 🎯 Overview

A web-based educational game that uses AI to generate math and English challenges tailored for kids based on their grade level and learning preferences. The platform will have both a frontend and a backend, with AI-powered question generation, and basic progress tracking.

**Weekend MVP Goal:** Create a playable version within 2 days for Grades 2 & 3 (Math/English) on a home network. Focus on core question generation and play loop.

---

## 🧱 System Architecture

This section outlines the high-level architecture of the KidSkills educational application.

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

### Backend Components

- **FastAPI Application**: Main backend framework that handles API requests and orchestrates the game logic
- **Database Module**: Manages player data, progress, and game state
- **OpenRouter Service**: Interfaces with AI models to dynamically generate questions
- **Question Generator**: Creates and validates questions based on subject, grade level, and difficulty
- **Answer Validator**: Compares player answers to correct answers and determines correctness
- **Feedback Generator**: Produces AI-powered detailed feedback for grammar correction activities

### AI Integration

The application uses the following AI components:

1. **Question Generation**:
   - OpenRouter API is used to dynamically generate age-appropriate questions
   - System prompts designed for each subject and difficulty level
   - Fallback to pre-defined questions when API is unavailable or returns invalid data

2. **Advanced Feedback Mechanism**:
   - Dedicated `/grammar/feedback` API endpoint for detailed grammar feedback
   - Sends original question, user's answer, and correct answer to the AI model
   - Customized prompts based on whether the answer was correct or incorrect
   - Implementation:
     - `generate_grammar_feedback` function in `openrouter_service.py`
     - Pydantic schemas for request/response validation
     - Frontend integration in `DirectAnswerInput` component
     - Fallback feedback in case of API failures
   - Response time optimization with async processing

3. **Error Handling**:
   - Robust error handling for AI service outages
   - Fallback to pre-defined responses
   - Detailed logging for debugging AI interactions

### Frontend Components

### 🔐 Player Selection (Simplified)
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

4. **Grammar Correction** (Direct Answer)
   - Grammatically incorrect sentences that the player must correct
   - Player types in the corrected sentence
   - Answer validation uses case-insensitive comparison with some flexibility for extra spaces
   - Examples:
     - "She don't like ice cream." should be corrected to "She doesn't like ice cream."
     - "The cats is playing." should be corrected to "The cats are playing."

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

### 4. Grammar Correction
- **Format**: Grammatically incorrect sentence that needs to be corrected by the player
- **UI Implementation**: 
  - Text area input for typing the corrected sentence
  - Submit button to check answer
  - Visual feedback: Highlights differences between user's answer and correct answer
- **Example**: 
  - "He walk to school everyday." should be corrected to "He walks to school everyday."
  - "They was playing in the park." should be corrected to "They were playing in the park."
- **Answer Validation**: 
  - Case-insensitive string comparison
  - Optional normalization to account for extra spaces or alternative punctuation
  - Highlight differences between submitted answer and correct answer when incorrect
- **Feedback Flow**:
  1. Player types in their corrected sentence
  2. Player clicks the Submit button
  3. If correct: 
     - Text area gets green border
     - Pink and blue confetti rains down for 5 seconds
     - AI-powered detailed feedback explains what grammar rule they applied correctly
     - Game automatically advances to next question after 6 seconds
  4. If incorrect:
     - Text area gets red border
     - Correct sentence is displayed below
     - AI-powered detailed feedback explains what grammar mistake they missed
     - Game automatically advances to next question after 6 seconds
- **AI Feedback Enhancement**:
  - After submission, the system sends both the original question and the student's answer to the AI
  - For correct answers: AI explains what grammatical error was identified and how it was properly fixed
  - For incorrect answers: AI provides a gentle explanation of what was missed and offers a helpful tip
  - Feedback is tailored for elementary school level understanding
  - Fallback feedback is provided if the AI service is unavailable

#### Enhanced Randomization for Grammar Correction
To ensure variety in grammar correction questions, the system should incorporate:

1. **Diverse Error Types**:
   - Subject-verb agreement errors (e.g., "The dog bark loudly")
   - Verb tense errors (e.g., "Yesterday, she walk to school")
   - Pronoun errors (e.g., "Me went to the store")
   - Article usage (e.g., "She has a apple")
   - Pluralization errors (e.g., "Three cat are playing")
   - Double negatives (e.g., "She don't have no pencils")
   - Adjective order (e.g., "The blue big ball")
   - Preposition usage (e.g., "She arrived to home")

2. **Varied Sentence Patterns**:
   - Simple sentences with subject-verb-object
   - Compound sentences with conjunctions
   - Sentences with prepositional phrases
   - Questions with errors
   - Sentences with different tenses (past, present, future)
   - Sentences with modifiers and adverbs

3. **Diverse Topics and Contexts**:
   - School-related sentences
   - Family-related sentences
   - Nature/animal-related sentences
   - Sports and hobbies
   - Everyday activities
   - Seasonal events and holidays

4. **Prompt Randomization Parameters**:
   ```python
   def generate_grammar_correction_prompt(grade, difficulty):
       # Randomly select error type
       error_types = [
           "subject-verb agreement", 
           "verb tense", 
           "pronoun usage", 
           "article usage",
           "plural forms", 
           "prepositions"
       ]
       
       # Select complexity appropriate for grade level
       if grade <= 2:  # Grades 1-2
           # Simpler error types for younger students
           error_type = random.choice(error_types[:3])  
           
           # Select topics relevant to younger students
           topics = ["school activities", "family", "pets", "playground games"]
           topic = random.choice(topics)
           
           # Simpler sentence structures
           sentence_type = "simple sentence"
       else:  # Grade 3+
           # Full range of error types for older students
           error_type = random.choice(error_types) 
           
           # More diverse topics
           topics = ["school subjects", "hobbies", "nature", "sports", "community", "daily routines"]
           topic = random.choice(topics)
           
           # More varied sentence structures
           sentence_types = ["simple sentence", "compound sentence", "question", "sentence with prepositional phrase"]
           sentence_type = random.choice(sentence_types)
       
       # Build the prompt with specific randomization instructions
       prompt = f"""
       Create a {difficulty.lower()} {grade}-grade level English grammar correction question.
       
       Write a {sentence_type} about {topic} with exactly ONE grammatical error involving {error_type}.
       The error should be appropriate for a {grade}-grade student to identify and fix.
       
       The question should be the incorrect sentence, and the answer should be the fully corrected sentence.
       Make sure the sentence sounds natural and uses age-appropriate vocabulary.
       Do not use the same pattern as these examples: "She don't like ice cream", "The cats is playing", "He walk to school".
       """
       
       return prompt
   ```

5. **Implementation Strategy**:
   - Update the `construct_prompt` function to use the enhanced randomization approach
   - Set a higher temperature value (0.7-0.8) specifically for grammar correction to increase variety
   - Include specific instructions to avoid repeating patterns from previous questions
   - Add logging to track and analyze the types of questions being generated

These enhancements will significantly increase question variety while maintaining grade-level appropriateness.

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
1. **New Component: DirectAnswerInput**
   - [x] Create a new component for direct answer input with text area
   - [x] Add styling for correct/incorrect text input feedback
   - [x] Implement answer submission logic

2. **Update QuestionDisplay**
   - [x] Enhance component to differentiate between question types
   - [x] Add conditional rendering for multiple choice vs. direct answer questions
   - [x] Update emoji/icon selection to include grammar correction (📝✏️)

3. **API Service Updates**
   - [x] Modify `getQuestion()` function to support direct-answer type
   - [x] Update `submitAnswer()` function to handle text answers

4. **CSS Styling**
   - [x] Add styles for text area input
   - [x] Style correct/incorrect feedback for direct answers
   - [x] Create transitions and animations for text input

5. **Testing**
   - [ ] Test grammar correction activity in isolation
   - [ ] Test integration with the rest of the application
   - [ ] Test response handling and feedback display

### Grammar Correction Activity Implementation Checklist

#### Backend Tasks
1. **OpenRouter Service Updates**
   - [x] Update the `DirectAnswerQuestion` schema to support grammar correction prompts
   - [x] Enhance `construct_prompt()` function to support Grammar Correction sub-activity
   - [x] Add sample prompts specifically for grammar correction
   - [x] Add logic to normalize answers (trim whitespace, case-insensitive comparison)
   - [x] Implement `generate_grammar_feedback` function for detailed AI feedback

2. **API Schema Updates**
   - [x] Update `GetQuestionRequest` schema to support the Grammar Correction sub-activity
   - [x] Add JSON schema examples for direct-answer grammar correction questions
   - [x] Update answer validation to handle direct text answers
   - [x] Create schemas for grammar feedback requests and responses

3. **API Endpoints**
   - [x] Create `/grammar/feedback` endpoint to provide detailed feedback
   - [x] Implement error handling and fallbacks for AI service failures

4. **Fallback Questions**
   - [x] Create 3-5 fallback grammar correction questions in case the API fails

#### Frontend Tasks
1. **Component Updates** 
   - [x] Create DirectAnswerInput component for text input
   - [x] Update QuestionDisplay for conditional rendering based on question type
   - [x] Add detailed feedback display to DirectAnswerInput component
   - [x] Implement loading state during feedback generation

2. **API Service Updates**
   - [x] Modify API service to support grammar feedback endpoint
   - [x] Update answer handling for direct-answer questions
   - [x] Implement error handling for feedback retrieval

3. **CSS Styling**
   - [x] Add styles for text area input and feedback display
   - [x] Create visual differentiation between correct/incorrect states
   - [x] Style the detailed feedback presentation

4. **Testing**
   - [ ] Test grammar correction activity end-to-end
   - [ ] Verify AI feedback generation and display
   - [ ] Test fallback mechanisms when AI service is unavailable

### Development Guidelines

1. **Implementation Approach**
   - Focus on getting the backend API working first
   - Create a minimal frontend that can fetch and display questions
   - Add answer validation and scoring
   - Enhance the UI and user experience
   - Add more question types and activity variations as time permits

2. **Testing Strategy**
   - Test each activity type in isolation
   - Verify integration with the rest of the application
   - Ensure proper error handling and fallback mechanisms
   - Test the complete user flow from question generation to feedback display

## Completed Features & Future Enhancements

### Completed Features
- [x] Base game functionality with question generation and answer validation
- [x] Multiple choice questions for Math and English activities
- [x] Direct answer input for Grammar Correction
- [x] AI-powered detailed feedback for Grammar Correction
- [x] Visual feedback with confetti for correct answers
- [x] Responsive sidebar design for settings
- [x] Session scoring and streaks

### Future Enhancements
- [ ] Add direct answer support for other subjects/activities
- [ ] Implement basic statistics tracking (% correct by activity type)
- [ ] Improve answer validation with partial correctness scoring
- [ ] Add highlighting for specific grammar errors in incorrect answers
- [ ] Enhance visual design with more engaging animations
- [ ] Add user accounts and long-term progress tracking
- [ ] Implement reading comprehension with more sophisticated question types

## API Endpoints

The backend exposes the following RESTful API endpoints:

### Player Management

- **GET /api/players**
  - Returns a list of all registered players
  - Response: Array of player objects with their details

- **POST /api/players**
  - Creates a new player
  - Request body: `{ "name": string, "age": number, "grade": number, "avatar": string }`
  - Response: Created player object

- **DELETE /api/players/{player_id}**
  - Deletes a player by ID
  - Response: 204 No Content

### Challenge/Question Management

- **POST /api/challenges/generate**
  - Generates a new question based on parameters
  - Request body: `{ "player_id": number, "subject": string, "sub_activity": string, "difficulty": string, "question_type": string }`
  - Response: Question object with ID, text, choices (if applicable), and other metadata

- **POST /api/challenges/submit**
  - Submits an answer to a question
  - Request body: `{ "player_id": number, "question_id": string, "answer": string }`
  - Response: `{ "is_correct": boolean, "correct_answer": string, "feedback": string }`

### Feedback Management

- **POST /api/grammar/feedback**
  - Generates detailed AI feedback for grammar correction answers
  - Request body: `{ "question": string, "user_answer": string, "correct_answer": string, "is_correct": boolean }`
  - Response: `{ "feedback": string }`
  - Description: This endpoint analyzes both the question and student response to provide tailored educational feedback. For correct answers, it explains what grammar rule was correctly applied. For incorrect answers, it gently explains what was missed and provides helpful guidance.

## Data Flow

The following diagrams illustrate the data flow for key user interactions:

### Grammar Correction Feedback Flow

```
┌─────────────┐          ┌─────────────┐           ┌───────────────┐         ┌──────────────┐
│             │          │             │           │               │         │              │
│   Student   │────1────▶│   Frontend  │─────2────▶│    Backend    │────3───▶│ OpenRouter   │
│             │          │             │           │               │         │      AI      │
│             │◀───6─────│             │◀────5─────│               │◀───4────│              │
└─────────────┘          └─────────────┘           └───────────────┘         └──────────────┘
```

1. **Student to Frontend**:
   - Student receives incorrect grammar sentence
   - Student submits corrected version
   - Frontend determines initial correctness

2. **Frontend to Backend**:
   - Frontend sends:
     - Original question (incorrect sentence)
     - Student's answer (their correction)
     - Correct answer (from initial submission response)
     - Whether answer was correct (boolean)

3. **Backend to AI**:
   - Backend calls OpenRouter with appropriate prompt
   - Prompt includes context and instructions tailored based on correctness

4. **AI to Backend**:
   - AI generates personalized feedback
   - Explains grammar rule (if correct) or mistake (if incorrect)
   - Uses child-friendly language

5. **Backend to Frontend**:
   - Returns structured feedback response
   - Includes fallback feedback if AI failed

6. **Frontend to Student**:
   - Displays feedback in UI
   - Shows loading state while feedback is being generated
   - Presents feedback in appropriate styling based on correctness

This approach provides value beyond simple right/wrong feedback by explaining the underlying grammar concepts to the student, making it more educational.