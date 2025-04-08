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
  
  // Get the player ID from the question object or localStorage
  const getPlayerId = () => {
    // Check if player_id is in the question object
    if (question && question.player_id) {
      console.log("Found player_id in question object:", question.player_id);
      return question.player_id;
    }
    
    // Try to get from localStorage as fallback
    const playerData = localStorage.getItem('currentPlayer');
    if (playerData) {
      try {
        const player = JSON.parse(playerData);
        if (player && player.id) {
          console.log("Found player_id in localStorage:", player.id);
          return player.id;
        }
      } catch (e) {
        console.error("Error parsing player data from localStorage:", e);
      }
    }
    
    console.log("No player_id found, returning null");
    return null; // No player ID found
  };
  
  // Clear the input when question changes
  useEffect(() => {
    setDetailedFeedback('');
    setAiEvaluation(null);
    
    // For Grammar Correction, pre-populate the answer field with the question text
    if (question && question.sub_activity === 'Grammar Correction') {
      setAnswer(question.question);
    } else {
      setAnswer('');
    }
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

        // If the feedback from server already has meaningful feedback, use that
        if (feedback.feedback && !feedback.feedback.includes("Oops! The correct")) {
          console.log("Using server feedback:", feedback.feedback);
          setDetailedFeedback(feedback.feedback);
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
  
  // Add debug logging for evaluating state changes
  useEffect(() => {
    console.log("Evaluating state changed:", isEvaluating);
  }, [isEvaluating]);
  
  const handleSubmit = async () => {
    if (!answer.trim() || loading || submitted || isEvaluating) return;
    
    const isGrammarCorrection = question.sub_activity === 'Grammar Correction';
    const isReadingComprehension = question.sub_activity === 'Reading Comprehension';
    
    console.log("Setting evaluating state to true");
    setIsEvaluating(true);
    
    // Force a delay to ensure React has time to update the UI before evaluation starts
    await new Promise(resolve => setTimeout(resolve, 100));
    
    // Force redraw to ensure UI updates immediately
    setTimeout(() => {
      console.log("Evaluation state in setTimeout:", isEvaluating);
    }, 0);
    
    const startTime = Date.now();
    
    // Different evaluation based on question type
    if (isGrammarCorrection) {
      try {
        // For grammar correction, use AI grammar evaluation
        console.log("Starting grammar evaluation API call at:", new Date().toISOString());
        const evaluation = await evaluateGrammarCorrection(
          question.question,      // Original incorrect sentence
          answer,                 // User's attempted correction
          question.answer,        // Expected correct answer from the question object
          getPlayerId()           // Player ID
        );
        console.log("Finished grammar evaluation API call at:", new Date().toISOString());
        
        // Ensure loading indicator shows for at least 3 seconds
        const elapsedTime = Date.now() - startTime;
        const minLoadingTime = 3000; // 3 seconds minimum
        if (elapsedTime < minLoadingTime) {
          console.log(`Waiting ${minLoadingTime - elapsedTime}ms to ensure loading is visible`);
          await new Promise(resolve => setTimeout(resolve, minLoadingTime - elapsedTime));
        }
        
        setAiEvaluation(evaluation);
        // Set detailed feedback directly from the evaluation
        setDetailedFeedback(evaluation.feedback || '');
        
        // Pass the AI evaluation result to the parent component instead of raw answer
        console.log("About to call onAnswer and complete evaluation");
        onAnswer(answer, evaluation);
        console.log("Evaluation complete, setting isEvaluating to false");
        // Turn off loading indicator after everything is done
        setIsEvaluating(false);
      } catch (error) {
        console.error("Error in grammar evaluation:", error);
        // If evaluation fails, submit the answer without AI evaluation
        onAnswer(answer);
        // Turn off loading indicator
        setIsEvaluating(false);
      }
    } 
    else if (isReadingComprehension) {
      try {
        // For reading comprehension, use AI reading evaluation
        const evaluation = await evaluateReadingComprehension(
          question.passage,       // Reading passage
          question.question,      // Question about the passage
          answer,                 // User's answer
          question.answer         // Expected correct answer
        );
        
        // Ensure loading indicator shows for at least 3 seconds
        const elapsedTime = Date.now() - startTime;
        const minLoadingTime = 3000; // 3 seconds minimum
        if (elapsedTime < minLoadingTime) {
          console.log(`Waiting ${minLoadingTime - elapsedTime}ms to ensure loading is visible`);
          await new Promise(resolve => setTimeout(resolve, minLoadingTime - elapsedTime));
        }
        
        setAiEvaluation(evaluation);
        // Pass the AI evaluation result to the parent component
        onAnswer(answer, evaluation);
        // Turn off loading indicator
        setIsEvaluating(false);
      } catch (error) {
        console.error("Error in reading comprehension evaluation:", error);
        onAnswer(answer);
        setIsEvaluating(false);
      }
    }
    else {
      try {
        // For other types, just submit the answer as before
        
        // Ensure loading indicator shows for at least 3 seconds
        const elapsedTime = Date.now() - startTime;
        const minLoadingTime = 3000; // 3 seconds minimum
        if (elapsedTime < minLoadingTime) {
          console.log(`Waiting ${minLoadingTime - elapsedTime}ms to ensure loading is visible`);
          await new Promise(resolve => setTimeout(resolve, minLoadingTime - elapsedTime));
        }
        
        onAnswer(answer);
        // Turn off loading indicator
        setIsEvaluating(false);
      } catch (error) {
        console.error("Error in basic answer submission:", error);
        onAnswer(answer);
        setIsEvaluating(false);
      }
    }
  };
  
  const handleNextQuestion = () => {
    if (onNextQuestion) {
      onNextQuestion();
    }
  };
  
  const getInputClass = () => {
    if (isEvaluating) return 'direct-answer-input evaluating';
    if (!submitted) return 'direct-answer-input';
    return feedback?.is_correct ? 'direct-answer-input correct' : 'direct-answer-input incorrect';
  };
  
  const isGrammarCorrection = question.sub_activity === 'Grammar Correction';
  
  const inputStyle = {
    fontSize: '1rem',
    color: '#212529',
    fontWeight: 'normal',
    position: 'relative'
  };
  
  return (
    <div className="direct-answer-container">
      <div style={{ position: 'relative' }}>
        <textarea
          className={getInputClass()}
          value={answer}
          onChange={(e) => setAnswer(e.target.value)}
          placeholder={isGrammarCorrection ? "Type the corrected sentence here..." : "Type your answer here..."}
          disabled={loading || submitted || isEvaluating}
          rows={3}
          style={inputStyle}
        />
      </div>
      
      <div className="action-container">
        {!submitted ? (
          <button 
            className="btn btn-lg btn-primary submit-btn"
            onClick={handleSubmit}
            disabled={!answer.trim() || loading || submitted || isEvaluating}
            style={{
              ...(isEvaluating ? {
                background: '#ff1493',
                color: 'white',
                boxShadow: '0 0 20px rgba(255, 20, 147, 0.7)',
                border: 'none',
                position: 'relative',
                overflow: 'hidden',
                transform: 'scale(1.05)',
                transition: 'all 0.3s ease'
              } : {})
            }}
          >
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              position: 'relative',
              zIndex: 2
            }}>
              {isEvaluating ? (
                <>
                  <div className="spinner-border text-white me-2" 
                       role="status" 
                       style={{
                         width: '2rem',
                         height: '2rem',
                         borderWidth: '0.25rem'
                       }}></div>
                  <span style={{ fontSize: '1.3rem', fontWeight: 'bold' }}>Evaluating...</span>
                </>
              ) : (
                <>
                  <i className="bi bi-check-circle me-2"></i>
                  <span>Submit Answer</span>
                </>
              )}
            </div>
            
            {isEvaluating && (
              <div style={{
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                background: 'linear-gradient(45deg, rgba(255,105,180,0.6) 25%, rgba(255,20,147,0.6) 25%, rgba(255,20,147,0.6) 50%, rgba(255,105,180,0.6) 50%, rgba(255,105,180,0.6) 75%, rgba(255,20,147,0.6) 75%, rgba(255,20,147,0.6))',
                backgroundSize: '40px 40px',
                animation: 'move-background 1s linear infinite',
                zIndex: 1
              }}></div>
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
          {!feedback.is_correct && !isGrammarCorrection && (
            <div className="correct-answer-display">
              <h4>Correct Answer:</h4>
              <div className="correct-answer">{feedback.correct_answer}</div>
            </div>
          )}
          
          {isGrammarCorrection && (
            <div className="detailed-feedback">
              <h4>
                <i className={`bi ${feedback.is_correct ? 'bi-lightbulb' : 'bi-info-circle'}`}></i> 
                Grammar Feedback:
              </h4>
              {loadingFeedback ? (
                <div className="loading-feedback">
                  <div className="spinner" style={{ width: '20px', height: '20px', borderWidth: '2px' }}></div> 
                  <span>Loading feedback...</span>
                </div>
              ) : (
                <div className="feedback-text">
                  {detailedFeedback || feedback.feedback}
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