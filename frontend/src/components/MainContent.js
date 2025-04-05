import React from 'react';
import QuestionDisplay from './QuestionDisplay';
import FeedbackDisplay from './FeedbackDisplay';
import ScoreDisplay from './ScoreDisplay';

const MainContent = ({
  selectedPlayer,
  currentQuestion,
  feedback,
  selectedAnswer,
  score,
  questionCount,
  streak,
  gameCompleted,
  loading,
  handleAnswer,
  nextQuestion,
  resetGame
}) => {
  if (!selectedPlayer) {
    return (
      <div className="main-content">
        <div className="welcome-screen">
          <h2>Welcome to AI Kids Challenge Game!</h2>
          <p>Please select a player from the sidebar to start.</p>
          <div className="welcome-image">
            <img src="/assets/welcome-graphic.png" alt="Welcome" className="img-fluid" />
          </div>
        </div>
      </div>
    );
  }

  if (gameCompleted) {
    return (
      <div className="main-content">
        <div className="game-completion">
          <h2>Game Completed!</h2>
          <ScoreDisplay 
            score={score} 
            questionCount={questionCount} 
            streak={streak} 
          />
          <div className="completion-message">
            <p>Great job, {selectedPlayer.name}! You've completed the challenge.</p>
          </div>
          <button 
            className="btn btn-primary mt-4" 
            onClick={resetGame}
          >
            Start New Game
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="main-content">
      {currentQuestion ? (
        <div className="game-content">
          <div className="game-header">
            <ScoreDisplay 
              score={score} 
              questionCount={questionCount} 
              streak={streak} 
            />
          </div>
          
          <div className="game-body">
            <QuestionDisplay 
              question={currentQuestion} 
              onAnswer={handleAnswer} 
              loading={loading} 
              submitted={feedback !== null}
              feedback={feedback}
              selectedChoice={selectedAnswer}
            />
          </div>
        </div>
      ) : (
        <div className="start-screen">
          <h2>Ready to Play, {selectedPlayer.name}?</h2>
          <p>Select your subject and difficulty level in the sidebar, then click "Start Game".</p>
          <div className="start-image">
            <img src="/assets/start-graphic.png" alt="Start Game" className="img-fluid" />
          </div>
        </div>
      )}
    </div>
  );
};

export default MainContent; 