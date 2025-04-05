import React, { useState } from 'react';
import PlayerSelection from './PlayerSelection';
import GameSettings from './GameSettings';

const Sidebar = ({ 
  players, 
  selectedPlayer, 
  settings, 
  onSelectPlayer, 
  onUpdateSettings,
  onStartGame,
  toggleContinuousMode
}) => {
  const [showPlayers, setShowPlayers] = useState(!selectedPlayer);
  
  const handlePlayerSelect = (player) => {
    onSelectPlayer(player);
    setShowPlayers(false);
  };
  
  const handleChangePlayer = () => {
    setShowPlayers(true);
  };
  
  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <h2><i className="bi bi-joystick"></i> Game Controls</h2>
      </div>
      
      {showPlayers ? (
        <PlayerSelection 
          players={players} 
          onSelectPlayer={handlePlayerSelect} 
        />
      ) : selectedPlayer ? (
        <div className="sidebar-content">
          <div className="player-info">
            <h3><i className="bi bi-person-circle"></i> {selectedPlayer.name}</h3>
            <p><i className="bi bi-mortarboard"></i> Grade {selectedPlayer.grade}</p>
            <button 
              className="btn btn-sm btn-outline-secondary mt-2" 
              onClick={handleChangePlayer}
            >
              <i className="bi bi-arrow-left-right"></i> Change Player
            </button>
          </div>
          
          <div className="activity-selection">
            <h4><i className="bi bi-gear-fill"></i> Current Activity</h4>
            <div className="current-activity">
              <div className="badge subject-badge">
                <i className="bi bi-book"></i> {settings.subject}
              </div>
              <div className="badge difficulty-badge">
                <i className="bi bi-bar-chart-fill"></i> {settings.difficulty}
              </div>
            </div>
          </div>
          
          <div className="settings-section">
            <GameSettings 
              settings={settings} 
              onUpdateSettings={onUpdateSettings} 
            />
            
            <button 
              className="btn btn-primary btn-lg mt-4 start-button" 
              onClick={onStartGame}
            >
              <i className="bi bi-play-fill"></i> Start New Game
            </button>
          </div>
        </div>
      ) : (
        <div className="empty-selection">
          <p><i className="bi bi-person-plus-fill"></i> Select a player to start</p>
          <button 
            className="btn btn-primary" 
            onClick={handleChangePlayer}
          >
            <i className="bi bi-person-fill"></i> Select Player
          </button>
        </div>
      )}
    </div>
  );
};

export default Sidebar; 