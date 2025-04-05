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
                    "type": "multiple-choice",
                    "sub_activity": "Addition/Subtraction"
                },
                {
                    "question": "What is 10 - 4?",
                    "choices": ["4", "5", "6", "7"],
                    "answer": "6",
                    "type": "multiple-choice",
                    "sub_activity": "Addition/Subtraction"
                },
                {
                    "question": "What is 2 × 3?",
                    "choices": ["4", "5", "6", "7"],
                    "answer": "6",
                    "type": "multiple-choice",
                    "sub_activity": "Multiplication/Division"
                },
                {
                    "question": "How many groups of 2 make 6?",
                    "choices": ["2", "3", "4", "5"],
                    "answer": "3",
                    "type": "multiple-choice",
                    "sub_activity": "Multiplication/Division"
                },
                {
                    "question": "Tom has 3 apples. Sarah has 4 apples. How many apples do they have together?",
                    "choices": ["5", "6", "7", "8"],
                    "answer": "7",
                    "type": "multiple-choice",
                    "sub_activity": "Word Problems"
                }
            ],
            "Medium": [
                {
                    "question": "What is 12 + 9?",
                    "choices": ["19", "21", "23", "25"],
                    "answer": "21",
                    "type": "multiple-choice",
                    "sub_activity": "Addition/Subtraction"
                },
                {
                    "question": "What is 15 - 7?",
                    "choices": ["5", "6", "7", "8"],
                    "answer": "8",
                    "type": "multiple-choice",
                    "sub_activity": "Addition/Subtraction"
                },
                {
                    "question": "What is 4 × 5?",
                    "choices": ["16", "18", "20", "22"],
                    "answer": "20",
                    "type": "multiple-choice",
                    "sub_activity": "Multiplication/Division"
                },
                {
                    "question": "How many groups of 4 make 16?",
                    "choices": ["2", "3", "4", "5"],
                    "answer": "4",
                    "type": "multiple-choice",
                    "sub_activity": "Multiplication/Division"
                },
                {
                    "question": "Emma has 15 stickers. She gives 6 to her friend. How many stickers does she have left?",
                    "choices": ["7", "8", "9", "10"],
                    "answer": "9",
                    "type": "multiple-choice",
                    "sub_activity": "Word Problems"
                }
            ],
            "Hard": [
                {
                    "question": "If you have 3 groups of 5 apples, how many apples do you have in total?",
                    "choices": ["8", "10", "15", "20"],
                    "answer": "15",
                    "type": "multiple-choice",
                    "sub_activity": "Multiplication/Division"
                },
                {
                    "question": "What is 25 - 8?",
                    "choices": ["15", "16", "17", "18"],
                    "answer": "17",
                    "type": "multiple-choice",
                    "sub_activity": "Addition/Subtraction"
                },
                {
                    "question": "What is 6 × 3?",
                    "choices": ["15", "16", "17", "18"],
                    "answer": "18",
                    "type": "multiple-choice",
                    "sub_activity": "Multiplication/Division"
                },
                {
                    "question": "Noah has 24 crayons. He divides them equally among 4 friends. How many crayons does each friend get?",
                    "choices": ["4", "6", "8", "10"],
                    "answer": "6",
                    "type": "multiple-choice",
                    "sub_activity": "Word Problems"
                }
            ]
        },
        "English": {
            "Easy": [
                {
                    "question": "Which word means the opposite of 'big'?",
                    "choices": ["large", "huge", "small", "tall"],
                    "answer": "small",
                    "type": "multiple-choice",
                    "sub_activity": "Opposites/Antonyms"
                },
                {
                    "question": "Which word means the opposite of 'hot'?",
                    "choices": ["warm", "cool", "cold", "nice"],
                    "answer": "cold",
                    "type": "multiple-choice",
                    "sub_activity": "Opposites/Antonyms"
                },
                {
                    "passage": "Tom has a red ball. He likes to play with it in the park. The ball is round and bouncy.",
                    "question": "What color is Tom's ball?",
                    "choices": ["blue", "green", "red", "yellow"],
                    "answer": "red",
                    "type": "reading-comprehension",
                    "sub_activity": "Reading Comprehension"
                },
                {
                    "question": "Which word is a noun in the sentence: 'The dog ran fast.'?",
                    "choices": ["The", "dog", "ran", "fast"],
                    "answer": "dog",
                    "type": "multiple-choice",
                    "sub_activity": "Nouns/Pronouns"
                }
            ],
            "Medium": [
                {
                    "question": "Which word is a noun?",
                    "choices": ["run", "happy", "book", "fast"],
                    "answer": "book",
                    "type": "multiple-choice",
                    "sub_activity": "Nouns/Pronouns"
                },
                {
                    "question": "Which word means the opposite of 'happy'?",
                    "choices": ["sad", "glad", "mad", "bad"],
                    "answer": "sad",
                    "type": "multiple-choice",
                    "sub_activity": "Opposites/Antonyms"
                },
                {
                    "passage": "Sarah went to the store. She bought apples and oranges. She wanted to make a fruit salad for her friends.",
                    "question": "Why did Sarah buy fruit?",
                    "choices": ["To eat alone", "To make a fruit salad", "To give away", "To plant trees"],
                    "answer": "To make a fruit salad",
                    "type": "reading-comprehension",
                    "sub_activity": "Reading Comprehension"
                }
            ],
            "Hard": [
                {
                    "question": "Complete the sentence: 'She ____ to the store yesterday.'",
                    "choices": ["go", "goes", "going", "went"],
                    "answer": "went",
                    "type": "multiple-choice",
                    "sub_activity": "Nouns/Pronouns"
                },
                {
                    "question": "Which word means the opposite of 'ancient'?",
                    "choices": ["old", "antique", "modern", "historic"],
                    "answer": "modern",
                    "type": "multiple-choice",
                    "sub_activity": "Opposites/Antonyms"
                },
                {
                    "passage": "Lisa had a problem. Her bike was broken and she needed to get to school. She decided to ask her neighbor for help. Her neighbor drove her to school in his car.",
                    "question": "How did Lisa get to school?",
                    "choices": ["She walked", "She rode her bike", "She took the bus", "She rode in a car"],
                    "answer": "She rode in a car",
                    "type": "reading-comprehension",
                    "sub_activity": "Reading Comprehension"
                }
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
                    "type": "multiple-choice",
                    "sub_activity": "Multiplication/Division"
                },
                {
                    "question": "What is 16 + 8?",
                    "choices": ["22", "24", "26", "28"],
                    "answer": "24",
                    "type": "multiple-choice",
                    "sub_activity": "Addition/Subtraction"
                },
                {
                    "question": "What is 20 - 12?",
                    "choices": ["6", "7", "8", "9"],
                    "answer": "8",
                    "type": "multiple-choice",
                    "sub_activity": "Addition/Subtraction"
                },
                {
                    "question": "Emma has 4 boxes with 6 markers in each box. How many markers does she have in total?",
                    "choices": ["18", "20", "22", "24"],
                    "answer": "24",
                    "type": "multiple-choice",
                    "sub_activity": "Word Problems"
                }
            ],
            "Medium": [
                {
                    "question": "What is 8 × 6?",
                    "choices": ["42", "46", "48", "54"],
                    "answer": "48",
                    "type": "multiple-choice",
                    "sub_activity": "Multiplication/Division"
                },
                {
                    "question": "What is 45 ÷ 9?",
                    "choices": ["4", "5", "6", "7"],
                    "answer": "5",
                    "type": "multiple-choice",
                    "sub_activity": "Multiplication/Division"
                },
                {
                    "question": "What is 37 + 25?",
                    "choices": ["52", "62", "72", "82"],
                    "answer": "62",
                    "type": "multiple-choice",
                    "sub_activity": "Addition/Subtraction"
                },
                {
                    "question": "Noah has 32 stickers. He gives 17 to his friends. How many stickers does he have left?",
                    "choices": ["13", "14", "15", "16"],
                    "answer": "15",
                    "type": "multiple-choice",
                    "sub_activity": "Word Problems"
                }
            ],
            "Hard": [
                {
                    "question": "What is 12 × 9?",
                    "choices": ["98", "108", "118", "128"],
                    "answer": "108",
                    "type": "multiple-choice",
                    "sub_activity": "Multiplication/Division"
                },
                {
                    "question": "What is 144 ÷ 12?",
                    "choices": ["10", "11", "12", "13"],
                    "answer": "12",
                    "type": "multiple-choice",
                    "sub_activity": "Multiplication/Division"
                },
                {
                    "question": "What is 156 - 78?",
                    "choices": ["68", "78", "86", "88"],
                    "answer": "78",
                    "type": "multiple-choice",
                    "sub_activity": "Addition/Subtraction"
                },
                {
                    "question": "A bakery made 96 cupcakes. They sold 3/4 of them. How many cupcakes are left?",
                    "choices": ["18", "24", "32", "36"],
                    "answer": "24",
                    "type": "multiple-choice",
                    "sub_activity": "Word Problems"
                }
            ]
        },
        "English": {
            "Easy": [
                {
                    "question": "Which word means the opposite of 'empty'?",
                    "choices": ["half", "full", "some", "none"],
                    "answer": "full",
                    "type": "multiple-choice",
                    "sub_activity": "Opposites/Antonyms"
                },
                {
                    "question": "Which word is a pronoun in the sentence: 'She went to the store.'?",
                    "choices": ["She", "went", "to", "store"],
                    "answer": "She",
                    "type": "multiple-choice",
                    "sub_activity": "Nouns/Pronouns"
                },
                {
                    "passage": "Max has a new puppy. The puppy likes to play and run. Max takes his puppy to the park every day.",
                    "question": "Where does Max take his puppy?",
                    "choices": ["home", "school", "park", "store"],
                    "answer": "park",
                    "type": "reading-comprehension",
                    "sub_activity": "Reading Comprehension"
                }
            ],
            "Medium": [
                {
                    "question": "Which word means the opposite of 'brave'?",
                    "choices": ["scared", "happy", "strong", "kind"],
                    "answer": "scared",
                    "type": "multiple-choice",
                    "sub_activity": "Opposites/Antonyms"
                },
                {
                    "question": "Which word is a possessive pronoun?",
                    "choices": ["they", "them", "their", "those"],
                    "answer": "their",
                    "type": "multiple-choice",
                    "sub_activity": "Nouns/Pronouns"
                },
                {
                    "passage": "Lily planted a garden. She planted carrots, tomatoes, and peppers. After six weeks, she was able to pick some vegetables for dinner.",
                    "question": "How long did it take before Lily could pick vegetables?",
                    "choices": ["two weeks", "four weeks", "six weeks", "eight weeks"],
                    "answer": "six weeks",
                    "type": "reading-comprehension",
                    "sub_activity": "Reading Comprehension"
                }
            ],
            "Hard": [
                {
                    "question": "Which word means the opposite of 'generous'?",
                    "choices": ["giving", "selfish", "kind", "helpful"],
                    "answer": "selfish",
                    "type": "multiple-choice",
                    "sub_activity": "Opposites/Antonyms"
                },
                {
                    "question": "Choose the correct pronoun: '___ are going to the museum tomorrow.'",
                    "choices": ["I", "He", "She", "We"],
                    "answer": "We",
                    "type": "multiple-choice",
                    "sub_activity": "Nouns/Pronouns"
                },
                {
                    "passage": "The science fair was on Friday. Jake worked on his project all week. He built a model of the solar system. Jake won first prize for his excellent work.",
                    "question": "What did Jake build for the science fair?",
                    "choices": ["a robot", "a model of the solar system", "a volcano", "a plant experiment"],
                    "answer": "a model of the solar system",
                    "type": "reading-comprehension",
                    "sub_activity": "Reading Comprehension"
                }
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

async def generate_question(grade: int, subject: str, sub_activity: str, difficulty: str, question_type: str = "multiple-choice") -> Dict[str, Any]:
    """
    Generate a question using OpenRouter API with Pydantic for structured output.
    
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
    
    # For MVP, we only support multiple-choice
    if question_type != "multiple-choice":
        question_type = "multiple-choice"
    
    try:
        # Construct the prompt based on settings, including sub_activity
        prompt = construct_prompt(int(grade_str), subject_norm, sub_activity_norm, difficulty_norm, question_type)
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
            return get_fallback_question(grade_str, subject_norm, sub_activity_norm, difficulty_norm)
        
        response_message = completion.choices[0].message
        if not hasattr(response_message, 'content') or not response_message.content:
            logger.error(f"[{request_id}] No content in response message")
            return get_fallback_question(grade_str, subject_norm, sub_activity_norm, difficulty_norm)
        
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
            
            # Add the sub_activity to the result
            result["sub_activity"] = sub_activity_norm
            
            logger.info(f"[{request_id}] Returning validated question")
            return result
        
        except json.JSONDecodeError as e:
            logger.error(f"[{request_id}] Failed to parse JSON: {str(e)}")
            logger.error(f"[{request_id}] Content: {cleaned_content}")
            return get_fallback_question(grade_str, subject_norm, sub_activity_norm, difficulty_norm)
            
        except ValidationError as e:
            logger.error(f"[{request_id}] Failed to validate with Pydantic: {str(e)}")
            return get_fallback_question(grade_str, subject_norm, sub_activity_norm, difficulty_norm)
            
    except Exception as e:
        logger.error(f"[{request_id}] Error generating question: {str(e)}")
        return get_fallback_question(grade_str, subject_norm, sub_activity_norm, difficulty_norm)

def construct_prompt(grade: int, subject: str, sub_activity: str, difficulty: str, question_type: str) -> str:
    """
    Construct a prompt for the AI model based on the settings.
    
    Args:
        grade: Student grade level
        subject: Subject area
        sub_activity: Sub-activity type
        difficulty: Difficulty level
        question_type: Type of question
        
    Returns:
        Prompt string for the AI model
    """
    import random
    
    base_prompt = f"Generate a {difficulty.lower()} {grade}-grade level {subject.lower()} question about {sub_activity} for elementary school students."
    
    if subject.lower() == "math":
        # Randomly select elements to include in the prompt
        random_name = random.choice(MATH_NAMES)
        random_name2 = random.choice([n for n in MATH_NAMES if n != random_name])  # Ensure different names
        random_objects = random.choice(MATH_OBJECTS)
        random_location = random.choice(MATH_LOCATIONS)
        random_activity = random.choice(MATH_ACTIVITIES)
        
        # Add specific context based on sub_activity
        if sub_activity == "Addition/Subtraction":
            if difficulty.lower() == "easy":
                prompt = f"{base_prompt} The question should involve basic {difficulty.lower()} arithmetic with addition or subtraction with small numbers."
                prompt += f" Consider using the name {random_name} and {random_objects} in your question."
            elif difficulty.lower() == "medium":
                prompt = f"{base_prompt} The question should involve addition or subtraction with larger numbers, possibly requiring carrying or borrowing."
                prompt += f" For example, a question about {random_name} having some {random_objects} and {random_activity} more or giving some away."
            else:  # Hard
                prompt = f"{base_prompt} The question should involve multi-step addition and subtraction problems or mental math strategies."
                prompt += f" For example, a question involving {random_name} and {random_name2} with different amounts of {random_objects}."
        
        elif sub_activity == "Multiplication/Division":
            if difficulty.lower() == "easy":
                prompt = f"{base_prompt} The question should involve basic multiplication or division with small numbers (up to 5)."
                prompt += f" Consider using the name {random_name} and groups of {random_objects} in your question."
            elif difficulty.lower() == "medium":
                prompt = f"{base_prompt} The question should involve multiplication or division with larger numbers (up to 10)."
                prompt += f" For example, a question about {random_name} arranging {random_objects} into equal groups."
            else:  # Hard
                prompt = f"{base_prompt} The question should involve more complex multiplication or division problems with larger numbers or remainders."
                prompt += f" For example, a multi-step problem where {random_name} needs to divide {random_objects} among friends."
        
        elif sub_activity == "Word Problems":
            if difficulty.lower() == "easy":
                prompt = f"{base_prompt} Create a simple word problem using {random_name} and {random_objects} that involves a single operation."
                prompt += f" The problem should be set at a {random_location}."
            elif difficulty.lower() == "medium":
                prompt = f"{base_prompt} Create a word problem using {random_name} and {random_objects} that requires two operations to solve."
                prompt += f" The problem could involve {random_name} {random_activity} at a {random_location}."
            else:  # Hard
                prompt = f"{base_prompt} Create a multi-step word problem that requires at least three operations or logical steps."
                prompt += f" The problem should involve {random_name} and {random_name2} with different amounts of {random_objects}."
        else:
            # Default math prompt if sub_activity is not recognized
            return construct_prompt(grade, subject, "Addition/Subtraction", difficulty, question_type)
            
    elif subject.lower() == "english":
        # Randomly select elements to include in the prompt
        random_topic = random.choice(ENGLISH_TOPICS)
        random_verb = random.choice(ENGLISH_VERBS)
        random_adjective = random.choice(ENGLISH_ADJECTIVES)
        random_noun = random.choice(ENGLISH_NOUNS)
        
        if sub_activity == "Opposites/Antonyms":
            if difficulty.lower() == "easy":
                prompt = f"{base_prompt} Create a question about identifying the opposite of a simple word like '{random_adjective}'."
                prompt += " Give 4 options with only one being the correct opposite."
            elif difficulty.lower() == "medium":
                prompt = f"{base_prompt} Create a question about finding the antonym of '{random_adjective}' or '{random_verb}'."
                prompt += " Provide 4 options with only one being the correct antonym."
            else:  # Hard
                prompt = f"{base_prompt} Create a question asking for the antonym of a more challenging word."
                prompt += " Ensure the options include words that might be confusing for students."
        
        elif sub_activity == "Reading Comprehension":
            if difficulty.lower() == "easy":
                prompt = f"{base_prompt} Create a very short reading passage (2-3 sentences) about {random_topic} that uses simple vocabulary, followed by a question about the main idea or a specific detail."
                prompt += f" Include a character named {random.choice(MATH_NAMES)}."
            elif difficulty.lower() == "medium":
                prompt = f"{base_prompt} Create a short reading passage (3-4 sentences) about {random_topic} set at a {random.choice(MATH_LOCATIONS)}, followed by a question that requires understanding the sequence of events or making a simple inference."
            else:  # Hard
                prompt = f"{base_prompt} Create a reading passage (4-5 sentences) about {random_topic} with slightly more complex vocabulary, followed by a question that requires deeper comprehension or inference."
                prompt += f" Include a problem that the character {random.choice(MATH_NAMES)} has to solve."
        
        elif sub_activity == "Nouns/Pronouns":
            if difficulty.lower() == "easy":
                prompt = f"{base_prompt} Create a question about identifying which word in a sentence is a noun."
                prompt += f" For example, a simple sentence about {random_topic} or {random.choice(MATH_NAMES)}."
            elif difficulty.lower() == "medium":
                prompt = f"{base_prompt} Create a question about choosing the correct pronoun to replace a noun in a sentence."
                prompt += f" For example, a sentence about {random.choice(MATH_NAMES)} and their {random_noun}."
            else:  # Hard
                prompt = f"{base_prompt} Create a question about selecting the correct pronoun in a more complex sentence or identifying a specific type of pronoun."
                prompt += f" The sentence could involve multiple characters like {random.choice(MATH_NAMES)} and {random.choice(MATH_NAMES)}."
        else:
            # Default english prompt if sub_activity is not recognized
            return construct_prompt(grade, subject, "Opposites/Antonyms", difficulty, question_type)
    
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
        grade: Student grade level
        subject: Subject area
        sub_activity: Sub-activity type
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
        fallback_question = random.choice(questions)
        
        # Add the sub_activity to the fallback question
        fallback_question["sub_activity"] = sub_activity
        
        return fallback_question
        
    except Exception as e:
        logger.error(f"Error getting fallback question: {str(e)}")
        
        # Absolute fallback in case even the fallback dictionary has issues
        return {
            "question": "What is 2 + 2?",
            "choices": ["3", "4", "5", "6"],
            "answer": "4",
            "type": "multiple-choice",
            "sub_activity": sub_activity
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