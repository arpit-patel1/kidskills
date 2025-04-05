import React from 'react';
import QuestionDisplay from './QuestionDisplay';
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
          <div className="welcome-emoji">
            <span role="img" aria-label="Welcome" className="welcome-emoji-icon">👋 🎮 🧠 🎯</span>
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
          <QuestionDisplay 
            question={currentQuestion} 
            onAnswer={handleAnswer} 
            loading={loading} 
            submitted={feedback !== null}
            feedback={feedback}
            selectedChoice={selectedAnswer}
            score={score}
            questionCount={questionCount}
            streak={streak}
          />
        </div>
      ) : (
        <div className="start-screen">
          <h2>Ready to Play, {selectedPlayer.name}?</h2>
          <p>Select your subject and difficulty level in the sidebar, then click "Start Game".</p>
          <div className="start-emoji">
            <span role="img" aria-label="Start Game" className="welcome-emoji-icon">🎮 🚀 ✨ 🎯</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default MainContent; 