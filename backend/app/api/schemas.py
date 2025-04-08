from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class GetQuestionRequest(BaseModel):
    """Request schema for getting a question."""
    player_id: int = Field(..., description="Player ID")
    subject: str = Field(..., description="Subject (math or english)")
    sub_activity: str = Field(..., description="Sub-activity (e.g., Addition/Subtraction, Opposites/Antonyms)")
    difficulty: str = Field(..., description="Difficulty level (easy, medium, hard)")
    question_type: str = Field("multiple-choice", description="Question type (multiple-choice, direct-answer, reading-comprehension)")
    timestamp: Optional[int] = Field(None, description="Optional timestamp to ensure fresh questions for new games")


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
    subject: str = Field(..., description="Subject")
    sub_activity: str = Field(..., description="Sub-activity")
    difficulty: str = Field(..., description="Difficulty level")
    
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
    preferred_sub_activity: Optional[str] = Field("Addition/Subtraction", description="Preferred sub-activity")
    preferred_difficulty: Optional[str] = Field("Easy", description="Preferred difficulty level")
    
    class Config:
        orm_mode = True


class ErrorResponse(BaseModel):
    """Response schema for errors."""
    detail: str = Field(..., description="Error message")


class GrammarFeedbackRequest(BaseModel):
    """Request schema for grammar feedback."""
    question: str = Field(..., description="The original question (incorrect sentence)")
    user_answer: str = Field(..., description="The user's answer")
    correct_answer: str = Field(..., description="The correct answer")
    is_correct: bool = Field(..., description="Whether the answer was correct")


class GrammarFeedbackResponse(BaseModel):
    """Response schema for grammar feedback."""
    feedback: str = Field(..., description="Detailed feedback on the grammar correction")


class GrammarCorrectionEvaluationRequest(BaseModel):
    """Request schema for grammar correction evaluation."""
    question: str = Field(..., description="The original question (incorrect sentence)")
    user_answer: str = Field(..., description="The user's answer (corrected sentence)")
    correct_answer: str = Field(..., description="The expected correct answer")
    player_id: Optional[int] = Field(None, description="Player ID for personalized feedback")


class GrammarCorrectionEvaluationResponse(BaseModel):
    """Response schema for grammar correction evaluation."""
    is_correct: bool = Field(..., description="Whether the answer is correct according to AI evaluation")
    feedback: str = Field(..., description="Detailed feedback on the answer")


class ReadingComprehensionEvaluationRequest(BaseModel):
    """Request schema for reading comprehension evaluation."""
    passage: str = Field(..., description="The reading passage")
    question: str = Field(..., description="The question about the passage")
    user_answer: str = Field(..., description="The user's answer")
    correct_answer: str = Field(..., description="The correct answer from the original question")


class ReadingComprehensionEvaluationResponse(BaseModel):
    """Response schema for reading comprehension evaluation."""
    is_correct: bool = Field(..., description="Whether the answer is correct according to AI evaluation")
    feedback: str = Field(..., description="Detailed feedback on the reading comprehension answer") 