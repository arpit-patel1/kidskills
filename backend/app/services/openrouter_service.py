import os
import json
import time
import re
from typing import Dict, Any, Optional, List, Literal
from openai import OpenAI
from dotenv import load_dotenv
import logging
from pydantic import BaseModel, Field, validator, ValidationError

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

# Load environment variables
load_dotenv()

# Get OpenRouter API key
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    logger.warning("OpenRouter API key not found. AI question generation will not work.")
else:
    # Log masked API key for debugging
    masked_key = OPENROUTER_API_KEY[:4] + "****" + OPENROUTER_API_KEY[-4:]
    logger.info(f"Using OpenRouter API key: {masked_key}")

# Get OpenRouter model from env or use default
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3-haiku-20240307")
logger.info(f"Using OpenRouter model: {OPENROUTER_MODEL}")

# Initialize OpenAI client for OpenRouter
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

# Define Pydantic models for structured output
class MultipleChoiceQuestion(BaseModel):
    question: str = Field(..., description="The question text")
    choices: List[str] = Field(..., min_items=2, max_items=4, description="An array of possible answers")
    answer: str = Field(..., description="The correct answer, must be one of the choices")
    type: Literal["multiple-choice"] = Field("multiple-choice", description="The question type")
    
    @validator('answer')
    def answer_must_be_in_choices(cls, v, values):
        if 'choices' in values and v not in values['choices']:
            raise ValueError(f'Answer "{v}" must be one of the choices: {values["choices"]}')
        return v
    
    def to_dict(self):
        # Handle both Pydantic v1 and v2 methods
        if hasattr(self, "model_dump"):
            return self.model_dump()
        return self.dict()  # Fallback for older Pydantic versions

class DirectAnswerQuestion(BaseModel):
    question: str = Field(..., description="The question text")
    answer: str = Field(..., description="The correct answer")
    type: Literal["direct-answer"] = Field("direct-answer", description="The question type")
    
    def to_dict(self):
        # Handle both Pydantic v1 and v2 methods
        if hasattr(self, "model_dump"):
            return self.model_dump()
        return self.dict()  # Fallback for older Pydantic versions

class ReadingComprehensionQuestion(BaseModel):
    passage: str = Field(..., description="The reading text")
    question: str = Field(..., description="The question about the passage")
    choices: List[str] = Field(..., min_items=2, max_items=4, description="An array of possible answers")
    answer: str = Field(..., description="The correct answer, must be one of the choices")
    type: Literal["reading-comprehension"] = Field("reading-comprehension", description="The question type")
    
    @validator('answer')
    def answer_must_be_in_choices(cls, v, values):
        if 'choices' in values and v not in values['choices']:
            raise ValueError(f'Answer "{v}" must be one of the choices: {values["choices"]}')
        return v
    
    def to_dict(self):
        # Handle both Pydantic v1 and v2 methods
        if hasattr(self, "model_dump"):
            return self.model_dump()
        return self.dict()  # Fallback for older Pydantic versions

# Fallback questions in case the API fails
FALLBACK_QUESTIONS = {
    "2": {  # Grade 2
        "Math": {
            "Easy": [
                {
                    "question": "What is 5 + 3?",
                    "choices": ["7", "8", "9", "10"],
                    "answer": "8",
                    "type": "multiple-choice"
                },
                {
                    "question": "What is 10 - 4?",
                    "choices": ["4", "5", "6", "7"],
                    "answer": "6",
                    "type": "multiple-choice"
                },
            ],
            "Medium": [
                {
                    "question": "What is 12 + 9?",
                    "choices": ["19", "21", "23", "25"],
                    "answer": "21",
                    "type": "multiple-choice"
                },
                {
                    "question": "What is 15 - 7?",
                    "choices": ["5", "6", "7", "8"],
                    "answer": "8",
                    "type": "multiple-choice"
                },
            ],
            "Hard": [
                {
                    "question": "If you have 3 groups of 5 apples, how many apples do you have in total?",
                    "choices": ["8", "10", "15", "20"],
                    "answer": "15",
                    "type": "multiple-choice"
                },
                {
                    "question": "What is 25 - 8?",
                    "choices": ["15", "16", "17", "18"],
                    "answer": "17",
                    "type": "multiple-choice"
                },
            ]
        },
        "English": {
            "Easy": [
                {
                    "question": "Which word means the opposite of 'big'?",
                    "choices": ["large", "huge", "small", "tall"],
                    "answer": "small",
                    "type": "multiple-choice"
                },
                {
                    "question": "What is the correct spelling?",
                    "choices": ["frend", "friend", "freind", "frened"],
                    "answer": "friend",
                    "type": "multiple-choice"
                },
            ],
            "Medium": [
                {
                    "question": "Which word is a noun?",
                    "choices": ["run", "happy", "book", "fast"],
                    "answer": "book",
                    "type": "multiple-choice"
                },
                {
                    "question": "What is the plural of 'child'?",
                    "choices": ["childs", "childes", "childen", "children"],
                    "answer": "children",
                    "type": "multiple-choice"
                },
            ],
            "Hard": [
                {
                    "question": "Complete the sentence: 'She ____ to the store yesterday.'",
                    "choices": ["go", "goes", "going", "went"],
                    "answer": "went",
                    "type": "multiple-choice"
                },
                {
                    "question": "What is a sentence that ends with a question mark called?",
                    "choices": ["statement", "question", "exclamation", "command"],
                    "answer": "question",
                    "type": "multiple-choice"
                },
            ]
        }
    },
    "3": {  # Grade 3
        "Math": {
            "Easy": [
                {
                    "question": "What is 7 × 3?",
                    "choices": ["18", "20", "21", "24"],
                    "answer": "21",
                    "type": "multiple-choice"
                },
                {
                    "question": "What is 16 ÷ 4?",
                    "choices": ["2", "3", "4", "5"],
                    "answer": "4",
                    "type": "multiple-choice"
                },
            ],
            "Medium": [
                {
                    "question": "What is 9 × 6?",
                    "choices": ["48", "54", "56", "60"],
                    "answer": "54",
                    "type": "multiple-choice"
                },
                {
                    "question": "What is 27 ÷ 3?",
                    "choices": ["7", "8", "9", "10"],
                    "answer": "9",
                    "type": "multiple-choice"
                },
            ],
            "Hard": [
                {
                    "question": "If a rectangle has a length of 8 cm and a width of 5 cm, what is its area?",
                    "choices": ["13 cm²", "26 cm²", "40 cm²", "64 cm²"],
                    "answer": "40 cm²",
                    "type": "multiple-choice"
                },
                {
                    "question": "What is 156 + 287?",
                    "choices": ["343", "423", "443", "453"],
                    "answer": "443",
                    "type": "multiple-choice"
                },
            ]
        },
        "English": {
            "Easy": [
                {
                    "question": "Which word is a synonym for 'happy'?",
                    "choices": ["sad", "angry", "joyful", "tired"],
                    "answer": "joyful",
                    "type": "multiple-choice"
                },
                {
                    "question": "Which sentence is written correctly?",
                    "choices": [
                        "The dog is running fast.",
                        "The dog is running fastly.",
                        "The dog is run fast.",
                        "The dog running fast."
                    ],
                    "answer": "The dog is running fast.",
                    "type": "multiple-choice"
                },
            ],
            "Medium": [
                {
                    "question": "What is the main idea in a paragraph called?",
                    "choices": ["title", "heading", "topic sentence", "conclusion"],
                    "answer": "topic sentence",
                    "type": "multiple-choice"
                },
                {
                    "question": "Which word is a verb?",
                    "choices": ["beautiful", "quickly", "jump", "happy"],
                    "answer": "jump",
                    "type": "multiple-choice"
                },
            ],
            "Hard": [
                {
                    "question": "Which of these is a compound sentence?",
                    "choices": [
                        "She ran to the store.",
                        "She ran to the store and bought milk.",
                        "Running to the store quickly.",
                        "After running to the store."
                    ],
                    "answer": "She ran to the store and bought milk.",
                    "type": "multiple-choice"
                },
                {
                    "question": "What is the past tense of 'bring'?",
                    "choices": ["bringed", "brang", "brought", "bringing"],
                    "answer": "brought",
                    "type": "multiple-choice"
                },
            ]
        }
    }
}

# Add these lists at the top level of the file, after the imports and before any functions
# Various elements to randomize math questions
MATH_NAMES = [
    "Emma", "Liam", "Olivia", "Noah", "Ava", "William", "Sophia", "James", "Isabella", "Benjamin",
    "Mia", "Elijah", "Harper", "Lucas", "Amelia", "Mason", "Evelyn", "Logan", "Abigail", "Alexander",
    "Emily", "Ethan", "Elizabeth", "Jacob", "Sofia", "Michael", "Avery", "Daniel", "Ella", "Henry",
    "Madison", "Jackson", "Scarlett", "Sebastian", "Grace", "Aiden", "Chloe", "Matthew", "Victoria", "Samuel"
]

MATH_OBJECTS = [
    "apples", "oranges", "bananas", "pencils", "markers", "crayons", "books", "notebooks", 
    "cookies", "candies", "toys", "dolls", "cars", "blocks", "stickers", "coins", "marbles",
    "flowers", "plants", "trees", "dogs", "cats", "birds", "fish", "stickers", "cards",
    "erasers", "rulers", "paper clips", "buttons", "beads", "balls", "balloons", "cupcakes"
]

MATH_LOCATIONS = [
    "store", "school", "park", "library", "home", "garden", "zoo", "farm", "beach", 
    "playground", "museum", "bakery", "party", "classroom", "bookstore", "market", "kitchen",
    "backyard", "basement", "garage", "attic", "treehouse", "clubhouse", "campsite", "amusement park"
]

MATH_ACTIVITIES = [
    "collecting", "buying", "sharing", "giving away", "selling", "counting", "finding", "arranging",
    "packing", "distributing", "sorting", "planting", "picking", "saving", "winning", "losing",
    "receiving", "dividing", "grouping", "organizing", "displaying", "gathering", "earning"
]

MATH_WORD_PROBLEM_TEMPLATES = [
    "{person} has {num1} {objects}. They {activity} {num2} more. How many {objects} do they have now?",
    "{person} had {num1} {objects}. They {activity} {num2} of them. How many {objects} do they have left?",
    "{person} and {person2} have {num1} and {num2} {objects} respectively. How many {objects} do they have in total?",
    "There are {num1} {objects} at the {location}. {person} brings {num2} more. How many {objects} are there now?",
    "{person} wants to share {num1} {objects} equally among {num2} friends. How many {objects} will each friend get?",
    "{person} has {num1} {objects} and {person2} has {num2} {objects}. How many more {objects} does {person} have?",
    "{person} arranges {num1} {objects} in {num2} equal rows. How many {objects} are in each row?",
    "{person} buys {num1} {objects} from the {location} for ${num2} each. How much money did {person} spend?",
    "If {person} collects {num1} {objects} each day, how many {objects} will {person} have after {num2} days?",
    "{person} has {num1} {objects}. {person2} has {num2} times as many. How many {objects} does {person2} have?"
]

# English randomization elements can be added in a similar way
ENGLISH_TOPICS = [
    "animals", "plants", "weather", "seasons", "family", "friends", "school", "sports",
    "hobbies", "food", "travel", "colors", "shapes", "vehicles", "clothes", "emotions",
    "celebrations", "movies", "music", "books", "nature", "planets", "oceans", "mountains",
    "insects", "dinosaurs", "community helpers", "transportation", "outer space", "zoo animals",
    "farm animals", "pets", "fairy tales", "superheroes", "holidays", "art", "science", "history"
]

ENGLISH_VERBS = [
    "run", "jump", "swim", "play", "read", "write", "draw", "paint", "sing", "dance",
    "eat", "drink", "sleep", "walk", "talk", "laugh", "smile", "cry", "help", "watch",
    "listen", "speak", "work", "study", "learn", "teach", "make", "build", "create", "find",
    "explore", "discover", "climb", "fly", "throw", "catch", "kick", "push", "pull", "ride",
    "drive", "visit", "grow", "plant", "cook", "bake", "clean", "wash", "fold", "carry"
]

ENGLISH_ADJECTIVES = [
    "happy", "sad", "big", "small", "fast", "slow", "hot", "cold", "new", "old",
    "good", "bad", "easy", "hard", "funny", "serious", "loud", "quiet", "clean", "dirty",
    "bright", "dark", "soft", "hard", "sweet", "sour", "tall", "short", "strong", "weak",
    "brave", "scared", "kind", "mean", "pretty", "ugly", "smart", "silly", "friendly", "shy",
    "young", "smooth", "rough", "shiny", "dull", "heavy", "light", "thick", "thin", "sharp"
]

ENGLISH_NOUNS = [
    "dog", "cat", "bird", "fish", "tree", "flower", "house", "car", "book", "toy",
    "ball", "game", "chair", "table", "bed", "door", "window", "phone", "computer", "school",
    "friend", "family", "teacher", "student", "doctor", "police", "firefighter", "park", "store", "zoo",
    "mountain", "river", "ocean", "beach", "forest", "cake", "cookie", "ice cream", "pizza", "sandwich"
]

ENGLISH_WORD_PATTERNS = [
    "Synonyms - words that mean the same as '{word}'",
    "Antonyms - words that mean the opposite of '{word}'",
    "Words that rhyme with '{word}'",
    "Words that start with the same letter as '{word}'",
    "Compound words that include '{word}'",
    "The correct spelling of '{word}'",
    "The plural form of '{word}'",
    "The past tense of '{word}'",
    "The correct definition of '{word}'",
    "Identifying '{word}' as a noun/verb/adjective"
]

ENGLISH_GRAMMAR_TEMPLATES = [
    "Which sentence uses the correct form of '{verb}'?",
    "Which sentence has the correct punctuation?",
    "Which word is a {part_of_speech}?",
    "Fill in the blank: '{sentence_start} _____ {sentence_end}'",
    "Which sentence is grammatically correct?",
    "Which word should come next in this sentence: '{sentence}'",
    "What is the correct article (a/an/the) to use with '{noun}'?",
    "What is the correct prefix to use with '{word}' to mean '{meaning}'?",
    "What is the correct suffix to add to '{word}' to make it '{desired_form}'?",
    "Which sentence uses '{word}' correctly?"
]

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

async def generate_question(grade: int, subject: str, difficulty: str, question_type: str = "multiple-choice") -> Dict[str, Any]:
    """
    Generate a question using OpenRouter API with Pydantic for structured output.
    
    Args:
        grade: Student grade level (2 or 3)
        subject: Subject area ("math" or "english", will be capitalized)
        difficulty: Difficulty level ("easy", "medium", "hard", will be capitalized)
        question_type: Type of question ("multiple-choice", "direct-answer", "reading-comprehension")
        
    Returns:
        Dictionary containing question data
    """
    request_id = f"{time.time():.0f}"
    logger.info(f"[{request_id}] Generating question: grade={grade}, subject={subject}, difficulty={difficulty}, type={question_type}")
    
    # Validate inputs and normalize case
    grade_str = str(grade)
    subject_norm = subject.capitalize()  # Convert "math" to "Math"
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
    
    # For MVP, we only support multiple-choice
    if question_type != "multiple-choice":
        question_type = "multiple-choice"
    
    try:
        # Construct the prompt based on settings
        prompt = construct_prompt(int(grade_str), subject_norm, difficulty_norm, question_type)
        logger.info(f"[{request_id}] Prompt: {prompt}")
        
        # Select appropriate schema class
        schema_class = MultipleChoiceQuestion
        if question_type == "direct-answer":
            schema_class = DirectAnswerQuestion
        elif question_type == "reading-comprehension":
            schema_class = ReadingComprehensionQuestion
        
        # Create a simple, explicit JSON schema string with clear examples
        json_schema_str = """
You must return a valid JSON object with exactly these fields for a multiple-choice question:
{
  "question": "Your question text goes here",
  "choices": ["Option 1", "Option 2", "Option 3", "Option 4"],
  "answer": "The correct option that exactly matches one of the choices",
  "type": "multiple-choice"
}

CRITICAL REQUIREMENTS:
1. The "type" field MUST be exactly "multiple-choice" (not "object" or anything else)
2. The "answer" field MUST exactly match one of the choices
3. There MUST be exactly 4 choices
4. DO NOT nest fields inside "properties" or any other wrapper
5. DO NOT add any additional fields or metadata
6. DO NOT add schema descriptions, field definitions, or explanations
7. DO NOT wrap your response in markdown code blocks (```json)
8. Return ONLY the raw JSON object
"""
        
        # Create the enhanced prompt with explicit instructions
        enhanced_prompt = f"""
{prompt}

{json_schema_str}

Here's an example of a valid response for a {grade_str}-grade {subject_norm.lower()} {difficulty_norm.lower()} question:

{{"question": "Emma has 7 apples and Noah has 5 apples. How many apples do they have in total?",
"choices": ["10", "11", "12", "13"],
"answer": "12",
"type": "multiple-choice"}}
"""
        
        # Log the enhanced prompt
        logger.info(f"[{request_id}] Enhanced prompt with schema instructions: {enhanced_prompt[:200]}...")
        
        # Use the fallback method which has proven more reliable
        logger.info(f"[{request_id}] Making API call to OpenRouter with model {OPENROUTER_MODEL}")
        start_time = time.time()
        
        # Use the standard create method with json_object format
        completion = client.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=[
                {"role": "system", "content": "You are an educational question generator that creates valid JSON objects for multiple-choice questions. Your entire output must be a single, flat JSON object with these exact keys: 'question', 'choices', 'answer', and 'type'. DO NOT create nested JSON schemas. DO NOT include any 'properties' wrapper. DO NOT use 'type': 'object'. Always use 'type': 'multiple-choice'."},
                {"role": "user", "content": enhanced_prompt}
            ],
            temperature=0.5,
            top_p=0.9,
            response_format={"type": "json_object"}
        )
        
        api_time = time.time() - start_time
        logger.info(f"[{request_id}] API call completed in {api_time:.2f}s")
        
        # Extract and validate response
        if not completion or not hasattr(completion, 'choices') or not completion.choices:
            logger.error(f"[{request_id}] No valid response from API")
            return get_fallback_question(grade_str, subject_norm, difficulty_norm)
        
        response_message = completion.choices[0].message
        if not hasattr(response_message, 'content') or not response_message.content:
            logger.error(f"[{request_id}] No content in response message")
            return get_fallback_question(grade_str, subject_norm, difficulty_norm)
        
        content = response_message.content.strip()
        logger.info(f"[{request_id}] Raw response content: {content[:200]}...")
        
        # Clean the content in case it's wrapped in markdown
        cleaned_content = clean_markdown_json(content)
        if content != cleaned_content:
            logger.info(f"[{request_id}] Cleaned JSON from markdown: {cleaned_content[:200]}...")
        
        try:
            # Parse JSON content
            json_data = json.loads(cleaned_content)
            logger.info(f"[{request_id}] Successfully parsed JSON: {json.dumps(json_data)[:200]}...")
            
            # Attempt to repair malformed JSON before validation
            repaired_json = repair_malformed_json(json_data)
            
            # Validate with Pydantic
            validated_data = schema_class(**repaired_json)
            logger.info(f"[{request_id}] Successfully validated with Pydantic")
            
            # Convert to dictionary
            result = validated_data.to_dict()  # Use to_dict() helper method
            logger.info(f"[{request_id}] Returning validated question")
            return result
        
        except json.JSONDecodeError as e:
            logger.error(f"[{request_id}] Failed to parse JSON: {str(e)}")
            logger.error(f"[{request_id}] Content: {cleaned_content}")
            return get_fallback_question(grade_str, subject_norm, difficulty_norm)
            
        except ValidationError as e:
            logger.error(f"[{request_id}] Failed to validate with Pydantic: {str(e)}")
            return get_fallback_question(grade_str, subject_norm, difficulty_norm)
            
    except Exception as e:
        logger.error(f"[{request_id}] Error generating question: {str(e)}")
        return get_fallback_question(grade_str, subject_norm, difficulty_norm)

def construct_prompt(grade: int, subject: str, difficulty: str, question_type: str) -> str:
    """
    Construct a prompt for the AI model based on the settings.
    
    Args:
        grade: Student grade level
        subject: Subject area
        difficulty: Difficulty level
        question_type: Type of question
        
    Returns:
        Prompt string for the AI model
    """
    import random
    
    base_prompt = f"Generate a {difficulty.lower()} {grade}-grade level {subject.lower()} question for elementary school students."
    
    if subject.lower() == "math":
        # Randomly select elements to include in the prompt
        random_name = random.choice(MATH_NAMES)
        random_name2 = random.choice([n for n in MATH_NAMES if n != random_name])  # Ensure different names
        random_objects = random.choice(MATH_OBJECTS)
        random_location = random.choice(MATH_LOCATIONS)
        random_activity = random.choice(MATH_ACTIVITIES)
        
        # Add randomization elements to the prompt
        if difficulty.lower() == "easy":
            if question_type == "multiple-choice":
                prompt = f"{base_prompt} The question should involve basic {difficulty.lower()} arithmetic (addition/subtraction with small numbers)."
                prompt += f" Consider using the name {random_name} and {random_objects} in your question."
                prompt += " The question should be multiple choice with exactly 4 options. The correct answer must be one of the options."
            else:
                prompt = f"{base_prompt} Create a simple word problem using {random_name} and {random_objects}."
                prompt += " The question should require a direct numerical answer."
        else:
            # For medium/hard difficulty, ensure we use the same successful format as easy questions
            if question_type == "multiple-choice":
                # Use the same structure as easy questions but with more complex arithmetic
                if difficulty.lower() == "medium":
                    operations = "addition/subtraction with larger numbers, or basic multiplication/division"
                else:  # Hard
                    operations = "multiplication, division, or multi-step problems"
                
                prompt = f"{base_prompt} The question should involve {operations}."
                prompt += f" Consider using the name {random_name} and {random_objects} in your question."
                prompt += " The question should be multiple choice with exactly 4 options. The correct answer must be one of the options."
                
                # Add a specific example based on difficulty
                if difficulty.lower() == "medium":
                    prompt += f" For example, a question about {random_name} having some {random_objects} and {random_activity} more."
                else:  # Hard
                    prompt += f" For example, a question about {random_name} arranging {random_objects} into equal groups."
            else:
                # For direct answer questions
                prompt = f"{base_prompt} Create a word problem involving {random_name} and {random_objects}."
                prompt += " The question should require a direct numerical answer."
    
    elif subject.lower() == "english":
        # Randomly select elements to include in the prompt
        random_topic = random.choice(ENGLISH_TOPICS)
        random_verb = random.choice(ENGLISH_VERBS)
        random_adjective = random.choice(ENGLISH_ADJECTIVES)
        random_noun = random.choice(ENGLISH_NOUNS)
        
        if question_type == "multiple-choice":
            # For variety, choose different types of English questions
            if difficulty.lower() == "easy":
                # Simple vocabulary or grammar questions
                question_type_options = [
                    f"Create a question about identifying which picture shows a '{random_noun}'.",
                    f"Create a question about matching the word '{random_noun}' to its picture.",
                    f"Create a question about the letter that '{random_noun}' starts with.",
                    f"Create a simple '{random_adjective}' vs '{random.choice([a for a in ENGLISH_ADJECTIVES if a != random_adjective])}' comparison question."
                ]
                prompt = f"{base_prompt} {random.choice(question_type_options)}"
            
            elif difficulty.lower() == "medium":
                # Medium vocabulary, spelling, or basic grammar
                word_pattern = random.choice(ENGLISH_WORD_PATTERNS).format(word=random.choice([random_noun, random_verb, random_adjective]))
                prompt = f"{base_prompt} Create a question about {word_pattern}."
            
            else:  # Hard
                # More complex grammar or reading comprehension
                grammar_template = random.choice(ENGLISH_GRAMMAR_TEMPLATES)
                part_of_speech = random.choice(["noun", "verb", "adjective", "adverb"])
                sentence_start = f"{random.choice(MATH_NAMES)} {random.choice(ENGLISH_VERBS)}s"
                sentence_end = f"the {random.choice(ENGLISH_ADJECTIVES)} {random.choice(ENGLISH_NOUNS)}"
                
                # Format the grammar template with substitutions
                formatted_template = grammar_template.format(
                    verb=random_verb,
                    part_of_speech=part_of_speech,
                    sentence_start=sentence_start,
                    sentence_end=sentence_end,
                    sentence=f"{sentence_start} {sentence_end}",
                    noun=random_noun,
                    word=random.choice([random_noun, random_verb, random_adjective]),
                    meaning="opposite meaning",
                    desired_form="past tense"
                )
                
                prompt = f"{base_prompt} {formatted_template}"
            
            prompt += " The question should be multiple choice with exactly 4 options. The correct answer must be one of the options."
        
        elif question_type == "direct-answer":
            question_types = [
                f"Create a spelling question for the word '{random.choice(ENGLISH_NOUNS)}'.",
                f"Create a question asking for a synonym of '{random_adjective}'.",
                f"Create a question asking for an antonym of '{random_adjective}'.",
                f"Create a question asking for the definition of '{random_noun}'.",
                f"Create a question asking for a rhyming word for '{random_noun}'."
            ]
            prompt = f"{base_prompt} {random.choice(question_types)} The question should require a short text answer."
        
        else:  # reading-comprehension
            prompt = f"{base_prompt} Create a very short reading passage (2-3 sentences) about {random_topic} that uses the word '{random_verb}' and '{random_adjective}', followed by a question about it with 4 multiple choice options."
            # Add specific instructions for the passage content
            passage_elements = [
                f"Include a character named {random.choice(MATH_NAMES)}.",
                f"Set the story at a {random.choice(MATH_LOCATIONS)}.",
                f"Involve the character doing something with {random.choice(MATH_OBJECTS)}.",
                f"Include a problem that the character has to solve."
            ]
            prompt += f" {random.choice(passage_elements)}"
    
    logger.info(f"Generated randomized prompt: {prompt}")
    return prompt

def get_fallback_question(grade: str, subject: str, difficulty: str) -> Dict[str, Any]:
    """
    Get a fallback question when the API fails.
    
    Args:
        grade: Student grade level
        subject: Subject area
        difficulty: Difficulty level
        
    Returns:
        Dictionary containing question data
    """
    import random
    
    try:
        # Default to a valid combination if the specified one doesn't exist
        if grade not in FALLBACK_QUESTIONS:
            grade = "2"
        
        if subject not in FALLBACK_QUESTIONS[grade]:
            subject = "Math"
            
        if difficulty not in FALLBACK_QUESTIONS[grade][subject]:
            difficulty = "Easy"
            
        # Get all questions for the specified criteria
        questions = FALLBACK_QUESTIONS[grade][subject][difficulty]
        
        # Randomly select a question from the available options
        return random.choice(questions)
        
    except Exception as e:
        logger.error(f"Error getting fallback question: {str(e)}")
        
        # Absolute fallback in case even the fallback dictionary has issues
        return {
            "question": "What is 2 + 2?",
            "choices": ["3", "4", "5", "6"],
            "answer": "4",
            "type": "multiple-choice"
        }

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
    
    # Case 2: Response has all the right fields but wrong type value or missing type
    if "question" in json_data and "choices" in json_data and "answer" in json_data:
        # Fix or add the type field
        json_data["type"] = "multiple-choice"
        logger.info(f"Fixed 'type' field in JSON response")
        return json_data
    
    # Case 3: Direct answer question format
    if "question" in json_data and "answer" in json_data and "choices" not in json_data:
        json_data["type"] = "direct-answer"
        logger.info(f"Set type to 'direct-answer' for question without choices")
        return json_data
    
    # Case 4: Reading comprehension format
    if "passage" in json_data and "question" in json_data and "choices" in json_data and "answer" in json_data:
        json_data["type"] = "reading-comprehension"
        logger.info(f"Set type to 'reading-comprehension' for passage-based question")
        return json_data
    
    # If we can't fix it, return the original (validation will fail and we'll use fallback)
    logger.warning(f"Could not repair malformed JSON structure: {str(json_data)[:100]}...")
    return json_data 