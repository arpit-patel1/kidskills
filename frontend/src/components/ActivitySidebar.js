import React from 'react';
import GameSettings from './GameSettings';

const ActivitySidebar = ({ 
  selectedPlayer, 
  settings, 
  onUpdateSettings,
  onStartGame,
  loading
}) => {
  return (
    <div className="sidebar activity-sidebar">
      <div className="sidebar-header">
        <h2><i className="bi bi-joystick"></i> Game Controls</h2>
      </div>
      
      {selectedPlayer ? (
        <div className="sidebar-content">
          <div className="settings-section">
            <GameSettings 
              settings={settings} 
              onUpdateSettings={onUpdateSettings} 
            />
            
            <button 
              className="btn btn-primary mt-4 start-button" 
              onClick={onStartGame}
              disabled={loading}
            >
              {loading ? (
                <>
                  <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                  Loading...
                </>
              ) : (
                <>
                  <i className="bi bi-play-fill"></i> Start Game
                </>
              )}
            </button>
          </div>
        </div>
      ) : (
        <div className="empty-selection">
          <i className="bi bi-person-plus-fill empty-icon"></i>
          <p>Please select a player to start</p>
        </div>
      )}
    </div>
  );
};

export default ActivitySidebar; 