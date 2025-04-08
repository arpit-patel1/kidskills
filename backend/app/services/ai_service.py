import os
import json
import time
import random
import re
import logging
from typing import Dict, Any, Optional, List, Literal, Union, Callable
from dotenv import load_dotenv
from pydantic import BaseModel, Field, validator, ValidationError, root_validator
from ollama import AsyncClient
from .fallback_questions import get_fallback_question as get_fallback
import math
import operator

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

# Define math calculation tool for the LLM
async def calculator(expression: str, question: str) -> str:
    """
    Evaluates a mathematical expression and returns the result.
    Handles basic arithmetic operations, simple fractions, and functions.
    
    Args:
        expression: A mathematical expression as a string
        question: The question being solved (for context)
        
    Returns:
        The result of the calculation as a string
    """
    logger.info(f"Calculator tool received: {expression}")
    logger.info(f"Question context: {question}")
    
    try:
        # Clean the expression
        expression = expression.strip()
        
        # Define safe operations
        safe_dict = {
            'abs': abs,
            'round': round,
            'min': min,
            'max': max,
            'sum': sum,
            'pow': pow,
            'int': int,
            'float': float,
            'sqrt': math.sqrt,
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
            'floor': math.floor,
            'ceil': math.ceil,
            'pi': math.pi,
            'e': math.e
        }
        
        # Add basic operators
        safe_dict.update({
            '+': operator.add,
            '-': operator.sub,
            '*': operator.mul,
            '/': operator.truediv,
            '//': operator.floordiv,
            '%': operator.mod,
            '**': operator.pow
        })
        
        # Evaluate the expression
        result = eval(expression, {"__builtins__": {}}, safe_dict)
        
        # Format the result
        if isinstance(result, int) or result.is_integer():
            formatted_result = str(int(result))
        else:
            # Round to 4 decimal places for readability
            formatted_result = str(round(result, 4))
            # Remove trailing zeros
            if '.' in formatted_result:
                formatted_result = formatted_result.rstrip('0').rstrip('.')
        
        logger.info(f"Calculator result: {formatted_result}")
        return formatted_result
    
    except Exception as e:
        error_msg = f"Error calculating expression '{expression}': {str(e)}"
        logger.error(error_msg)
        return f"Error: {str(e)}"

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
    
    The calculator tool for math questions can be enabled/disabled by setting the
    ENABLE_MATH_TOOLS environment variable to "true" or "false" in the .env file.
    """
    logger.info(f"[{request_id}] Generating multiple-choice question")
    
    # Determine temperature based on subject/activity
    temperature = 0.5  # default
    if subject == "English":
        if sub_activity == "Opposites/Antonyms":
            temperature = 0.9
            logger.info(f"[{request_id}] Using higher temperature of {temperature} for Opposites/Antonyms")
        elif sub_activity == "Synonyms":
            temperature = 0.8
            logger.info(f"[{request_id}] Using higher temperature of {temperature} for Synonyms")
        else:
            temperature = 0.7
            logger.info(f"[{request_id}] Using higher temperature of {temperature} for {sub_activity}")
    
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
IMPORTANT: Always add appropriate emojis to the question text to make it more engaging for children. Emojis can be placed anywhere in the question - in the middle or at the end of the text. Choose emojis that relate to the subject matter of the question."""

    if subject == "Math":
        system_message += """
For math questions, follow these CRITICAL rules:

1. Question Completeness:
   - Every question MUST include ALL numbers needed to solve it
   - NEVER ask about unknown quantities without providing the numbers
   - Example of BAD question: "What is the sum of James's age and his brother's age?" (no numbers provided)
   - Example of GOOD question: "James is 7 years old and his brother is 5 years old. What is the sum of their ages?"

2. Word Problem Requirements:
   - Always provide specific numbers in the problem statement
   - Make sure the scenario is complete and solvable
   - Include all necessary information to find the answer
   - Example of BAD question: "Sarah has some apples and gives some to her friend. How many does she have left?"
   - Example of GOOD question: "Sarah has 8 apples and gives 3 to her friend. How many apples does she have left?"

3. Multiple Choice Guidelines:
   - The correct answer MUST be one of the choices
   - Wrong answers should be plausible but clearly incorrect
   - All numbers in choices should be appropriate for the grade level
   - Example of BAD choices: ["10", "12", "15", "20"] for a question with no numbers
   - Example of GOOD choices: ["10", "12", "15", "20"] for "What is 7 + 5?"

4. Validation Steps:
   - First, write the complete question with all numbers
   - Then, calculate the correct answer
   - Generate plausible wrong answers
   - Double-check that the question is solvable with the given information
   - Verify that the correct answer is one of the choices

5. IMPORTANT - Use Calculator Tool When Needed:
   - When you need to calculate any math operation (addition, subtraction, multiplication, division, etc.), 
     use the 'calculator' tool provided to you
   - This ensures your calculations are accurate
   - ALWAYS provide both the 'expression' and the 'question' parameters:
     - 'expression': The mathematical expression to calculate (e.g., "28 + 35")
     - 'question': The actual question you're solving (e.g., "If Sam has 28 apples and gets 35 more, how many does he have in total?")
   - Providing the question helps maintain context between your questions and calculations
   - Use the calculator tool for generating answer choices too, to ensure they're mathematically sound

6. CRITICAL - Answer Validation Process:
   - Step 1: Design your question first (e.g., "5 + 9 = ?")
   - Step 2: Use the calculator tool to compute the EXACT answer (e.g., "5 + 9" → 14)
   - Step 3: Use this calculator result as your correct answer
   - Step 4: Create choices that MUST include this exact calculator result
   - Step 5: Double-check that the "answer" field matches one of the choices
   - Step 6: NEVER include a correct answer that wasn't one of the choices

7. CRITICAL - Choice Selection Requirements:
   - You MUST include the calculated answer in the choices array
   - Example: If calculator says 14, then "14" MUST be in choices
   - NEVER set an answer that is not in the choices
   - Before finalizing, verify that answer appears in choices

Remember: Every question must be complete and solvable with the information provided. If you're unsure, use simpler numbers or a different question type."""

    if subject == "English" and sub_activity == "Opposites/Antonyms":
        system_message += " When asked to use a specific word in a question about opposites/antonyms, you MUST use exactly that word and not substitute it with a different word. Follow the exact template provided in the prompt."
    
    if subject == "English" and sub_activity == "Synonyms":
        system_message += """
CRITICAL INSTRUCTIONS FOR SYNONYM QUESTIONS - READ CAREFULLY:

1. Synonyms vs Antonyms: 
   - Synonyms have SIMILAR meanings (like "happy" and "joyful")
   - Antonyms have OPPOSITE meanings (like "happy" and "sad")
   - This question is about SYNONYMS (similar meanings), NOT antonyms

2. Examples of correct synonym pairs:
   - big → large, huge, enormous, gigantic
   - small → tiny, little, miniature, petite
   - happy → joyful, glad, cheerful, delighted
   - sad → unhappy, gloomy, miserable, downcast
   - clean → tidy, spotless, immaculate, pristine
   - dirty → filthy, grimy, soiled, unclean
   - cold → chilly, cool, frosty, frigid
   - hot → warm, heated, burning, fiery

3. Examples of INCORRECT answers (these are antonym pairs, NOT synonyms):
   - big ≠ small (these are opposites, not synonyms)
   - happy ≠ sad (these are opposites, not synonyms)
   - clean ≠ dirty (these are opposites, not synonyms)
   - hot ≠ cold (these are opposites, not synonyms)
   - dark ≠ light (these are opposites, not synonyms)

4. Words with 'un', 'in', 'im', 'dis' prefixes are usually antonyms:
   - clean vs unclean (these are opposites, not synonyms)
   - happy vs unhappy (these are opposites, not synonyms)
   - possible vs impossible (these are opposites, not synonyms)

5. Double-check your answer:
   - Make sure the correct answer has a SIMILAR meaning to the word in the question
   - Verify your answer is NOT an opposite/antonym of the word in the question
   - If you're asked for a synonym of "clean," the answer should be a word like "tidy" (similar meaning), NOT "dirty" or "unclean" (opposite meaning)

I will be testing your understanding of the difference between synonyms and antonyms. You MUST ensure your answer is a true synonym (similar meaning), not an antonym (opposite meaning).
"""
    
    try:
        # Make API call
        start_time = time.time()
        
        model = os.getenv("OLLAMA_MATH_MODEL") if subject == "Math" else os.getenv("OLLAMA_MODEL")
        
        # Available functions for tool calling
        available_functions = {
            "calculator": calculator
        }
        
        # Set up tools for math questions
        tools = None
        if subject == "Math" and ENABLE_MATH_TOOLS:
            # Define calculator tool
            calculator_tool = {
                "type": "function",
                "function": {
                    "name": "calculator",
                    "description": "Calculate the result of a mathematical expression",
                    "parameters": {
                        "type": "object",
                        "required": ["expression", "question"],
                        "properties": {
                            "expression": {
                                "type": "string", 
                                "description": "The mathematical expression to calculate (e.g., '2+2', '5*3', etc.)"
                            },
                            "question": {
                                "type": "string",
                                "description": "The mathematical question being solved (provides context for the calculation)"
                            }
                        }
                    }
                }
            }
            tools = [calculator_tool]
            logger.info(f"[{request_id}] Adding calculator tool for math question")
        elif subject == "Math" and not ENABLE_MATH_TOOLS:
            logger.info(f"[{request_id}] Math tools disabled by ENABLE_MATH_TOOLS setting")
        
        # Initialize messages array with system and user message
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ]
        
        # Flag to track if we're doing a conversation with tool calls
        using_tools = subject == "Math" and ENABLE_MATH_TOOLS
        max_tool_calls = 5  # Limit the number of tool calls to avoid infinite loops
        tool_call_count = 0
        final_content = None
        final_output = None
        
        # If we're using tools, we need to have a conversation that could involve multiple turns
        while using_tools and tool_call_count < max_tool_calls:
            # Make API call
            ollama_response = await ollama_async_client.chat(
                model=model,
                messages=messages,
                options={"temperature": temperature},
                tools=tools if subject == "Math" and ENABLE_MATH_TOOLS else None,
                stream=False
            )
            
            # Log the response
            logger.info(f"[{request_id}] OLLAMA response: {ollama_response}")
            
            # Check if there are any tool calls in the response
            if ollama_response.message.tool_calls:
                tool_call_count += 1
                
                # Process each tool call
                for tool in ollama_response.message.tool_calls:
                    # Ensure the function is available, and then call it
                    if function_to_call := available_functions.get(tool.function.name):
                        logger.info(f"[{request_id}] Calling function: {tool.function.name}")
                        logger.info(f"[{request_id}] Arguments: {tool.function.arguments}")
                        
                        try:
                            # Call the function with the arguments
                            output = await function_to_call(**tool.function.arguments)
                            logger.info(f"[{request_id}] Function output: {output}")
                            final_output = output
                        except Exception as e:
                            error_msg = f"Error calling function {tool.function.name}: {str(e)}"
                            logger.error(f"[{request_id}] {error_msg}")
                            output = f"Error: {str(e)}"
                            final_output = output
                    else:
                        logger.error(f"[{request_id}] Function {tool.function.name} not found")
                        output = f"Error: Function {tool.function.name} not found"
                        final_output = output
                
                # Add the function response to messages for the model to use
                messages.append(ollama_response.message)
                messages.append({"role": "tool", "content": str(final_output), "name": tool.function.name})
            else:
                # No more tool calls, we're done
                final_content = ollama_response.message.content
                break
        
        # For non-math subjects or when tool calls are complete, just get the final content
        if not using_tools:
            ollama_response = await ollama_async_client.chat(
                model=model,
                messages=messages,
                format=MultipleChoiceQuestion.model_json_schema(),
                options={"temperature": temperature}
            )
            final_content = ollama_response.message.content
            
            # Log the raw response for debugging, especially for English questions
            if subject == "English":
                logger.info(f"[{request_id}] Raw API response for {subject} - {sub_activity}: {final_content[:500]}...")
        
        api_time = time.time() - start_time
        logger.info(f"[{request_id}] API call completed in {api_time:.2f}s with {tool_call_count} tool calls")
        
        try:
            # Try to parse the final content as JSON
            json_data = json.loads(final_content)
            
            # Ensure that the returned JSON has the proper structure
            if "question" not in json_data or "choices" not in json_data or "answer" not in json_data:
                logger.warning(f"[{request_id}] Incomplete JSON response: {final_content}")
                return get_fallback_question(str(grade), subject, sub_activity, difficulty)
            
            # Log the complete parsed response for debugging
            logger.info(f"[{request_id}] Parsed JSON response: {json.dumps(json_data, indent=2)}")
            
            # Check the number of choices and log it
            choices = json_data.get("choices", [])
            logger.info(f"[{request_id}] Number of choices: {len(choices)}")
            logger.info(f"[{request_id}] Choices: {choices}")
            
            # Ensure type field is set correctly
            json_data["type"] = "multiple-choice"
            
            # For math questions, validate that the answer is in the choices
            if subject == "Math":
                answer = json_data["answer"]
                choices = json_data["choices"]
                
                # Check if the answer is in the choices
                if answer not in choices:
                    logger.warning(f"[{request_id}] Answer '{answer}' not in choices {choices}")
                    
                    # Add the answer to the choices, replacing one of the options
                    if len(choices) > 0:
                        # If there are choices, replace the last one with the correct answer
                        choices[-1] = answer
                        logger.info(f"[{request_id}] Fixed choices to include answer: {choices}")
                    else:
                        # If there are no choices, create a basic set with the answer
                        num_answer = float(answer) if answer.replace('.', '', 1).isdigit() else 0
                        choices = [
                            str(int(num_answer - 2) if num_answer - 2 >= 0 else int(num_answer + 2)),
                            str(int(num_answer - 1) if num_answer - 1 >= 0 else int(num_answer + 3)),
                            answer,
                            str(int(num_answer + 1))
                        ]
                        logger.info(f"[{request_id}] Created new choices with answer: {choices}")
                    
                    # Update the JSON data
                    json_data["choices"] = choices
            
            # Validation for English activities, especially Mushroom Kingdom Vocabulary
            if subject == "English":
                answer = json_data["answer"]
                choices = json_data["choices"]
                question = json_data["question"]
                
                # Check if the choices appear to be in the question text
                choice_markers = ["A)", "B)", "C)", "D)", "1)", "2)", "3)", "4)", "a)", "b)", "c)", "d)"]
                has_choice_markers = any(marker in question for marker in choice_markers)
                
                if has_choice_markers:
                    logger.warning(f"[{request_id}] Choices may be included in question text: {question}")
                    
                    # Try to extract just the question part by looking for the first choice marker
                    for marker in choice_markers:
                        if marker in question:
                            # Split at the first marker
                            parts = question.split(marker, 1)
                            cleaned_question = parts[0].strip()
                            logger.info(f"[{request_id}] Cleaned question: {cleaned_question}")
                            json_data["question"] = cleaned_question
                            break
                
                # Check if the answer is in the choices
                if answer not in choices:
                    logger.warning(f"[{request_id}] English question: Answer '{answer}' not in choices {choices}")
                    
                    # Add the answer to the choices if it's not there
                    if len(choices) > 0:
                        choices[-1] = answer
                        logger.info(f"[{request_id}] Fixed English choices to include answer: {choices}")
                    else:
                        logger.warning(f"[{request_id}] No choices provided for English question")
                        # Create some basic choices for fallback
                        choices = ["Option A", "Option B", answer, "Option C"]
                        logger.info(f"[{request_id}] Created fallback choices: {choices}")
                    
                    json_data["choices"] = choices
                
                # Ensure we have at least 4 choices for multiple choice questions
                if len(choices) < 4:
                    logger.warning(f"[{request_id}] Too few choices ({len(choices)}) for {sub_activity}")
                    
                    # Add additional choices to reach 4 if needed
                    while len(choices) < 4:
                        new_choice = f"Option {chr(65 + len(choices))}"  # Option A, Option B, etc.
                        if new_choice not in choices and new_choice != answer:
                            choices.append(new_choice)
                            logger.info(f"[{request_id}] Added extra choice: {new_choice}")
                    
                    json_data["choices"] = choices
            
            # We are removing all synonym validation to rely on better prompt instructions
            
            return json_data
        except json.JSONDecodeError:
            logger.error(f"[{request_id}] Failed to parse JSON from response: {final_content[:200]}...")
            return get_fallback_question(str(grade), subject, sub_activity, difficulty)
        
    except Exception as e:
        logger.error(f"[{request_id}] Error generating multiple-choice question: {str(e)}")
        logger.exception(e)  # Log the full stack trace
        return get_fallback_question(str(grade), subject, sub_activity, difficulty)

async def generate_direct_answer_question(grade: int, subject: str, sub_activity: str, difficulty: str, request_id: str) -> Dict[str, Any]:
    """Generate a direct answer question."""
    logger.info(f"[{request_id}] Generating direct-answer question")
    
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
IMPORTANT: Always add appropriate emojis to the question text to make it more engaging for children. Emojis can be placed anywhere in the question - in the middle or at the end of the text. Choose emojis that relate to the subject matter of the question."""
    
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

        ollama_response = await ollama_async_client.chat(model=os.getenv("OLLAMA_MODEL"),
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            format=DirectAnswerQuestion.model_json_schema(),
            options={"temperature": temperature},
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

async def generate_reading_comprehension_question(grade: int, subject: str, sub_activity: str, difficulty: str, request_id: str) -> Dict[str, Any]:
    """Generate a reading comprehension question."""
    logger.info(f"[{request_id}] Generating reading-comprehension question")
    
    # Reading comprehension uses higher temperature
    temperature = 0.8
    logger.info(f"[{request_id}] Using higher temperature of {temperature} for reading comprehension")
    
    # Construct prompt specifically for reading comprehension
    prompt = construct_prompt(grade, subject, sub_activity, difficulty, "reading-comprehension")
    logger.info(f"[{request_id}] Constructed prompt: {prompt[:100]}...")
    
    # Create system message specific for reading comprehension with explicit instructions
    system_message = """You are an AI that generates educational reading comprehension questions for elementary school students.
Your responses MUST be in valid JSON format with the following fields:
1. 'passage': A short reading text appropriate for the grade level
2. 'question': A question about the passage
3. 'choices': An array of EXACTLY 4 possible answers
4. 'answer': The correct answer (which must be one of the choices)
5. 'type': Must be exactly "reading-comprehension"

Example format:
{
  "passage": "Sam has a red ball. 🔴 He likes to play with it in the park. 🌳 The ball bounces high when he throws it. ⬆️",
  "question": "What color is Sam's ball? 🔴",
  "choices": ["Red", "Blue", "Green", "Yellow"],
  "answer": "Red",
  "type": "reading-comprehension"
}

IMPORTANT: Always include all these fields exactly as shown.
IMPORTANT: Always provide EXACTLY 4 choices for the question. No more, no less.
IMPORTANT: Always add appropriate emojis throughout the passage text to make it more engaging and visually interesting for children. Emojis can be placed in the middle or at the end of sentences.
IMPORTANT: Also add appropriate emojis to the question text to make it more engaging. Emojis can be placed anywhere in the question - in the middle or at the end of the text. Choose emojis that relate to the subject matter."""
    
    try:
        # Make API call
        start_time = time.time()

        ollama_response = await ollama_async_client.chat(model=os.getenv("OLLAMA_MODEL"),
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            format=ReadingComprehensionQuestion.model_json_schema(),
            options={"temperature": temperature},
        )

        logger.info(f"[{request_id}] OLLAMA response: {ollama_response}")
        api_time = time.time() - start_time
        logger.info(f"[{request_id}] API call completed in {api_time:.2f}s")
        
        # Log the raw response content for debugging
        content = ollama_response.message.content
        logger.info(f"[{request_id}] Raw API response for reading comprehension: {content[:500]}...")
        
        json_data = json.loads(content)
        
        # Ensure type is set correctly
        json_data["type"] = "reading-comprehension"
        
        # Validate and fix the choices
        choices = json_data.get("choices", [])
        logger.info(f"[{request_id}] Reading comprehension - Number of choices: {len(choices)}")
        logger.info(f"[{request_id}] Reading comprehension - Choices: {choices}")
        
        # Check if choices are in the question text
        question = json_data.get("question", "")
        choice_markers = ["A)", "B)", "C)", "D)", "1)", "2)", "3)", "4)", "a)", "b)", "c)", "d)"]
        has_choice_markers = any(marker in question for marker in choice_markers)
        
        if has_choice_markers:
            logger.warning(f"[{request_id}] Reading comprehension - Choices may be included in question text: {question}")
            
            # Try to extract just the question part by looking for the first choice marker
            for marker in choice_markers:
                if marker in question:
                    # Split at the first marker
                    parts = question.split(marker, 1)
                    cleaned_question = parts[0].strip()
                    logger.info(f"[{request_id}] Reading comprehension - Cleaned question: {cleaned_question}")
                    json_data["question"] = cleaned_question
                    break
        
        # Check if the answer is in the choices
        answer = json_data.get("answer", "")
        if answer and answer not in choices:
            logger.warning(f"[{request_id}] Reading comprehension - Answer '{answer}' not in choices {choices}")
            
            # Add the answer to the choices if not already present
            if len(choices) > 0:
                choices[-1] = answer
                logger.info(f"[{request_id}] Fixed reading comprehension choices to include answer: {choices}")
            else:
                logger.warning(f"[{request_id}] No choices provided for reading comprehension question")
                choices = ["Option A", "Option B", answer, "Option C"]
                logger.info(f"[{request_id}] Created fallback choices: {choices}")
            
            json_data["choices"] = choices
        
        # Ensure we have exactly 4 choices
        if len(choices) < 4:
            logger.warning(f"[{request_id}] Too few choices ({len(choices)}) for reading comprehension")
            
            # Add additional choices to reach 4
            while len(choices) < 4:
                new_choice = f"Option {chr(65 + len(choices))}"  # Option A, Option B, etc.
                if new_choice not in choices and new_choice != answer:
                    choices.append(new_choice)
                    logger.info(f"[{request_id}] Added extra choice: {new_choice}")
            
            json_data["choices"] = choices
        elif len(choices) > 4:
            logger.warning(f"[{request_id}] Too many choices ({len(choices)}) for reading comprehension")
            
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
            
            logger.info(f"[{request_id}] Reduced choices to: {choices}")
            json_data["choices"] = choices
        
        # Add metadata
        json_data["sub_activity"] = sub_activity
        json_data["subject"] = subject
        json_data["difficulty"] = difficulty
        
        return json_data
        
    except Exception as e:
        logger.error(f"[{request_id}] Error generating reading-comprehension question: {str(e)}")
        logger.exception(e)  # Log the full stack trace
        return get_fallback_question(str(grade), subject, sub_activity, difficulty)

def construct_mario_math_prompt(grade: int, difficulty: str) -> str:
    """
    Constructs a prompt for the Mushroom Kingdom Calculations math activity.
    
    Args:
        grade: Student grade level (2-3)
        difficulty: Difficulty level ("Easy", "Medium", "Hard")
        
    Returns:
        A prompt string for generating a Mario-themed math question
    """
    # Get random Mario elements for the question
    character1 = random.choice(MARIO_CHARACTERS)
    character2 = random.choice([c for c in MARIO_CHARACTERS if c != character1])
    items = random.choice(MARIO_ITEMS)
    location = random.choice(MARIO_LOCATIONS)
    activity = random.choice(MARIO_ACTIVITIES)
    
    # Determine number ranges based on grade and difficulty
    if grade <= 2:
        if difficulty == "Easy":
            num_range = "1-10"
            sum_range = "should not exceed 20"
            diff_range = "should not go below 0"
        elif difficulty == "Medium":
            num_range = "1-20"
            sum_range = "should not exceed 30"
            diff_range = "should not go below 0"
        else:  # Hard
            num_range = "1-30"
            sum_range = "should not exceed 50"
            diff_range = "should not go below 0"
    else:  # Grade 3
        if difficulty == "Easy":
            num_range = "1-20"
            sum_range = "should not exceed 40"
            diff_range = "should not go below 0"
        elif difficulty == "Medium":
            num_range = "1-50"
            sum_range = "should not exceed 100"
            diff_range = "should not go below 0"
        else:  # Hard
            num_range = "1-100"
            sum_range = "should not exceed 200"
            diff_range = "should not go below 0"
    
    # Random seed for uniqueness
    random_seed = getRandomSeed()
    
    prompt = f"""
    Generate a {difficulty.lower()} {grade}-grade level math question in a Mario and Luigi themed world for elementary students.
    
    Use the following Mario-themed elements in your question:
    - Characters: {character1} and/or {character2}
    - Items: {items}
    - Location: {location}
    - Activity: {activity}
    
    Number range should be {num_range} with results {sum_range}, {diff_range}.
    
    Use this random seed for variety: {random_seed}
    
    The question should be about math problems that Mario characters encounter, such as collecting coins, 
    defeating enemies, calculating scores, or measuring distances in the Mushroom Kingdom.
    Make the question fun and engaging for kids who love Mario games.
    
    The math should be appropriate for grade {grade} and should require basic operations 
    (addition, subtraction, multiplication, or division depending on grade level).
    
    The correct answer must be one of the multiple choice options.
    
    IMPORTANT: After creating the Mario-themed math problem:
    1. Use the calculator tool to compute the exact answer
    2. Use the calculator tool to create reasonable wrong answers
    3. Verify all calculations are correct using the calculator tool
    4. Ensure the choices are appropriate for the grade level and the correct answer is included
    
    CRITICAL WORKFLOW:
    1. FIRST, design your Mario math problem with explicit numbers
    2. SECOND, use the calculator tool to compute the exact answer:
       - Pass the mathematical expression (e.g., "8 + 12" for collecting coins)
       - ALSO pass the full Mario-themed question as the "question" parameter
    3. THIRD, include this exact calculator result in your choices
    4. FOURTH, set this calculator result as the "answer" field
    5. VERIFY that your "answer" value appears in the "choices" array
    """
    
    return prompt

def construct_mario_english_prompt(grade: int, difficulty: str) -> str:
    """
    Constructs a prompt for the Mushroom Kingdom Vocabulary English activity.
    
    Args:
        grade: Student grade level (2-3)
        difficulty: Difficulty level ("Easy", "Medium", "Hard")
        
    Returns:
        A prompt string for generating a Mario-themed English question
    """
    # Get random Mario elements for the question
    character1 = random.choice(MARIO_CHARACTERS)
    character2 = random.choice([c for c in MARIO_CHARACTERS if c != character1])
    items = random.choice(MARIO_ITEMS)
    location = random.choice(MARIO_LOCATIONS)
    
    # Random seed for uniqueness
    random_seed = getRandomSeed()
    
    prompt = f"""
    Generate a {difficulty.lower()} {grade}-grade level English vocabulary question in a Mario and Luigi themed world for elementary students.
    
    Use the following Mario-themed elements in your question:
    - Characters: {character1} and/or {character2}
    - Items: {items}
    - Location: {location}
    
    Use this random seed for variety: {random_seed}
    
    The question should focus on one of the following:
    1. Word meanings/definitions in a Mario context
    2. Synonyms/antonyms with Mario-themed examples
    3. Completing sentences about Mario adventures with appropriate vocabulary
    4. Identifying parts of speech in Mario-themed sentences
    
    Make the question fun and engaging for kids who love Mario games while teaching important English concepts.
    
    The vocabulary should be appropriate for grade {grade} students.
    
    IMPORTANT REQUIREMENTS:
    - The correct answer must be one of the multiple choice options
    - You MUST provide EXACTLY 4 choices in your answer
    - The question and choices should be clearly separate (don't include choices as part of the question text)
    - Make sure all 4 choices are realistic and appropriate for the grade level
    """
    
    return prompt

def construct_prompt(grade: int, subject: str, sub_activity: str, difficulty: str, question_type: str) -> str:
    """
    Constructs a prompt based on the parameters for AI question generation.
    
    Args:
        grade: Student grade level (2-3)
        subject: Subject area ("Math" or "English")
        sub_activity: Sub-activity type (e.g., "Addition/Subtraction", "Opposites/Antonyms")
        difficulty: Difficulty level ("Easy", "Medium", "Hard")
        question_type: Type of question ("multiple-choice", "direct-answer", "reading-comprehension")
        
    Returns:
        A prompt string for generating an educational question
    """
    # Handle Mario-themed activities
    if sub_activity == "Mushroom Kingdom Calculations" and subject == "Math":
        return construct_mario_math_prompt(grade, difficulty)
    
    if sub_activity == "Mushroom Kingdom Vocabulary" and subject == "English":
        return construct_mario_english_prompt(grade, difficulty)
    
    # Proceed with standard prompts for other activities...
    logger = logging.getLogger(__name__)
    logger.info(f"Constructing prompt for: Grade {grade}, {subject}, {sub_activity}, {difficulty}")
    
    # Default base prompt
    prompt = f"Generate a {difficulty.lower()} {grade}-grade level {subject.lower()} question about {sub_activity} for elementary school students."
    
    # Math subject
    if subject == "Math":
        # Generate random elements for more diverse questions
        person1 = random.choice(MATH_NAMES)
        person2 = random.choice([n for n in MATH_NAMES if n != person1])  # Ensure different name
        objects = random.choice(MATH_OBJECTS)
        location = random.choice(MATH_LOCATIONS)
        activity = random.choice(MATH_ACTIVITIES)
        
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
        
        # Different prompt structures for each sub-activity
        if sub_activity == "Addition/Subtraction":
            # Apply random variation to the prompt itself
            operation = random.choice([
                "addition", "subtraction", 
                "adding", "subtracting",
                "sums", "differences"
            ])
            
            # Random seed for uniqueness
            random_seed = getRandomSeed()
            
            prompt = f"""
            Generate a {difficulty.lower()} {grade}-grade level math question about {operation} for elementary students.
            
            Number range should be {num_range} with results {sum_range}, {diff_range}.
            
            Use this random seed for variety: {random_seed}
            
            You can optionally incorporate these elements to make the question more interesting:
            - Names: {person1} and/or {person2}
            - Objects: {objects}
            - Location: {location}
            
            The question should require either addition or subtraction to solve, appropriate for grade {grade}.
            Make sure to generate a DIFFERENT question than ones you've generated before.
            
            The correct answer must be one of the multiple choice options.
            
            IMPORTANT: After creating the addition or subtraction problem:
            1. Use the calculator tool to compute the exact answer:
               - Pass the mathematical expression (e.g., "7 + 3")
               - ALSO pass the full question as the context parameter
            2. Use the calculator tool to generate plausible wrong answers (by adding or subtracting 1, 2, or 10 from the correct answer)
            3. Double-check that all calculations are correct using the calculator tool
            4. Make sure the correct answer is included in the choices
            
            CRITICAL WORKFLOW:
            1. FIRST, design your math problem (e.g., "7 + 3" or "8 - 5")
            2. SECOND, use the calculator tool to compute the exact answer:
               - Pass the mathematical expression (e.g., "7 + 3")
               - ALSO pass the full question as the context parameter
            3. THIRD, include this exact calculator result in your choices
            4. FOURTH, set this calculator result as the "answer" field
            5. VERIFY that your "answer" value appears in the "choices" array
            """
            
        elif sub_activity == "Multiplication/Division":
            if grade <= 2:  # Simpler for grade 2
                table_range = "up to 5 (e.g., 2×4, 3×3, 5×2)"
                division_range = "simple division with no remainders"
            else:  # Grade 3+
                if difficulty.lower() == "easy":
                    table_range = "up to 5 (e.g., 3×4, 5×2)"
                    division_range = "simple division with no remainders"
                elif difficulty.lower() == "medium":
                    table_range = "up to 10 (e.g., 6×7, 8×4)"
                    division_range = "may include simple remainders"
                else:  # Hard
                    table_range = "up to 12 (e.g., 8×9, 12×6)"
                    division_range = "may include remainders"
            
            # Random seed for uniqueness
            random_seed = getRandomSeed()
            
            prompt = f"""
            Generate a {difficulty.lower()} {grade}-grade level math question about multiplication or division.
            
            For multiplication, use times tables {table_range}.
            For division, use {division_range}.
            
            Use this random seed for variety: {random_seed}
            
            You can optionally incorporate these elements:
            - Names: {person1} and/or {person2}
            - Objects arranged in groups/rows: {objects}
            - Location: {location}
            
            Make sure to generate a DIFFERENT question than ones you've generated before.
            
            The correct answer must be one of the multiple choice options.
            
            IMPORTANT: After creating the multiplication or division problem:
            1. Use the calculator tool to compute the correct answer
            2. Use the calculator tool to generate plausible wrong answers by creating variations of the calculation
            3. Double-check all calculations with the calculator tool
            4. Make sure choices are appropriate for the grade level
            
            CRITICAL WORKFLOW:
            1. FIRST, design your math problem (e.g., "3 × 4" or "10 ÷ 2")
            2. SECOND, use the calculator tool to compute the exact answer:
               - Pass the mathematical expression (e.g., "3 * 4" or "10 / 2")
               - ALSO pass the full question as the "question" parameter
            3. THIRD, include this exact calculator result in your choices
            4. FOURTH, set this calculator result as the "answer" field
            5. VERIFY that your "answer" value appears in the "choices" array
            """
            
        elif sub_activity == "Word Problems":
            # Select a random template and replace placeholders
            template = random.choice(MATH_WORD_PROBLEM_TEMPLATES)
            
            # Determine appropriate number ranges for word problems
            if grade <= 2:
                if difficulty.lower() == "easy":
                    num_descrip = "simple one-step problem with small numbers (1-10)"
                else:
                    num_descrip = "one-step problem with numbers up to 20"
            else:
                if difficulty.lower() == "easy":
                    num_descrip = "one-step problem with numbers up to 30"
                elif difficulty.lower() == "medium":
                    num_descrip = "one or two-step problem with numbers up to 50"
                else:
                    num_descrip = "two-step problem with numbers up to 100"
            
            # Random seed for uniqueness
            random_seed = getRandomSeed()
            
            prompt = f"""
            Generate a {difficulty.lower()} {grade}-grade level math word problem.
            
            The problem should be a {num_descrip}.
            
            Use this random seed for variety: {random_seed}
            
            Include these elements in your word problem:
            - Name: {person1} (and optionally {person2})
            - Objects: {objects}
            - Activity: {activity}
            - Location: {location}
            
            Make sure the problem is appropriate for grade {grade} students and has a clear solution.
            Create a DIFFERENT problem than ones you've generated before.
            
            The correct answer must be one of the multiple choice options.
            
            IMPORTANT: After creating the word problem:
            1. Use the calculator tool to solve the problem step-by-step
            2. Ensure the correct answer is included in the choices
            3. Use the calculator tool to generate plausible wrong answers that are mathematically different from the correct answer
            4. Double-check your solution with the calculator tool before finalizing
            
            CRITICAL WORKFLOW:
            1. FIRST, design your word problem with explicit numbers
            2. SECOND, use the calculator tool to compute the exact answer:
               - Pass the mathematical expression (e.g., "5 * 4" for "5 boxes with 4 apples each")
               - ALSO pass the full word problem as the "question" parameter
            3. THIRD, include this exact calculator result in your choices
            4. FOURTH, set this calculator result as the "answer" field
            5. VERIFY that your "answer" value appears in the "choices" array
            """
        
        # Log the enhanced prompt details
        logger.info(f"Math question randomization - Sub-activity: {sub_activity}, Person: {person1}, Objects: {objects}, Location: {location}")
    
    # English subject
    elif subject == "English":
        if sub_activity == "Opposites/Antonyms":
            # Get random elements for variety
            target_words = [word for word in ENGLISH_ADJECTIVES if word != "happy"]  # Exclude 'happy' to avoid repetition
            target_word = random.choice(target_words)
            random_seed = getRandomSeed()
            prompt_templates = [
                f"What is the opposite of '{target_word}'?",
                f"Which word means the opposite of '{target_word}'?",
                f"Select the word that has the opposite meaning of '{target_word}'.",
                f"Choose the antonym for '{target_word}'.",
                f"Which of these words is most opposite in meaning to '{target_word}'?"
            ]
            prompt_template = random.choice(prompt_templates)
            
            if grade <= 2:  # Grade 1-2
                prompt = f"""
                Generate a {difficulty.lower()} {grade}-grade level English question about opposites or antonyms.
                
                YOU MUST use exactly this question format WITHOUT changing the word: "{prompt_template}"
                
                You MUST use the word '{target_word}' in your question. DO NOT substitute it with a different word.
                DO NOT use the word 'happy' in your question - this word has been overused.
                
                Use this random seed for variety: {random_seed}
                
                The question should ask for the opposite of a simple word appropriate for this grade level.
                
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
                
                IMPORTANT REQUIREMENTS:
                - Provide EXACTLY 4 multiple choice options (no more, no less)
                - Ensure the correct answer (the true opposite/antonym) is one of the 4 choices
                - Make all choices grade-appropriate
                - Keep the choices separate from the question text
                """
            
            # Log the enhanced prompt details
            logger.info(f"Opposites/Antonyms randomization - Target word: {target_word}, Template: {prompt_template}, Seed: {random_seed}")
            
            return prompt
        
        elif sub_activity == "Synonyms":
            # Get random elements for variety
            target_words = [word for word in ENGLISH_ADJECTIVES if word != "big"]  # Exclude 'big' to avoid repetition
            target_word = random.choice(target_words)
            random_seed = getRandomSeed()
            prompt_templates = [
                f"What is another word for '{target_word}'?",
                f"Which word means the same as '{target_word}'?",
                f"Select the word that has the same meaning as '{target_word}'.",
                f"Choose the synonym for '{target_word}'.",
                f"Which of these words is most similar in meaning to '{target_word}'?"
            ]
            prompt_template = random.choice(prompt_templates)
            
            if grade <= 2:  # Grade 1-2
                prompt = f"""
                Generate a {difficulty.lower()} {grade}-grade level English question about synonyms or similar words.
                
                YOU MUST use exactly this question format WITHOUT changing the word: "{prompt_template}"
                
                You MUST use the word '{target_word}' in your question. DO NOT substitute it with a different word.
                DO NOT use the word 'big' in your question - this word has been overused.
                
                Use this random seed for variety: {random_seed}
                
                CRITICAL INSTRUCTIONS FOR SYNONYMS QUESTION:
                
                This is a question about SYNONYMS (words with SIMILAR meanings), NOT ANTONYMS (words with OPPOSITE meanings).
                
                Follow these steps carefully:
                1. Create a question asking for a synonym of '{target_word}'
                2. Generate EXACTLY 4 answer choices that include at least one TRUE SYNONYM of '{target_word}'
                3. Make the correct answer be a word that has a SIMILAR meaning to '{target_word}'
                4. Triple-check that the correct answer is NOT an antonym or opposite of '{target_word}'
                5. Verify that you haven't accidentally marked an opposite/antonym as the correct answer
                
                Examples of correct synonym pairings:
                - clean → spotless, tidy, pristine (these all have similar meanings)
                - dirty → filthy, grimy, soiled (these all have similar meanings)
                - cold → chilly, cool, frigid (these all have similar meanings)
                - hot → warm, heated, burning (these all have similar meanings)
                
                ESPECIALLY AVOID THIS ERROR: Do not mark words with opposite meanings as synonyms.
                For example, do NOT mark 'clean' and 'dirty' as synonyms - they are antonyms!
                Do NOT mark 'unclean' as a synonym of 'clean' - adding 'un' creates an antonym!
                """
            else:  # Grade 3+
                prompt = f"""
                Generate a {difficulty.lower()} {grade}-grade level English question about synonyms or similar words.
                
                YOU MUST use exactly this question format WITHOUT changing the word: "{prompt_template}"
                
                You MUST use the word '{target_word}' in your question. DO NOT substitute it with a different word.
                DO NOT use the word 'big' in your question - this word has been overused.
                
                Use this random seed for variety: {random_seed}
                
                CRITICAL INSTRUCTIONS FOR SYNONYMS QUESTION:
                
                This is a question about SYNONYMS (words with SIMILAR meanings), NOT ANTONYMS (words with OPPOSITE meanings).
                
                Follow these steps carefully:
                1. Create a question asking for a synonym of '{target_word}'
                2. Generate EXACTLY 4 answer choices that include at least one TRUE SYNONYM of '{target_word}'
                3. Make the correct answer be a word that has a SIMILAR meaning to '{target_word}'
                4. Triple-check that the correct answer is NOT an antonym or opposite of '{target_word}'
                5. Verify that you haven't accidentally marked an opposite/antonym as the correct answer
                
                Examples of correct synonym pairings:
                - clean → spotless, tidy, pristine (these all have similar meanings)
                - dirty → filthy, grimy, soiled (these all have similar meanings)
                - cold → chilly, cool, frigid (these all have similar meanings)
                - hot → warm, heated, burning (these all have similar meanings)
                
                ESPECIALLY AVOID THIS ERROR: Do not mark words with opposite meanings as synonyms.
                For example, do NOT mark 'clean' and 'dirty' as synonyms - they are antonyms!
                Do NOT mark 'unclean' as a synonym of 'clean' - adding 'un' creates an antonym!
                """
            
            # Log the enhanced prompt details
            logger.info(f"Synonyms randomization - Target word: {target_word}, Template: {prompt_template}, Seed: {random_seed}")
            
            return prompt
        
        elif sub_activity == "Reading Comprehension":
            # Select random elements to create varied passages
            topic = random.choice(READING_TOPICS)
            
            location = random.choice(READING_LOCATIONS)
            
            character1 = random.choice(NAMES)
            character2 = random.choice([n for n in NAMES if n != character1])
            
            # Determine question complexity based on grade and difficulty
            if grade <= 2:  # Grade 1-2
                if difficulty.lower() == "easy":
                    passage_length = "very short (2-3 sentences)"
                    question_type = "about the main idea or a specific detail"
                elif difficulty.lower() == "medium":
                    passage_length = "short (3-4 sentences)"
                    question_type = "that requires understanding the sequence of events or making a simple inference"
                else:  # Hard
                    passage_length = "reading passage (4-5 sentences)"
                    question_type = "that requires deeper comprehension or making an inference"
            else:  # Grade 3+
                if difficulty.lower() == "easy":
                    passage_length = "short (3-4 sentences)"
                    question_type = "about key details or main idea"
                elif difficulty.lower() == "medium":
                    passage_length = "reading passage (4-5 sentences)"
                    question_type = "that requires understanding relationships between ideas or making an inference"
                else:  # Hard
                    passage_length = "reading passage (5-6 sentences)"
                    question_type = "that requires understanding cause and effect or drawing conclusions"
            
            # Random seed for uniqueness
            random_seed = getRandomSeed()
            
            prompt = f"""
            Generate a {difficulty.lower()} {grade}-grade level english question about Reading Comprehension for elementary school students.
            
            Create a {passage_length} about {topic} set at a {location}, followed by a question {question_type}.
            
            Include these characters in your passage: {character1} and optionally {character2}.
            
            Use this random seed for variety: {random_seed}
            
            Make sure to generate a DIFFERENT passage than ones you've generated before.
            Try to vary your writing style, sentence patterns, and vocabulary.
            
            The passage should:
            - Use vocabulary appropriate for grade {grade}
            - Have a clear beginning, middle, and end
            - Include interesting details that might be asked about in the question
            - Vary between descriptive, narrative, or informative styles
            
            Your question should be thoughtful and require students to really understand the passage.
            
            IMPORTANT REQUIREMENTS:
            - Provide EXACTLY 4 multiple choice options (no more, no less)
            - Ensure the correct answer is one of the 4 choices
            - Make all choices reasonable so the answer isn't too obvious
            - Keep the choices separate from the question text
            
            Return as a JSON object with 'passage', 'question', 'choices' (array of 4 options), and 'answer' (correct choice).
            """
            
            # Log the enhanced prompt details
            logger.info(f"Reading Comprehension randomization - Topic: {topic}, Location: {location}, Characters: {character1}/{character2}, Seed: {random_seed}")
            
            return prompt
        
        elif sub_activity == "Nouns/Pronouns":
            if grade <= 2:  # Grade 1-2
                return f"Generate a {difficulty.lower()} {grade}-grade level English question about basic nouns or pronouns. The question should be appropriate for this grade level."
            else:  # Grade 3+
                return f"Generate a {difficulty.lower()} {grade}-grade level English question about nouns or pronouns. The question could involve identifying or using the correct noun or pronoun in a sentence."
                
        elif sub_activity == "Grammar Correction":
            if question_type != "direct-answer":
                # Force direct-answer for grammar correction
                question_type = "direct-answer"
                logger.info("Forcing direct-answer question type for Grammar Correction")
                
            # Apply enhanced randomization for grammar correction
            
            # Randomly select error type
            error_types = [
                "subject-verb agreement", 
                "verb tense", 
                "pronoun usage", 
                "article usage",
                "plural forms", 
                "prepositions"
            ]
            
            # Get random elements to include in the prompt
            selected_names = random.sample(NAMES, 2)  # Pick 2 different names
            scenario = random.choice(SCENARIOS)
            location = random.choice(LOCATIONS)
            object_name = random.choice(OBJECTS)
            time_expression = random.choice(TIME_EXPRESSIONS)
            
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
            
            Use these elements in your sentence:
            - Names: {selected_names[0]} and/or {selected_names[1]}
            - Activity: {scenario}
            - Location: {location}
            - Object: {object_name}
            - Time expression: {time_expression}
            
            The question should be the incorrect sentence, and the answer should be the fully corrected sentence.
            Make sure the sentence sounds natural and uses age-appropriate vocabulary.
            Do not use the same pattern as these examples: "She don't like ice cream", "The cats is playing", "He walk to school".
            
            IMPORTANT: This is a direct-answer question type, NOT multiple-choice. Return a JSON object with 'question', 'answer' and 'type' fields. 
            The 'type' field MUST be 'direct-answer', NOT 'multiple-choice'.
            Do NOT include 'choices' field in the response.
            
            Example JSON format:
            {{
                "question": "The boy play with toys.",
                "answer": "The boy plays with toys.",
                "type": "direct-answer"
            }}
            """
            
            # Log the enhanced prompt details
            logger.info(f"Grammar correction randomization - Error type: {error_type}, Names: {selected_names}, Scenario: {scenario}, Location: {location}, Object: {object_name}, Time: {time_expression}")
        
        else:
            # Default english prompt if sub_activity is not recognized
            # Don't override the sub_activity with Opposites/Antonyms - use the requested one
            return prompt
    
    # Add the standard format instructions for the chosen question type
    if question_type == "multiple-choice":
        prompt += " The question should be multiple choice with exactly 4 options. The correct answer must be one of the options."
    elif question_type == "direct-answer":
        prompt += " The question should require a short direct answer."
    else:  # reading-comprehension
        prompt += " The passage should be followed by a multiple-choice question with 4 options. The correct answer must be one of the options."
    
    logger.info(f"Generated prompt with sub-activity ({sub_activity}): {prompt}")
    return prompt

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
    Generate detailed feedback for a grammar correction answer using Ollama.
    
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
    
    try:
        logger.info(f"[{request_id}] Generating grammar feedback")
        start_time = time.time()
        
        # Make API call to Ollama for feedback
        # use async client
        ollama_response = await ollama_async_client.chat(
            model=os.getenv("OLLAMA_MODEL"),
            messages=[
                {"role": "system", "content": "You are a friendly, supportive elementary school teacher providing feedback on grammar corrections. Keep your responses short, simple, and encouraging."},
                {"role": "user", "content": prompt}
            ],
            options={"temperature": 0.5}
        )
        
        api_time = time.time() - start_time
        logger.info(f"[{request_id}] API call completed in {api_time:.2f}s")
        logger.info(f"[{request_id}] OLLAMA response: {ollama_response}")
        
        # Extract the feedback
        feedback = ollama_response.message.content.strip()
        logger.info(f"[{request_id}] Generated feedback: {feedback[:100]}...")
        
        feedback = remove_think_tags(feedback)

        return feedback
        
    except Exception as e:
        logger.error(f"[{request_id}] Error generating feedback: {str(e)}")
        return get_fallback_feedback(is_correct)

def get_fallback_feedback(is_correct: bool) -> str:
    """Get fallback feedback when the API fails."""
    if is_correct:
        return "Great job correcting the sentence! You identified the grammar mistake and fixed it correctly. Keep up the good work!"
    else:
        return "Good try! The sentence needed a grammar fix. Look carefully at things like verb tense, subject-verb agreement, or word usage. You'll get it next time!"

def getRandomSeed() -> int:
    """Generate a random seed for AI prompts to increase variety."""
    return random.randint(1000, 9999)

async def evaluate_grammar_correction(question: str, user_answer: str, correct_answer: str, player_name: str = "student") -> dict:
    """
    Evaluate a grammar correction answer using Ollama API and provide detailed feedback.
    
    Args:
        question: The original question (incorrect sentence)
        user_answer: The student's corrected answer
        correct_answer: The expected correct answer
        player_name: The name of the player to address in the feedback
        
    Returns:
        Dictionary with is_correct (bool) and feedback (str)
    """
    logger = logging.getLogger(__name__)
    request_id = f"{time.time():.0f}"
    
    # Create a prompt to evaluate the answer
    prompt = f"""
You are evaluating a student's grammar correction answer. Please review the following:

ORIGINAL INCORRECT SENTENCE:
{question}

EXPECTED CORRECT ANSWER:
{correct_answer}

STUDENT'S ANSWER:
{user_answer}

STUDENT'S NAME:
{player_name}

First, determine if the student's answer is essentially correct. Consider:
1. Did they fix the primary grammar issue(s)?
2. Is their sentence grammatically correct, even if worded differently than the expected answer?
3. Does their correction maintain the original meaning of the sentence?

Be somewhat lenient - if they fixed the main grammar issue but made a minor spelling mistake, still consider it correct.

Then provide brief, encouraging feedback (2-3 sentences) appropriate for an elementary school student.
IMPORTANT: Your feedback should:
- Address the student by their name ({player_name})
- Avoid overused phrases like "fantastic work" or "great job" at the beginning of every response
- Be specific about what grammar rule was applied correctly/incorrectly
- Vary your tone, word choice, and sentence structure
- Use age-appropriate language but don't oversimplify
- Sometimes ask a follow-up question to encourage further learning

Return your response in this JSON format:
{{
  "is_correct": true/false,
  "feedback": "Your varied, personalized feedback here"
}}
"""
    
    try:
        logger.info(f"[{request_id}] Evaluating grammar correction answer")
        start_time = time.time()
        
        # Make API call to Ollama for evaluation
        ollama_response = await ollama_async_client.chat(
            model=os.getenv("OLLAMA_MODEL"),
            messages=[
                {"role": "system", "content": f"""You are a thoughtful, creative elementary school teacher evaluating grammar corrections. 
You assess whether students fixed the main grammar issue, even if their wording differs from the expected answer.

When providing feedback:
1. Address the student by name ({player_name})
2. Use varied openings and expressions (avoid repetitive phrases like "Great job!" or "That's fantastic work!")
3. Be specific about the grammar rule that was applied or missed
4. Vary your feedback style - sometimes be encouraging, sometimes curious, sometimes explanatory
5. Occasionally include a simple grammar tip or a brief follow-up question
6. Never address the student by names mentioned in the question text.

Your feedback should sound natural and personalized, not formulaic."""},
                {"role": "user", "content": prompt}
            ],
            format={"type": "object", "properties": {"is_correct": {"type": "boolean"}, "feedback": {"type": "string"}}}
        )
        
        api_time = time.time() - start_time
        logger.info(f"[{request_id}] API call completed in {api_time:.2f}s")
        logger.info(f"[{request_id}] OLLAMA response: {ollama_response}")
        
        # Parse the JSON response and remove think tags from feedback
        evaluation_result = json.loads(ollama_response.message.content)
        
        # If evaluation_result is already a dict, use it directly
        if isinstance(evaluation_result, dict):
            # Remove think tags if any
            if "feedback" in evaluation_result and isinstance(evaluation_result["feedback"], str):
                evaluation_result["feedback"] = remove_think_tags(evaluation_result["feedback"])
        else:
            # Convert to dict if needed and remove think tags
            evaluation_result = remove_think_tags(evaluation_result)
        
        # Validate the required fields are present
        if "is_correct" not in evaluation_result or "feedback" not in evaluation_result:
            logger.error(f"[{request_id}] Missing required fields in evaluation result")
            return get_fallback_grammar_evaluation(question, user_answer, correct_answer, player_name)
        
        # Convert is_correct to boolean if it's a string
        if isinstance(evaluation_result["is_correct"], str):
            evaluation_result["is_correct"] = evaluation_result["is_correct"].lower() == "true"
        
        logger.info(f"[{request_id}] Evaluation result: correct={evaluation_result['is_correct']}, feedback={evaluation_result['feedback'][:50]}...")
        
        return evaluation_result
            
    except Exception as e:
        logger.error(f"[{request_id}] Error evaluating grammar correction: {str(e)}")
        return get_fallback_grammar_evaluation(question, user_answer, correct_answer, player_name)

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
    Evaluate a reading comprehension answer using Ollama API and provide detailed feedback.
    
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
    
    # Create a prompt to evaluate the answer
    prompt = f"""
You are evaluating a student's answer to a reading comprehension question. Please review the following:

READING PASSAGE:
{passage}

QUESTION:
{question}

CORRECT ANSWER FROM QUESTION:
{correct_answer}

STUDENT'S ANSWER:
{user_answer}

First, determine if the student's answer is essentially correct. Consider the meaning and understanding, not just exact words.
Then provide brief, encouraging feedback (2-3 sentences) appropriate for an elementary school student.

Return your response in this JSON format:
{{
  "is_correct": true/false,
  "feedback": "Your feedback here"
}}
"""
    
    try:
        logger.info(f"[{request_id}] Evaluating reading comprehension answer")
        start_time = time.time()
        
        # Make API call to Ollama for evaluation
        ollama_response = await ollama_async_client.chat(
            model=os.getenv("OLLAMA_MODEL"),
            messages=[
                {"role": "system", "content": "You are a helpful, supportive elementary school teacher evaluating reading comprehension answers. You judge answers based on understanding rather than exact wording. You provide constructive, encouraging feedback."},
                {"role": "user", "content": prompt}
            ],
            format={"type": "object", "properties": {"is_correct": {"type": "boolean"}, "feedback": {"type": "string"}}}
        )
        
        api_time = time.time() - start_time
        logger.info(f"[{request_id}] API call completed in {api_time:.2f}s")
        logger.info(f"[{request_id}] OLLAMA response: {ollama_response}")
        
        # Parse the JSON response
        evaluation_result = json.loads(ollama_response.message.content)
        evaluation_result = remove_think_tags(evaluation_result)
        # Validate the required fields are present
        if "is_correct" not in evaluation_result or "feedback" not in evaluation_result:
            logger.error(f"[{request_id}] Missing required fields in evaluation result")
            return get_fallback_reading_evaluation(user_answer, correct_answer)
        
        # Convert is_correct to boolean if it's a string
        if isinstance(evaluation_result["is_correct"], str):
            evaluation_result["is_correct"] = evaluation_result["is_correct"].lower() == "true"
        
        logger.info(f"[{request_id}] Evaluation result: correct={evaluation_result['is_correct']}, feedback={evaluation_result['feedback'][:50]}...")
        
        return evaluation_result
            
    except Exception as e:
        logger.error(f"[{request_id}] Error evaluating reading comprehension: {str(e)}")
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