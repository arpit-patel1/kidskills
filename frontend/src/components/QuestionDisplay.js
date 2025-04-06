import React, { useState, useEffect } from 'react';
import DirectAnswerInput from './DirectAnswerInput';

const QuestionDisplay = ({ 
  question,
  onAnswer, 
  loading, 
  submitted = false, 
  feedback = null,
  selectedChoice: parentSelectedChoice = null,
  score = 0,
  questionCount = 0,
  streak = 0,
  onNextQuestion
}) => {
  const [localSelectedChoice, setLocalSelectedChoice] = useState(null);
  const [localSubmitted, setLocalSubmitted] = useState(false);
  
  // Use either local submission state or the prop passed from parent
  const isSubmitted = submitted || localSubmitted;
  
  // Use the parent's selectedChoice if provided, otherwise use local state
  const selectedChoice = parentSelectedChoice || localSelectedChoice;

  // Clear state when question changes
  useEffect(() => {
    setLocalSelectedChoice(null);
    setLocalSubmitted(false);
  }, [question]);
  
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
  };
  
  const handleNextQuestion = () => {
    if (onNextQuestion) {
      onNextQuestion();
    }
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
  
  // Generate star emojis based on streak
  const renderStars = () => {
    if (streak === 0) return null;
    const stars = Array(Math.min(streak, 5)).fill('⭐').join('');
    return stars;
  };
  
  // Check if this is a direct answer question
  const isDirectAnswer = question.type === 'direct-answer';
  
  // Add debugging statements
  console.log('Question Type:', question.type);
  console.log('Is Direct Answer:', isDirectAnswer);
  console.log('Full Question Object:', question);
  
  return (
    <div className="question-display">
      <div className="question-card">
        <div className="fixed-score-display">
          Score: {score} / {questionCount}
        </div>
        
        {streak > 0 && (
          <div className="fixed-streak-display">
            <i className="bi bi-lightning-fill"></i>
            <span className="fixed-streak-stars">{renderStars()}</span>
          </div>
        )}
        
        <div className="question-text">
          {question.question}
        </div>
        
        {isDirectAnswer ? (
          <DirectAnswerInput
            question={question}
            onAnswer={onAnswer}
            loading={loading}
            submitted={isSubmitted}
            feedback={feedback}
            onNextQuestion={onNextQuestion}
          />
        ) : (
          <>
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
            
            <div className="action-container">
              {!isSubmitted ? (
                <button 
                  className="btn btn-primary btn-lg submit-btn"
                  onClick={handleSubmit}
                  disabled={!selectedChoice || loading || isSubmitted}
                  style={{ marginTop: '10px' }}
                >
                  <i className="bi bi-check-circle"></i> Submit Answer
                </button>
              ) : (
                <button 
                  className="btn btn-success btn-lg submit-btn"
                  onClick={handleNextQuestion}
                  disabled={loading}
                  style={{ marginTop: '10px' }}
                >
                  <i className="bi bi-arrow-right-circle"></i> Next Question
                </button>
              )}
            </div>
          </>
        )}
      </div>
      
      {/* Move status container outside the question card */}
      <div className="status-container">
        {loading && (
          <div className="status-item loading-status">
            <div className="spinner"></div>
            <p>Checking your answer...</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default QuestionDisplay; 