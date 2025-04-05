import React from 'react';
import GameSettings from './GameSettings';

const ActivitySidebar = ({ 
  selectedPlayer, 
  settings, 
  onUpdateSettings,
  onStartGame
}) => {
  return (
    <div className="sidebar activity-sidebar">
      <div className="sidebar-header">
        <h2><i className="bi bi-joystick"></i> Game Controls</h2>
      </div>
      
      {selectedPlayer ? (
        <div className="sidebar-content">
          <div className="settings-section">
            <div className="current-player-info">
              <div className="avatar-wrapper">
                <div className="player-avatar">
                  <div className="default-avatar"></div>
                </div>
                <h3>{selectedPlayer.name}</h3>
              </div>
              <p><i className="bi bi-mortarboard-fill"></i> Grade {selectedPlayer.grade}</p>
            </div>
            
            <div className="activity-selection">
              <h4><i className="bi bi-gear-fill"></i> Current Settings</h4>
              <div className="current-activity">
                <div className="badge subject-badge">
                  <i className="bi bi-book"></i> {settings.subject}
                </div>
                <div className="badge difficulty-badge">
                  <i className="bi bi-bar-chart-fill"></i> {settings.difficulty}
                </div>
              </div>
            </div>
            
            <GameSettings 
              settings={settings} 
              onUpdateSettings={onUpdateSettings} 
            />
            
            <button 
              className="btn btn-primary mt-4 start-button" 
              onClick={onStartGame}
            >
              <i className="bi bi-play-fill"></i> Start Game
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