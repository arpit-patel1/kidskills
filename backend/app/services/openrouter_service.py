import os
import json
import time
import re
from typing import Dict, Any, Optional, List, Literal
from openai import OpenAI
from dotenv import load_dotenv
import logging
from pydantic import BaseModel, Field, validator, ValidationError, root_validator
import random

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

# Constants for question randomization
NAMES = [
    "Ava", "Noah", "Emma", "Liam", "Olivia", "Jackson", "Sophia", "Lucas", 
    "Mia", "Aiden", "Isabella", "Ethan", "Riley", "Elijah", "Aria", 
    "Grayson", "Amelia", "Mason", "Charlotte", "Logan", "Harper", "James",
    "Evelyn", "Alexander", "Abigail", "Michael", "Emily", "Benjamin", "Elizabeth", 
    "Zoe", "William", "Sofia", "Daniel", "Avery", "Matthew", "Scarlett", "Henry",
    "Victoria", "Sebastian", "Madison", "Jack", "Luna", "Owen", "Grace", "Isaiah",
    "Chloe", "Leo", "Penelope", "Ryan", "Layla", "Nathan", "Audrey"
]

MATH_NAMES = NAMES  # Can be used for Math questions specifically

# Reading topics for comprehension questions
READING_TOPICS = [
    "animals", "family", "school", "seasons", "weather", "space", 
    "ocean", "holidays", "food", "sports", "music", "art", 
    "nature", "travel", "community", "plants", "vehicles",
    "dinosaurs", "robots", "magic", "friendship", "pets", 
    "adventures", "insects", "birds", "camping", "cooking",
    "gardening", "jungle", "desert", "mountains", "inventions",
    "circus", "planets", "fairy tales", "superheroes", "dragons"
]

# Locations for reading passages
READING_LOCATIONS = [
    "park", "home", "school", "garden", "beach", "forest", 
    "zoo", "playground", "library", "museum", "farm", 
    "neighborhood", "classroom", "kitchen", "backyard",
    "treehouse", "cave", "castle", "island", "mountain",
    "space station", "boat", "train", "airplane", "submarine",
    "aquarium", "amusement park", "campsite", "cottage",
    "desert", "jungle", "bakery", "hospital", "laboratory"
]

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

class DirectAnswerQuestion(BaseModel):
    question: str = Field(..., description="The question text")
    answer: str = Field(..., description="The correct answer")
    type: Literal["direct-answer"] = Field("direct-answer", description="The question type")
    
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
        
    def normalize_answer(self, user_answer: str) -> bool:
        """
        Normalize and compare a user answer with the correct answer.
        This is useful for grammar correction where slight differences
        in spacing or capitalization should be ignored.
        """
        # Clean up both answers by removing extra spaces and converting to lowercase
        correct = self.answer.strip().lower()
        user = user_answer.strip().lower()
        
        # Basic exact match after normalization
        if correct == user:
            return True
            
        # TODO: Add more sophisticated comparison if needed:
        # - Remove punctuation for comparison
        # - Allow for alternative phrasings
        # - Use word-by-word comparison
        
        return False

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

# Add fallback questions for Grammar Correction sub-activity
for grade in ["2", "3"]:
    for difficulty in ["Easy", "Medium", "Hard"]:
        if "English" not in FALLBACK_QUESTIONS[grade]:
            FALLBACK_QUESTIONS[grade]["English"] = {}
        
        if difficulty not in FALLBACK_QUESTIONS[grade]["English"]:
            FALLBACK_QUESTIONS[grade]["English"][difficulty] = []
        
        # Add grammar correction fallback questions
        grammar_fallbacks = [
            {
                "question": "She don't like ice cream.",
                "answer": "She doesn't like ice cream.",
                "type": "direct-answer",
                "sub_activity": "Grammar Correction"
            },
            {
                "question": "The cats is playing outside.",
                "answer": "The cats are playing outside.",
                "type": "direct-answer",
                "sub_activity": "Grammar Correction"
            },
            {
                "question": "He walk to school everyday.",
                "answer": "He walks to school everyday.",
                "type": "direct-answer",
                "sub_activity": "Grammar Correction"
            },
            {
                "question": "They was playing in the park.",
                "answer": "They were playing in the park.",
                "type": "direct-answer",
                "sub_activity": "Grammar Correction"
            }
        ]
        
        # Add these fallbacks to the existing ones
        for fallback in grammar_fallbacks:
            FALLBACK_QUESTIONS[grade]["English"][difficulty].append(fallback)

# Add these lists at the top level of the file, after the imports and before any functions
# Various elements to randomize math questions
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

# Lists for enhanced grammar correction randomization
# List of diverse names representing different cultures/backgrounds
SCENARIOS = [
    "playing at the park", "visiting the zoo", "reading in the library",
    "working on a science project", "helping in the garden", "baking cookies",
    "building a sandcastle", "drawing a picture", "solving a math problem",
    "writing a story", "practicing piano", "feeding the fish", "walking the dog",
    "riding a bicycle", "swimming in the pool", "making a craft", "going on a hike",
    "shopping at the grocery store", "celebrating a birthday", "visiting grandparents",
    "cleaning their room", "planting flowers", "watching a movie", "playing soccer",
    "building with blocks", "singing in the choir", "eating lunch", "taking a test",
    "going camping", "flying a kite", "collecting leaves", "looking at stars",
    "playing video games", "writing a letter", "making a sandwich", "painting a picture",
    "playing basketball", "doing homework", "telling a joke", "learning an instrument",
    "folding laundry", "walking to school", "riding the bus", "playing with friends",
    "sharing toys", "helping a teacher", "taking care of a pet", "jumping rope",
    "playing board games", "exploring a museum"
]

# Objects that can be used in sentences
OBJECTS = [
    "book", "ball", "pencil", "apple", "backpack", "toy", "bicycle", "computer",
    "sandwich", "painting", "puzzle", "kite", "rock", "flower", "tree", "hat",
    "cup", "box", "shoe", "game", "picture", "notebook", "crayon", "tablet",
    "chair", "desk", "blocks", "doll", "truck", "markers", "glue", "scissors"
]

# Settings/locations for contextual variety
LOCATIONS = [
    "classroom", "playground", "home", "library", "park", "beach", "museum",
    "aquarium", "zoo", "garden", "kitchen", "cafeteria", "gymnasium", "art room",
    "backyard", "treehouse", "swimming pool", "farm", "forest", "shopping mall",
    "school bus", "soccer field", "birthday party", "science lab", "music room"
]

# Time expressions for adding temporal context
TIME_EXPRESSIONS = [
    "yesterday", "last week", "this morning", "after school", "during recess",
    "before dinner", "on the weekend", "last summer", "every day", "tomorrow",
    "next week", "at night", "in the afternoon", "on Monday", "during lunch"
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
    
    # For MVP, we mostly support multiple-choice, but handle special cases
    if question_type != "multiple-choice" and question_type != "direct-answer" and question_type != "reading-comprehension":
        question_type = "multiple-choice"
    
    # Special handling for Grammar Correction
    if sub_activity_norm == "Grammar Correction":
        if question_type != "direct-answer":
            logger.info(f"[{request_id}] Grammar Correction activity detected, forcing direct-answer question type")
            question_type = "direct-answer"
    
    # Determine temperature: standard or higher for some question types
    temperature = 0.5  # default temperature
    
    # Use higher temperature for some question types to get more variety
    if subject_norm == "English":
        if sub_activity_norm == "Grammar Correction":
            temperature = 0.7
            logger.info(f"[{request_id}] Using higher temperature of {temperature} for grammar correction")
        elif sub_activity_norm == "Reading Comprehension": 
            temperature = 0.8
            logger.info(f"[{request_id}] Using higher temperature of {temperature} for reading comprehension")
        elif sub_activity_norm == "Opposites/Antonyms":
            temperature = 0.9
            logger.info(f"[{request_id}] Using higher temperature of {temperature} for Opposites/Antonyms")
        else:
            # For all other English activities
            temperature = 0.7
            logger.info(f"[{request_id}] Using higher temperature of {temperature} for {sub_activity_norm}")
    
    try:
        # Construct a prompt for the OpenRouter model
        prompt = construct_prompt(grade=int(grade_str), subject=subject_norm, sub_activity=sub_activity_norm, difficulty=difficulty_norm, question_type=question_type)
        
        logger.info(f"[{request_id}] Constructed prompt: {prompt[:100]}...")
        
        # If API key is not available, use fallback questions
        if not OPENROUTER_API_KEY:
            logger.warning(f"[{request_id}] No API key available, using fallback question")
            return get_fallback_question(grade_str, subject_norm, sub_activity_norm, difficulty_norm)
        
        # Determine which model class to use based on question_type
        if question_type == "multiple-choice":
            schema_class = MultipleChoiceQuestion
        elif question_type == "direct-answer":
            schema_class = DirectAnswerQuestion
        else:  # reading-comprehension
            schema_class = ReadingComprehensionQuestion
        
        # Make API call to OpenRouter
        start_time = time.time()
        
        # Create system message that's appropriate for the subject/activity
        system_message = "You are an AI that generates educational questions for elementary school students. Your responses should be in JSON format with a question, choices (for multiple choice), and the correct answer. Always use the field name 'answer' (not 'correct_answer') for the correct answer field."
        
        # Enhance system message for Opposites/Antonyms to avoid repetitive questions
        if subject_norm == "English" and sub_activity_norm == "Opposites/Antonyms":
            system_message += " When asked to use a specific word in a question about opposites/antonyms, you MUST use exactly that word and not substitute it with a different word. Follow the exact template provided in the prompt."
        
        completion = client.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            top_p=0.8
        )
        api_time = time.time() - start_time
        logger.info(f"[{request_id}] API call completed in {api_time:.2f}s")
        
        # Extract and clean the response content
        if not completion.choices or not hasattr(completion.choices[0], 'message'):
            logger.error(f"[{request_id}] No valid response from API")
            return get_fallback_question(grade_str, subject_norm, sub_activity_norm, difficulty_norm)
            
        response_message = completion.choices[0].message
        if not hasattr(response_message, 'content') or not response_message.content:
            logger.error(f"[{request_id}] No content in response message")
            return get_fallback_question(grade_str, subject_norm, sub_activity_norm, difficulty_norm)
            
        content = response_message.content.strip()
        
        # Clean up the response to extract JSON
        cleaned_content = clean_markdown_json(content)
        if not cleaned_content:
            logger.error(f"[{request_id}] Failed to extract JSON from response")
            logger.error(f"[{request_id}] Original content: {content[:200]}...")
            return get_fallback_question(grade_str, subject_norm, sub_activity_norm, difficulty_norm)
        
        try:
            # Parse JSON content
            json_data = json.loads(cleaned_content)
            logger.info(f"[{request_id}] Successfully parsed JSON: {json.dumps(json_data)[:200]}...")
            
            # Add sub_activity to the JSON data before repair/validation
            json_data["sub_activity"] = sub_activity_norm
            
            # Attempt to repair malformed JSON before validation
            repaired_json = repair_malformed_json(json_data)
            
            # Validate with Pydantic
            validated_data = schema_class(**repaired_json)
            logger.info(f"[{request_id}] Successfully validated with Pydantic")
            
            # Convert to dictionary
            result = validated_data.to_dict()  # Use to_dict() helper method
            
            # Always ensure sub_activity is in the result
            result["sub_activity"] = sub_activity_norm
            
            # For grammar correction, double-check that type is direct-answer
            if sub_activity_norm == "Grammar Correction" and result.get("type") != "direct-answer":
                logger.info(f"[{request_id}] Forcing direct-answer type for Grammar Correction after validation")
                result["type"] = "direct-answer"
                # Remove choices if they somehow got through
                if "choices" in result:
                    del result["choices"]
            
            # Add the subject and difficulty to the result
            result["subject"] = subject_norm
            result["difficulty"] = difficulty_norm
            
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
    Construct a prompt for the OpenRouter model based on the given parameters.
    
    Args:
        grade: Student grade level (e.g., 2, 3)
        subject: Subject area (Math, English)
        sub_activity: Sub-activity type 
        difficulty: Difficulty level (Easy, Medium, Hard)
        question_type: Type of question (multiple-choice, direct-answer, reading-comprehension)
        
    Returns:
        String prompt for the AI model
    """
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
                """
            else:  # Grade 3+
                prompt = f"""
                Generate a {difficulty.lower()} {grade}-grade level English question about opposites or antonyms.
                
                YOU MUST use exactly this question format WITHOUT changing the word: "{prompt_template}"
                
                You MUST use the word '{target_word}' in your question. DO NOT substitute it with a different word.
                DO NOT use the word 'happy' in your question - this word has been overused.
                
                Use this random seed for variety: {random_seed}
                
                The question should ask for the opposite of a word appropriate for this grade level.
                """
            
            # Log the enhanced prompt details
            logger.info(f"Opposites/Antonyms randomization - Target word: {target_word}, Template: {prompt_template}, Seed: {random_seed}")
            
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
        
        # Filter questions for the specific sub-activity if possible
        matching_questions = [q for q in questions if q.get("sub_activity") == sub_activity]
        
        # If we have matching questions, use those, otherwise use all available questions
        question_pool = matching_questions if matching_questions else questions
        
        # Randomly select a question from the available options
        fallback_question = random.choice(question_pool)
        
        # Add the sub_activity to the fallback question if it's not already there
        if "sub_activity" not in fallback_question:
            fallback_question["sub_activity"] = sub_activity
        
        # Add clear logging about the selected fallback
        logger.info(f"Selected fallback question type: {fallback_question.get('type', 'unknown')} for {sub_activity}")
        
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

async def generate_grammar_feedback(question: str, user_answer: str, correct_answer: str, is_correct: bool) -> str:
    """
    Generate detailed feedback for a grammar correction answer using OpenRouter.
    
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
        
        # Make API call to OpenRouter for feedback
        completion = client.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=[
                {"role": "system", "content": "You are a friendly, supportive elementary school teacher providing feedback on grammar corrections. Keep your responses short, simple, and encouraging."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=150
        )
        
        api_time = time.time() - start_time
        logger.info(f"[{request_id}] API call completed in {api_time:.2f}s")
        
        # Extract the feedback
        if not completion or not hasattr(completion, 'choices') or not completion.choices:
            logger.error(f"[{request_id}] No valid response from API")
            return get_fallback_feedback(is_correct)
        
        response_message = completion.choices[0].message
        if not hasattr(response_message, 'content') or not response_message.content:
            logger.error(f"[{request_id}] No content in response message")
            return get_fallback_feedback(is_correct)
        
        feedback = response_message.content.strip()
        logger.info(f"[{request_id}] Generated feedback: {feedback[:100]}...")
        
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

async def evaluate_grammar_correction(question: str, user_answer: str, correct_answer: str) -> dict:
    """
    Evaluate a grammar correction answer using OpenRouter API and provide detailed feedback.
    
    Args:
        question: The original question (incorrect sentence)
        user_answer: The student's corrected answer
        correct_answer: The expected correct answer
        
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

First, determine if the student's answer is essentially correct. Consider:
1. Did they fix the primary grammar issue(s)?
2. Is their sentence grammatically correct, even if worded differently than the expected answer?
3. Does their correction maintain the original meaning of the sentence?

Be somewhat lenient - if they fixed the main grammar issue but made a minor spelling mistake, still consider it correct.

Then provide brief, encouraging feedback (2-3 sentences) appropriate for an elementary school student.

Return your response in this JSON format:
{{
  "is_correct": true/false,
  "feedback": "Your feedback here"
}}
"""
    
    try:
        logger.info(f"[{request_id}] Evaluating grammar correction answer")
        start_time = time.time()
        
        # Make API call to OpenRouter for evaluation
        completion = client.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful, supportive elementary school teacher evaluating grammar corrections. You judge answers based on whether the student fixed the main grammar issue, even if their wording differs from the expected answer. You provide constructive, encouraging feedback."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,  # Lower temperature for more consistent evaluation
            response_format={"type": "json_object"}
        )
        
        api_time = time.time() - start_time
        logger.info(f"[{request_id}] API call completed in {api_time:.2f}s")
        
        # Extract the evaluation results
        if not completion or not hasattr(completion, 'choices') or not completion.choices:
            logger.error(f"[{request_id}] No valid response from API")
            return get_fallback_grammar_evaluation(question, user_answer, correct_answer)
        
        response_message = completion.choices[0].message
        if not hasattr(response_message, 'content') or not response_message.content:
            logger.error(f"[{request_id}] No content in response message")
            return get_fallback_grammar_evaluation(question, user_answer, correct_answer)
        
        try:
            # Parse the JSON response
            evaluation_result = json.loads(response_message.content.strip())
            
            # Validate the required fields are present
            if "is_correct" not in evaluation_result or "feedback" not in evaluation_result:
                logger.error(f"[{request_id}] Missing required fields in evaluation result")
                return get_fallback_grammar_evaluation(question, user_answer, correct_answer)
            
            # Convert is_correct to boolean if it's a string
            if isinstance(evaluation_result["is_correct"], str):
                evaluation_result["is_correct"] = evaluation_result["is_correct"].lower() == "true"
            
            logger.info(f"[{request_id}] Evaluation result: correct={evaluation_result['is_correct']}, feedback={evaluation_result['feedback'][:50]}...")
            
            return evaluation_result
            
        except json.JSONDecodeError:
            logger.error(f"[{request_id}] Failed to parse JSON response: {response_message.content[:100]}...")
            return get_fallback_grammar_evaluation(question, user_answer, correct_answer)
            
    except Exception as e:
        logger.error(f"[{request_id}] Error evaluating grammar correction: {str(e)}")
        return get_fallback_grammar_evaluation(question, user_answer, correct_answer)

def get_fallback_grammar_evaluation(question: str, user_answer: str, correct_answer: str) -> dict:
    """Get fallback evaluation when the API fails."""
    # Simple string similarity to determine correctness as fallback
    user_lower = user_answer.lower().strip()
    correct_lower = correct_answer.lower().strip()
    
    # Very basic fallback evaluation - same as current system
    is_correct = user_lower == correct_lower
    
    if is_correct:
        feedback = "Great job! You fixed the grammar error correctly."
    else:
        feedback = "Good effort! Take another look at the sentence and check for grammar errors."
    
    return {
        "is_correct": is_correct,
        "feedback": feedback
    }

async def evaluate_reading_comprehension(passage: str, question: str, user_answer: str, correct_answer: str) -> dict:
    """
    Evaluate a reading comprehension answer using OpenRouter API and provide detailed feedback.
    
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
        
        # Make API call to OpenRouter for evaluation
        completion = client.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful, supportive elementary school teacher evaluating reading comprehension answers. You judge answers based on understanding rather than exact wording. You provide constructive, encouraging feedback."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,  # Lower temperature for more consistent evaluation
            response_format={"type": "json_object"}
        )
        
        api_time = time.time() - start_time
        logger.info(f"[{request_id}] API call completed in {api_time:.2f}s")
        
        # Extract the evaluation results
        if not completion or not hasattr(completion, 'choices') or not completion.choices:
            logger.error(f"[{request_id}] No valid response from API")
            return get_fallback_reading_evaluation(user_answer, correct_answer)
        
        response_message = completion.choices[0].message
        if not hasattr(response_message, 'content') or not response_message.content:
            logger.error(f"[{request_id}] No content in response message")
            return get_fallback_reading_evaluation(user_answer, correct_answer)
        
        try:
            # Parse the JSON response
            evaluation_result = json.loads(response_message.content.strip())
            
            # Validate the required fields are present
            if "is_correct" not in evaluation_result or "feedback" not in evaluation_result:
                logger.error(f"[{request_id}] Missing required fields in evaluation result")
                return get_fallback_reading_evaluation(user_answer, correct_answer)
            
            # Convert is_correct to boolean if it's a string
            if isinstance(evaluation_result["is_correct"], str):
                evaluation_result["is_correct"] = evaluation_result["is_correct"].lower() == "true"
            
            logger.info(f"[{request_id}] Evaluation result: correct={evaluation_result['is_correct']}, feedback={evaluation_result['feedback'][:50]}...")
            
            return evaluation_result
            
        except json.JSONDecodeError:
            logger.error(f"[{request_id}] Failed to parse JSON response: {response_message.content[:100]}...")
            return get_fallback_reading_evaluation(user_answer, correct_answer)
            
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