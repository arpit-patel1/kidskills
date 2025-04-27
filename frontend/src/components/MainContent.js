import React from 'react';
import QuestionDisplay from './QuestionDisplay';
import GujaratiTracingActivity from './GujaratiTracingActivity';
import { QUESTIONS_PER_GAME } from '../hooks/useGameState';

const MainContent = ({
  selectedPlayer,
  settings,
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
      ? Math.round((score / questionCount) * 100) 
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
          <div className="completion-stats">
            <div className="completion-stat">
              <span>Score: </span>
              <strong>{score}</strong>
            </div>
            <div className="completion-stat">
              <span>Questions: </span>
              <strong>{questionCount}/{QUESTIONS_PER_GAME}</strong>
            </div>
            <div className="completion-stat">
              <span>Accuracy: </span>
              <strong>{accuracyPercentage}%</strong>
            </div>
            <div className="completion-achievement">
              <span>Achievement: </span>
              <strong>{getAchievementLevel()}</strong>
            </div>
          </div>
          <button 
            className="btn btn-primary start-btn" 
            onClick={() => resetGame(false)}
            style={{ marginTop: '20px' }}
          >
            Play Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="main-content">
      {settings?.subject === 'Gujarati' && settings?.sub_activity === 'Letter Tracing' && selectedPlayer ? (
          <GujaratiTracingActivity playerId={selectedPlayer.id} />
      ) : currentQuestion ? (
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