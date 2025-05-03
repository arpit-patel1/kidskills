import random
# import logging # Remove standard logging
# logger = logging.getLogger(__name__) # Remove standard logger instantiation
from loguru import logger # Import loguru logger

from .constants import (
    NAMES, MATH_NAMES, READING_TOPICS, READING_LOCATIONS,
    MATH_OBJECTS, MATH_LOCATIONS, MATH_ACTIVITIES, MATH_WORD_PROBLEM_TEMPLATES,
    ENGLISH_TOPICS, ENGLISH_VERBS, ENGLISH_ADJECTIVES, ENGLISH_NOUNS,
    ENGLISH_WORD_PATTERNS, ENGLISH_GRAMMAR_TEMPLATES,
    SCENARIOS, OBJECTS, LOCATIONS, TIME_EXPRESSIONS,
    MARIO_CHARACTERS, MARIO_ITEMS, MARIO_LOCATIONS, MARIO_ACTIVITIES,
    GRAMMAR_ERROR_TYPES
)

def getRandomSeed() -> int:
    """Generate a random seed for AI prompts to increase variety."""
    return random.randint(1000, 9999)


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
    # logger = logging.getLogger(__name__) # Remove standard logger instantiation
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

def construct_grammar_correction_prompt(grade: int, difficulty: str) -> str:
    """
    Construct a prompt for generating grammar correction questions.
    """
    # Get randomized seed for variety
    random_seed = getRandomSeed()

    # Import constants for randomization
    # from app.services.constants import NAMES, SCENARIOS, LOCATIONS, OBJECTS, TIME_EXPRESSIONS, ENGLISH_TOPICS, GRAMMAR_ERROR_TYPES # Ensure it's imported here too - Note: Already imported at top

    # Choose a specific grammar error type to focus on
    if grade <= 2:  # Grades 1-2
        # Simpler errors for younger students
        # Focus on subject-verb, singular/plural, basic pronouns, basic possessives
        possible_errors = [e for e in GRAMMAR_ERROR_TYPES if e in [
            "subject-verb agreement",
            "singular/plural nouns",
            "pronoun usage",
            "possessive nouns/pronouns"
        ]]
        error_type = random.choice(possible_errors)
    else:  # Grade 3+
        # Use the full range for older students
        error_type = random.choice(GRAMMAR_ERROR_TYPES)

    # Choose random context elements for variety
    person = random.choice(NAMES)
    person2 = random.choice([name for name in NAMES if name != person])
    scenario = random.choice(SCENARIOS)
    location = random.choice(LOCATIONS)
    object_name = random.choice(OBJECTS)
    time_expression = random.choice(TIME_EXPRESSIONS)
    topic = random.choice(ENGLISH_TOPICS)

    # Build the focused prompt with the new two-step approach
    prompt = f"""
    **Goal:** Create a grammar correction question for a {difficulty.lower()} {grade}-grade student.

    **Step 1: Formulate a Correct Sentence**
    First, create a grammatically CORRECT and natural-sounding English sentence. Make it age-appropriate and engaging (use emojis!).
    Use some of these elements for context (optional):
        - Character(s): {person}, {person2}
        - Activity/Scenario: {scenario}
        - Location: {location}
        - Object: {object_name}
        - Time: {time_expression}
        - Topic: {topic}
    Let this correct sentence be the basis for the 'answer' field in the final JSON.

    **Step 2: Introduce ONE Specific Error**
    Now, take the correct sentence you formulated and introduce EXACTLY ONE grammatical error of the type: **'{error_type}'**.
    This modified sentence (with the single error) will be the value for the 'question' field in the final JSON.

    **Output Format:** Return ONLY a valid JSON object containing the result of Step 2 (the incorrect sentence) and Step 1 (the correct sentence) with these EXACT keys:
    {{
      "question": "[The sentence modified in Step 2 with the ONE '{error_type}' error]",
      "answer": "[The original CORRECT sentence formulated in Step 1]",
      "type": "direct-answer"
    }}

    **Example (if Step 1 sentence was "The cat jumps high." and error type was 'subject-verb agreement'):**
    {{
      "question": "The cat jump high. 🐈",
      "answer": "The cat jumps high.",
      "type": "direct-answer"
    }}

    **CRITICAL:**
    - The 'question' field MUST contain the sentence with the specified grammatical error.
    - The 'answer' field MUST contain the original, perfectly correct sentence.
    - Only include the SINGLE specified error type.
    - Ensure the final output is ONLY the JSON object, with no extra text before or after.
    """

    # Log the randomization details
    logger.info(f"Grammar correction prompt generation - Error type: {error_type}, Grade: {grade}, Difficulty: {difficulty}, Seed: {random_seed}")
    logger.debug(f"Using context: Person={person}, Location={location}, Scenario={scenario}")

    return prompt

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