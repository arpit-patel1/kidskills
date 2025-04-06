import React, { useState, useEffect } from 'react';
import { getGrammarFeedback } from '../services/api';

const DirectAnswerInput = ({ 
  question,
  onAnswer,
  loading,
  submitted,
  feedback,
  onNextQuestion
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
  
  const handleNextQuestion = () => {
    if (onNextQuestion) {
      onNextQuestion();
    }
  };
  
  const getInputClass = () => {
    if (!submitted) return 'direct-answer-input';
    return feedback?.is_correct ? 'direct-answer-input correct' : 'direct-answer-input incorrect';
  };
  
  const isGrammarCorrection = question.sub_activity === 'Grammar Correction';
  
  const inputStyle = {
    fontSize: '1rem',
    color: '#212529',
    fontWeight: 'normal'
  };
  
  return (
    <div className="direct-answer-container">
      <textarea
        className={getInputClass()}
        value={answer}
        onChange={(e) => setAnswer(e.target.value)}
        placeholder={isGrammarCorrection ? "Type the corrected sentence here..." : "Type your answer here..."}
        disabled={loading || submitted}
        rows={3}
        style={inputStyle}
      />
      
      <div className="action-container">
        {!submitted ? (
          <button 
            className="btn btn-primary btn-lg submit-btn"
            onClick={handleSubmit}
            disabled={!answer.trim() || loading || submitted}
          >
            <i className="bi bi-check-circle"></i> Submit Answer
          </button>
        ) : (
          <button 
            className="btn btn-success btn-lg submit-btn"
            onClick={handleNextQuestion}
            disabled={loading}
          >
            <i className="bi bi-arrow-right-circle"></i> Next Question
          </button>
        )}
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
            <div className="user-answer-display" style={{ marginBottom: '15px', fontSize: '0.9rem' }}>
              <span style={{ fontWeight: 'bold', color: '#495057' }}>Your answer:</span>
              <div style={{ 
                padding: '5px 8px', 
                backgroundColor: 'rgba(255,255,255,0.7)', 
                borderRadius: '4px', 
                marginTop: '3px', 
                color: '#212529'
              }}>
                {answer}
              </div>
            </div>
          )}
          
          {isGrammarCorrection && (
            <div className="detailed-feedback">
              <h4>
                <i className={`bi ${feedback.is_correct ? 'bi-lightbulb' : 'bi-info-circle'}`}></i> 
                Grammar Explanation:
              </h4>
              {loadingFeedback ? (
                <div className="loading-feedback">
                  <div className="spinner" style={{ width: '20px', height: '20px', borderWidth: '2px' }}></div> 
                  <span>Loading feedback...</span>
                </div>
              ) : (
                <div className="feedback-text">
                  {detailedFeedback}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default DirectAnswerInput; 