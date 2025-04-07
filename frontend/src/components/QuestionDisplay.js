import React, { useState, useEffect } from 'react';
import DirectAnswerInput from './DirectAnswerInput';
import { QUESTIONS_PER_GAME } from '../hooks/useGameState';

const QuestionDisplay = ({ 
  question,
  onAnswer, 
  loading, 
  loadingNextQuestion,
  nextQuestionTimer,
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
    console.log("Question changed, resetting local state");
    setLocalSelectedChoice(null);
    setLocalSubmitted(false);
    
    // Add a log to help debug question transitions
    if (question) {
      console.log("New question received in QuestionDisplay:", question.id);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [question?.id]); // Only depend on question ID to prevent unnecessary rerenders
  
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
    
    // For higher streaks, add special indicators
    if (streak >= 20) {
      return '🔥🔥🔥🔥🔥';
    } else if (streak >= 15) {
      return '👑👑👑👑👑';
    } else if (streak >= 10) {
      return '🏆🏆🏆🏆🏆';
    } else if (streak >= 7) {
      return '🥇🥇🥇🥇🥇';
    } else if (streak >= 5) {
      return '🥈🥈🥈🥈🥈';
    } else {
      return Array(Math.min(streak, 5)).fill('⭐').join('');
    }
  };
  
  // Get streak tooltip text that shows bonus points
  const getStreakTooltip = () => {
    if (streak >= 15) return '+20 points bonus!';
    if (streak >= 10) return '+15 points bonus!';
    if (streak >= 5) return '+10 points bonus!';
    if (streak >= 3) return '+5 points bonus!';
    return '';
  };
  
  // Check if this is a direct answer question
  const isDirectAnswer = question.type === 'direct-answer';
  
  // Check if this is a reading comprehension question
  const isReadingComprehension = question.type === 'reading-comprehension';
  
  // Add debugging statements
  console.log('Question Type:', question.type);
  console.log('Is Direct Answer:', isDirectAnswer);
  console.log('Is Reading Comprehension:', isReadingComprehension);
  console.log('Full Question Object:', question);
  
  // Calculate progress percentage (for 1000 question game)
  const progressPercentage = (questionCount / QUESTIONS_PER_GAME) * 100;
  
  return (
    <div className="question-display">
      <div className={`question-card ${loadingNextQuestion ? 'loading-transition' : ''}`}>
        <div className="fixed-score-display">
          Score: {score} / {questionCount}
        </div>
        
        {/* Progress bar for 1000 question game */}
        <div className="progress mb-3" style={{ height: "8px" }}>
          <div 
            className="progress-bar" 
            role="progressbar" 
            style={{ width: `${progressPercentage}%` }} 
            aria-valuenow={progressPercentage} 
            aria-valuemin="0" 
            aria-valuemax="100">
          </div>
        </div>
        <div className="text-center mb-2 small text-muted">
          Question {questionCount} of {QUESTIONS_PER_GAME}
        </div>
        
        {streak > 0 && (
          <div className="fixed-streak-display">
            <i className="bi bi-lightning-fill"></i>
            <span className="fixed-streak-stars">{renderStars()}</span>
            {streak >= 3 && (
              <span className="streak-bonus-indicator">{getStreakTooltip()}</span>
            )}
          </div>
        )}
        
        {isReadingComprehension && question.passage && (
          <div className="reading-passage">
            <h4>Reading Passage:</h4>
            <div className="passage-text">{question.passage}</div>
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
                  disabled={loading || isSubmitted || loadingNextQuestion}
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
                  disabled={!selectedChoice || loading || isSubmitted || loadingNextQuestion}
                  style={{ marginTop: '10px' }}
                >
                  <i className="bi bi-check-circle"></i> Submit Answer
                </button>
              ) : (
                <button 
                  className="btn btn-success btn-lg submit-btn"
                  onClick={handleNextQuestion}
                  disabled={loading || loadingNextQuestion}
                  style={{ marginTop: '10px' }}
                >
                  <i className="bi bi-arrow-right-circle"></i> Next Question
                </button>
              )}
            </div>
          </>
        )}
        
        {/* Overlay for loading next question */}
        {loadingNextQuestion && (
          <div className="loading-overlay">
            <div className="loading-overlay-content">
              <div className="spinner"></div>
              <div className="timer-counter">{nextQuestionTimer}s</div>
              <div className="loading-text">Loading next question...</div>
            </div>
          </div>
        )}
      </div>
      
      {/* No longer needed - removed "Checking your answer..." status container */}
    </div>
  );
};

export default QuestionDisplay; 