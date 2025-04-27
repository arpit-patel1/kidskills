import os
import json
import time
import random
import re
import logging
from typing import Dict, Any, Optional, List, Literal, Union, Callable, Tuple
from dotenv import load_dotenv
from pydantic import BaseModel, Field, validator, ValidationError, root_validator
from ollama import AsyncClient
from .fallback_questions import get_fallback_question as get_fallback
from .prompts import construct_prompt, construct_mario_english_prompt
import math
import operator
import httpx
import uuid
import asyncio

# Load environment variables
load_dotenv()

# Get Ollama configuration from env
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
ENABLE_MATH_TOOLS = os.getenv("ENABLE_MATH_TOOLS", "true").lower() == "true"

# Initialize Ollama client with configured base URL
ollama_async_client = AsyncClient(host=OLLAMA_BASE_URL)

# Log configuration settings
logger = logging.getLogger(__name__)
logger.info(f"OLLAMA_MODEL: {OLLAMA_MODEL}")
logger.info(f"OLLAMA_BASE_URL: {OLLAMA_BASE_URL}")
logger.info(f"ENABLE_MATH_TOOLS: {ENABLE_MATH_TOOLS}")

# Import constants from constants.py
from .constants import (
    NAMES, MATH_NAMES, READING_TOPICS, READING_LOCATIONS,
    MATH_OBJECTS, MATH_LOCATIONS, MATH_ACTIVITIES, MATH_WORD_PROBLEM_TEMPLATES,
    ENGLISH_TOPICS, ENGLISH_VERBS, ENGLISH_ADJECTIVES, ENGLISH_NOUNS,
    ENGLISH_WORD_PATTERNS, ENGLISH_GRAMMAR_TEMPLATES,
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

logger = logging.getLogger(__name__)
logger.info(f"Logging to {log_file}")

# Get Ollama model from env or use default
logger.info(f"Using Ollama model: {OLLAMA_MODEL}")

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

def clean_markdown_json(text: str) -> str:
    """
    Clean JSON from markdown code blocks and remove any extra text.
    
    Args:
        text: Text that might contain markdown code blocks
        
    Returns:
        Cleaned JSON string
    """
    # Remove leading/trailing whitespace
    text = text.strip()
    
    # Handle markdown code blocks with language specifiers
    if "```" in text:
        # Find the first code block opening
        start_idx = text.find("```")
        # Find where the actual JSON content starts (skip language specifier if present)
        content_start = text.find("\n", start_idx) + 1
        
        # Find the closing code block
        end_idx = text.find("```", content_start)
        if end_idx == -1:  # No closing code block found
            # Just take everything after the opening code block
            json_content = text[content_start:]
        else:
            # Extract the content between the code block markers
            json_content = text[content_start:end_idx].strip()
        
        return json_content
    
    # Try to find JSON object boundaries if no code blocks
    if text.strip().startswith("{") and "}" in text:
        # Find first opening brace
        start_idx = text.find("{")
        # Find last closing brace
        end_idx = text.rfind("}")
        if end_idx > start_idx:
            return text[start_idx:end_idx+1]
    
    # If no clear JSON markers, return the original (stripped)
    return text

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
    Generate a multiple choice question.
    
    For math and English activities, this uses the Langflow API.
    For other subjects/activities, it uses the Ollama-based implementation.
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
    
    # For other subjects, use the existing implementation
    temperature = 0.7  # default
    logger.info(f"[{request_id}] Using temperature of {temperature} for {subject} {sub_activity}")
    
    # Construct prompt specifically for multiple choice
    prompt = construct_prompt(grade, subject, sub_activity, difficulty, "multiple-choice")
    logger.info(f"[{request_id}] Constructed prompt: {prompt}")
    
    # Create system message with explicit format requirements
    system_message = """You are an AI that generates educational multiple-choice questions for elementary school students.
Your responses MUST be in valid JSON format with the following fields:
1. 'question': The question text
2. 'choices': An array of EXACTLY 4 possible answers
3. 'answer': The correct answer (which must be one of the choices)
4. 'type': Must be exactly "multiple-choice"

Example format:
{
  "question": "What is 2 + 2? 🔢",
  "choices": ["3", "4", "5", "6"],
  "answer": "4",
  "type": "multiple-choice"
}

IMPORTANT: Always include all these fields exactly as shown.
IMPORTANT: Always provide EXACTLY 4 choices for the multiple-choice question. No more, no less.
IMPORTANT: Always add multiple emojis to the question text to make it more engaging for children. Add emojis at the beginning, in the middle, and at the end of questions. For example: "🌍 What is the capital of France? This is a geography question! 🗼 🏙️"""
    
    try:
        # Make API call
        start_time = time.time()
        
        # Generate a random seed for variety
        random_seed = getRandomSeed()
        logger.info(f"[{request_id}] Using random seed: {random_seed}")
        
        ollama_response = await ollama_async_client.chat(
            model=os.getenv("OLLAMA_MODEL"),
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            options={"temperature": temperature, "seed": random_seed},
            stream=False
        )
        
        logger.info(f"[{request_id}] OLLAMA response: {ollama_response}")
        api_time = time.time() - start_time
        logger.info(f"[{request_id}] API call completed in {api_time:.2f}s")
        
        # Extract the content
        content = ollama_response.message.content
        logger.info(f"[{request_id}] Raw content: {content[:100]}...")
        
        # Parse the JSON response
        json_data = json.loads(content)
        
        # Validate the response has the required fields
        if not all(field in json_data for field in ["question", "choices", "answer"]):
            logger.warning(f"[{request_id}] Incomplete JSON response: {json_data}")
            return get_fallback_question(grade, subject, sub_activity, difficulty)
        
        # Ensure all choices and answer are strings
        json_data["choices"] = [str(choice) for choice in json_data["choices"]]
        json_data["answer"] = str(json_data["answer"])
        
        # Ensure we have exactly 4 choices
        choices = json_data["choices"]
        if len(choices) != 4:
            logger.warning(f"[{request_id}] Wrong number of choices: {len(choices)}")
            
            # Fix the number of choices
            if len(choices) < 4:
                # Add placeholder choices if we don't have enough
                while len(choices) < 4:
                    new_choice = f"Option {len(choices) + 1}"
                    choices.append(new_choice)
                logger.info(f"[{request_id}] Added placeholder choices: {choices}")
            else:
                # Truncate to 4 choices if we have too many
                choices = choices[:4]
                logger.info(f"[{request_id}] Truncated to 4 choices: {choices}")
            
            json_data["choices"] = choices
        
        # Set the correct type
        json_data["type"] = "multiple-choice"
        
        # Add subject info
        json_data["subject"] = subject
        json_data["sub_activity"] = sub_activity
        json_data["difficulty"] = difficulty
        
        return json_data
        
    except Exception as e:
        logger.error(f"[{request_id}] Error generating multiple-choice question: {str(e)}")
        logger.exception(e)  # Log the full stack trace
        return get_fallback_question(grade, subject, sub_activity, difficulty)

async def generate_direct_answer_question(grade: int, subject: str, sub_activity: str, difficulty: str, request_id: str) -> Dict[str, Any]:
    """Generate a direct answer question."""
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
            logger.info(f"[{request_id}] Falling back to Ollama for Grammar Correction")
    
    # Grammar correction uses higher temperature
    temperature = 0.7 if sub_activity == "Grammar Correction" else 0.5
    logger.info(f"[{request_id}] Using temperature of {temperature} for direct answer")
    
    # Construct prompt specifically for direct answer
    prompt = construct_prompt(grade, subject, sub_activity, difficulty, "direct-answer")
    logger.info(f"[{request_id}] Constructed prompt: {prompt[:100]}...")
    
   
    # Create system message with explicit format requirements
    system_message = """You are an AI that generates educational direct-answer questions for elementary school students.
Your responses MUST be in valid JSON format with the following fields:
1. 'question': The question text
2. 'answer': The correct answer
3. 'type': Must be exactly "direct-answer"

Example format:
{
  "question": "What is the capital of France? 🗼",
  "answer": "Paris",
  "type": "direct-answer"
}

IMPORTANT: Always include all these fields exactly as shown.
IMPORTANT: Always add multiple emojis to the question text to make it more engaging for children. Add emojis at the beginning, in the middle, and at the end of questions. For example: "🌍 What is the capital of France? This is a geography question! 🗼 🏙️"""
    
    if sub_activity == "Grammar Correction":
        system_message += """ For Grammar Correction, provide a sentence with a grammatical error that the student needs to correct.

Example for Grammar Correction:
{
  "question": "The dog run very fast.",
  "answer": "The dog runs very fast.",
  "type": "direct-answer"
}
"""
    
    try:

        # Make API call
        start_time = time.time()
        
        # Generate a random seed for variety
        random_seed = getRandomSeed()
        logger.info(f"[{request_id}] Using random seed: {random_seed} for direct answer")

        ollama_response = await ollama_async_client.chat(model=os.getenv("OLLAMA_MODEL"),
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            format=DirectAnswerQuestion.model_json_schema(),
            options={"temperature": temperature, "seed": random_seed},
        )

        logger.info(f"[{request_id}] OLLAMA response: {ollama_response}")
        api_time = time.time() - start_time
        logger.info(f"[{request_id}] API call completed in {api_time:.2f}s")
        
        # Log the raw response content for debugging
        content = ollama_response.message.content
        logger.info(f"[{request_id}] Raw API response for direct-answer ({sub_activity}): {content[:500]}...")
        
        json_data = json.loads(content)
        
        # Log the parsed response
        logger.info(f"[{request_id}] Parsed direct-answer response: {json.dumps(json_data, indent=2)}")
        
        return json_data
        
    except Exception as e:
        logger.error(f"[{request_id}] Error generating direct-answer question: {str(e)}")
        logger.exception(e)  # Log the full stack trace
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

def repair_malformed_json(json_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Repair malformed JSON responses from the AI model.
    
    Some models return nested structures or incorrect schema. This function
    attempts to extract the correct data structure from various malformed responses.
    
    Args:
        json_data: The parsed JSON data from the API response
        
    Returns:
        A corrected JSON structure that should match our expected schema
    """
    logger.info(f"Checking and repairing malformed JSON if needed: {str(json_data)[:100]}...")
    
    # Handle Grammar Correction questions - these must be direct-answer type
    if "question" in json_data and "answer" in json_data and "sub_activity" in json_data:
        if json_data["sub_activity"] == "Grammar Correction":
            # Grammar correction questions must be direct-answer type
            logger.info(f"Grammar Correction activity detected in JSON, forcing direct-answer question type")
            json_data["type"] = "direct-answer"
            
            # Remove any 'choices' property if it exists for Grammar Correction
            if "choices" in json_data:
                logger.info(f"Removing unexpected 'choices' from Grammar Correction question")
                del json_data["choices"]
                
            return json_data
    
    # Case 1: Response has a "properties" wrapper (common with some models)
    if "properties" in json_data and isinstance(json_data["properties"], dict):
        properties = json_data["properties"]
        # Try to extract the actual question data
        repaired = {}
        
        # Extract question
        if "question" in properties:
            if isinstance(properties["question"], dict):
                if "description" in properties["question"]:
                    repaired["question"] = properties["question"]["description"]
                elif "title" in properties["question"]:
                    repaired["question"] = properties["question"]["title"]
            elif isinstance(properties["question"], str):
                repaired["question"] = properties["question"]
        
        # Extract choices
        if "choices" in properties:
            if isinstance(properties["choices"], dict):
                if "items" in properties["choices"]:
                    repaired["choices"] = properties["choices"]["items"]
                elif "enum" in properties["choices"]:
                    repaired["choices"] = properties["choices"]["enum"]
                elif "examples" in properties["choices"]:
                    repaired["choices"] = properties["choices"]["examples"]
                elif "description" in properties["choices"] and "[" in properties["choices"]["description"]:
                    # Try to parse a string representation of an array
                    try:
                        choices_str = properties["choices"]["description"]
                        # Extract text between square brackets
                        match = re.search(r'\[(.*)\]', choices_str)
                        if match:
                            items_str = match.group(1)
                            # Split by commas and clean up
                            items = [item.strip(' "\'') for item in items_str.split(',')]
                            repaired["choices"] = items
                    except Exception as e:
                        logger.error(f"Failed to parse choices from string: {str(e)}")
            elif isinstance(properties["choices"], list):
                repaired["choices"] = properties["choices"]
        
        # Extract answer
        if "answer" in properties:
            if isinstance(properties["answer"], dict):
                if "description" in properties["answer"]:
                    repaired["answer"] = properties["answer"]["description"]
                elif "example" in properties["answer"]:
                    repaired["answer"] = properties["answer"]["example"]
            elif isinstance(properties["answer"], str):
                repaired["answer"] = properties["answer"]
        
        # Set the correct type
        repaired["type"] = "multiple-choice"
        
        logger.info(f"Repaired nested 'properties' JSON: {str(repaired)[:100]}...")
        return repaired
    
    # Case 2: Response has "correct_answer" instead of "answer"
    if "question" in json_data and "choices" in json_data and "correct_answer" in json_data and "answer" not in json_data:
        json_data["answer"] = json_data["correct_answer"]
        logger.info(f"Renamed 'correct_answer' to 'answer' in JSON response")
        # Fix or add the type field
        if "type" not in json_data:
            json_data["type"] = "multiple-choice"
        return json_data
    
    # Case 3: Response has all the right fields but wrong type value or missing type
    if "question" in json_data and "choices" in json_data and "answer" in json_data:
        # Fix or add the type field
        json_data["type"] = "multiple-choice"
        logger.info(f"Fixed 'type' field in JSON response")
        return json_data
    
    # Case 4: Direct answer question format
    if "question" in json_data and "answer" in json_data and "choices" not in json_data:
        # Make sure type is set to direct-answer
        json_data["type"] = "direct-answer"
        logger.info(f"Set type to 'direct-answer' for question without choices")
        
        # If sub_activity is in the response but not a known key, handle it
        if "sub_activity" in json_data and not isinstance(json_data["sub_activity"], str):
            if isinstance(json_data["sub_activity"], dict) and "description" in json_data["sub_activity"]:
                json_data["sub_activity"] = json_data["sub_activity"]["description"]
        
        # Remove any 'choices' property if it somehow exists
        if "choices" in json_data:
            logger.info(f"Removing unexpected 'choices' from direct-answer question")
            del json_data["choices"]
            
        return json_data
    
    # Case 5: Reading comprehension format
    if "passage" in json_data and "question" in json_data and "choices" in json_data and "answer" in json_data:
        json_data["type"] = "reading-comprehension"
        logger.info(f"Set type to 'reading-comprehension' for passage-based question")
        return json_data
    
    # If we can't fix it, return the original (validation will fail and we'll use fallback)
    logger.warning(f"Could not repair malformed JSON structure: {str(json_data)[:100]}...")
    return json_data

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
            langflow_workflow = os.getenv("LANGFLOW_WORKFLOW_GRAMMAR_CORRECTION", "grammar-correction")
            
            # Construct the API URL
            url = f"{langflow_host}/api/v1/run/{langflow_workflow}"
            
            # Create a unique session ID
            session_id = f"session_{str(uuid.uuid4())}"
            
            # Create a prompt based on whether the answer was correct or not
            if is_correct:
                prompt = f"""
                The student was given this grammatically incorrect sentence: "{question}"
                
                The student correctly fixed it to: "{user_answer}"
                
                The correct answer is: "{correct_answer}"
                
                Please provide a short, encouraging response (2-3 sentences) explaining what grammatical error they fixed correctly. Use language appropriate for an elementary school student. Focus on the specific grammar rule they applied.
                """
            else:
                prompt = f"""
                The student was given this grammatically incorrect sentence: "{question}"
                
                The student attempted to fix it with: "{user_answer}"
                
                The correct answer is: "{correct_answer}"
                
                Please provide a short, gentle response (2-3 sentences) explaining what grammar error they missed or fixed incorrectly. Use language appropriate for an elementary school student. Give a simple tip to help them understand the grammar rule.
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
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                
                # Parse the response
                response_data = response.json()
                
                # Extract the feedback from the response
                feedback_str = extract_question_from_langflow_response(response_data, request_id)
                
                # Clean up session messages to avoid accumulating in Langflow storage
                await delete_langflow_session_messages(session_id, request_id)
                
                if feedback_str:
                    # Clean up the feedback string
                    feedback_str = remove_think_tags(feedback_str)
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

def construct_math_multiple_choice_prompt(grade: int, sub_activity: str, difficulty: str) -> str:
    """
    Constructs a prompt for generating math multiple choice questions for Langflow API.
    This is a simplified version without tool usage instructions.
    
    Args:
        grade: Student grade level
        sub_activity: The math sub-activity (Addition/Subtraction, Multiplication/Division, etc.)
        difficulty: Difficulty level (Easy, Medium, Hard)
        
    Returns:
        A formatted prompt string
    """
    # Define number ranges based on grade and difficulty
    if grade <= 2:  # Grade 1-2
        if difficulty.lower() == "easy":
            num_range = "1-10"
            sum_range = "up to 20"
            diff_range = "no negative numbers"
        elif difficulty.lower() == "medium":
            num_range = "5-20"
            sum_range = "up to 30"
            diff_range = "no negative numbers"
        else:  # Hard
            num_range = "10-30"
            sum_range = "up to 50"
            diff_range = "no negative numbers"
    else:  # Grade 3+
        if difficulty.lower() == "easy":
            num_range = "10-30"
            sum_range = "up to 50"
            diff_range = "no negative numbers"
        elif difficulty.lower() == "medium":
            num_range = "20-50"
            sum_range = "up to 100"
            diff_range = "no negative numbers"
        else:  # Hard
            num_range = "30-100"
            sum_range = "up to 150"
            diff_range = "may include negative results"
    
    # Generate random elements for more diverse questions
    person1 = random.choice(MATH_NAMES)
    person2 = random.choice([n for n in MATH_NAMES if n != person1])  # Ensure different name
    objects = random.choice(MATH_OBJECTS)
    location = random.choice(MATH_LOCATIONS)
    activity = random.choice(MATH_ACTIVITIES)
    
    # Generate a random seed for variety
    random_seed = getRandomSeed()
    
    # Customize prompt based on sub-activity
    if sub_activity == "Addition/Subtraction":
        prompt = f"""
        Generate a {difficulty.lower()} {grade}-grade level math question about addition or subtraction.
        
        Use number range: {num_range}
        Sum range: {sum_range}
        Difference range: {diff_range}
        
        You can optionally incorporate these elements:
        - Names: {person1} and/or {person2}
        - Objects: {objects}
        - Location: {location}
        - Activity: {activity}
        
        Make the question fun and engaging for elementary school students.
        Add emojis to make it more appealing to children.
        
        Return a JSON with these fields:
        - "question": The complete question text with all necessary information to solve it
        - "choices": Exactly 4 possible answers (the correct answer and 3 wrong answers)
        - "answer": The correct answer (must be one of the choices)
        - "type": "multiple-choice"
        """
    elif sub_activity == "Multiplication/Division":
        # Define ranges based on grade
        if grade <= 2:  # Grade 1-2
            table_range = "up to 5"
            division_range = "simple divisions with results 1-5"
        elif grade <= 3:  # Grade 3
            table_range = "up to 10"
            division_range = "divisions with results 1-10"
        else:  # Grade 4+
            table_range = "up to 12"
            division_range = "divisions with divisors up to 12"
            
        prompt = f"""
        Generate a {difficulty.lower()} {grade}-grade level math question about multiplication or division.
        
        For multiplication, use times tables {table_range}.
        For division, use {division_range}.
        
        Use this random seed for variety: {random_seed}
        
        You can optionally incorporate these elements:
        - Names: {person1} and/or {person2}
        - Objects arranged in groups/rows: {objects}
        - Location: {location}
        
        Make the question fun and engaging for elementary school students.
        Add emojis to make it more appealing to children.
        
        Return a JSON with these fields:
        - "question": The complete question text with all necessary information to solve it
        - "choices": Exactly 4 possible answers (the correct answer and 3 wrong answers)
        - "answer": The correct answer (must be one of the choices)
        - "type": "multiple-choice"
        """
    elif sub_activity == "Word Problems":
        prompt = f"""
        Generate a {difficulty.lower()} {grade}-grade level math word problem.
        
        Use number range: {num_range}
        Sum range: {sum_range}
        Difference range: {diff_range}
        
        Create a story-based problem using these elements:
        - Characters: {person1} and {person2}
        - Objects: {objects}
        - Setting: {location}
        - Activity: {activity}
        
        Make sure the problem:
        - Has a clear question
        - Provides all necessary information to solve it
        - Is appropriate for {grade}-grade students
        - Is fun and engaging
        
        Add emojis to make it more appealing to children.
        
        Return a JSON with these fields:
        - "question": The complete word problem with all necessary information
        - "choices": Exactly 4 possible answers (the correct answer and 3 wrong answers)
        - "answer": The correct answer (must be one of the choices)
        - "type": "multiple-choice"
        """
    elif sub_activity == "Mushroom Kingdom Calculations":
        # Use Mario-themed elements
        character1 = random.choice(["Mario", "Luigi", "Princess Peach", "Toad", "Yoshi"])
        character2 = random.choice(["Bowser", "Koopa Troopa", "Goomba", "Wario", "Boo"])
        items = random.choice(["coins", "power stars", "super mushrooms", "fire flowers", "1-up mushrooms"])
        location = random.choice(["Mushroom Kingdom", "Peach's Castle", "Bowser's Castle", "Yoshi's Island", "Wario's Woods"])
        activity = random.choice(["collecting coins", "defeating enemies", "jumping on platforms", "racing go-karts", "solving puzzles"])
        
        prompt = f"""
        Generate a {difficulty.lower()} {grade}-grade level math question in a Mario and Luigi themed world for elementary students.
        
        Use the following Mario-themed elements in your question:
        - Characters: {character1} and/or {character2}
        - Items: {items}
        - Location: {location}
        - Activity: {activity}
        
        Number range should be {num_range} with results {sum_range}, {diff_range}.
        
        The question should be about math problems that Mario characters encounter, such as collecting coins, 
        defeating enemies, calculating scores, or measuring distances in the Mushroom Kingdom.
        Make the question fun and engaging for kids who love Mario games.
        
        The math should be appropriate for grade {grade} and should require basic operations 
        (addition, subtraction, multiplication, or division depending on grade level).
        
        Add emojis to make it more appealing to children.
        
        Return a JSON with these fields:
        - "question": The complete Mario-themed question with all necessary information
        - "choices": Exactly 4 possible answers (the correct answer and 3 wrong answers)
        - "answer": The correct answer (must be one of the choices)
        - "type": "multiple-choice"
        """
    else:
        # Generic math prompt for other sub-activities
        prompt = f"""
        Generate a {difficulty.lower()} {grade}-grade level math question about {sub_activity}.
        
        Use number range: {num_range}
        
        You can optionally incorporate these elements:
        - Names: {person1} and/or {person2}
        - Objects: {objects}
        - Location: {location}
        - Activity: {activity}
        
        Make the question fun and engaging for elementary school students.
        Add emojis to make it more appealing to children.
        
        Return a JSON with these fields:
        - "question": The complete question text with all necessary information to solve it
        - "choices": Exactly 4 possible answers (the correct answer and 3 wrong answers)
        - "answer": The correct answer (must be one of the choices)
        - "type": "multiple-choice"
        """
    
    return prompt

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
        question_json_str = question_json_str.strip()
        
        # Try to extract just the JSON part from the text
        try:
            # Find the first occurrence of '{'
            json_start = question_json_str.find('{')
            if json_start >= 0:
                # Extract from the first '{' to the end of the string
                question_json_str = question_json_str[json_start:]
                logger.info(f"[{request_id}] Extracted JSON part starting at position {json_start}")
        except Exception as e:
            logger.error(f"[{request_id}] Error extracting JSON part: {str(e)}")
            
        logger.info(f"[{request_id}] Extracted JSON string: {question_json_str}")
    
    return question_json_str

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
    session_id = f"session_{str(uuid.uuid4())}"
    
    # Generate a custom prompt for math questions
    custom_prompt = construct_math_multiple_choice_prompt(grade, sub_activity, difficulty)
    print(f"Custom prompt: {custom_prompt}")
    
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
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            # Parse the response
            response_data = response.json()
            print(f"Response data: {response_data}")
            
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
            response = await client.delete(url)
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

def construct_reading_comprehension_prompt(grade: int, sub_activity: str, difficulty: str) -> str:
    """
    Constructs a prompt for generating reading comprehension questions for Langflow API.
    
    Args:
        grade: Student grade level
        sub_activity: The English sub-activity (Reading Comprehension)
        difficulty: Difficulty level (Easy, Medium, Hard)
        
    Returns:
        A formatted prompt string
    """
    # Determine passage length based on grade and difficulty
    if grade <= 1:
        passage_length = "very short passage (2-3 sentences)"
    elif grade <= 2:
        passage_length = "short passage (3-5 sentences)"
    elif grade <= 3:
        passage_length = "medium-length passage (5-7 sentences)"
    else:
        passage_length = "longer passage (7-10 sentences)"
    
    # Adjust for difficulty
    if difficulty.lower() == "easy":
        if grade <= 2:
            passage_length = "very short passage (2-3 simple sentences)"
        else:
            passage_length = "short passage (3-5 simple sentences)"
    elif difficulty.lower() == "hard":
        if grade >= 3:
            passage_length = "longer passage (7-10 sentences with varied structure)"
    
    # Generate random elements for more diverse questions
    character1 = random.choice(["Emma", "Liam", "Olivia", "Noah", "Ava", "Lucas", "Isabella", "Mason", "Sophia", "Ethan"])
    character2 = random.choice(["Jackson", "Mia", "Aiden", "Charlotte", "Elijah", "Amelia", "Grayson", "Harper", "Benjamin", "Evelyn"])
    location = random.choice(["park", "school", "beach", "library", "museum", "zoo", "farm", "store", "garden", "playground"])
    topic = random.choice(["friendship", "animals", "family", "school", "adventure", "kindness", "seasons", "nature", "community", "discovery"])
    
    # Specify question type based on grade level
    if grade <= 2:
        question_type = "about a simple fact from the passage"
    else:
        question_type = random.choice([
            "about a detail from the passage",
            "about the main idea",
            "that requires making an inference",
            "about a character's feelings or motivations",
            "about the meaning of a word in context"
        ])
    
    # Generate a random seed for variety
    random_seed = getRandomSeed()
    
    prompt = f"""
    Generate a {difficulty.lower()} {grade}-grade level reading comprehension passage and question for elementary school students.
    
    Create a {passage_length} about {topic} set at a {location}, followed by a multiple-choice question {question_type}.
    
    Include these characters in your passage: {character1} and optionally {character2}.
    
    Use this random seed for variety: {random_seed}
    
    The passage should:
    - Use vocabulary appropriate for grade {grade}
    - Have a clear beginning, middle, and end
    - Include interesting details that might be asked about in the question
    - Vary between descriptive, narrative, or informative styles
    - Add multiple emojis throughout the passage to make it more engaging for children
    
    Your question should be thoughtful and require students to really understand the passage.
    
    Return a JSON with these fields:
    - "passage": The reading text with emojis
    - "question": The question about the passage with emojis
    - "choices": Exactly 4 possible answers (the correct answer and 3 wrong answers)
    - "answer": The correct answer (must be one of the choices)
    - "type": "reading-comprehension"
    
    IMPORTANT REQUIREMENTS:
    - Provide EXACTLY 4 multiple choice options (no more, no less)
    - Ensure the correct answer is one of the 4 choices
    - Make all choices reasonable so the answer isn't too obvious
    - Keep the choices separate from the question text
    - Add emojis throughout the passage and question
    """
    
    return prompt

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
    session_id = f"session_{str(uuid.uuid4())}"
    
    # Generate a custom prompt for reading comprehension questions
    custom_prompt = construct_reading_comprehension_prompt(grade, sub_activity, difficulty)
    print(f"Reading Comprehension prompt: {custom_prompt}")
    
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
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            # Parse the response
            response_data = response.json()
            print(f"Response data: {response_data}")
            
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

def construct_opposites_antonyms_prompt(grade: int, difficulty: str) -> str:
    """
    Constructs a prompt for generating English opposites/antonyms questions for Langflow API.
    
    Args:
        grade: Student grade level
        difficulty: Difficulty level (Easy, Medium, Hard)
        
    Returns:
        A formatted prompt string
    """
    # Get random elements for variety
    target_words = [word for word in ENGLISH_ADJECTIVES if word != "happy"]  # Exclude 'happy' to avoid repetition
    target_word = random.choice(target_words)
    random_seed = getRandomSeed()
    
    # Choose a random prompt template
    prompt_templates = [
        f"What is the opposite of '{target_word}'?",
        f"Which word means the opposite of '{target_word}'?",
        f"Select the word that has the opposite meaning of '{target_word}'.",
        f"Choose the antonym for '{target_word}'.",
        f"Which of these words is most opposite in meaning to '{target_word}'?"
    ]
    prompt_template = random.choice(prompt_templates)
    
    # Create grade-appropriate prompts
    if grade <= 2:  # Grade 1-2
        prompt = f"""
        Generate a {difficulty.lower()} {grade}-grade level English question about opposites or antonyms.
        
        YOU MUST use exactly this question format WITHOUT changing the word: "{prompt_template}"
        
        You MUST use the word '{target_word}' in your question. DO NOT substitute it with a different word.
        DO NOT use the word 'happy' in your question - this word has been overused.
        
        Use this random seed for variety: {random_seed}
        
        The question should ask for the opposite of a simple word appropriate for this grade level.
        
        Add emojis to make the question more engaging for children.
        
        Return a JSON with these fields:
        - "question": The question text with emojis
        - "choices": Exactly 4 possible answers (the correct answer and 3 wrong answers)
        - "answer": The correct answer (must be one of the choices)
        - "type": "multiple-choice"
        
        IMPORTANT REQUIREMENTS:
        - Provide EXACTLY 4 multiple choice options (no more, no less)
        - Ensure the correct answer (the true opposite/antonym) is one of the 4 choices
        - Make all choices grade-appropriate
        - Keep the choices separate from the question text
        """
    else:  # Grade 3+
        prompt = f"""
        Generate a {difficulty.lower()} {grade}-grade level English question about opposites or antonyms.
        
        YOU MUST use exactly this question format WITHOUT changing the word: "{prompt_template}"
        
        You MUST use the word '{target_word}' in your question. DO NOT substitute it with a different word.
        DO NOT use the word 'happy' in your question - this word has been overused.
        
        Use this random seed for variety: {random_seed}
        
        The question should ask for the opposite of a word appropriate for this grade level.
        
        Add emojis to make the question more engaging for children.
        
        Return a JSON with these fields:
        - "question": The question text with emojis
        - "choices": Exactly 4 possible answers (the correct answer and 3 wrong answers)
        - "answer": The correct answer (must be one of the choices)
        - "type": "multiple-choice"
        
        IMPORTANT REQUIREMENTS:
        - Provide EXACTLY 4 multiple choice options (no more, no less)
        - Ensure the correct answer (the true opposite/antonym) is one of the 4 choices
        - Make all choices grade-appropriate
        - Keep the choices separate from the question text
        """
    
    # Log the enhanced prompt details
    logger.info(f"Opposites/Antonyms randomization - Target word: {target_word}, Template: {prompt_template}, Seed: {random_seed}")
    
    return prompt

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
    session_id = f"session_{str(uuid.uuid4())}"
    
    # Generate a custom prompt for opposites/antonyms questions
    custom_prompt = construct_opposites_antonyms_prompt(grade, difficulty)
    print(f"Opposites/Antonyms prompt: {custom_prompt}")
    
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
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            # Parse the response
            response_data = response.json()
            print(f"Response data: {response_data}")
            
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

def construct_synonyms_prompt(grade: int, difficulty: str) -> str:
    """
    Constructs a prompt for generating English synonyms questions for Langflow API.
    
    Args:
        grade: Student grade level
        difficulty: Difficulty level (Easy, Medium, Hard)
        
    Returns:
        A formatted prompt string
    """
    # Get random elements for variety
    target_words = [word for word in ENGLISH_ADJECTIVES if word != "big"]  # Exclude 'big' to avoid repetition
    target_word = random.choice(target_words)
    random_seed = getRandomSeed()
    
    # Choose a random prompt template
    prompt_templates = [
        f"What is a synonym for '{target_word}'?",
        f"Which word means the same as '{target_word}'?",
        f"Select the word that has a similar meaning to '{target_word}'.",
        f"Choose the synonym for '{target_word}'.",
        f"Which of these words is most similar in meaning to '{target_word}'?"
    ]
    prompt_template = random.choice(prompt_templates)
    
    # Create grade-appropriate prompts
    if grade <= 2:  # Grade 1-2
        prompt = f"""
        Generate a {difficulty.lower()} {grade}-grade level English question about synonyms (words with similar meanings).
        
        YOU MUST use exactly this question format WITHOUT changing the word: "{prompt_template}"
        
        You MUST use the word '{target_word}' in your question. DO NOT substitute it with a different word.
        DO NOT use the word 'big' in your question - this word has been overused.
        
        Use this random seed for variety: {random_seed}
        
        The question should ask for a word with a similar meaning to a simple word appropriate for this grade level.
        
        Add emojis to make the question more engaging for children.
        
        CRITICAL INSTRUCTIONS FOR SYNONYMS QUESTION:
        
        This is a question about SYNONYMS (words with SIMILAR meanings), NOT ANTONYMS (words with OPPOSITE meanings).
        
        Follow these steps carefully:
        1. Create a question asking for a synonym of '{target_word}'
        2. Generate EXACTLY 4 answer choices that include at least one TRUE SYNONYM of '{target_word}'
        3. Make the correct answer be a word that has a SIMILAR meaning to '{target_word}'
        4. Triple-check that the correct answer is NOT an antonym or opposite of '{target_word}'
        5. Verify that you haven't accidentally marked an opposite/antonym as the correct answer
        
        Return a JSON with these fields:
        - "question": The question text with emojis
        - "choices": Exactly 4 possible answers (the correct answer and 3 wrong answers)
        - "answer": The correct answer (must be one of the choices)
        - "type": "multiple-choice"
        
        IMPORTANT REQUIREMENTS:
        - Provide EXACTLY 4 multiple choice options (no more, no less)
        - Ensure the correct answer (the true synonym) is one of the 4 choices
        - Make all choices grade-appropriate
        - Keep the choices separate from the question text
        """
    else:  # Grade 3+
        prompt = f"""
        Generate a {difficulty.lower()} {grade}-grade level English question about synonyms (words with similar meanings).
        
        YOU MUST use exactly this question format WITHOUT changing the word: "{prompt_template}"
        
        You MUST use the word '{target_word}' in your question. DO NOT substitute it with a different word.
        DO NOT use the word 'big' in your question - this word has been overused.
        
        Use this random seed for variety: {random_seed}
        
        The question should ask for a word with a similar meaning to a word appropriate for this grade level.
        
        Add emojis to make the question more engaging for children.
        
        CRITICAL INSTRUCTIONS FOR SYNONYMS QUESTION:
        
        This is a question about SYNONYMS (words with SIMILAR meanings), NOT ANTONYMS (words with OPPOSITE meanings).
        
        Follow these steps carefully:
        1. Create a question asking for a synonym of '{target_word}'
        2. Generate EXACTLY 4 answer choices that include at least one TRUE SYNONYM of '{target_word}'
        3. Make the correct answer be a word that has a SIMILAR meaning to '{target_word}'
        4. Triple-check that the correct answer is NOT an antonym or opposite of '{target_word}'
        5. Verify that you haven't accidentally marked an opposite/antonym as the correct answer
        
        Return a JSON with these fields:
        - "question": The question text with emojis
        - "choices": Exactly 4 possible answers (the correct answer and 3 wrong answers)
        - "answer": The correct answer (must be one of the choices)
        - "type": "multiple-choice"
        
        IMPORTANT REQUIREMENTS:
        - Provide EXACTLY 4 multiple choice options (no more, no less)
        - Ensure the correct answer (the true synonym) is one of the 4 choices
        - Make all choices grade-appropriate
        - Keep the choices separate from the question text
        """
    
    # Log the enhanced prompt details
    logger.info(f"Synonyms randomization - Target word: {target_word}, Template: {prompt_template}, Seed: {random_seed}")
    
    return prompt

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
    session_id = f"session_{str(uuid.uuid4())}"
    
    # Generate a custom prompt for synonyms questions
    custom_prompt = construct_synonyms_prompt(grade, difficulty)
    print(f"Synonyms prompt: {custom_prompt}")
    
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
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            # Parse the response
            response_data = response.json()
            print(f"Response data: {response_data}")
            
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
    session_id = f"session_{str(uuid.uuid4())}"
    
    # Generate a custom prompt for grammar correction questions
    custom_prompt = construct_grammar_correction_prompt(grade, difficulty)
    print(f"Grammar correction custom prompt: {custom_prompt}")
    
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
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            # Parse the response
            response_data = response.json()
            print(f"Langflow response data for grammar correction: {response_data}")
            
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

def construct_grammar_correction_prompt(grade: int, difficulty: str) -> str:
    """
    Construct a prompt for generating grammar correction questions.
    """
    # Get randomized seed for variety
    random_seed = getRandomSeed()
    
    # Define common variables
    pronouns = ["I", "you", "he", "she", "it", "we", "they", "me", "him", "her", "us", "them"]
    nouns = ["cat", "dog", "boy", "girl", "teacher", "student", "tree", "book", "pencil", "car", "house", "school"]
    error_types = ["subject-verb agreement", "singular/plural nouns", "pronoun usage", "possessive nouns"]
    
    # Choose random elements
    if grade <= 2:  # Grades 1-2
        # Simpler options for younger students
        error_type = random.choice(error_types[:2])  # Only basic errors
        
    else:  # Grade 3+
        # Fuller range of error types for older students
        error_type = random.choice(error_types)
    
    # Build the base prompt
    prompt = f"""Create a {difficulty.lower()} {grade}-grade level English grammar correction question focusing on {error_type}.
Write a sentence with ONE grammatical error. The error should be appropriate for {grade}-grade students to identify and fix.
The question should be short and clear, and the answer should be the corrected sentence.
"""
    
    # Log the randomization details
    logger.info(f"Grammar correction prompt generation - Error type: {error_type}, Grade: {grade}, Difficulty: {difficulty}, Seed: {random_seed}")
    
    return prompt

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
    session_id = f"session_{str(uuid.uuid4())}"
    
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
            response = await client.post(url, json=payload, headers=headers)
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
    session_id = f"session_{str(uuid.uuid4())}"
    
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
            response = await client.post(url, json=payload, headers=headers)
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
    session_id = f"session_{str(uuid.uuid4())}"
    
    # Generate a custom prompt for Mario English questions
    custom_prompt = construct_mario_english_prompt(grade, difficulty)
    print(f"Mario English prompt: {custom_prompt}")
    
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
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            # Parse the response
            response_data = response.json()
            print(f"Response data: {response_data}")
            
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
    session_id = f"session_{str(uuid.uuid4())}"
    
    # Generate a custom prompt for nouns/pronouns questions
    custom_prompt = construct_nouns_pronouns_prompt(grade, difficulty)
    print(f"Nouns/Pronouns prompt: {custom_prompt}")
    
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
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            # Parse the response
            response_data = response.json()
            print(f"Response data: {response_data}")
            
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

def construct_nouns_pronouns_prompt(grade: int, difficulty: str) -> str:
    """
    Construct a prompt for generating nouns/pronouns questions.
    
    Args:
        grade: Student grade level (1-5)
        difficulty: Difficulty level (Easy, Medium, Hard)
        
    Returns:
        String containing the prompt
    """
    # Get randomized seed for variety
    random_seed = getRandomSeed()
    
    # Select names and objects for variety
    selected_names = random.sample(NAMES, 2)
    objects = random.sample(ENGLISH_NOUNS, 3)
    
    # Determine complexity based on grade level
    if grade <= 2:  # Grades 1-2
        # For younger students, focus on basic nouns and pronouns identification
        question_types = [
            "identifying common nouns", 
            "identifying proper nouns",
            "matching pronouns to nouns",
            "basic singular/plural nouns"
        ]
    else:  # Grades 3+
        # For older students, include more complex concepts
        question_types = [
            "identifying common and proper nouns",
            "identifying subject and object pronouns",
            "replacing nouns with appropriate pronouns",
            "possessive nouns and pronouns",
            "singular/plural noun forms",
            "pronoun-antecedent agreement"
        ]
    
    # Select a random question type appropriate for the grade level
    question_type = random.choice(question_types)
    
    # Build the prompt with specific instructions
    prompt = f"""Generate a {difficulty.lower()} {grade}-grade level English multiple-choice question about {question_type}.
The question should be appropriate for {grade}-grade students and include exactly 4 answer choices.

Use these elements in your question:
- Names: {selected_names[0]} and/or {selected_names[1]}
- Objects: {objects[0]}, {objects[1]}, and/or {objects[2]}

Make sure to:
1. Include appropriate emojis to make the question engaging
2. Create exactly 4 answer choices (A, B, C, D)
3. Ensure one clear correct answer
4. Make the question clear and grade-appropriate

Return a JSON object with 'question', 'choices' (array of 4 strings), and 'answer' (the correct choice string).

Example format:
{{
  "question": "📝 Which word in the sentence is a noun? The dog played in the yard.",
  "choices": ["dog", "played", "in", "the"],
  "answer": "dog"
}}
"""
    
    # Log the prompt details
    logger.info(f"Nouns/Pronouns prompt generation - Type: {question_type}, Grade: {grade}, Difficulty: {difficulty}, Names: {selected_names}, Objects: {objects}, Seed: {random_seed}")
    
    return prompt