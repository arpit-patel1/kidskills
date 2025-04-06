import React, { useState, useEffect } from 'react';
import { getGrammarFeedback, evaluateGrammarCorrection, evaluateReadingComprehension } from '../services/api';

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
  const [aiEvaluation, setAiEvaluation] = useState(null);
  const [isEvaluating, setIsEvaluating] = useState(false);
  
  // Clear the input when question changes
  useEffect(() => {
    setAnswer('');
    setDetailedFeedback('');
    setAiEvaluation(null);
  }, [question]);
  
  // Get detailed feedback when receiving basic feedback
  useEffect(() => {
    const fetchDetailedFeedback = async () => {
      if (submitted && feedback && question.sub_activity === 'Grammar Correction') {
        // If we already have AI evaluation, use its feedback directly
        if (aiEvaluation && aiEvaluation.feedback) {
          console.log("Using AI evaluation feedback:", aiEvaluation.feedback);
          setDetailedFeedback(aiEvaluation.feedback);
          return;
        }

        // Otherwise, get feedback via API
        setLoadingFeedback(true);
        try {
          // Get detailed AI feedback on why the answer was correct/incorrect
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
  }, [submitted, feedback, question, answer, aiEvaluation]);
  
  const handleSubmit = async () => {
    if (!answer.trim() || loading || submitted || isEvaluating) return;
    
    const isGrammarCorrection = question.sub_activity === 'Grammar Correction';
    const isReadingComprehension = question.sub_activity === 'Reading Comprehension';
    
    setIsEvaluating(true);
    
    try {
      // Different evaluation based on question type
      if (isGrammarCorrection) {
        // For grammar correction, use AI grammar evaluation
        const evaluation = await evaluateGrammarCorrection(
          question.question,      // Original incorrect sentence
          answer,                 // User's attempted correction
          question.answer         // Expected correct answer from the question object
        );
        
        setAiEvaluation(evaluation);
        // Pass the AI evaluation result to the parent component instead of raw answer
        onAnswer(answer, evaluation);
      } 
      else if (isReadingComprehension) {
        // For reading comprehension, use AI reading evaluation
        const evaluation = await evaluateReadingComprehension(
          question.passage,       // Reading passage
          question.question,      // Question about the passage
          answer,                 // User's answer
          question.answer         // Expected correct answer
        );
        
        setAiEvaluation(evaluation);
        // Pass the AI evaluation result to the parent component
        onAnswer(answer, evaluation);
      }
      else {
        // For other types, just submit the answer as before
        onAnswer(answer);
      }
    } catch (error) {
      console.error("Error during AI evaluation:", error);
      // If evaluation fails, submit the answer without AI evaluation
      onAnswer(answer);
    } finally {
      setIsEvaluating(false);
    }
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
        disabled={loading || submitted || isEvaluating}
        rows={3}
        style={inputStyle}
      />
      
      <div className="action-container">
        {!submitted ? (
          <button 
            className="btn btn-primary btn-lg submit-btn"
            onClick={handleSubmit}
            disabled={!answer.trim() || loading || submitted || isEvaluating}
          >
            {isEvaluating ? (
              <>
                <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                Evaluating...
              </>
            ) : (
              <>
                <i className="bi bi-check-circle"></i> Submit Answer
              </>
            )}
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
                backgroundColor: '#ffffff', 
                borderRadius: '4px', 
                marginTop: '3px', 
                color: '#212529'
              }}>
                {answer}
              </div>
              
              {feedback.ai_evaluated && (
                <div style={{ 
                  marginTop: '8px', 
                  fontSize: '0.8rem', 
                  fontStyle: 'italic',
                  padding: '3px',
                  backgroundColor: '#e0f3ff',
                  borderRadius: '4px'
                }}>
                  <i className="bi bi-robot"></i> Evaluated by AI
                </div>
              )}
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