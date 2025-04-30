from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid
import time
import os
import random
import pathlib
import base64 # For decoding image data
import io # For handling image bytes

# Image processing libraries - will need adding to requirements.txt
from PIL import Image
import numpy as np
from skimage.metrics import structural_similarity as ssim

from app.database.database import get_db
from app.models.models import Player, Progress
from app.services.ai_service import generate_question, generate_grammar_feedback, evaluate_grammar_correction, evaluate_reading_comprehension
from app.api.schemas import (
    GetQuestionRequest, 
    SubmitAnswerRequest, 
    QuestionResponse, 
    AnswerResponse,
    CreatePlayerRequest,
    PlayerResponse,
    GrammarFeedbackRequest,
    GrammarFeedbackResponse,
    GrammarCorrectionEvaluationRequest,
    GrammarCorrectionEvaluationResponse,
    ReadingComprehensionEvaluationRequest,
    ReadingComprehensionEvaluationResponse,
    SubmitTraceRequest,
    SubmitTraceResponse,
)

# --- New Schema for Letter Response ---
from pydantic import BaseModel

class LetterResponse(BaseModel):
    letter_id: str # Filename, e.g., "ક.png"
    image_url: str # Relative URL path, e.g., "/static/gujarati_letters/ક.png"
# --- End New Schema ---

router = APIRouter()

# In-memory store for active questions
# In a real app, you'd store these in a database
ACTIVE_QUESTIONS = {}

@router.post("/challenges/generate", response_model=QuestionResponse)
async def get_challenge(
    request: GetQuestionRequest,
    db: Session = Depends(get_db)
):
    """Get a new challenge question."""
    # Verify player exists
    player = db.query(Player).filter(Player.id == request.player_id).first()
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Player with ID {request.player_id} not found"
        )
    
    # Check if this is a new game request (indicated by timestamp parameter)
    is_new_game = "timestamp" in request.dict() and request.dict()["timestamp"] is not None
    
    # Track if player has previous questions and their settings
    previous_settings = None
    active_keys = list(ACTIVE_QUESTIONS.keys())
    player_keys = [key for key in active_keys if key.startswith(f"player_{request.player_id}_")]
    
    if player_keys:
        # Get the most recent question details for this player
        last_question_key = player_keys[-1]
        last_question = ACTIVE_QUESTIONS.get(last_question_key, {})
        if last_question:
            previous_settings = {
                "subject": last_question.get("subject"),
                "sub_activity": last_question.get("sub_activity")
            }
    
    # Check if subject or sub-activity changed
    settings_changed = previous_settings and (
        previous_settings["subject"] != request.subject or 
        previous_settings["sub_activity"] != request.sub_activity
    )
    
    # Clear previous questions for this player if it's a new game request or subject/activity changed
    if is_new_game or settings_changed:
        if settings_changed:
            print(f"Settings changed from {previous_settings} to {{'subject': '{request.subject}', 'sub_activity': '{request.sub_activity}'}} - clearing previous questions")
        
        for key in player_keys:
            del ACTIVE_QUESTIONS[key]
    
    # Generate a question
    question_data = await generate_question(
        grade=player.grade,
        subject=request.subject,
        sub_activity=request.sub_activity,
        difficulty=request.difficulty,
        question_type=request.question_type
    )
    
    # Add a unique ID to the question
    question_data["id"] = str(uuid.uuid4())
    
    # Ensure sub_activity is included in the response
    if "sub_activity" not in question_data:
        question_data["sub_activity"] = request.sub_activity
    
    # Ensure subject and difficulty are included in the response
    if "subject" not in question_data:
        question_data["subject"] = request.subject
    if "difficulty" not in question_data:
        question_data["difficulty"] = request.difficulty
    
    # Store the question for this player
    ACTIVE_QUESTIONS[f"player_{request.player_id}_{question_data['id']}"] = question_data
    
    return question_data


@router.post("/challenges/submit", response_model=AnswerResponse)
async def submit_answer(
    request: SubmitAnswerRequest,
    db: Session = Depends(get_db)
):
    """Submit an answer to a challenge."""
    print(f"Received answer submission: {request}")
    
    # Get player information
    player = db.query(Player).filter(Player.id == request.player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail=f"Player with ID {request.player_id} not found")
    
    player_name = player.name
    
    # Get the question details - in a real implementation, would fetch from the database
    question_data = ACTIVE_QUESTIONS.get(f"player_{request.player_id}_{request.question_id}")
    if not question_data:
        raise HTTPException(status_code=404, detail=f"Question {request.question_id} not found")
    
    print(f"Found question in memory: {question_data}")
    
    # Extract the user's answer from the request
    user_answer = request.answer
    
    # Extract question details
    question_type = question_data.get("type", "multiple-choice")
    question_subject = question_data.get("subject", "Math")
    question_sub_activity = question_data.get("sub_activity", "Addition/Subtraction")
    
    # Get the correct answer from the original question
    correct_answer = question_data.get("answer", "")
    if not correct_answer:
        # Some questions might use 'correct_answer' instead of 'answer'
        correct_answer = question_data.get("correct_answer", "")
    
    if not correct_answer:
        # If we still can't find the correct answer
        raise HTTPException(status_code=500, detail="Could not determine correct answer for this question")
    
    # Check specific activity types
    is_grammar_correction = question_sub_activity == "Grammar Correction"
    is_reading_comprehension = question_sub_activity == "Reading Comprehension"
    
    # Default to false (will be set below)
    is_correct = False
    feedback = ""
    
    # For grammar correction, use AI evaluation
    if is_grammar_correction:
        try:
            # Use AI to evaluate the grammar correction answer
            evaluation_result = await evaluate_grammar_correction(
                question=question_data.get("question", ""),
                user_answer=user_answer,
                correct_answer=correct_answer,
                is_correct=user_answer == correct_answer,
                trace_id=str(time.time())
            )
            
            # Get the evaluation result
            is_correct = evaluation_result.get('is_correct', False)
            ai_feedback = evaluation_result.get('feedback', '')
            
            # Set feedback based on AI evaluation
            if is_correct:
                feedback = ai_feedback
            else:
                # For incorrect answers, include the correct answer in the feedback
                feedback = f"{ai_feedback}\n\nThe correct answer is: {correct_answer}"
                
            print(f"AI evaluation for grammar correction - is_correct: {is_correct}, feedback: {ai_feedback}")
        except Exception as e:
            print(f"Error during AI evaluation, falling back to string comparison: {str(e)}")
            # Fall back to string comparison if AI evaluation fails
            normalized_correct = correct_answer.strip().lower()
            normalized_user = user_answer.strip().lower()
            is_correct = normalized_correct == normalized_user
            
            # Create feedback message
            if is_correct:
                feedback = f"Great job, {player_name}! You corrected the sentence perfectly."
            else:
                feedback = f"Good try, {player_name}! The correct answer is: {correct_answer}"
    
    else:  # This 'else' should now handle reading comprehension too
        # Regular string comparison for other question types
        is_correct = user_answer == correct_answer
    
        print(f"Answer is {'correct' if is_correct else 'incorrect'}")
        
        # Create feedback message
        if is_correct:
            feedback = "Correct! 🎉"
        else:
            feedback = f"Oops! The correct answer is: {correct_answer}"
    
    # In a real implementation, would create a record of the answer
    # progress = Progress(...)
    # db.add(progress)
    # db.commit()
    
    response = {
        "is_correct": is_correct,
        "correct_answer": correct_answer,
        "feedback": feedback
    }
    
    print(f"Sending response: {response}")
    return response


@router.get("/players")
async def get_players(db: Session = Depends(get_db)):
    """Get all players."""
    players = db.query(Player).all()
    return players


@router.post("/players", response_model=PlayerResponse, status_code=status.HTTP_201_CREATED)
async def create_player(
    request: CreatePlayerRequest,
    db: Session = Depends(get_db)
):
    """Create a new player."""
    # Check if player with this name already exists
    existing_player = db.query(Player).filter(Player.name == request.name).first()
    if existing_player:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Player with name '{request.name}' already exists"
        )
    
    # Default sub-activity based on subject
    default_sub_activity = "Addition/Subtraction"  # Default for Math
    
    # Create new player
    player = Player(
        name=request.name,
        age=request.age,
        grade=request.grade,
        avatar=request.avatar,
        preferred_subject="Math",
        preferred_sub_activity=default_sub_activity,
        preferred_difficulty="Easy"
    )
    
    db.add(player)
    db.commit()
    db.refresh(player)
    
    return player

@router.delete("/players/{player_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_player(
    player_id: int,
    db: Session = Depends(get_db)
):
    """Delete a player and all their progress records."""
    # Verify player exists
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Player with ID {player_id} not found"
        )
    
    # Delete associated progress records first
    db.query(Progress).filter(Progress.player_id == player_id).delete()
    
    # Delete the player
    db.delete(player)
    db.commit()
    
    # Also remove any active questions for this player from memory
    active_keys = list(ACTIVE_QUESTIONS.keys())
    for key in active_keys:
        if key.startswith(f"player_{player_id}_"):
            del ACTIVE_QUESTIONS[key]
    
    return None 

@router.post("/grammar/feedback", response_model=GrammarFeedbackResponse)
async def get_grammar_feedback(request: GrammarFeedbackRequest):
    """Get detailed feedback for a grammar correction answer."""
    try:
        # Generate detailed feedback using Ollama
        feedback = await generate_grammar_feedback(
            question=request.question,
            user_answer=request.user_answer,
            correct_answer=request.correct_answer,
            is_correct=request.is_correct
        )
        
        return {"feedback": feedback}
    except Exception as e:
        print(f"Error generating grammar feedback: {str(e)}")
        # Provide fallback feedback
        if request.is_correct:
            feedback = "Great job correcting the sentence! You identified the grammar mistake and fixed it correctly."
        else:
            feedback = "Good try! Look carefully at the sentence structure and try again."
        return {"feedback": feedback}

@router.post("/grammar/evaluate", response_model=GrammarCorrectionEvaluationResponse)
async def evaluate_grammar_correction_route(request: GrammarCorrectionEvaluationRequest):
    """Evaluate a grammar correction answer using AI."""
    try:
        print(f"Grammar correction evaluation request received: {request}")
        
        # Get player name if player_id is provided
        player_name = "student"
        if hasattr(request, "player_id") and request.player_id is not None:
            try:
                print(f"Player ID found in request: {request.player_id}")
                # Get the database session
                db = next(get_db())
                player = db.query(Player).filter(Player.id == request.player_id).first()
                if player:
                    player_name = player.name
                    print(f"Found player name: {player_name}")
                else:
                    print(f"No player found with ID: {request.player_id}")
            except Exception as e:
                print(f"Error getting player name from DB: {str(e)}")
        else:
            print("No player_id in request or player_id is None")
        
        # Check if the answer is correct
        user_lower = request.user_answer.lower().strip()
        correct_lower = request.correct_answer.lower().strip()
        is_correct = user_lower == correct_lower
        
        # Generate evaluation using Ollama
        result = await evaluate_grammar_correction(
            question=request.question,
            user_answer=request.user_answer,
            correct_answer=request.correct_answer,
            is_correct=is_correct,
            trace_id=str(time.time())
        )
        
        print(f"Grammar evaluation result: {result}")
        return result
    except Exception as e:
        print(f"Error in grammar evaluation route: {str(e)}")
        # Provide fallback evaluation
        user_lower = request.user_answer.lower().strip()
        correct_lower = request.correct_answer.lower().strip()
        is_correct = user_lower == correct_lower
        
        # Use the enhanced fallback evaluation with varied feedback
        player_name = "student"  # Default fallback
        try:
            if hasattr(request, "player_id") and request.player_id:
                db = next(get_db())
                player = db.query(Player).filter(Player.id == request.player_id).first()
                if player:
                    player_name = player.name
        except Exception:
            pass  # Silently continue with default player_name if error occurs
        
        # Create simple fallback feedback
        if is_correct:
            feedback = f"Great job, {player_name}! You corrected the sentence perfectly."
        else:
            feedback = f"Good try, {player_name}! The correct answer is: {correct_lower}"
        
        fallback = {
            "is_correct": is_correct,
            "feedback": feedback
        }
        
        print(f"Using fallback evaluation: {fallback}")
        return fallback

@router.post("/reading/evaluate", response_model=ReadingComprehensionEvaluationResponse)
async def evaluate_reading_comprehension_route(request: ReadingComprehensionEvaluationRequest):
    """Evaluate a reading comprehension answer using AI."""
    try:
        # Generate evaluation using Ollama
        result = await evaluate_reading_comprehension(
            passage=request.passage,
            question=request.question,
            user_answer=request.user_answer,
            correct_answer=request.correct_answer
        )
        
        return result
    except Exception as e:
        print(f"Error evaluating reading comprehension: {str(e)}")
        # Provide fallback evaluation
        user_lower = request.user_answer.lower().strip()
        correct_lower = request.correct_answer.lower().strip()
        is_correct = user_lower == correct_lower or user_lower in correct_lower or correct_lower in user_lower
        
        if is_correct:
            feedback = "Great job! Your answer shows you understood the passage well."
        else:
            feedback = "Good try! Take another look at the passage for the answer."
            
        return {"is_correct": is_correct, "feedback": feedback} 

# --- New Endpoint for Gujarati Letters ---

# Define the base directory for static files relative to this file's location
# Assuming routes.py is in backend/app/api/
STATIC_FILES_DIR = pathlib.Path(__file__).parent.parent.parent / "static"
GUJARATI_LETTERS_DIR = STATIC_FILES_DIR / "gujarati_letters"

@router.get("/letters/gujarati/random", response_model=LetterResponse)
async def get_random_gujarati_letter():
    """Get a random Gujarati letter image URL."""
    try:
        if not GUJARATI_LETTERS_DIR.is_dir():
            print(f"Error: Directory not found at {GUJARATI_LETTERS_DIR}")
            raise HTTPException(status_code=500, detail="Gujarati letter image directory not found.")

        # List all PNG files in the directory
        letter_files = [f for f in os.listdir(GUJARATI_LETTERS_DIR) if f.lower().endswith('.png')]

        if not letter_files:
            print(f"Error: No PNG files found in {GUJARATI_LETTERS_DIR}")
            raise HTTPException(status_code=404, detail="No Gujarati letter images found.")

        # Select a random letter file
        random_letter_file = random.choice(letter_files)

        # Construct the relative URL path for the frontend
        # This assumes FastAPI is configured to serve static files from '/static'
        image_url_path = f"/static/gujarati_letters/{random_letter_file}"

        return {
            "letter_id": random_letter_file,
            "image_url": image_url_path
        }
    except Exception as e:
        print(f"Error getting random Gujarati letter: {e}")
        raise HTTPException(status_code=500, detail="Internal server error retrieving letter image.")

# --- End New Endpoint ---

# --- New Endpoint for Submitting Gujarati Trace ---

@router.post("/letters/gujarati/submit_trace", response_model=SubmitTraceResponse)
async def submit_gujarati_trace(request: SubmitTraceRequest):
    """Receive and evaluate a Gujarati letter tracing attempt."""
    try:
        # 1. Decode the submitted image data
        try:
            # Remove 'data:image/png;base64,' prefix if present
            if "," in request.image_data:
                header, encoded_data = request.image_data.split(",", 1)
            else:
                encoded_data = request.image_data
            image_bytes = base64.b64decode(encoded_data)
            submitted_image_pil = Image.open(io.BytesIO(image_bytes))
        except (base64.binascii.Error, IOError, ValueError) as decode_err:
            print(f"Error decoding image data: {decode_err}")
            raise HTTPException(status_code=400, detail="Invalid image data format.")

        # 2. Load the target letter image
        target_letter_path = GUJARATI_LETTERS_DIR / request.letter_id
        if not target_letter_path.is_file():
            print(f"Error: Target letter image not found at {target_letter_path}")
            raise HTTPException(status_code=404, detail=f"Target letter '{request.letter_id}' not found.")
        
        target_image_pil = Image.open(target_letter_path)

        # 3. Preprocess images for comparison
        # Convert to grayscale
        target_gray = target_image_pil.convert('L')
        submitted_gray = submitted_image_pil.convert('L')

        # Resize submitted image to match target dimensions (use LANCZOS for quality)
        if target_gray.size != submitted_gray.size:
             submitted_gray = submitted_gray.resize(target_gray.size, Image.Resampling.LANCZOS)

        # Convert images to NumPy arrays
        target_array = np.array(target_gray)
        submitted_array = np.array(submitted_gray)

        # Ensure arrays have the same shape (should be guaranteed by resize)
        if target_array.shape != submitted_array.shape:
             raise HTTPException(status_code=500, detail="Internal error: Image shapes mismatch after processing.")

        # 4. Calculate Structural Similarity Index (SSIM)
        # data_range is the range of pixel values (0-255 for 8-bit grayscale)
        similarity_index, _ = ssim(target_array, submitted_array, full=True, data_range=target_array.max() - target_array.min())
        
        # Convert SSIM from [-1, 1] range to [0, 100] percentage
        score_percent = max(0, (similarity_index + 1) / 2) * 100

        # 5. Generate feedback based on score
        if score_percent >= 90:
            feedback = "Excellent tracing! You're a master at Gujarati letters! 🎉✨"
        elif score_percent >= 75:
            feedback = "Great job! Your tracing looks wonderful! 👍🌟"
        elif score_percent >= 50:
            feedback = "Good try! Keep practicing the shape. 😊"
        elif score_percent >= 30:
            feedback = "Nice effort! Try to follow the curves of the letter. 🤗"
        else:
            feedback = "Keep trying! With practice, you'll get better at tracing. 💪"
        
        # (Optional) Log the progress - requires DB session and Progress model update
        # db = next(get_db())
        # progress = Progress(player_id=request.player_id, subject="Gujarati", sub_activity="Letter Tracing", question_text=request.letter_id, user_answer=f"score:{score_percent:.2f}", is_correct=(score_percent >= 75)) # Define correctness threshold
        # db.add(progress)
        # db.commit()

        return {
            "similarity_score": score_percent,
            "feedback": feedback
        }

    except HTTPException as http_exc: # Re-raise HTTP exceptions
        raise http_exc
    except Exception as e:
        print(f"Error processing trace submission: {e}")
        raise HTTPException(status_code=500, detail="Internal server error processing trace.")

# --- End New Endpoint --- 