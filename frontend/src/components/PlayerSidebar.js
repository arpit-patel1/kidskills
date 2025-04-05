import React from 'react';
import PlayerSelection from './PlayerSelection';

const PlayerSidebar = ({ 
  players, 
  selectedPlayer, 
  onSelectPlayer
}) => {
  return (
    <div className="sidebar player-sidebar">
      <div className="sidebar-header">
        <h2>Player Selection</h2>
      </div>
      
      {selectedPlayer ? (
        <div className="sidebar-content">
          <div className="player-info">
            <h3>{selectedPlayer.name}</h3>
            <p>Grade {selectedPlayer.grade}</p>
            <button 
              className="btn btn-sm btn-outline-secondary mt-2" 
              onClick={() => onSelectPlayer(null)}
            >
              Change Player
            </button>
          </div>
          
          <div className="player-selection-container mt-4">
            <h4>Other Players</h4>
            <div className="players-grid">
              {players
                .filter(player => player.id !== selectedPlayer.id)
                .map(player => (
                  <div 
                    key={player.id} 
                    className="player-card compact"
                    onClick={() => onSelectPlayer(player)}
                  >
                    <div className="player-avatar">
                      <div className="emoji-avatar small">😊</div>
                    </div>
                    <div className="player-info">
                      <h3>{player.name}</h3>
                      <p>Grade {player.grade}</p>
                    </div>
                  </div>
                ))}
            </div>
          </div>
        </div>
      ) : (
        <PlayerSelection 
          players={players} 
          onSelectPlayer={onSelectPlayer} 
        />
      )}
    </div>
  );
};

export default PlayerSidebar; 