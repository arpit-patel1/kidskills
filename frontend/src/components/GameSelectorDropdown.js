import React, { useState, useEffect } from 'react';
import { SUB_ACTIVITIES } from '../constants';

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
  const [previousStartGameLoading, setPreviousStartGameLoading] = useState(startGameLoading);
  
  // Reset temp settings when actual settings change
  useEffect(() => {
    setTempSettings(settings);
  }, [settings]);
  
  // Effect to close dropdown when a game is first loaded
  // or when loading starts/finishes
  useEffect(() => {
    // Only track previous states, don't manipulate dropdown
    setPreviousStartGameLoading(startGameLoading);
    
    // Close dropdown ONLY when a question has been successfully loaded
    // (a new question exists AND we were previously loading)
    if (!!currentQuestion && previousStartGameLoading && showDropdown) {
      setShowDropdown(false);
    }
  }, [currentQuestion, previousStartGameLoading, showDropdown, startGameLoading]);
  
  const handleResetGame = () => {
    console.log("Ending game with current settings:", settings);
    resetGame();
    setShowDropdown(false);
  };
  
  const handleSettingChange = (e) => {
    const { name, value } = e.target;
    
    // If changing subject, we need to update sub-activity as well
    if (name === 'subject') {
      const newSubject = value;
      const validSubActivities = SUB_ACTIVITIES[newSubject] || [];
      const defaultSubActivity = validSubActivities[0] || 'Addition/Subtraction';
      
      console.log(`Subject changed to ${newSubject}, updating sub-activity to ${defaultSubActivity}`);
      
      // Update both subject and sub-activity together
      setTempSettings(prev => ({
        ...prev,
        subject: newSubject,
        sub_activity: defaultSubActivity
      }));
    } else {
      // For other settings, just update the one that changed
      setTempSettings(prev => ({
        ...prev,
        [name]: value
      }));
    }
    
    console.log(`Changed setting ${name} to ${value}`);
  };

  const handleStartGame = () => {
    console.log("======= STARTING NEW GAME =======");
    console.log("Current settings state:", settings);
    console.log("Temporary settings state:", tempSettings);
    
    // Apply temp settings to actual settings
    onUpdateSettings(tempSettings);
    
    // Add delay to verify settings are applied before starting the game
    setTimeout(() => {
      console.log("Settings after update, before starting game:", tempSettings);
      // Start the game with these settings
      onStartGame(tempSettings);
    }, 0);
    
    // Always keep dropdown open when starting a game to show the loading state
    // The dropdown will close when the question loads in the useEffect
  };
  
  return (
    <div className="game-dropdown-container">
      <button 
        className="game-dropdown-button" 
        onClick={() => selectedPlayer && setShowDropdown(prev => !prev)}
        disabled={!selectedPlayer || startGameLoading}
        style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}
      >
        {startGameLoading ? (
          <>
            <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
            Loading...
          </>
        ) : (
          <>
            <i className="bi bi-controller me-2"></i>
            {currentQuestion ? `${settings.subject}: ${settings.sub_activity}` : 'Play Game'}
            <i className={`bi bi-chevron-${showDropdown ? 'up' : 'down'} ms-2`}></i>
          </>
        )}
      </button>

      {showDropdown && selectedPlayer && (
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
                    <option value="Gujarati">Gujarati</option>
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
                    {SUB_ACTIVITIES[tempSettings.subject]?.map(activity => (
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
                      <span>Loading Game...</span>
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