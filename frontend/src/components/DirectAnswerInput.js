import React, { useState, useEffect } from 'react';
import { getGrammarFeedback } from '../services/api';

const DirectAnswerInput = ({ 
  question,
  onAnswer,
  loading,
  submitted,
  feedback
}) => {
  const [answer, setAnswer] = useState('');
  const [detailedFeedback, setDetailedFeedback] = useState('');
  const [loadingFeedback, setLoadingFeedback] = useState(false);
  
  // Clear the input when question changes
  useEffect(() => {
    setAnswer('');
    setDetailedFeedback('');
  }, [question]);
  
  // Get detailed feedback when receiving basic feedback
  useEffect(() => {
    const fetchDetailedFeedback = async () => {
      if (submitted && feedback && question.sub_activity === 'Grammar Correction') {
        setLoadingFeedback(true);
        try {
          const result = await getGrammarFeedback(
            question.question,           // Original incorrect sentence
            answer,                      // User's attempted correction
            feedback.correct_answer,     // Correct answer
            feedback.is_correct          // Whether they got it right
          );
          setDetailedFeedback(result.feedback);
        } catch (error) {
          console.error("Error getting detailed feedback:", error);
        } finally {
          setLoadingFeedback(false);
        }
      }
    };
    
    fetchDetailedFeedback();
  }, [submitted, feedback, question, answer]);
  
  const handleSubmit = () => {
    if (!answer.trim() || loading || submitted) return;
    onAnswer(answer);
  };
  
  const getInputClass = () => {
    if (!submitted) return 'direct-answer-input';
    return feedback?.is_correct ? 'direct-answer-input correct' : 'direct-answer-input incorrect';
  };
  
  const isGrammarCorrection = question.sub_activity === 'Grammar Correction';
  
  return (
    <div className="direct-answer-container">
      <textarea
        className={getInputClass()}
        value={answer}
        onChange={(e) => setAnswer(e.target.value)}
        placeholder={isGrammarCorrection ? "Type the corrected sentence here..." : "Type your answer here..."}
        disabled={loading || submitted}
        rows={3}
      />
      
      <div className="action-container">
        <button 
          className="btn btn-primary btn-lg submit-btn"
          onClick={handleSubmit}
          disabled={!answer.trim() || loading || submitted}
        >
          <i className="bi bi-check-circle"></i> Submit Answer
        </button>
      </div>
      
      {submitted && feedback && (
        <div className={`feedback-container ${feedback.is_correct ? 'feedback-correct' : 'feedback-incorrect'}`}>
          {!feedback.is_correct && (
            <div className="correct-answer-display">
              <h4>Correct Answer:</h4>
              <div className="correct-answer">{feedback.correct_answer}</div>
            </div>
          )}
          
          {isGrammarCorrection && (
            <div className="detailed-feedback">
              <h4>Feedback:</h4>
              {loadingFeedback ? (
                <div className="loading-feedback">Loading feedback...</div>
              ) : (
                <div className="feedback-text">{detailedFeedback}</div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default DirectAnswerInput; 