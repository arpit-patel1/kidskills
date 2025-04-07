from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid

from app.database.database import get_db
from app.models.models import Player, Progress
from app.services.ai_service import generate_question, generate_grammar_feedback, evaluate_grammar_correction, FALLBACK_QUESTIONS, evaluate_reading_comprehension
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
    ReadingComprehensionEvaluationResponse
)

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
    
    # Clear previous questions for this player if it's a new game request or subject/activity changed
    if is_new_game:
        active_keys = list(ACTIVE_QUESTIONS.keys())
        for key in active_keys:
            if key.startswith(f"player_{request.player_id}_"):
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
                correct_answer=correct_answer
            )
            
            # Get the evaluation result
            is_correct = evaluation_result.get('is_correct', False)
            
            # Set feedback based on AI evaluation
            if is_correct:
                feedback = "Correct! 🎉"
            else:
                feedback = f"Oops! The correct sentence is: {correct_answer}"
                
            print(f"AI evaluation for grammar correction - is_correct: {is_correct}, feedback: {evaluation_result.get('feedback', '')}")
        except Exception as e:
            print(f"Error during AI evaluation, falling back to string comparison: {str(e)}")
            # Fall back to string comparison if AI evaluation fails
            normalized_correct = correct_answer.strip().lower()
            normalized_user = user_answer.strip().lower()
            is_correct = normalized_correct == normalized_user
            
            # Create feedback message
            if is_correct:
                feedback = "Correct! 🎉"
            else:
                feedback = f"Oops! The correct sentence is: {correct_answer}"
    
    # For reading comprehension, use AI evaluation
    elif is_reading_comprehension:
        try:
            # Use AI to evaluate the reading comprehension answer
            evaluation_result = await evaluate_reading_comprehension(
                passage=question_data.get("passage", ""),
                question=question_data.get("question", ""),
                user_answer=user_answer,
                correct_answer=correct_answer
            )
            
            # Get the evaluation result
            is_correct = evaluation_result.get('is_correct', False)
            
            # Set feedback based on AI evaluation
            if is_correct:
                feedback = "Correct! 🎉"
            else:
                feedback = f"Oops! The correct answer is: {correct_answer}"
                
            print(f"AI evaluation for reading comprehension - is_correct: {is_correct}, feedback: {evaluation_result.get('feedback', '')}")
        except Exception as e:
            print(f"Error during reading evaluation, falling back to string comparison: {str(e)}")
            # Fall back to string comparison if AI evaluation fails
            normalized_correct = correct_answer.strip().lower()
            normalized_user = user_answer.strip().lower()
            is_correct = normalized_correct == normalized_user or normalized_user in normalized_correct or normalized_correct in normalized_user
            
            # Create feedback message
            if is_correct:
                feedback = "Correct! 🎉"
            else:
                feedback = f"Oops! The correct answer is: {correct_answer}"
    
    else:
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
        # Generate evaluation using Ollama
        result = await evaluate_grammar_correction(
            question=request.question,
            user_answer=request.user_answer,
            correct_answer=request.correct_answer
        )
        
        return result
    except Exception as e:
        print(f"Error evaluating grammar correction: {str(e)}")
        # Provide fallback evaluation
        user_lower = request.user_answer.lower().strip()
        correct_lower = request.correct_answer.lower().strip()
        is_correct = user_lower == correct_lower
        
        if is_correct:
            feedback = "Great job! You fixed the grammar error correctly."
        else:
            feedback = "Good try! Check the sentence structure again."
            
        return {"is_correct": is_correct, "feedback": feedback}

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