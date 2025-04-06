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

  return (
    <div className="app">
      <ConfettiEffect show={showConfetti} />
      
      <header className="app-header">
        <h1>KidSkills <i className="bi bi-stars"></i></h1>
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
          loadingNextQuestion={loadingNextQuestion}
          nextQuestionTimer={nextQuestionTimer}
          handleAnswer={handleAnswer}
          nextQuestion={nextQuestion}
          resetGame={resetGame}
        />
        
        <PlayerSidebar
          players={players}
          selectedPlayer={selectedPlayer}
          onSelectPlayer={selectPlayer}
          onPlayersUpdated={fetchPlayers}
        />
      </div>
      
      <footer className="app-footer">
        <p><i className="bi bi-controller"></i> KidSkills • Powered by AI <i className="bi bi-rocket-takeoff"></i></p>
      </footer>
    </div>
  );
}

export default App;
