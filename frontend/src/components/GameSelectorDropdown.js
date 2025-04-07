import React, { useState, useEffect } from 'react';

const GameSelectorDropdown = ({ 
  selectedPlayer,
  currentQuestion,
  resetGame,
  settings,
  onUpdateSettings,
  onStartGame,
  startGameLoading
}) => {
  const [showDropdown, setShowDropdown] = useState(false);
  const [tempSettings, setTempSettings] = useState(settings);
  const [previousQuestionState, setPreviousQuestionState] = useState(!!currentQuestion);
  
  // Reset temp settings when actual settings change
  useEffect(() => {
    setTempSettings(settings);
  }, [settings]);
  
  // Effect to close dropdown when a game is first loaded
  // but not when trying to open it during an active game
  useEffect(() => {
    const questionStarted = !previousQuestionState && !!currentQuestion;
    if (questionStarted && showDropdown) {
      setShowDropdown(false);
    }
    setPreviousQuestionState(!!currentQuestion);
  }, [currentQuestion, showDropdown, previousQuestionState]);
  
  const handleResetGame = () => {
    resetGame();
    setShowDropdown(false);
  };
  
  const handleSettingChange = (e) => {
    const { name, value } = e.target;
    setTempSettings(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleStartGame = () => {
    // Apply temp settings to actual settings
    onUpdateSettings(tempSettings);
    // Start the game
    onStartGame();
    // Keep dropdown open while loading to show spinner
    if (!startGameLoading) {
      setShowDropdown(false);
    }
  };
  
  // Only show when a player is selected
  if (!selectedPlayer) {
    return null;
  }
  
  // Subject to sub-activity mapping
  const subActivities = {
    Math: ['Addition/Subtraction', 'Multiplication/Division', 'Word Problems'],
    English: ['Opposites/Antonyms', 'Reading Comprehension', 'Nouns/Pronouns', 'Grammar Correction']
  };
  
  return (
    <div className="game-dropdown-container">
      <button 
        className="game-dropdown-button" 
        onClick={() => setShowDropdown(prev => !prev)}
        disabled={startGameLoading}
      >
        {startGameLoading ? (
          <>
            <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
            Loading...
          </>
        ) : (
          <>
            <i className="bi bi-controller me-2"></i>
            {currentQuestion ? 'Current Game' : 'Play Game'}
            <i className={`bi bi-chevron-${showDropdown ? 'up' : 'down'} ms-2`}></i>
          </>
        )}
      </button>

      {showDropdown && (
        <div className="game-dropdown-menu">
          <div className="dropdown-header">
            <strong>{currentQuestion ? 'Game Options' : 'Game Settings'}</strong>
            <button 
              className="close-dropdown" 
              onClick={() => setShowDropdown(false)}
            >
              <i className="bi bi-x-lg"></i>
            </button>
          </div>
          
          <div className="game-options-list">
            {currentQuestion && (
              <>
                <div 
                  className="game-option"
                  onClick={handleResetGame}
                >
                  <i className="bi bi-arrow-counterclockwise me-2"></i>
                  End Current Game
                </div>
                <div className="dropdown-divider"></div>
              </>
            )}
            
            {!currentQuestion && (
              <div className="game-settings-panel">
                <div className="settings-row">
                  <label htmlFor="subject">Subject</label>
                  <select 
                    id="subject"
                    name="subject"
                    className="form-control"
                    value={tempSettings.subject}
                    onChange={handleSettingChange}
                    disabled={startGameLoading}
                  >
                    <option value="Math">Math</option>
                    <option value="English">English</option>
                  </select>
                </div>
                
                <div className="settings-row">
                  <label htmlFor="sub_activity">Activity Type</label>
                  <select 
                    id="sub_activity"
                    name="sub_activity"
                    className="form-control"
                    value={tempSettings.sub_activity}
                    onChange={handleSettingChange}
                    disabled={startGameLoading}
                  >
                    {subActivities[tempSettings.subject]?.map(activity => (
                      <option key={activity} value={activity}>{activity}</option>
                    ))}
                  </select>
                </div>
                
                <div className="settings-row">
                  <label htmlFor="difficulty">Difficulty</label>
                  <select 
                    id="difficulty"
                    name="difficulty"
                    className="form-control"
                    value={tempSettings.difficulty}
                    onChange={handleSettingChange}
                    disabled={startGameLoading}
                  >
                    <option value="Easy">Easy</option>
                    <option value="Medium">Medium</option>
                    <option value="Hard">Hard</option>
                  </select>
                </div>
                
                <button 
                  className="btn btn-primary start-game-button"
                  onClick={handleStartGame}
                  disabled={startGameLoading}
                >
                  {startGameLoading ? (
                    <>
                      <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                      Loading Game...
                    </>
                  ) : (
                    <>
                      <i className="bi bi-play-fill me-2"></i>
                      Start Game
                    </>
                  )}
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default GameSelectorDropdown; 