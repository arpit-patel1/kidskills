import os
import json
import time
import random
import re
import logging
from typing import Dict, Any, Optional, List, Literal, Union, Callable, Tuple
from dotenv import load_dotenv
from pydantic import BaseModel, Field, validator, ValidationError, root_validator
from loguru import logger
#from ollama import AsyncClient
from .fallback_questions import get_fallback_question as get_fallback
from .prompts import (
    construct_prompt, construct_mario_english_prompt,
    construct_math_multiple_choice_prompt,
    construct_reading_comprehension_prompt,
    construct_opposites_antonyms_prompt,
    construct_synonyms_prompt,
    construct_grammar_correction_prompt,
    construct_nouns_pronouns_prompt
)
import math
import operator
import httpx
import uuid
import asyncio
# Load environment variables
load_dotenv()

# Get Ollama configuration from env
ENABLE_MATH_TOOLS = os.getenv("ENABLE_MATH_TOOLS", "true").lower() == "true"

HTTPX_TIMEOUT = 120.0

# Initialize Ollama client with configured base URL

# Log configuration settings
logger.info(f"ENABLE_MATH_TOOLS: {ENABLE_MATH_TOOLS}")

# Import constants from constants.py
from .constants import (
    NAMES, MATH_NAMES, READING_TOPICS, READING_LOCATIONS,
    MATH_OBJECTS, MATH_LOCATIONS, MATH_ACTIVITIES, MATH_WORD_PROBLEM_TEMPLATES,
    ENGLISH_TOPICS, ENGLISH_VERBS, ENGLISH_ADJECTIVES, ENGLISH_NOUNS,
    ENGLISH_WORD_PATTERNS, ENGLISH_GRAMMAR_TEMPLATES, GRAMMAR_ERROR_TYPES,
    SCENARIOS, OBJECTS, LOCATIONS, TIME_EXPRESSIONS,
    MARIO_CHARACTERS, MARIO_ITEMS, MARIO_LOCATIONS, MARIO_ACTIVITIES
)

# Configure enhanced logging with file output
# Create logs directory at the project root
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "logs")
os.makedirs(LOG_DIR, exist_ok=True)
log_file = os.path.join(LOG_DIR, "backend.log")

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()  # Also log to console
    ]
)

logger.info(f"Logging to {log_file}")

# Get Ollama model from env or use default

# Define Pydantic models for structured output
class MultipleChoiceQuestion(BaseModel):
    question: str = Field(..., description="The question text")
    choices: List[str] = Field(..., min_items=2, max_items=4, description="An array of possible answers")
    answer: str = Field(..., description="The correct answer, must be one of the choices")
    type: str = Field("multiple-choice", description="The type of question")
    
class DirectAnswerQuestion(BaseModel):
    question: str = Field(..., description="The question text")
    answer: str = Field(..., description="The correct answer")
    type: str = Field("direct-answer", description="The type of question")
    
class ReadingComprehensionQuestion(BaseModel):
    passage: str = Field(..., description="The reading text")
    question: str = Field(..., description="The question about the passage")
    choices: List[str] = Field(..., min_items=2, max_items=4, description="An array of possible answers")
    answer: str = Field(..., description="The correct answer, must be one of the choices")
    
    @validator('answer')
    def answer_must_be_in_choices(cls, v, values):
        if 'choices' in values and v not in values['choices']:
            raise ValueError(f'Answer "{v}" must be one of the choices: {values["choices"]}')
        return v
    
    @root_validator(pre=True)
    def check_correct_answer(cls, values):
        # If 'correct_answer' is provided instead of 'answer', use that
        if 'correct_answer' in values and 'answer' not in values:
            values['answer'] = values['correct_answer']
            logger.info("Using 'correct_answer' field as 'answer'")
        return values
    
    def to_dict(self):
        # Handle both Pydantic v1 and v2 methods
        if hasattr(self, "model_dump"):
            return self.model_dump()
        return self.dict()  # Fallback for older Pydantic versions

async def generate_question(grade: int, subject: str, sub_activity: str, difficulty: str, question_type: str = "multiple-choice") -> Dict[str, Any]:
    """
    Dispatcher function that routes to specialized question generators based on type.
    
    Args:
        grade: Student grade level (2 or 3)
        subject: Subject area ("math" or "english", will be capitalized)
        sub_activity: Sub-activity type (e.g., "Addition/Subtraction", "Opposites/Antonyms")
        difficulty: Difficulty level ("easy", "medium", "hard", will be capitalized)
        question_type: Type of question ("multiple-choice", "direct-answer", "reading-comprehension")
        
    Returns:
        Dictionary containing question data
    """
    request_id = f"{time.time():.0f}"
    logger.info(f"[{request_id}] Generating question: grade={grade}, subject={subject}, sub_activity={sub_activity}, difficulty={difficulty}, type={question_type}")
    
    # Validate inputs and normalize case
    grade_str = str(grade)
    subject_norm = subject.capitalize()  # Convert "math" to "Math"
    sub_activity_norm = sub_activity  # Keep as is, will be validated in construct_prompt
    difficulty_norm = difficulty.capitalize()  # Convert "easy" to "Easy"
    
    if grade_str not in ["1", "2", "3", "4", "5"]:
        logger.warning(f"[{request_id}] Invalid grade: {grade}, defaulting to grade 2")
        grade_str = "2"
        
    if subject_norm not in ["Math", "English"]:
        logger.warning(f"[{request_id}] Invalid subject: {subject}, defaulting to Math")
        subject_norm = "Math"
    
    if difficulty_norm not in ["Easy", "Medium", "Hard"]:
        logger.warning(f"[{request_id}] Invalid difficulty: {difficulty}, defaulting to Easy")
        difficulty_norm = "Easy"
    
    # Define valid sub-activities for each subject
    math_activities = ["Addition/Subtraction", "Multiplication/Division", "Word Problems", "Mushroom Kingdom Calculations"]
    english_activities = ["Opposites/Antonyms", "Synonyms", "Reading Comprehension", "Nouns/Pronouns", "Grammar Correction", "Mushroom Kingdom Vocabulary"]
    
    # Validate sub-activity against subject and provide default if invalid
    if subject_norm == "Math" and sub_activity_norm not in math_activities:
        logger.warning(f"[{request_id}] Invalid Math sub-activity: {sub_activity_norm}, defaulting to Addition/Subtraction")
        sub_activity_norm = "Addition/Subtraction"
    elif subject_norm == "English" and sub_activity_norm not in english_activities:
        logger.warning(f"[{request_id}] Invalid English sub-activity: {sub_activity_norm}, defaulting to Opposites/Antonyms")
        sub_activity_norm = "Opposites/Antonyms"
    
    # For Grammar Correction, always use direct-answer
    if sub_activity_norm == "Grammar Correction":
        logger.info(f"[{request_id}] Grammar Correction activity detected, forcing direct-answer question type")
        question_type = "direct-answer"
    
    # Dispatch to the appropriate specialized generator
    try:
        if question_type == "multiple-choice":
            return await generate_multiple_choice_question(int(grade_str), subject_norm, sub_activity_norm, difficulty_norm, request_id)
        elif question_type == "direct-answer":
            return await generate_direct_answer_question(int(grade_str), subject_norm, sub_activity_norm, difficulty_norm, request_id)
        elif question_type == "reading-comprehension":
            return await generate_reading_comprehension_question(int(grade_str), subject_norm, sub_activity_norm, difficulty_norm, request_id)
        else:
            # Default to multiple-choice if type is unrecognized
            logger.warning(f"[{request_id}] Unrecognized question type: {question_type}, defaulting to multiple-choice")
            return await generate_multiple_choice_question(int(grade_str), subject_norm, sub_activity_norm, difficulty_norm, request_id)
    except Exception as e:
        logger.error(f"[{request_id}] Error in question generation: {str(e)}")
        return get_fallback_question(grade_str, subject_norm, sub_activity_norm, difficulty_norm)

async def generate_multiple_choice_question(grade: int, subject: str, sub_activity: str, difficulty: str, request_id: str) -> Dict[str, Any]:
    """
    Generate a multiple choice question using Langflow API or fallback.
    """
    logger.info(f"[{request_id}] Generating multiple-choice question")
    
    # Use Langflow API for specific question types
    if subject == "Math":
        return await generate_math_multiple_choice_langflow(grade, sub_activity, difficulty, request_id)
    elif subject == "English" and sub_activity == "Opposites/Antonyms":
        return await generate_english_opposites_antonyms_langflow(grade, sub_activity, difficulty, request_id)
    elif subject == "English" and sub_activity == "Synonyms":
        return await generate_english_synonyms_langflow(grade, sub_activity, difficulty, request_id)
    elif subject == "English" and sub_activity == "Reading Comprehension":
        return await generate_reading_comprehension_question(grade, subject, sub_activity, difficulty, request_id)
    elif subject == "English" and sub_activity == "Mushroom Kingdom Vocabulary":
        return await generate_mario_english_langflow(grade, sub_activity, difficulty, request_id)
    elif subject == "English" and sub_activity == "Nouns/Pronouns":
        return await generate_english_nouns_pronouns_langflow(grade, sub_activity, difficulty, request_id)
    
    # For other subjects/activities not explicitly handled by Langflow, use fallback
    logger.warning(f"[{request_id}] No specific Langflow generator found for {subject} - {sub_activity}. Using fallback.")
    return get_fallback_question(str(grade), subject, sub_activity, difficulty)

async def generate_direct_answer_question(grade: int, subject: str, sub_activity: str, difficulty: str, request_id: str) -> Dict[str, Any]:
    """Generate a direct answer question using Langflow API or fallback."""
    logger.info(f"[{request_id}] Generating direct-answer question")
    
    # If this is Grammar Correction, use Langflow API if available
    if sub_activity == "Grammar Correction":
        try:
            # Check if LANGFLOW_WORKFLOW_GRAMMAR_CORRECTION is set
            if os.getenv("LANGFLOW_WORKFLOW_GRAMMAR_CORRECTION"):
                logger.info(f"[{request_id}] Using Langflow API for Grammar Correction")
                return await generate_grammar_correction_langflow(grade, difficulty, request_id)
        except Exception as e:
            logger.error(f"[{request_id}] Error using Langflow for Grammar Correction: {str(e)}")
            logger.info(f"[{request_id}] Falling back for Grammar Correction")
            # Fall through to the general fallback mechanism
    
    # If not Grammar Correction or Langflow failed, use fallback
    logger.warning(f"[{request_id}] No specific Langflow generator used for direct answer {subject} - {sub_activity}. Using fallback.")
    return get_fallback_question(str(grade), subject, sub_activity, difficulty)

def get_fallback_question(grade: str, subject: str, sub_activity: str, difficulty: str) -> Dict[str, Any]:
    """
    Get a fallback question when the API fails.
    
    Args:
        grade: Student grade level (unused in simplified version)
        subject: Subject area
        sub_activity: Sub-activity type
        difficulty: Difficulty level (unused in simplified version)
        
    Returns:
        Dictionary containing question data
    """
    # Use the simplified fallback question function from the fallback_questions module
    # that only depends on subject and sub_activity
    return get_fallback(subject, sub_activity)

def remove_think_tags(text: str) -> str:
    """
    Remove <think> tags and their content from the text.
    
    Args:
        text: The text containing think tags
        
    Returns:
        Text with think tags and their content removed
    """
    # Remove think tags and their content
    return re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)

async def generate_grammar_feedback(question: str, user_answer: str, correct_answer: str, is_correct: bool) -> str:
    """
    Generate detailed feedback for a grammar correction answer using Langflow API.
    
    Args:
        question: The original question (incorrect sentence)
        user_answer: The student's answer (their attempted correction)
        correct_answer: The correct answer
        is_correct: Whether the student's answer was correct
        
    Returns:
        Detailed feedback string
    """
    logger = logging.getLogger(__name__)
    request_id = f"{time.time():.0f}"
    
    # Try using Langflow for grammar feedback if available
    try:
        if os.getenv("LANGFLOW_WORKFLOW_GRAMMAR_EVALUATION"):
            logger.info(f"[{request_id}] Using Langflow API for grammar feedback")
            
            # Get Langflow configuration from environment
            langflow_host = os.getenv("LANGFLOW_HOST", "http://localhost:7860")
            # Use the evaluation workflow, as it's designed for feedback
            langflow_workflow = os.getenv("LANGFLOW_WORKFLOW_GRAMMAR_EVALUATION", "grammar-evaluation") # Updated workflow name
            
            # Construct the API URL
            url = f"{langflow_host}/api/v1/run/{langflow_workflow}"
            
            # Create a unique session ID
            session_id = f"kidskills_{str(uuid.uuid4())}"
            
            # Create a prompt based on whether the answer was correct or not
            if is_correct:
                prompt = f"""
                The student was given this grammatically incorrect sentence: "{question}"
                
                The student correctly fixed it to: "{user_answer}"
                
                The correct answer is: "{correct_answer}"
                
                Please provide a short, encouraging response (2-3 sentences) explaining what grammatical error they fixed correctly. Use language appropriate for an elementary school student. Focus on the specific grammar rule they applied. Include an emoji.
                """
            else:
                prompt = f"""
                The student was given this grammatically incorrect sentence: "{question}"
                
                The student attempted to fix it with: "{user_answer}"
                
                The correct answer is: "{correct_answer}"
                
                Please provide a short, gentle response (2-3 sentences) explaining what grammar error they missed or fixed incorrectly. Use language appropriate for an elementary school student. Give a simple tip to help them understand the grammar rule. Include an emoji.
                """
            
            # Prepare the request payload
            payload = {
                "input_value": prompt,
                "output_type": "chat",
                "input_type": "chat",
                "session_id": str(session_id),
                "output_component": "",
                "tweaks": None,
            }
            
            # Set up headers
            headers = {
                "Content-Type": "application/json"
            }
            
            # Make the API request using httpx
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers, timeout=HTTPX_TIMEOUT) # Added timeout
                response.raise_for_status()
                
                # Parse the response
                response_data = response.json()
                
                # Extract the feedback from the response
                feedback_str = extract_question_from_langflow_response(response_data, request_id)
                
                # Clean up session messages to avoid accumulating in Langflow storage
                await delete_langflow_session_messages(session_id, request_id)
                
                if feedback_str:
                    # The removal is now handled by extract_question_from_langflow_response
                    # feedback_str = remove_think_tags(feedback_str) # This call is now redundant
                    logger.info(f"[{request_id}] Generated feedback: {feedback_str[:100]}...")
                    return feedback_str
    except Exception as e:
        logger.error(f"[{request_id}] Error generating feedback with Langflow: {str(e)}")
    
    # If Langflow fails or is not available, use the fallback
    logger.info(f"[{request_id}] Using fallback for grammar feedback")
    feedback_data = get_fallback_feedback(is_correct)
    return feedback_data["feedback"]

def get_fallback_feedback(is_correct: bool) -> Dict[str, Any]:
    """
    Get fallback feedback for grammar correction when AI evaluation fails.
    
    Args:
        is_correct: Whether the user's answer is correct
        
    Returns:
        Dictionary with feedback on the answer
    """
    if is_correct:
        feedbacks = [
            "That's correct! You fixed the grammar error perfectly. 😊",
            "Well done! You spotted the mistake and fixed it correctly. 👍",
            "Good job! Your answer is grammatically correct. 🌟",
            "You got it right! Your correction shows good grammar skills. 😄",
            "Excellent work! You fixed the sentence correctly. 🎉"
        ]
    else:
        feedbacks = [
            "Not quite right. Try looking at the verbs in the sentence. 🤔",
            "Almost there! Check if the subject and verb agree with each other. 📝",
            "Keep trying! Look at how the words work together in the sentence. 💪",
            "That's not correct yet. Think about the proper word order. 🧩",
            "Not exactly. Consider whether you need singular or plural forms. 📚"
        ]
    
    return {
        "is_correct": is_correct,
        "feedback": random.choice(feedbacks)
    }

def getRandomSeed() -> int:
    """Generate a random seed for AI prompts to increase variety."""
    return random.randint(1000, 9999)

async def evaluate_grammar_correction(user_answer: str, correct_answer: str, question: str, is_correct: bool, trace_id: str) -> Dict[str, Any]:
    """
    Generate a response to a grammar correction answer.

    Args:
        user_answer: User's answer
        correct_answer: Correct answer to the question
        question: The question that was asked
        is_correct: Whether the user's answer was correct
        trace_id: Trace ID for logging

    Returns:
        Dictionary with feedback on the answer
    """
    
    # Try using Langflow for grammar correction evaluation
    try:
        if os.getenv("LANGFLOW_WORKFLOW_GRAMMAR_EVALUATION"):
            logger.info(f"[{trace_id}] Using Langflow API for grammar correction evaluation")
            return await evaluate_grammar_correction_langflow(user_answer, correct_answer, question, is_correct, trace_id)
    except Exception as e:
        logger.error(f"[{trace_id}] Error using Langflow for grammar correction evaluation: {str(e)}")
    
    # If Langflow is not available or fails, use the fallback implementation
    logger.info(f"[{trace_id}] Using fallback for grammar correction evaluation")
    return get_fallback_feedback(is_correct)

def get_fallback_grammar_evaluation(question: str, user_answer: str, correct_answer: str, player_name: str = "student") -> dict:
    """Get fallback evaluation when the API fails."""
    # Simple string similarity to determine correctness as fallback
    user_lower = user_answer.lower().strip()
    correct_lower = correct_answer.lower().strip()
    
    # Very basic fallback evaluation - same as current system
    is_correct = user_lower == correct_lower
    
    # More varied feedback options
    correct_feedback_options = [
        f"I like how you fixed that sentence, {player_name}! You identified the grammar error correctly.",
        f"Nice work on the grammar correction, {player_name}! You spotted the error and fixed it well.",
        f"{player_name}, you've got a good eye for grammar! Your correction makes the sentence much clearer.",
        f"The sentence looks much better now, {player_name}. You fixed the grammar problem perfectly.",
        f"You found the grammar mistake, {player_name}! Your correction makes the sentence grammatically correct."
    ]
    
    incorrect_feedback_options = [
        f"I see what you tried to do, {player_name}. Check the sentence again and look for grammar errors.",
        f"{player_name}, you're on the right track! Look at the verb and subject to see if they match properly.",
        f"Almost there, {player_name}! Read the sentence out loud and see if it sounds right.",
        f"Try again, {player_name}. Look carefully at how the words work together in the sentence.",
        f"Keep working on it, {player_name}! Consider whether the sentence uses the correct verb tense."
    ]
    
    if is_correct:
        feedback = random.choice(correct_feedback_options)
    else:
        feedback = random.choice(incorrect_feedback_options)
    
    return {
        "is_correct": is_correct,
        "feedback": feedback
    }

async def evaluate_reading_comprehension(passage: str, question: str, user_answer: str, correct_answer: str) -> dict:
    """
    Evaluate a reading comprehension answer using Langflow API and provide detailed feedback.
    
    Args:
        passage: The reading passage text
        question: The question about the passage
        user_answer: The student's answer
        correct_answer: The correct answer from the original question
        
    Returns:
        Dictionary with is_correct (bool) and feedback (str)
    """
    logger = logging.getLogger(__name__)
    request_id = f"{time.time():.0f}"
    
    # Try using Langflow for reading comprehension evaluation if available
    try:
        if os.getenv("LANGFLOW_WORKFLOW_READING_COMPREHENSION"):
            logger.info(f"[{request_id}] Using Langflow API for reading comprehension evaluation")
            return await evaluate_reading_comprehension_langflow(passage, question, user_answer, correct_answer, request_id)
    except Exception as e:
        logger.error(f"[{request_id}] Error using Langflow for reading comprehension evaluation: {str(e)}")
    
    # If Langflow is not available or fails, use the fallback implementation
    logger.info(f"[{request_id}] Using fallback for reading comprehension evaluation")
    return get_fallback_reading_evaluation(user_answer, correct_answer)

def get_fallback_reading_evaluation(user_answer: str, correct_answer: str) -> dict:
    """Get fallback evaluation when the API fails."""
    # Simple string similarity to determine correctness as fallback
    user_lower = user_answer.lower().strip()
    correct_lower = correct_answer.lower().strip()
    
    # Very basic fallback evaluation
    is_correct = user_lower == correct_lower or user_lower in correct_lower or correct_lower in user_lower
    
    if is_correct:
        feedback = "Great job! Your answer shows you understood the passage well. You identified the key information correctly!"
    else:
        feedback = "Good effort! Take another look at the passage and see if you can find the specific details that answer the question."
    
    return {
        "is_correct": is_correct,
        "feedback": feedback
    }

async def generate_math_multiple_choice_langflow(grade: int, sub_activity: str, difficulty: str, request_id: str) -> Dict[str, Any]:
    """
    Generate a math multiple choice question using Langflow API.
    
    Args:
        grade: Student grade level (2-3)
        sub_activity: Sub-activity type (e.g., "Addition/Subtraction", "Multiplication/Division")
        difficulty: Difficulty level ("Easy", "Medium", "Hard")
        request_id: Unique request identifier for logging
        
    Returns:
        Dictionary containing question data
    """
    logger.info(f"[{request_id}] Generating math multiple-choice question using Langflow API")
    
    # Get Langflow configuration from environment
    langflow_host = os.getenv("LANGFLOW_HOST", "http://localhost:7860")
    langflow_workflow = os.getenv("LANGFLOW_WORKFLOW_MATH_MULTIPLE_CHOICE", "math-multiple-choice")
    
    # Construct the API URL
    url = f"{langflow_host}/api/v1/run/{langflow_workflow}"
    
    # Create a unique session ID
    session_id = f"kidskills_{str(uuid.uuid4())}"
    
    # Generate a custom prompt for math questions
    custom_prompt = construct_math_multiple_choice_prompt(grade, sub_activity, difficulty)
    logger.debug(f"[{request_id}] Custom Math Prompt: {custom_prompt}")
    
    # Prepare the request payload
    payload = {
        "input_value": custom_prompt,
        "output_type": "chat",
        "input_type": "chat",
        "session_id": str(session_id),
        "output_component": "",
        "tweaks": None,
    }
    
    # Set up headers
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        # Make the API request using httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=HTTPX_TIMEOUT) # Added timeout
            response.raise_for_status()
            
            # Parse the response
            response_data = response.json()
            logger.debug(f"[{request_id}] Langflow Math Response: {response_data}")
            
            # Extract the question JSON string from the response
            question_json_str = extract_question_from_langflow_response(response_data, request_id)
            
            # Clean up session messages to avoid accumulating in Langflow storage
            # We do this in a fire-and-forget manner to not block the response
            await delete_langflow_session_messages(session_id, request_id)
            
            # If we couldn't find the question data, use a fallback
            if not question_json_str:
                logger.warning(f"[{request_id}] Could not extract question data from API response")
                logger.warning(f"[{request_id}] Response structure: {json.dumps(response_data, indent=2)[:1000]}")
                return get_fallback_question(grade, "Math", sub_activity, difficulty)
            
            # Parse the JSON string to get the question data
            try:
                question_data = json.loads(question_json_str)
                
                # Create a properly formatted question dictionary
                formatted_question = {
                    "question": question_data.get("question", ""),
                    "choices": [str(choice) for choice in question_data.get("choices", [])],
                    "answer": str(question_data.get("answer", "")),
                    "type": "multiple-choice",
                    "sub_activity": sub_activity
                }
                
                # Validate the response
                if not all(key in formatted_question for key in ["question", "choices", "answer"]):
                    logger.warning(f"[{request_id}] Incomplete question data: {formatted_question}")
                    return get_fallback_question(grade, "Math", sub_activity, difficulty)
                
                # Ensure we have exactly 4 choices
                if len(formatted_question["choices"]) != 4:
                    logger.warning(f"[{request_id}] Invalid number of choices: {len(formatted_question['choices'])}")
                    return get_fallback_question(grade, "Math", sub_activity, difficulty)
                
                # Ensure the answer is in the choices
                if formatted_question["answer"] not in formatted_question["choices"]:
                    logger.warning(f"[{request_id}] Answer not in choices: {formatted_question['answer']} not in {formatted_question['choices']}")
                    return get_fallback_question(grade, "Math", sub_activity, difficulty)
                
                logger.info(f"[{request_id}] Successfully generated question using Langflow API")
                return formatted_question
                
            except json.JSONDecodeError as e:
                logger.error(f"[{request_id}] Error parsing question JSON: {str(e)}")
                logger.error(f"[{request_id}] Raw JSON string: {question_json_str}")
                return get_fallback_question(grade, "Math", sub_activity, difficulty)
            
    except httpx.HTTPError as e:
        error_details = {
            "error_type": type(e).__name__,
            "error_message": str(e),
            "url": url,
            "workflow": langflow_workflow
        }
        # For HTTP response errors, try to get more details
        if hasattr(e, 'response') and e.response is not None:
            error_details["status_code"] = e.response.status_code
            try:
                error_details["response_body"] = e.response.text
            except:
                error_details["response_body"] = "Could not extract response body"
                
        logger.error(f"[{request_id}] HTTP error from Langflow API: {error_details}")
        return get_fallback_question(grade, "Math", sub_activity, difficulty)
    except Exception as e:
        logger.error(f"[{request_id}] Error calling Langflow API: {str(e)}")
        return get_fallback_question(grade, "Math", sub_activity, difficulty)

async def delete_langflow_session_messages(session_id: str, request_id: str) -> bool:
    """
    Delete all messages for a specific Langflow session.
    
    Args:
        session_id: The Langflow session ID
        request_id: Unique request identifier for logging
        
    Returns:
        True if successful, False otherwise
    """
    logger.info(f"[{request_id}] Deleting Langflow session messages for session ID: {session_id}")
    
    # Get Langflow configuration from environment
    langflow_host = os.getenv("LANGFLOW_HOST", "http://localhost:7860")
    
    # Construct the API URL
    url = f"{langflow_host}/api/v1/monitor/messages/session/{session_id}"
    
    try:
        # Make the DELETE request using httpx
        async with httpx.AsyncClient() as client:
            response = await client.delete(url, timeout=10.0) # Added shorter timeout for delete
            response.raise_for_status()
            
            # Log success
            logger.info(f"[{request_id}] Successfully deleted messages for session ID: {session_id}")
            return True
            
    except httpx.HTTPError as e:
        logger.error(f"[{request_id}] HTTP error deleting Langflow session messages: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"[{request_id}] Error deleting Langflow session messages: {str(e)}")
        return False

async def generate_reading_comprehension_question(grade: int, subject: str, sub_activity: str, difficulty: str, request_id: str) -> Dict[str, Any]:
    """
    Generate a reading comprehension question using Langflow API.
    
    Args:
        grade: Student grade level
        subject: Subject (English)
        sub_activity: Sub-activity type (Reading Comprehension)
        difficulty: Difficulty level (Easy, Medium, Hard)
        request_id: Unique request identifier for logging
        
    Returns:
        Dictionary containing question data
    """
    logger.info(f"[{request_id}] Generating reading comprehension question using Langflow API")
    
    # Get Langflow configuration from environment
    langflow_host = os.getenv("LANGFLOW_HOST", "http://localhost:7860")
    langflow_workflow = os.getenv("LANGFLOW_WORKFLOW_READING_COMPREHENSION", "reading-comprehension")
    
    # Construct the API URL
    url = f"{langflow_host}/api/v1/run/{langflow_workflow}"
    
    # Create a unique session ID
    session_id = f"kidskills_{str(uuid.uuid4())}"
    
    # Generate a custom prompt for reading comprehension questions
    custom_prompt = construct_reading_comprehension_prompt(grade, sub_activity, difficulty)
    logger.debug(f"[{request_id}] Reading Comprehension Prompt: {custom_prompt}")
    
    # Prepare the request payload
    payload = {
        "input_value": custom_prompt,
        "output_type": "chat",
        "input_type": "chat",
        "session_id": str(session_id),
        "output_component": "",
        "tweaks": None,
    }
    
    # Set up headers
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        # Make the API request using httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=HTTPX_TIMEOUT) # Added timeout
            response.raise_for_status()
            
            # Parse the response
            response_data = response.json()
            logger.debug(f"[{request_id}] Langflow Reading Comprehension Response: {response_data}")
            
            # Extract the question JSON string from the response
            question_json_str = extract_question_from_langflow_response(response_data, request_id)
            
            # Clean up session messages to avoid accumulating in Langflow storage
            await delete_langflow_session_messages(session_id, request_id)
            
            # If we couldn't find the question data, use a fallback
            if not question_json_str:
                logger.warning(f"[{request_id}] Could not extract question data from API response")
                logger.warning(f"[{request_id}] Response structure: {json.dumps(response_data, indent=2)[:1000]}")
                return get_fallback_question(grade, subject, sub_activity, difficulty)
            
            # Parse the JSON string to get the question data
            try:
                question_data = json.loads(question_json_str)
                
                # Create a properly formatted question dictionary
                formatted_question = {
                    "passage": question_data.get("passage", ""),
                    "question": question_data.get("question", ""),
                    "choices": [str(choice) for choice in question_data.get("choices", [])],
                    "answer": str(question_data.get("answer", "")),
                    "type": "reading-comprehension",
                    "sub_activity": sub_activity,
                    "subject": subject,
                    "difficulty": difficulty
                }
                
                # Validate the response
                if not all(key in formatted_question for key in ["passage", "question", "choices", "answer"]):
                    logger.warning(f"[{request_id}] Incomplete question data: {formatted_question}")
                    return get_fallback_question(grade, subject, sub_activity, difficulty)
                
                # Ensure we have exactly 4 choices
                if len(formatted_question["choices"]) != 4:
                    logger.warning(f"[{request_id}] Invalid number of choices: {len(formatted_question['choices'])}")
                    
                    # Fix the number of choices
                    choices = formatted_question["choices"]
                    answer = formatted_question["answer"]
                    
                    if len(choices) < 4:
                        # Add additional choices to reach 4
                        while len(choices) < 4:
                            new_choice = f"Option {chr(65 + len(choices))}"  # Option A, Option B, etc.
                            if new_choice not in choices and new_choice != answer:
                                choices.append(new_choice)
                                logger.info(f"[{request_id}] Added extra choice: {new_choice}")
                    elif len(choices) > 4:
                        # Keep the first 3 choices plus the correct answer
                        if answer in choices:
                            # Remove the answer temporarily
                            choices.remove(answer)
                            # Keep only the first 3 other choices
                            choices = choices[:3]
                            # Add the answer back
                            choices.append(answer)
                        else:
                            # Just keep the first 4 choices
                            choices = choices[:4]
                    
                    formatted_question["choices"] = choices
                
                # Ensure the answer is in the choices
                if formatted_question["answer"] not in formatted_question["choices"]:
                    logger.warning(f"[{request_id}] Answer not in choices: {formatted_question['answer']} not in {formatted_question['choices']}")
                    
                    # Add the answer to the choices
                    choices = formatted_question["choices"]
                    if len(choices) > 0:
                        choices[-1] = formatted_question["answer"]
                    else:
                        choices = ["Option A", "Option B", formatted_question["answer"], "Option C"]
                    
                    formatted_question["choices"] = choices
                
                logger.info(f"[{request_id}] Successfully generated reading comprehension question using Langflow API")
                return formatted_question
                
            except json.JSONDecodeError as e:
                logger.error(f"[{request_id}] Error parsing question JSON: {str(e)}")
                logger.error(f"[{request_id}] Raw JSON string: {question_json_str}")
                return get_fallback_question(grade, subject, sub_activity, difficulty)
            
    except httpx.HTTPError as e:
        logger.error(f"[{request_id}] HTTP error from Langflow API: {str(e)}")
        return get_fallback_question(grade, subject, sub_activity, difficulty)
    except Exception as e:
        logger.error(f"[{request_id}] Error calling Langflow API: {str(e)}")
        return get_fallback_question(grade, subject, sub_activity, difficulty)

async def generate_english_opposites_antonyms_langflow(grade: int, sub_activity: str, difficulty: str, request_id: str) -> Dict[str, Any]:
    """
    Generate an English opposites/antonyms question using Langflow API.
    
    Args:
        grade: Student grade level
        sub_activity: Sub-activity type (Opposites/Antonyms)
        difficulty: Difficulty level (Easy, Medium, Hard)
        request_id: Unique request identifier for logging
        
    Returns:
        Dictionary containing question data
    """
    logger.info(f"[{request_id}] Generating English opposites/antonyms question using Langflow API")
    
    # Get Langflow configuration from environment
    langflow_host = os.getenv("LANGFLOW_HOST", "http://localhost:7860")
    langflow_workflow = os.getenv("LANGFLOW_WORKFLOW_OPPOSITES_ANTONYMS", "opposites-antonyms")
    
    # Construct the API URL
    url = f"{langflow_host}/api/v1/run/{langflow_workflow}"
    
    # Create a unique session ID
    session_id = f"kidskills_{str(uuid.uuid4())}"
    
    # Generate a custom prompt for opposites/antonyms questions
    custom_prompt = construct_opposites_antonyms_prompt(grade, difficulty)
    logger.debug(f"[{request_id}] Opposites/Antonyms Prompt: {custom_prompt}")
    
    # Prepare the request payload
    payload = {
        "input_value": custom_prompt,
        "output_type": "chat",
        "input_type": "chat",
        "session_id": str(session_id),
        "output_component": "",
        "tweaks": None,
    }
    
    # Set up headers
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        # Make the API request using httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=HTTPX_TIMEOUT) # Added timeout
            response.raise_for_status()
            
            # Parse the response
            response_data = response.json()
            logger.debug(f"[{request_id}] Langflow Opposites/Antonyms Response: {response_data}")
            
            # Extract the question JSON string from the response
            question_json_str = extract_question_from_langflow_response(response_data, request_id)
            
            # Clean up session messages to avoid accumulating in Langflow storage
            await delete_langflow_session_messages(session_id, request_id)
            
            # If we couldn't find the question data, use a fallback
            if not question_json_str:
                logger.warning(f"[{request_id}] Could not extract question data from API response")
                logger.warning(f"[{request_id}] Response structure: {json.dumps(response_data, indent=2)[:1000]}")
                return get_fallback_question(grade, "English", sub_activity, difficulty)
            
            # Parse the JSON string to get the question data
            try:
                question_data = json.loads(question_json_str)
                
                # Create a properly formatted question dictionary
                formatted_question = {
                    "question": question_data.get("question", ""),
                    "choices": [str(choice) for choice in question_data.get("choices", [])],
                    "answer": str(question_data.get("answer", "")),
                    "type": "multiple-choice",
                    "sub_activity": sub_activity,
                    "subject": "English",
                    "difficulty": difficulty
                }
                
                # Validate the response
                if not all(key in formatted_question for key in ["question", "choices", "answer"]):
                    logger.warning(f"[{request_id}] Incomplete question data: {formatted_question}")
                    return get_fallback_question(grade, "English", sub_activity, difficulty)
                
                # Ensure we have exactly 4 choices
                if len(formatted_question["choices"]) != 4:
                    logger.warning(f"[{request_id}] Invalid number of choices: {len(formatted_question['choices'])}")
                    
                    # Fix the number of choices
                    choices = formatted_question["choices"]
                    answer = formatted_question["answer"]
                    
                    if len(choices) < 4:
                        # Add additional choices to reach 4
                        while len(choices) < 4:
                            new_choice = f"Option {chr(65 + len(choices))}"  # Option A, Option B, etc.
                            if new_choice not in choices and new_choice != answer:
                                choices.append(new_choice)
                                logger.info(f"[{request_id}] Added extra choice: {new_choice}")
                    elif len(choices) > 4:
                        # Keep the first 3 choices plus the correct answer
                        if answer in choices:
                            # Remove the answer temporarily
                            choices.remove(answer)
                            # Keep only the first 3 other choices
                            choices = choices[:3]
                            # Add the answer back
                            choices.append(answer)
                        else:
                            # Just keep the first 4 choices
                            choices = choices[:4]
                    
                    formatted_question["choices"] = choices
                
                # Ensure the answer is in the choices
                if formatted_question["answer"] not in formatted_question["choices"]:
                    logger.warning(f"[{request_id}] Answer not in choices: {formatted_question['answer']} not in {formatted_question['choices']}")
                    
                    # Add the answer to the choices
                    choices = formatted_question["choices"]
                    if len(choices) > 0:
                        choices[-1] = formatted_question["answer"]
                    else:
                        choices = ["Option A", "Option B", formatted_question["answer"], "Option C"]
                    
                    formatted_question["choices"] = choices
                
                logger.info(f"[{request_id}] Successfully generated opposites/antonyms question using Langflow API")
                return formatted_question
                
            except json.JSONDecodeError as e:
                logger.error(f"[{request_id}] Error parsing question JSON: {str(e)}")
                logger.error(f"[{request_id}] Raw JSON string: {question_json_str}")
                return get_fallback_question(grade, "English", sub_activity, difficulty)
            
    except httpx.HTTPError as e:
        error_details = {
            "error_type": type(e).__name__,
            "error_message": str(e),
            "url": url,
            "workflow": langflow_workflow
        }
        # For HTTP response errors, try to get more details
        if hasattr(e, 'response') and e.response is not None:
            error_details["status_code"] = e.response.status_code
            try:
                error_details["response_body"] = e.response.text
            except:
                error_details["response_body"] = "Could not extract response body"
                
        logger.error(f"[{request_id}] HTTP error from Langflow API for opposites/antonyms: {error_details}")
        return get_fallback_question(grade, "English", sub_activity, difficulty)
    except Exception as e:
        logger.error(f"[{request_id}] Error calling Langflow API: {str(e)}")
        return get_fallback_question(grade, "English", sub_activity, difficulty)

async def generate_english_synonyms_langflow(grade: int, sub_activity: str, difficulty: str, request_id: str) -> Dict[str, Any]:
    """
    Generate an English synonyms question using Langflow API.
    
    Args:
        grade: Student grade level
        sub_activity: Sub-activity type (Synonyms)
        difficulty: Difficulty level (Easy, Medium, Hard)
        request_id: Unique request identifier for logging
        
    Returns:
        Dictionary containing question data
    """
    logger.info(f"[{request_id}] Generating English synonyms question using Langflow API")
    
    # Get Langflow configuration from environment
    langflow_host = os.getenv("LANGFLOW_HOST", "http://localhost:7860")
    langflow_workflow = os.getenv("LANGFLOW_WORKFLOW_SYNONYMS", "synonyms")
    
    # Construct the API URL
    url = f"{langflow_host}/api/v1/run/{langflow_workflow}"
    
    # Create a unique session ID
    session_id = f"kidskills_{str(uuid.uuid4())}"
    
    # Generate a custom prompt for synonyms questions
    custom_prompt = construct_synonyms_prompt(grade, difficulty)
    logger.debug(f"[{request_id}] Synonyms Prompt: {custom_prompt}")
    
    # Prepare the request payload
    payload = {
        "input_value": custom_prompt,
        "output_type": "chat",
        "input_type": "chat",
        "session_id": str(session_id),
        "output_component": "",
        "tweaks": None,
    }
    
    # Set up headers
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        # Make the API request using httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=HTTPX_TIMEOUT) # Added timeout
            response.raise_for_status()
            
            # Parse the response
            response_data = response.json()
            logger.debug(f"[{request_id}] Langflow Synonyms Response: {response_data}")
            
            # Extract the question JSON string from the response
            question_json_str = extract_question_from_langflow_response(response_data, request_id)
            
            # Clean up session messages to avoid accumulating in Langflow storage
            await delete_langflow_session_messages(session_id, request_id)
            
            # If we couldn't find the question data, use a fallback
            if not question_json_str:
                logger.warning(f"[{request_id}] Could not extract question data from API response")
                logger.warning(f"[{request_id}] Response structure: {json.dumps(response_data, indent=2)[:1000]}")
                return get_fallback_question(grade, "English", sub_activity, difficulty)
            
            # Parse the JSON string to get the question data
            try:
                question_data = json.loads(question_json_str)
                
                # Create a properly formatted question dictionary
                formatted_question = {
                    "question": question_data.get("question", ""),
                    "choices": [str(choice) for choice in question_data.get("choices", [])],
                    "answer": str(question_data.get("answer", "")),
                    "type": "multiple-choice",
                    "sub_activity": sub_activity,
                    "subject": "English",
                    "difficulty": difficulty
                }
                
                # Validate the response
                if not all(key in formatted_question for key in ["question", "choices", "answer"]):
                    logger.warning(f"[{request_id}] Incomplete question data: {formatted_question}")
                    return get_fallback_question(grade, "English", sub_activity, difficulty)
                
                # Ensure we have exactly 4 choices
                if len(formatted_question["choices"]) != 4:
                    logger.warning(f"[{request_id}] Invalid number of choices: {len(formatted_question['choices'])}")
                    
                    # Fix the number of choices
                    choices = formatted_question["choices"]
                    answer = formatted_question["answer"]
                    
                    if len(choices) < 4:
                        # Add additional choices to reach 4
                        while len(choices) < 4:
                            new_choice = f"Option {chr(65 + len(choices))}"  # Option A, Option B, etc.
                            if new_choice not in choices and new_choice != answer:
                                choices.append(new_choice)
                                logger.info(f"[{request_id}] Added extra choice: {new_choice}")
                    elif len(choices) > 4:
                        # Keep the first 3 choices plus the correct answer
                        if answer in choices:
                            # Remove the answer temporarily
                            choices.remove(answer)
                            # Keep only the first 3 other choices
                            choices = choices[:3]
                            # Add the answer back
                            choices.append(answer)
                        else:
                            # Just keep the first 4 choices
                            choices = choices[:4]
                    
                    formatted_question["choices"] = choices
                
                # Ensure the answer is in the choices
                if formatted_question["answer"] not in formatted_question["choices"]:
                    logger.warning(f"[{request_id}] Answer not in choices: {formatted_question['answer']} not in {formatted_question['choices']}")
                    
                    # Add the answer to the choices
                    choices = formatted_question["choices"]
                    if len(choices) > 0:
                        choices[-1] = formatted_question["answer"]
                    else:
                        choices = ["Option A", "Option B", formatted_question["answer"], "Option C"]
                    
                    formatted_question["choices"] = choices
                
                logger.info(f"[{request_id}] Successfully generated synonyms question using Langflow API")
                return formatted_question
                
            except json.JSONDecodeError as e:
                logger.error(f"[{request_id}] Error parsing question JSON: {str(e)}")
                logger.error(f"[{request_id}] Raw JSON string: {question_json_str}")
                return get_fallback_question(grade, "English", sub_activity, difficulty)
            
    except httpx.HTTPError as e:
        error_details = {
            "error_type": type(e).__name__,
            "error_message": str(e),
            "url": url,
            "workflow": langflow_workflow
        }
        # For HTTP response errors, try to get more details
        if hasattr(e, 'response') and e.response is not None:
            error_details["status_code"] = e.response.status_code
            try:
                error_details["response_body"] = e.response.text
            except:
                error_details["response_body"] = "Could not extract response body"
                
        logger.error(f"[{request_id}] HTTP error from Langflow API for synonyms: {error_details}")
        return get_fallback_question(grade, "English", sub_activity, difficulty)
    except Exception as e:
        logger.error(f"[{request_id}] Error calling Langflow API: {str(e)}")
        return get_fallback_question(grade, "English", sub_activity, difficulty)

async def generate_grammar_correction_langflow(grade: int, difficulty: str, request_id: str) -> Dict[str, Any]:
    """
    Generate a grammar correction question using Langflow API.
    
    Args:
        grade: Student grade level (1-5)
        difficulty: Difficulty level ("Easy", "Medium", "Hard")
        request_id: Unique request identifier for logging
        
    Returns:
        Dictionary containing question data
    """
    logger.info(f"[{request_id}] Generating grammar correction question using Langflow API")
    
    # Get Langflow configuration from environment
    langflow_host = os.getenv("LANGFLOW_HOST", "http://localhost:7860")
    langflow_workflow = os.getenv("LANGFLOW_WORKFLOW_GRAMMAR_CORRECTION", "grammar-correction")
    
    # Construct the API URL
    url = f"{langflow_host}/api/v1/run/{langflow_workflow}"
    
    # Create a unique session ID
    session_id = f"kidskills_{str(uuid.uuid4())}"
    
    # Generate a custom prompt for grammar correction questions
    custom_prompt = construct_grammar_correction_prompt(grade, difficulty)
    logger.debug(f"[{request_id}] Grammar Correction Prompt: {custom_prompt}")
    
    # Prepare the request payload
    payload = {
        "input_value": custom_prompt,
        "output_type": "chat",
        "input_type": "chat",
        "session_id": str(session_id),
        "output_component": "",
        "tweaks": None,
    }
    
    # Set up headers
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        # Make the API request using httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=HTTPX_TIMEOUT) # Added timeout
            response.raise_for_status()
            
            # Parse the response
            response_data = response.json()
            logger.debug(f"[{request_id}] Langflow Grammar Correction Response: {response_data}")
            
            # Extract the question JSON string from the response
            question_json_str = extract_question_from_langflow_response(response_data, request_id)
            
            # Clean up session messages to avoid accumulating in Langflow storage
            # We do this in a fire-and-forget manner to not block the response
            await delete_langflow_session_messages(session_id, request_id)
            
            # If we couldn't find the question data, use a fallback
            if not question_json_str:
                logger.warning(f"[{request_id}] Could not extract question data from Langflow API response")
                return get_fallback_grammar_correction(grade, difficulty)
            
            # Parse the JSON string to get the question data
            try:
                question_data = json.loads(question_json_str)
                
                # Create a properly formatted question dictionary
                formatted_question = {
                    "question": question_data.get("question", ""),
                    "answer": question_data.get("answer", ""),
                    "type": "direct-answer",
                    "sub_activity": "Grammar Correction"
                }
                
                # Validate the response
                if not all(key in formatted_question for key in ["question", "answer"]):
                    logger.warning(f"[{request_id}] Incomplete question data: {formatted_question}")
                    return get_fallback_grammar_correction(grade, difficulty)
                
                # Remove any choices if they exist (grammar correction is direct-answer type)
                if "choices" in formatted_question:
                    del formatted_question["choices"]
                
                logger.info(f"[{request_id}] Successfully generated grammar correction question using Langflow API")
                return formatted_question
                
            except json.JSONDecodeError as e:
                logger.error(f"[{request_id}] Error parsing grammar correction JSON: {str(e)}")
                logger.error(f"[{request_id}] Raw JSON string: {question_json_str}")
                return get_fallback_grammar_correction(grade, difficulty)
            
    except httpx.HTTPError as e:
        error_details = {
            "error_type": type(e).__name__,
            "error_message": str(e),
            "url": url,
            "workflow": langflow_workflow
        }
        # For HTTP response errors, try to get more details
        if hasattr(e, 'response') and e.response is not None:
            error_details["status_code"] = e.response.status_code
            try:
                error_details["response_body"] = e.response.text
            except:
                error_details["response_body"] = "Could not extract response body"
                
        logger.error(f"[{request_id}] HTTP error from Langflow API for grammar correction: {error_details}")
        return get_fallback_grammar_correction(grade, difficulty)
    except Exception as e:
        logger.error(f"[{request_id}] Error calling Langflow API for grammar correction: {str(e)}")
        return get_fallback_grammar_correction(grade, difficulty)

def get_fallback_grammar_correction(grade: int, difficulty: str) -> Dict[str, Any]:
    """
    Generate a fallback grammar correction question when the API fails.
    
    Args:
        grade: Student grade level
        difficulty: Difficulty level (Easy, Medium, Hard)
        
    Returns:
        Dictionary containing fallback question data
    """
    # Define simple fallback questions based on grade level
    fallbacks = [
        {
            "question": "The dog run very fast. 🐕",
            "answer": "The dog runs very fast.",
            "type": "direct-answer",
            "sub_activity": "Grammar Correction"
        },
        {
            "question": "She don't like ice cream. 🍦",
            "answer": "She doesn't like ice cream.",
            "type": "direct-answer",
            "sub_activity": "Grammar Correction"
        },
        {
            "question": "They is going to the park. 🌳",
            "answer": "They are going to the park.",
            "type": "direct-answer",
            "sub_activity": "Grammar Correction"
        },
        {
            "question": "The cats is playing. 😺",
            "answer": "The cats are playing.",
            "type": "direct-answer",
            "sub_activity": "Grammar Correction"
        },
        {
            "question": "He walk to school yesterday. 🏫",
            "answer": "He walked to school yesterday.",
            "type": "direct-answer",
            "sub_activity": "Grammar Correction"
        }
    ]
    
    # Return a random fallback question
    return random.choice(fallbacks)

async def evaluate_grammar_correction_langflow(user_answer: str, correct_answer: str, question: str, is_correct: bool, trace_id: str) -> Dict[str, Any]:
    """
    Evaluate grammar correction answers using Langflow API.
    
    Args:
        user_answer: User's answer
        correct_answer: Correct answer to the question
        question: The question that was asked
        is_correct: Whether the user's answer was correct
        trace_id: Trace ID for logging
        
    Returns:
        Dictionary with feedback on the answer
    """
    logger.info(f"[{trace_id}] Evaluating grammar correction using Langflow API")
    
    # Get Langflow configuration from environment
    langflow_host = os.getenv("LANGFLOW_HOST", "http://localhost:7860")
    langflow_workflow = os.getenv("LANGFLOW_WORKFLOW_GRAMMAR_EVALUATION", "grammar-evaluation")
    
    # Construct the API URL
    url = f"{langflow_host}/api/v1/run/{langflow_workflow}"
    
    # Create a unique session ID
    session_id = f"kidskills_{str(uuid.uuid4())}"
    
    # Prepare the evaluation prompt
    eval_prompt = f"""
    Question: {question}
    Correct answer: {correct_answer}
    Student answer: {user_answer}
    Is correct: {"Yes" if is_correct else "No"}
    
    Provide friendly, encouraging feedback for this elementary school student's grammar correction.
    If the answer is correct, praise them and explain why it's correct.
    If incorrect, be encouraging and explain the grammar rule they missed, but don't give away the answer directly.
    Use simple language appropriate for young children and include a positive emoji at the end.
    
    Return only a JSON with these fields:
    - "is_correct": true/false (whether the student's answer is correct)
    - "feedback": your detailed, age-appropriate feedback
    """
    
    # Prepare the request payload
    payload = {
        "input_value": eval_prompt,
        "output_type": "chat",
        "input_type": "chat",
        "session_id": str(session_id),
        "output_component": "",
        "tweaks": None,
    }
    
    # Set up headers
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        # Make the API request using httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=HTTPX_TIMEOUT) # Added timeout
            response.raise_for_status()
            
            # Parse the response
            response_data = response.json()
            
            # Extract the feedback JSON string from the response
            feedback_json_str = extract_question_from_langflow_response(response_data, trace_id)
            
            # Clean up session messages to avoid accumulating in Langflow storage
            # We do this in a fire-and-forget manner to not block the response
            await delete_langflow_session_messages(session_id, trace_id)
            
            # If we couldn't find the feedback data, use a fallback
            if not feedback_json_str:
                logger.warning(f"[{trace_id}] Could not extract feedback data from Langflow API response")
                return get_fallback_feedback(is_correct)
            
            # Parse the JSON string to get the feedback data
            try:
                feedback_data = json.loads(feedback_json_str)
                
                # Validate the response
                if not all(key in feedback_data for key in ["is_correct", "feedback"]):
                    # Check if we have "correct" but not "is_correct"
                    if "correct" in feedback_data and "feedback" in feedback_data:
                        # Transform the response to use is_correct instead of correct
                        feedback_data["is_correct"] = feedback_data.pop("correct")
                    else:
                        logger.warning(f"[{trace_id}] Incomplete feedback data: {feedback_data}")
                        return get_fallback_feedback(is_correct)
                
                logger.info(f"[{trace_id}] Successfully evaluated grammar correction using Langflow API")
                return feedback_data
                
            except json.JSONDecodeError as e:
                logger.error(f"[{trace_id}] Error parsing grammar correction feedback JSON: {str(e)}")
                logger.error(f"[{trace_id}] Raw JSON string: {feedback_json_str}")
                return get_fallback_feedback(is_correct)
            
    except httpx.HTTPError as e:
        error_details = {
            "error_type": type(e).__name__,
            "error_message": str(e),
            "url": url,
            "workflow": langflow_workflow
        }
        # For HTTP response errors, try to get more details
        if hasattr(e, 'response') and e.response is not None:
            error_details["status_code"] = e.response.status_code
            try:
                error_details["response_body"] = e.response.text
            except:
                error_details["response_body"] = "Could not extract response body"
                
        logger.error(f"[{trace_id}] HTTP error from Langflow API for grammar evaluation: {error_details}")
        return get_fallback_grammar_evaluation(question, user_answer, correct_answer)
    except Exception as e:
        logger.error(f"[{trace_id}] Error calling Langflow API for grammar evaluation: {str(e)}")
        return get_fallback_grammar_evaluation(question, user_answer, correct_answer)

async def evaluate_reading_comprehension_langflow(passage: str, question: str, user_answer: str, correct_answer: str, trace_id: str) -> Dict[str, Any]:
    """
    Evaluate reading comprehension answers using Langflow API.
    
    Args:
        passage: The reading passage text
        question: The question about the passage
        user_answer: The student's answer
        correct_answer: The correct answer from the original question
        trace_id: Trace ID for logging
        
    Returns:
        Dictionary with feedback on the answer
    """
    logger.info(f"[{trace_id}] Evaluating reading comprehension using Langflow API")
    
    # Get Langflow configuration from environment
    langflow_host = os.getenv("LANGFLOW_HOST", "http://localhost:7860")
    langflow_workflow = os.getenv("LANGFLOW_WORKFLOW_READING_COMPREHENSION", "reading-comprehension")
    
    # Construct the API URL
    url = f"{langflow_host}/api/v1/run/{langflow_workflow}"
    
    # Create a unique session ID
    session_id = f"kidskills_{str(uuid.uuid4())}"
    
    # Prepare the evaluation prompt
    eval_prompt = f"""
    Reading Passage: {passage}
    
    Question: {question}
    
    Correct answer: {correct_answer}
    
    Student answer: {user_answer}
    
    Provide friendly, encouraging feedback for this elementary school student's reading comprehension answer.
    Evaluate whether the student's answer is correct based on understanding the passage, not just exact word matching.
    Use simple language appropriate for young children and include a positive emoji at the end.
    
    Return only a JSON with these fields:
    - "is_correct": true/false (whether the student's answer correctly addresses the question)
    - "feedback": your detailed, age-appropriate feedback
    """
    
    # Prepare the request payload
    payload = {
        "input_value": eval_prompt,
        "output_type": "chat",
        "input_type": "chat",
        "session_id": str(session_id),
        "output_component": "",
        "tweaks": None,
    }
    
    # Set up headers
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        # Make the API request using httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=HTTPX_TIMEOUT) # Added timeout
            response.raise_for_status()
            
            # Parse the response
            response_data = response.json()
            
            # Extract the feedback JSON string from the response
            feedback_json_str = extract_question_from_langflow_response(response_data, trace_id)
            
            # Clean up session messages to avoid accumulating in Langflow storage
            # We do this in a fire-and-forget manner to not block the response
            await delete_langflow_session_messages(session_id, trace_id)
            
            # If we couldn't find the feedback data, use a fallback
            if not feedback_json_str:
                logger.warning(f"[{trace_id}] Could not extract feedback data from Langflow API response")
                return get_fallback_reading_evaluation(user_answer, correct_answer)
            
            # Parse the JSON string to get the feedback data
            try:
                feedback_data = json.loads(feedback_json_str)
                
                # Validate the response
                if not all(key in feedback_data for key in ["is_correct", "feedback"]):
                    logger.warning(f"[{trace_id}] Incomplete feedback data: {feedback_data}")
                    return get_fallback_reading_evaluation(user_answer, correct_answer)
                
                logger.info(f"[{trace_id}] Successfully evaluated reading comprehension using Langflow API")
                return feedback_data
                
            except json.JSONDecodeError as e:
                logger.error(f"[{trace_id}] Error parsing reading comprehension feedback JSON: {str(e)}")
                logger.error(f"[{trace_id}] Raw JSON string: {feedback_json_str}")
                return get_fallback_reading_evaluation(user_answer, correct_answer)
            
    except httpx.HTTPError as e:
        error_details = {
            "error_type": type(e).__name__,
            "error_message": str(e),
            "url": url,
            "workflow": langflow_workflow
        }
        # For HTTP response errors, try to get more details
        if hasattr(e, 'response') and e.response is not None:
            error_details["status_code"] = e.response.status_code
            try:
                error_details["response_body"] = e.response.text
            except:
                error_details["response_body"] = "Could not extract response body"
                
        logger.error(f"[{trace_id}] HTTP error from Langflow API for reading comprehension evaluation: {error_details}")
        return get_fallback_reading_evaluation(user_answer, correct_answer)
    except Exception as e:
        logger.error(f"[{trace_id}] Error calling Langflow API for reading comprehension evaluation: {str(e)}")
        return get_fallback_reading_evaluation(user_answer, correct_answer)

async def generate_mario_english_langflow(grade: int, sub_activity: str, difficulty: str, request_id: str) -> Dict[str, Any]:
    """
    Generate a Mushroom Kingdom Vocabulary English question using Langflow API.
    
    Args:
        grade: Student grade level (2-3)
        sub_activity: Sub-activity type ("Mushroom Kingdom Vocabulary")
        difficulty: Difficulty level ("Easy", "Medium", "Hard")
        request_id: Unique request identifier for logging
        
    Returns:
        Dictionary containing question data
    """
    logger.info(f"[{request_id}] Generating Mario English question using Langflow API")
    
    # Get Langflow configuration from environment
    langflow_host = os.getenv("LANGFLOW_HOST", "http://localhost:7860")
    langflow_workflow = os.getenv("LANGFLOW_WORKFLOW_MARIO_ENGLISH", "mario-english")
    
    # Construct the API URL
    url = f"{langflow_host}/api/v1/run/{langflow_workflow}"
    
    # Create a unique session ID
    session_id = f"kidskills_{str(uuid.uuid4())}"
    
    # Generate a custom prompt for Mario English questions
    custom_prompt = construct_mario_english_prompt(grade, difficulty)
    logger.debug(f"[{request_id}] Mario English Prompt: {custom_prompt}")
    
    # Prepare the request payload
    payload = {
        "input_value": custom_prompt,
        "output_type": "chat",
        "input_type": "chat",
        "session_id": str(session_id),
        "output_component": "",
        "tweaks": None,
    }
    
    # Set up headers
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        # Make the API request using httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=HTTPX_TIMEOUT) # Added timeout
            response.raise_for_status()
            
            # Parse the response
            response_data = response.json()
            logger.debug(f"[{request_id}] Langflow Mario English Response: {response_data}")
            
            # Extract the question JSON string from the response
            question_json_str = extract_question_from_langflow_response(response_data, request_id)
            
            # Clean up session messages to avoid accumulating in Langflow storage
            await delete_langflow_session_messages(session_id, request_id)
            
            # If we couldn't find the question data, use a fallback
            if not question_json_str:
                logger.warning(f"[{request_id}] Could not extract question data from API response")
                logger.warning(f"[{request_id}] Response structure: {json.dumps(response_data, indent=2)[:1000]}")
                return get_fallback_question(grade, "English", sub_activity, difficulty)
            
            # Parse the JSON string to get the question data
            try:
                question_data = json.loads(question_json_str)
                
                # Create a properly formatted question dictionary
                formatted_question = {
                    "question": question_data.get("question", ""),
                    "choices": [str(choice) for choice in question_data.get("choices", [])],
                    "answer": str(question_data.get("answer", "")),
                    "type": "multiple-choice",
                    "sub_activity": sub_activity,
                    "subject": "English",
                    "difficulty": difficulty
                }
                
                # Validate the response
                if not all(key in formatted_question for key in ["question", "choices", "answer"]):
                    logger.warning(f"[{request_id}] Incomplete question data: {formatted_question}")
                    return get_fallback_question(grade, "English", sub_activity, difficulty)
                
                # Ensure we have exactly 4 choices
                if len(formatted_question["choices"]) != 4:
                    logger.warning(f"[{request_id}] Invalid number of choices: {len(formatted_question['choices'])}")
                    
                    # Fix the number of choices
                    choices = formatted_question["choices"]
                    if len(choices) < 4:
                        # Add placeholder choices if we don't have enough
                        while len(choices) < 4:
                            new_choice = f"Option {len(choices) + 1}"
                            choices.append(new_choice)
                    else:
                        # Truncate to 4 choices if we have too many
                        choices = choices[:4]
                    
                    formatted_question["choices"] = choices
                
                # Ensure the answer is in the choices
                if formatted_question["answer"] not in formatted_question["choices"]:
                    logger.warning(f"[{request_id}] Answer not in choices: {formatted_question['answer']} not in {formatted_question['choices']}")
                    
                    # Add the answer to the choices
                    choices = formatted_question["choices"]
                    if len(choices) > 0:
                        choices[-1] = formatted_question["answer"]
                    else:
                        choices = ["Option A", "Option B", formatted_question["answer"], "Option C"]
                    
                    formatted_question["choices"] = choices
                
                logger.info(f"[{request_id}] Successfully generated Mario English question using Langflow API")
                return formatted_question
                
            except json.JSONDecodeError as e:
                logger.error(f"[{request_id}] Error parsing question JSON: {str(e)}")
                logger.error(f"[{request_id}] Raw JSON string: {question_json_str}")
                return get_fallback_question(grade, "English", sub_activity, difficulty)
            
    except httpx.HTTPError as e:
        error_details = {
            "error_type": type(e).__name__,
            "error_message": str(e),
            "url": url,
            "workflow": langflow_workflow
        }
        # For HTTP response errors, try to get more details
        if hasattr(e, 'response') and e.response is not None:
            error_details["status_code"] = e.response.status_code
            try:
                error_details["response_body"] = e.response.text
            except:
                error_details["response_body"] = "Could not extract response body"
                
        logger.error(f"[{request_id}] HTTP error from Langflow API for Mario English: {error_details}")
        return get_fallback_question(grade, "English", sub_activity, difficulty)
    except Exception as e:
        logger.error(f"[{request_id}] Error calling Langflow API: {str(e)}")
        return get_fallback_question(grade, "English", sub_activity, difficulty)

async def generate_english_nouns_pronouns_langflow(grade: int, sub_activity: str, difficulty: str, request_id: str) -> Dict[str, Any]:
    """
    Generate an English nouns/pronouns question using Langflow API.
    
    Args:
        grade: Student grade level
        sub_activity: Sub-activity type (Nouns/Pronouns)
        difficulty: Difficulty level (Easy, Medium, Hard)
        request_id: Unique request identifier for logging
        
    Returns:
        Dictionary containing question data
    """
    logger.info(f"[{request_id}] Generating English nouns/pronouns question using Langflow API")
    
    # Get Langflow configuration from environment
    langflow_host = os.getenv("LANGFLOW_HOST", "http://localhost:7860")
    langflow_workflow = os.getenv("LANGFLOW_WORKFLOW_NOUNS_PRONOUNS", "nouns-pronouns")
    
    # Construct the API URL
    url = f"{langflow_host}/api/v1/run/{langflow_workflow}"
    
    # Create a unique session ID
    session_id = f"kidskills_{str(uuid.uuid4())}"
    
    # Generate a custom prompt for nouns/pronouns questions
    custom_prompt = construct_nouns_pronouns_prompt(grade, difficulty)
    logger.debug(f"[{request_id}] Nouns/Pronouns Prompt: {custom_prompt}")
    
    # Prepare the request payload
    payload = {
        "input_value": custom_prompt,
        "output_type": "chat",
        "input_type": "chat",
        "session_id": str(session_id),
        "output_component": "",
        "tweaks": None,
    }
    
    # Set up headers
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        # Make the API request using httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=HTTPX_TIMEOUT) # Added timeout
            response.raise_for_status()
            
            # Parse the response
            response_data = response.json()
            logger.debug(f"[{request_id}] Langflow Nouns/Pronouns Response: {response_data}")
            
            # Extract the question JSON string from the response
            question_json_str = extract_question_from_langflow_response(response_data, request_id)
            
            # Clean up session messages to avoid accumulating in Langflow storage
            await delete_langflow_session_messages(session_id, request_id)
            
            # If we couldn't find the question data, use a fallback
            if not question_json_str:
                logger.warning(f"[{request_id}] Could not extract question data from API response")
                logger.warning(f"[{request_id}] Response structure: {json.dumps(response_data, indent=2)[:1000]}")
                return get_fallback_question(grade, "English", sub_activity, difficulty)
            
            # Parse the JSON string to get the question data
            try:
                question_data = json.loads(question_json_str)
                
                # Create a properly formatted question dictionary
                formatted_question = {
                    "question": question_data.get("question", ""),
                    "choices": [str(choice) for choice in question_data.get("choices", [])],
                    "answer": str(question_data.get("answer", "")),
                    "type": "multiple-choice",
                    "sub_activity": sub_activity,
                    "subject": "English",
                    "difficulty": difficulty
                }
                
                # Validate the response
                if not all(key in formatted_question for key in ["question", "choices", "answer"]):
                    logger.warning(f"[{request_id}] Incomplete question data: {formatted_question}")
                    return get_fallback_question(grade, "English", sub_activity, difficulty)
                
                # Ensure we have exactly 4 choices
                if len(formatted_question["choices"]) != 4:
                    logger.warning(f"[{request_id}] Invalid number of choices: {len(formatted_question['choices'])}")
                    
                    # Fix the number of choices
                    choices = formatted_question["choices"]
                    answer = formatted_question["answer"]
                    
                    if len(choices) < 4:
                        # Add additional choices to reach 4
                        while len(choices) < 4:
                            new_choice = f"Option {chr(65 + len(choices))}"  # Option A, Option B, etc.
                            if new_choice not in choices and new_choice != answer:
                                choices.append(new_choice)
                                logger.info(f"[{request_id}] Added extra choice: {new_choice}")
                    elif len(choices) > 4:
                        # Keep the first 3 choices plus the correct answer
                        if answer in choices:
                            # Remove the answer temporarily
                            choices.remove(answer)
                            # Keep only the first 3 other choices
                            choices = choices[:3]
                            # Add the answer back
                            choices.append(answer)
                        else:
                            # Just keep the first 4 choices
                            choices = choices[:4]
                    
                    formatted_question["choices"] = choices
                
                # Ensure the answer is in the choices
                if formatted_question["answer"] not in formatted_question["choices"]:
                    logger.warning(f"[{request_id}] Answer not in choices: {formatted_question['answer']} not in {formatted_question['choices']}")
                    
                    # Add the answer to the choices
                    choices = formatted_question["choices"]
                    if len(choices) > 0:
                        choices[-1] = formatted_question["answer"]
                    else:
                        choices = ["Option A", "Option B", formatted_question["answer"], "Option C"]
                    
                    formatted_question["choices"] = choices
                
                logger.info(f"[{request_id}] Successfully generated nouns/pronouns question using Langflow API")
                return formatted_question
                
            except json.JSONDecodeError as e:
                logger.error(f"[{request_id}] Error parsing question JSON: {str(e)}")
                logger.error(f"[{request_id}] Raw JSON string: {question_json_str}")
                return get_fallback_question(grade, "English", sub_activity, difficulty)
            
    except httpx.HTTPError as e:
        error_details = {
            "error_type": type(e).__name__,
            "error_message": str(e),
            "url": url,
            "workflow": langflow_workflow
        }
        # For HTTP response errors, try to get more details
        if hasattr(e, 'response') and e.response is not None:
            error_details["status_code"] = e.response.status_code
            try:
                error_details["response_body"] = e.response.text
            except:
                error_details["response_body"] = "Could not extract response body"
                
        logger.error(f"[{request_id}] HTTP error from Langflow API for nouns/pronouns: {error_details}")
        return get_fallback_question(grade, "English", sub_activity, difficulty)
    except Exception as e:
        logger.error(f"[{request_id}] Error calling Langflow API: {str(e)}")
        return get_fallback_question(grade, "English", sub_activity, difficulty)

def extract_question_from_langflow_response(response_data: Dict[str, Any], request_id: str) -> Optional[str]:
    """
    Extract the question JSON string from the nested Langflow API response structure.

    Args:
        response_data: The parsed JSON response from the Langflow API
        request_id: Unique request identifier for logging

    Returns:
        The extracted question JSON string or None if not found
    """
    question_json_str = None

    try:
        # First, check if the response has the structure we expect
        if 'outputs' in response_data and isinstance(response_data['outputs'], list) and len(response_data['outputs']) > 0:
            main_output = response_data['outputs'][0]

            # Try to find the question data in the outputs array
            if 'outputs' in main_output and isinstance(main_output['outputs'], list) and len(main_output['outputs']) > 0:
                output_data = main_output['outputs'][0]

                # Try to extract from results -> message -> text
                if 'results' in output_data and 'message' in output_data['results'] and 'text' in output_data['results']['message']:
                    question_json_str = output_data['results']['message']['text']
                    logger.info(f"[{request_id}] Found question data in results.message.text")

                # Try to extract from results -> message -> data -> text
                elif ('results' in output_data and 'message' in output_data['results'] and
                      'data' in output_data['results']['message'] and 'text' in output_data['results']['message']['data']):
                    question_json_str = output_data['results']['message']['data']['text']
                    logger.info(f"[{request_id}] Found question data in results.message.data.text")

                # Try to extract from outputs -> message -> message
                elif 'outputs' in output_data and 'message' in output_data['outputs'] and 'message' in output_data['outputs']['message']:
                    question_json_str = output_data['outputs']['message']['message']
                    logger.info(f"[{request_id}] Found question data in outputs.message.message")

                # Try to extract from artifacts -> message
                elif 'artifacts' in output_data and 'message' in output_data['artifacts']:
                    question_json_str = output_data['artifacts']['message']
                    logger.info(f"[{request_id}] Found question data in artifacts.message")

                # Try to extract from messages
                elif 'messages' in output_data and isinstance(output_data['messages'], list) and len(output_data['messages']) > 0:
                    if 'message' in output_data['messages'][0]:
                        question_json_str = output_data['messages'][0]['message']
                        logger.info(f"[{request_id}] Found question data in messages[0].message")
    except Exception as e:
        logger.error(f"[{request_id}] Error extracting question data from response: {str(e)}")

    # If we found a JSON string, clean it up and extract only the JSON part
    if question_json_str:
        # Remove <think> tags FIRST
        question_json_str = remove_think_tags(question_json_str) # Ensure tags are removed

        question_json_str = question_json_str.strip()

        # Try to extract just the JSON part from the text
        try:
            # Find the first occurrence of '{'
            json_start = question_json_str.find('{')
            # Find the last occurrence of '}'
            json_end = question_json_str.rfind('}')

            if json_start != -1 and json_end != -1 and json_end > json_start:
                # Extract from the first '{' to the last '}'
                question_json_str = question_json_str[json_start:json_end+1]
                logger.info(f"[{request_id}] Extracted JSON part from position {json_start} to {json_end}")
            elif json_start != -1:
                 # Fallback: extract from the first '{' to the end if no '}' found or in wrong order
                 question_json_str = question_json_str[json_start:]
                 logger.warning(f"[{request_id}] Extracted JSON part starting at position {json_start}, but couldn't find balanced braces.")

        except Exception as e:
            logger.error(f"[{request_id}] Error extracting JSON part: {str(e)}")

        logger.info(f"[{request_id}] Cleaned JSON string: {question_json_str}")

    return question_json_str