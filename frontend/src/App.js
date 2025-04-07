import React, { useState } from 'react';
import './styles/theme.css';
import 'bootstrap/dist/css/bootstrap.min.css';
import 'bootstrap-icons/font/bootstrap-icons.css';
import useGameState from './hooks/useGameState';
import MainContent from './components/MainContent';
import ConfettiEffect from './components/ConfettiEffect';
import PlayerSelectionDropdown from './components/PlayerSelectionDropdown';
import GameSelectorDropdown from './components/GameSelectorDropdown';

function App() {
  const {
    players,
    selectedPlayer,
    settings,
    currentQuestion,
    loading,
    startGameLoading,
    error,
    feedback,
    selectedAnswer,
    score,
    questionCount,
    streak,
    showConfetti,
    gameCompleted,
    loadingNextQuestion,
    nextQuestionTimer,
    selectPlayer,
    updateSettings,
    startGame,
    handleAnswer,
    nextQuestion,
    resetGame,
    fetchPlayers
  } = useGameState();

  // Function to start a game with predefined settings
  const handleQuickStart = (quickSettings) => {
    // Update the settings
    updateSettings(quickSettings);
    // Start the game with these settings
    startGame();
  };

  return (
    <div className="app">
      <ConfettiEffect show={showConfetti} />
      
      <header className="app-header">
        <h1>KidSkills <i className="bi bi-stars"></i></h1>
        <p className="subtitle">Fun learning for young minds <i className="bi bi-emoji-smile"></i></p>
        
        <div className="dropdown-container">
          <PlayerSelectionDropdown 
            players={players}
            selectedPlayer={selectedPlayer}
            onSelectPlayer={selectPlayer}
            onPlayersUpdated={fetchPlayers}
          />
          
          <GameSelectorDropdown 
            selectedPlayer={selectedPlayer}
            currentQuestion={currentQuestion}
            resetGame={resetGame}
            settings={settings}
            onUpdateSettings={updateSettings}
            onStartGame={startGame}
            startGameLoading={startGameLoading}
          />
        </div>
      </header>
      
      {error && (
        <div className="error-message">
          <i className="bi bi-exclamation-triangle-fill"></i> {error}
        </div>
      )}
      
      <div className="app-layout">
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
          loadingNextQuestion={loadingNextQuestion}
          nextQuestionTimer={nextQuestionTimer}
          handleAnswer={handleAnswer}
          nextQuestion={nextQuestion}
          resetGame={resetGame}
        />
      </div>
      
      <footer className="app-footer">
        <p><i className="bi bi-controller"></i> KidSkills • Powered by AI <i className="bi bi-rocket-takeoff"></i></p>
      </footer>
    </div>
  );
}

export default App;
