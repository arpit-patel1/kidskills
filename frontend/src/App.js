import React from 'react';
import './styles/theme.css';
import 'bootstrap/dist/css/bootstrap.min.css';
import 'bootstrap-icons/font/bootstrap-icons.css';
import useGameState from './hooks/useGameState';
import PlayerSidebar from './components/PlayerSidebar';
import ActivitySidebar from './components/ActivitySidebar';
import MainContent from './components/MainContent';
import ConfettiEffect from './components/ConfettiEffect';

function App() {
  const {
    players,
    selectedPlayer,
    settings,
    currentQuestion,
    loading,
    error,
    feedback,
    selectedAnswer,
    score,
    questionCount,
    streak,
    showConfetti,
    gameCompleted,
    selectPlayer,
    updateSettings,
    startGame,
    handleAnswer,
    nextQuestion,
    resetGame
  } = useGameState();

  return (
    <div className="app">
      <ConfettiEffect show={showConfetti} />
      
      <header className="app-header">
        <h1><i className="bi bi-stars"></i> AI Kids Challenge Game</h1>
        <p className="subtitle">Fun learning for young minds <i className="bi bi-emoji-smile"></i></p>
      </header>
      
      {error && (
        <div className="error-message">
          <i className="bi bi-exclamation-triangle-fill"></i> {error}
        </div>
      )}
      
      <div className="app-layout">
        <ActivitySidebar
          selectedPlayer={selectedPlayer}
          settings={settings}
          onUpdateSettings={updateSettings}
          onStartGame={startGame}
        />
        
        <MainContent
          selectedPlayer={selectedPlayer}
          currentQuestion={currentQuestion}
          feedback={feedback}
          selectedAnswer={selectedAnswer}
          score={score}
          questionCount={questionCount}
          streak={streak}
          gameCompleted={gameCompleted}
          loading={loading}
          handleAnswer={handleAnswer}
          nextQuestion={nextQuestion}
          resetGame={resetGame}
        />
        
        <PlayerSidebar
          players={players}
          selectedPlayer={selectedPlayer}
          onSelectPlayer={selectPlayer}
        />
      </div>
      
      <footer className="app-footer">
        <p><i className="bi bi-controller"></i> AI Kids Challenge Game • Powered by OpenRouter <i className="bi bi-rocket-takeoff"></i></p>
      </footer>
    </div>
  );
}

export default App;
