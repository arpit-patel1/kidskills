from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class GetQuestionRequest(BaseModel):
    """Request schema for getting a question."""
    player_id: int = Field(..., description="Player ID")
    subject: str = Field(..., description="Subject (math or english)")
    difficulty: str = Field(..., description="Difficulty level (easy, medium, hard)")
    question_type: str = Field("multiple-choice", description="Question type (multiple-choice, direct-answer, reading-comprehension)")


class SubmitAnswerRequest(BaseModel):
    """Request schema for submitting an answer."""
    player_id: int = Field(..., description="Player ID")
    question_id: str = Field(..., description="Question ID")
    answer: str = Field(..., description="User's answer")


class CreatePlayerRequest(BaseModel):
    """Request schema for creating a new player."""
    name: str = Field(..., description="Player name")
    age: int = Field(..., description="Player age")
    grade: int = Field(..., description="Grade level (1-5)")
    avatar: Optional[str] = Field("default.png", description="Avatar image filename")


class QuestionResponse(BaseModel):
    """Response schema for a question."""
    id: str = Field(..., description="Question ID")
    question: str = Field(..., description="Question text")
    choices: Optional[List[str]] = Field(None, description="Multiple choice options")
    passage: Optional[str] = Field(None, description="Reading passage for comprehension questions")
    type: str = Field(..., description="Question type")
    
    class Config:
        orm_mode = True


class AnswerResponse(BaseModel):
    """Response schema for an answer submission."""
    is_correct: bool = Field(..., description="Whether the answer is correct")
    correct_answer: str = Field(..., description="The correct answer")
    feedback: str = Field(..., description="Feedback message")


class PlayerResponse(BaseModel):
    """Response schema for player data."""
    id: int = Field(..., description="Player ID")
    name: str = Field(..., description="Player name")
    grade: int = Field(..., description="Grade level")
    age: int = Field(..., description="Player age")
    avatar: Optional[str] = Field(None, description="Avatar image filename")
    preferred_subject: Optional[str] = Field("Math", description="Preferred subject")
    preferred_difficulty: Optional[str] = Field("Easy", description="Preferred difficulty level")
    
    class Config:
        orm_mode = True


class ErrorResponse(BaseModel):
    """Response schema for errors."""
    detail: str = Field(..., description="Error message") 