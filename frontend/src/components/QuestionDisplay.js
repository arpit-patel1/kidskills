import React, { useState, useEffect } from 'react';

const QuestionDisplay = ({ 
  question,
  onAnswer, 
  loading, 
  submitted = false, 
  feedback = null,
  selectedChoice: parentSelectedChoice = null
}) => {
  const [localSelectedChoice, setLocalSelectedChoice] = useState(null);
  const [localSubmitted, setLocalSubmitted] = useState(false);
  const [nextQuestionTimer, setNextQuestionTimer] = useState(null);
  const [timeLeft, setTimeLeft] = useState(6);
  
  // Use either local submission state or the prop passed from parent
  const isSubmitted = submitted || localSubmitted;
  
  // Use the parent's selectedChoice if provided, otherwise use local state
  const selectedChoice = parentSelectedChoice || localSelectedChoice;

  // Clear state when question changes
  useEffect(() => {
    setLocalSelectedChoice(null);
    setLocalSubmitted(false);
    setTimeLeft(6);
    
    // Clear any existing timer when question changes
    if (nextQuestionTimer) {
      clearTimeout(nextQuestionTimer);
    }
    
    return () => {
      if (nextQuestionTimer) {
        clearTimeout(nextQuestionTimer);
      }
    };
  }, [question, nextQuestionTimer]);
  
  // Countdown timer for next question
  useEffect(() => {
    let countdownInterval;
    
    if (isSubmitted && feedback) {
      countdownInterval = setInterval(() => {
        setTimeLeft((prevTime) => Math.max(0, prevTime - 1));
      }, 1000);
    }
    
    return () => {
      if (countdownInterval) {
        clearInterval(countdownInterval);
      }
    };
  }, [isSubmitted, feedback]);
  
  if (!question) {
    return null;
  }
  
  const handleChoiceSelection = (choice) => {
    if (!loading && !isSubmitted) {
      setLocalSelectedChoice(choice);
    }
  };
  
  const handleSubmit = async () => {
    if (!selectedChoice || loading || isSubmitted) return;
    
    setLocalSubmitted(true);
    
    // Send the answer to the parent component (useGameState hook)
    // which will call the API and get the result
    onAnswer(selectedChoice);
    
    // Set timer for auto-advancing to next question after 6 seconds
    const timer = setTimeout(() => {
      // This will be handled by the useGameState hook
      // We don't need to do anything here as the component will unmount
    }, 6000);
    
    setNextQuestionTimer(timer);
  };
  
  const getChoiceClass = (choice) => {
    if (!isSubmitted) {
      return selectedChoice === choice ? 'choice-btn selected' : 'choice-btn';
    }
    
    // After submission
    if (feedback) {
      // Parse the is_correct value to ensure it's a boolean
      // This helps with string values like "true" or "false"
      const isCorrect = feedback.is_correct === true || feedback.is_correct === "true";
      
      // Is this the choice the user selected?
      const isSelectedChoice = choice === selectedChoice;
      
      // Is this the correct answer?
      const isCorrectChoice = choice === feedback.correct_answer;
      
      // If user selected this choice
      if (isSelectedChoice) {
        if (isCorrect) {
          return 'choice-btn correct';
        } else {
          return 'choice-btn incorrect';
        }
      }
      
      // If this is the correct answer but user selected something else
      if (isCorrectChoice && !isCorrect) {
        return 'choice-btn correct';
      }
    }
    
    // All other buttons remain neutral
    return 'choice-btn';
  };
  
  // Get emoji based on subject and sub-activity
  const getEmoji = () => {
    if (question.subject === 'Math') {
      if (question.sub_activity === 'Addition/Subtraction') return '➕➖';
      if (question.sub_activity === 'Multiplication/Division') return '✖️➗';
      if (question.sub_activity === 'Word Problems') return '🧮📝';
      return '🧮';
    } else if (question.subject === 'English') {
      if (question.sub_activity === 'Opposites/Antonyms') return '⬆️⬇️';
      if (question.sub_activity === 'Reading Comprehension') return '📚🔍';
      if (question.sub_activity === 'Nouns/Pronouns') return '📝👤';
      return '📚';
    }
    return '🎓';
  };
  
  return (
    <div className="question-display">
      <div className="question-card">
        <div className="question-header">
          <span className="question-emoji">{getEmoji()}</span>
          <div className="question-info">
            <span className="question-subject">{question.subject || 'Challenge'}</span>
            <span className="question-sub-activity">{question.sub_activity}</span>
          </div>
        </div>
        
        <div className="question-text">{question.question}</div>
        
        <div className="choices-container">
          {question.choices.map((choice, index) => (
            <button
              key={index}
              className={getChoiceClass(choice)}
              onClick={() => handleChoiceSelection(choice)}
              disabled={loading || isSubmitted}
            >
              <span className="choice-letter">{String.fromCharCode(65 + index)}</span>
              <span className="choice-text">{choice}</span>
            </button>
          ))}
        </div>
        
        {loading && (
          <div className="loading-container">
            <div className="spinner"></div>
            <p>Checking your answer...</p>
          </div>
        )}
        
        {!isSubmitted && (
          <div className="submit-container">
            <button 
              className="btn btn-primary btn-lg submit-btn"
              onClick={handleSubmit}
              disabled={!selectedChoice || loading}
            >
              <i className="bi bi-check-circle"></i> Submit Answer
            </button>
          </div>
        )}
        
        {isSubmitted && feedback && (
          <div className="next-question-container">
            <div className="timer-circle">
              <div className="timer-number">{timeLeft}</div>
            </div>
            <p className="next-question-text">Next question soon!</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default QuestionDisplay; 