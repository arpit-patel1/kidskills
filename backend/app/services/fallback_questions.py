"""
Fallback questions for AI service.

This file contains a simplified set of fallback questions organized by subject and activity.
Each subject and activity has just one fallback question, as opposed to having questions
for each grade and difficulty level.
"""

FALLBACK_QUESTIONS = {
    "Math": {
        "Addition/Subtraction": {
            "question": "What is 5 + 3?",
            "choices": ["7", "8", "9", "10"],
            "answer": "8",
            "type": "multiple-choice"
        },
        "Multiplication/Division": {
            "question": "What is 2 × 3?",
            "choices": ["4", "5", "6", "7"],
            "answer": "6",
            "type": "multiple-choice"
        },
        "Word Problems": {
            "question": "Tom has 3 apples. Sarah has 4 apples. How many apples do they have together?",
            "choices": ["5", "6", "7", "8"],
            "answer": "7",
            "type": "multiple-choice"
        },
        "Mushroom Kingdom Calculations": {
            "question": "Mario collected 5 coins in World 1-1 and then 3 more coins in World 1-2. How many coins does he have in total?",
            "choices": ["5", "8", "10", "12"],
            "answer": "8",
            "type": "multiple-choice"
        },
        "Fractions": {
            "question": "What fraction of the circle is shaded if 2 out of 4 equal parts are shaded?",
            "choices": ["1/4", "1/2", "2/3", "3/4"],
            "answer": "1/2",
            "type": "multiple-choice"
        },
        "Time": {
            "question": "If it's 3:00 now, what time will it be in 2 hours?",
            "choices": ["4:00", "5:00", "6:00", "7:00"],
            "answer": "5:00", 
            "type": "multiple-choice"
        },
        "Money": {
            "question": "How many cents are in a quarter?",
            "choices": ["5", "10", "25", "50"],
            "answer": "25",
            "type": "multiple-choice"
        }
    },
    "English": {
        "Reading Comprehension": {
            "passage": "Sara has a dog. Her dog is brown. The dog likes to play in the park.",
            "question": "What color is Sara's dog?",
            "choices": ["Black", "Brown", "White", "Gray"],
            "answer": "Brown",
            "type": "multiple-choice" 
        },
        "Grammar Correction": {
            "question": "The boy play with toys.",
            "answer": "The boy plays with toys.",
            "type": "direct-answer"
        },
        "Spelling": {
            "question": "Which word is spelled correctly?",
            "choices": ["hapen", "happn", "happen", "hapen"],
            "answer": "happen",
            "type": "multiple-choice"
        },
        "Vocabulary": {
            "question": "What is the meaning of 'happy'?",
            "choices": ["Sad", "Angry", "Joyful", "Tired"],
            "answer": "Joyful",
            "type": "multiple-choice"
        },
        "Synonyms/Antonyms": {
            "question": "What is the opposite of 'hot'?",
            "choices": ["Warm", "Cold", "Cool", "Freezing"],
            "answer": "Cold",
            "type": "multiple-choice"
        },
        "Opposites/Antonyms": {
            "question": "What is the opposite of 'big'?",
            "choices": ["Large", "Small", "Huge", "Giant"],
            "answer": "Small",
            "type": "multiple-choice"
        }
    },
    "Science": {
        "Animals": {
            "question": "Which animal lives in water?",
            "choices": ["Dog", "Cat", "Fish", "Bird"],
            "answer": "Fish",
            "type": "multiple-choice"
        },
        "Plants": {
            "question": "What do plants need to grow?",
            "choices": ["Rocks", "Water", "Sand", "Toys"],
            "answer": "Water",
            "type": "multiple-choice"
        },
        "Weather": {
            "question": "What comes from clouds when it rains?",
            "choices": ["Sunshine", "Snow", "Water", "Wind"],
            "answer": "Water",
            "type": "multiple-choice"
        },
        "Seasons": {
            "question": "In which season do leaves fall from trees?",
            "choices": ["Spring", "Summer", "Fall", "Winter"],
            "answer": "Fall",
            "type": "multiple-choice"
        }
    }
}

def get_fallback_question(subject: str, sub_activity: str) -> dict:
    """
    Get a fallback question when the AI generation fails.
    
    Args:
        subject: Subject area (Math, English, Science)
        sub_activity: The specific activity within the subject
        
    Returns:
        Dictionary containing question data
    """
    try:
        # Check if subject exists in the dictionary
        if subject not in FALLBACK_QUESTIONS:
            subject = next(iter(FALLBACK_QUESTIONS))  # Get the first available subject
        
        # Check if sub_activity exists for that subject
        if sub_activity not in FALLBACK_QUESTIONS[subject]:
            # Get the first available sub_activity for the subject
            sub_activity = next(iter(FALLBACK_QUESTIONS[subject]))
        
        # Get the fallback question for this subject and sub_activity
        fallback_question = FALLBACK_QUESTIONS[subject][sub_activity].copy()
        
        # Add the sub_activity to the question data
        fallback_question["sub_activity"] = sub_activity
        
        return fallback_question
        
    except Exception as e:
        # Ultimate fallback in case of any errors
        return {
            "question": "What is 2 + 2?",
            "choices": ["3", "4", "5", "6"],
            "answer": "4",
            "type": "multiple-choice",
            "sub_activity": sub_activity
        } 