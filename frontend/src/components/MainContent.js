import React from 'react';
import QuestionDisplay from './QuestionDisplay';
import ScoreDisplay from './ScoreDisplay';
import { QUESTIONS_PER_GAME } from '../hooks/useGameState';

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
  loadingNextQuestion,
  nextQuestionTimer,
  handleAnswer,
  nextQuestion,
  resetGame
}) => {
  // Check if a game is loading from useGameState
  const isStartingGame = !currentQuestion && loading;
  
  if (!selectedPlayer) {
    return (
      <div className="main-content">
        <div className="welcome-screen">
          <h2>Welcome to AI Kids Challenge Game!</h2>
          <p>Please select a player from the header menu to start.</p>
          <div className="welcome-emoji">
            <span role="img" aria-label="Welcome" className="welcome-emoji-icon">👋 🎮 🧠 🎯</span>
          </div>
        </div>
      </div>
    );
  }

  if (gameCompleted) {
    // Calculate accuracy percentage
    const accuracyPercentage = questionCount > 0 
      ? Math.round((score / (questionCount * 10)) * 100) 
      : 0;
    
    // Determine achievement level based on score and questions
    const getAchievementLevel = () => {
      if (accuracyPercentage >= 90 && questionCount >= QUESTIONS_PER_GAME) return "🏆 Master Achiever";
      if (accuracyPercentage >= 80 && questionCount >= QUESTIONS_PER_GAME / 2) return "🥇 Expert Learner";
      if (accuracyPercentage >= 70 && questionCount >= QUESTIONS_PER_GAME / 4) return "🥈 Skilled Player";
      if (questionCount >= QUESTIONS_PER_GAME / 10) return "🎮 Game Explorer";
      return "👍 Good Start";
    };
    
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
            <div className="stats-summary mt-3">
              <h4 className="text-center mb-3">{getAchievementLevel()}</h4>
              
              <div className="d-flex justify-content-center align-items-center mb-3">
                <div className="progress" style={{ height: "20px", width: "80%" }}>
                  <div 
                    className="progress-bar bg-success" 
                    role="progressbar" 
                    style={{ width: `${accuracyPercentage}%` }} 
                    aria-valuenow={accuracyPercentage} 
                    aria-valuemin="0" 
                    aria-valuemax="100">
                    {accuracyPercentage}% Accuracy
                  </div>
                </div>
              </div>
              
              <div className="row text-center mb-3">
                <div className="col">
                  <div className="stat-box">
                    <div className="stat-value">{questionCount}</div>
                    <div className="stat-label">Questions Answered</div>
                  </div>
                </div>
                <div className="col">
                  <div className="stat-box">
                    <div className="stat-value">{score}</div>
                    <div className="stat-label">Total Score</div>
                  </div>
                </div>
              </div>
              
              <p className="text-center">
                You answered <strong>{questionCount}</strong> questions out of {QUESTIONS_PER_GAME}!
              </p>
            </div>
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
            loadingNextQuestion={loadingNextQuestion}
            nextQuestionTimer={nextQuestionTimer}
            submitted={feedback !== null}
            feedback={feedback}
            selectedChoice={selectedAnswer}
            score={score}
            questionCount={questionCount}
            streak={streak}
            onNextQuestion={nextQuestion}
          />
        </div>
      ) : loadingNextQuestion || isStartingGame ? (
        <div className="loading-screen">
          <div className="spinner-container">
            <div className="spinner"></div>
            <div className="timer-counter">{nextQuestionTimer > 0 ? `${nextQuestionTimer}s` : ''}</div>
            <div className="loading-text">
              {isStartingGame ? 'Starting game...' : 'Loading question...'}
            </div>
          </div>
        </div>
      ) : (
        <div className="start-screen">
          <h2>Ready to Play, {selectedPlayer.name}?</h2>
          <p>Click on "Play Game" in the header to configure and start your game!</p>
          <div className="start-emoji">
            <span role="img" aria-label="Start Game" className="welcome-emoji-icon">🎮 🚀 ✨ 🎯</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default MainContent; 