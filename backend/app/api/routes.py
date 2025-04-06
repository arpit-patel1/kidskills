from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid

from app.database.database import get_db
from app.models.models import Player, Progress
from app.services.openrouter_service import generate_question, generate_grammar_feedback, FALLBACK_QUESTIONS
from app.api.schemas import (
    GetQuestionRequest, 
    SubmitAnswerRequest, 
    QuestionResponse, 
    AnswerResponse,
    CreatePlayerRequest,
    PlayerResponse,
    GrammarFeedbackRequest,
    GrammarFeedbackResponse
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
    print(f"Received answer submission - Player: {request.player_id}, Question: {request.question_id}, Answer: {request.answer}")
    
    # Verify player exists
    player = db.query(Player).filter(Player.id == request.player_id).first()
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Player with ID {request.player_id} not found"
        )
    
    # Try to get the question from our in-memory store
    question_key = f"player_{request.player_id}_{request.question_id}"
    question = ACTIVE_QUESTIONS.get(question_key)
    
    # If we couldn't find the question, return a fallback
    if not question:
        print(f"Question not found in active questions: {question_key}")
        # Log what's in the active questions dict for debugging
        print(f"Active questions keys: {list(ACTIVE_QUESTIONS.keys())}")
        
        # This is a fallback - in a real app, you'd handle this differently
        return {
            "is_correct": False,
            "correct_answer": "Unknown",
            "feedback": "Sorry, we couldn't find that question. Please try a new one."
        }
    
    # Get the correct answer from the stored question
    correct_answer = str(question["answer"])
    user_answer = str(request.answer)
    
    print(f"Comparing answers - User: '{user_answer}' (type: {type(user_answer)}) vs Correct: '{correct_answer}' (type: {type(correct_answer)})")
    
    # Check if this is a grammar correction question
    is_grammar_correction = (
        question.get("sub_activity") == "Grammar Correction" and 
        question.get("type") == "direct-answer"
    )
    
    # Use normalized comparison for grammar correction
    if is_grammar_correction:
        # Simple normalization: remove extra spaces, convert to lowercase
        normalized_correct = correct_answer.strip().lower()
        normalized_user = user_answer.strip().lower()
        is_correct = normalized_correct == normalized_user
    else:
        # Now compare the user's answer to the correct answer (as strings)
        is_correct = user_answer == correct_answer
    
    print(f"Answer is {'correct' if is_correct else 'incorrect'}")
    
    # Create feedback message
    if is_correct:
        feedback = "Correct! 🎉"
    else:
        if is_grammar_correction:
            feedback = f"Oops! The correct sentence is: {correct_answer}"
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
        # Generate detailed feedback using OpenRouter
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