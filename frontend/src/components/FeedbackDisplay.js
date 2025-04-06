import React, { useEffect, useState } from 'react';

const FeedbackDisplay = ({ feedback, onNext }) => {
  const [timeLeft, setTimeLeft] = useState(4);
  
  useEffect(() => {
    const timer = setInterval(() => {
      setTimeLeft(prevTime => {
        const newValue = Math.max(0, prevTime - 1);
        if (newValue === 0 && onNext) {
          // Call onNext when timer reaches 0
          setTimeout(() => {
            onNext();
          }, 300); // Small delay to ensure UI renders 0 first
        }
        return newValue;
      });
    }, 1000);
    
    return () => clearInterval(timer);
  }, [onNext]);
  
  if (!feedback) {
    return null;
  }
  
  const feedbackClass = feedback.is_correct ? 'feedback-correct' : 'feedback-incorrect';
  const feedbackIcon = feedback.is_correct ? 
    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M9 16.17L4.83 12L3.41 13.41L9 19L21 7L19.59 5.59L9 16.17Z" fill="currentColor"/>
    </svg> :
    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M19 6.41L17.59 5L12 10.59L6.41 5L5 6.41L10.59 12L5 17.59L6.41 19L12 13.41L17.59 19L19 17.59L13.41 12L19 6.41Z" fill="currentColor"/>
    </svg>;
  
  return (
    <div className="feedback-container">
      <div className={`feedback ${feedbackClass}`}>
        <div className="feedback-header">
          {feedbackIcon}
          <h3>{feedback.is_correct ? 'Correct!' : 'Incorrect'}</h3>
        </div>
        <div className="feedback-message">
          {feedback.feedback}
        </div>
        
        {!feedback.is_correct && (
          <div className="correct-answer-display">
            <h4>Correct Answer:</h4>
            <div className="correct-answer">{feedback.correct_answer}</div>
          </div>
        )}
        
        <div className="next-question-countdown">
          <p>Next question in {timeLeft} seconds...</p>
        </div>
      </div>
    </div>
  );
};

export default FeedbackDisplay; 