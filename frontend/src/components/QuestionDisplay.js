import React, { useState, useEffect, useRef } from 'react';
import DirectAnswerInput from './DirectAnswerInput';
import { QUESTIONS_PER_GAME } from '../hooks/useGameState';
import LoadingAnimation from './animations/LoadingAnimation';
import '../styles/animations.css';

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
  const [isEvaluating, setIsEvaluating] = useState(false);
  const nextButtonRef = useRef(null);
  
  // Use either local submission state or the prop passed from parent
  const isSubmitted = submitted || localSubmitted;
  
  // Use the parent's selectedChoice if provided, otherwise use local state
  const selectedChoice = parentSelectedChoice || localSelectedChoice;

  // Clear state when question changes
  useEffect(() => {
    console.log("Question changed, resetting local state");
    setLocalSelectedChoice(null);
    setLocalSubmitted(false);
    setIsEvaluating(false);
    
    // Add a log to help debug question transitions
    if (question) {
      console.log("New question received in QuestionDisplay:", question.id);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [question?.id]); // Only depend on question ID to prevent unnecessary rerenders
  
  // Effect to focus the Next Question button when feedback appears
  useEffect(() => {
    if (isSubmitted && nextButtonRef.current) {
      // Use setTimeout to defer focus until after the current render cycle
      const timerId = setTimeout(() => {
        if (nextButtonRef.current) {
           console.log("Setting focus to Next Question button");
           nextButtonRef.current.focus();
        }
      }, 0);
      return () => clearTimeout(timerId); // Cleanup timeout
    }
  }, [isSubmitted]); // Run when submission state changes
  
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
    
    // Set evaluating state to show the animation
    setIsEvaluating(true);
    
    // Add a minimum delay to ensure the animation is visible
    const startTime = Date.now();
    const minAnimationTime = 3000; // 3 seconds minimum
    
    // Send the answer to the parent component (useGameState hook)
    // which will call the API and get the result
    onAnswer(selectedChoice);
    
    // Set submitted state after a delay to ensure animation is visible
    setTimeout(() => {
      setLocalSubmitted(true);
      
      // Keep animation visible for minimum time
      const elapsedTime = Date.now() - startTime;
      if (elapsedTime < minAnimationTime) {
        setTimeout(() => {
          setIsEvaluating(false);
        }, minAnimationTime - elapsedTime);
      } else {
        setIsEvaluating(false);
      }
    }, 500); // Short delay to let the API call start
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
  
  // Check if this is a direct answer question
  const isDirectAnswer = question.type === 'direct-answer';
  
  // Check if this is a reading comprehension question
  const isReadingComprehension = question.type === 'reading-comprehension';
  
  // Add debugging statements
  console.log('Question Type:', question.type);
  console.log('Is Direct Answer:', isDirectAnswer);
  console.log('Is Reading Comprehension:', isReadingComprehension);
  console.log('Full Question Object:', question);
  
  // Debug question properties specifically for Grammar Correction
  if (question.sub_activity === 'Grammar Correction') {
    console.log('Grammar Question - answer property:', question.answer);
    console.log('Grammar Question - properties:', Object.keys(question));
    // Check if there's any property that might contain the answer
    const potentialAnswerProps = Object.entries(question).filter(([key, value]) => 
      typeof value === 'string' && 
      value !== question.question && 
      key !== 'id' && 
      key !== 'type' && 
      key !== 'subject' && 
      key !== 'sub_activity' && 
      key !== 'difficulty'
    );
    console.log('Potential answer properties:', potentialAnswerProps);
  }
  
  // Calculate progress percentage (for 1000 question game)
  const progressPercentage = (questionCount / QUESTIONS_PER_GAME) * 100;
  
  // Function to get the subject for the loading animation
  const getAnimationSubject = () => {
    if (!question) return 'default';
    
    if (question.subject === 'Math') return 'Math';
    if (question.subject === 'English') return 'English';
    if (question.sub_activity && question.sub_activity.includes('Mario')) return 'Mario';
    
    return 'default';
  };
  
  return (
    <div className="question-display">
      <div className={`question-card ${loadingNextQuestion ? 'loading-transition' : ''}`}>
        <LoadingAnimation 
          subject={getAnimationSubject()}
          isVisible={loadingNextQuestion} 
          previousQuestion={question}
        />
        
        <div className="score-progress-container">
          <div className="score-circle">
            {score}
          </div>
          
          {/* Progress bar for questions - moved to be beside score */}
          <div className="progress-container">
            <div className="progress" style={{ height: "8px" }}>
              <div 
                className="progress-bar" 
                role="progressbar" 
                style={{ width: `${progressPercentage}%` }} 
                aria-valuenow={progressPercentage} 
                aria-valuemin="0" 
                aria-valuemax="100">
              </div>
            </div>
            <div className="small text-muted">
              Question {questionCount} of {QUESTIONS_PER_GAME}
            </div>
          </div>
        </div>
        
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
            loadingNextQuestion={loadingNextQuestion}
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
                  className={`btn btn-primary btn-lg submit-btn ${isEvaluating ? 'evaluating' : ''}`}
                  onClick={handleSubmit}
                  disabled={!selectedChoice || loading || isSubmitted || isEvaluating || loadingNextQuestion}
                >
                  {isEvaluating ? (
                    <span>Checking Answer...</span>
                  ) : (
                    <>
                      <i className="bi bi-check-circle me-2"></i>
                      <span>Submit Answer</span>
                    </>
                  )}
                </button>
              ) : (
                <button 
                  ref={nextButtonRef}
                  className={`btn btn-success btn-lg submit-btn ${loadingNextQuestion ? 'loading' : ''}`}
                  onClick={handleNextQuestion}
                  disabled={loading || loadingNextQuestion}
                  style={{ minWidth: '280px', minHeight: '60px', position: 'relative', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
                >
                  {loadingNextQuestion ? (
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'row', width: '100%' }}>
                      <div className="theme-spinner"></div>
                      <span className="loading-message">Next Question</span>
                      <div className="floating-icons">
                        <span className="icon">💖</span>
                        <span className="icon">✨</span>
                        <span className="icon">🌟</span>
                        <span className="icon">💫</span>
                        <span className="icon">💕</span>
                      </div>
                    </div>
                  ) : (
                    <>
                      <i className="bi bi-arrow-right-circle me-2"></i>
                      <span>Next Question</span>
                    </>
                  )}
                </button>
              )}
            </div>
          </>
        )}
      </div>
      
      {/* No longer needed - removed "Checking your answer..." status container */}
    </div>
  );
};

export default QuestionDisplay; 