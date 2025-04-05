import React from 'react';
import PlayerSelection from './PlayerSelection';

const PlayerSidebar = ({ 
  players, 
  selectedPlayer, 
  onSelectPlayer,
  onPlayersUpdated
}) => {
  return (
    <div className="sidebar player-sidebar">
      <div className="sidebar-header">
        <h2>Player Selection</h2>
      </div>
      
      {selectedPlayer ? (
        <div className="sidebar-content">
          <div>
            <h4>Current Player</h4>
            <div className="player-pill selected">
              {selectedPlayer.name} (Grade {selectedPlayer.grade})
            </div>
            <button 
              className="btn btn-sm btn-outline-secondary mt-2" 
              onClick={() => onSelectPlayer(null)}
            >
              Change Player
            </button>
          </div>
          
          {players.filter(player => player.id !== selectedPlayer.id).length > 0 && (
            <div className="mt-4">
              <h4>Other Players</h4>
              <div className="player-pills-container">
                {players
                  .filter(player => player.id !== selectedPlayer.id)
                  .map(player => (
                    <div 
                      key={player.id} 
                      className="player-pill"
                      onClick={() => onSelectPlayer(player)}
                    >
                      {player.name} (Grade {player.grade})
                    </div>
                  ))}
              </div>
            </div>
          )}
        </div>
      ) : (
        <PlayerSelection 
          players={players} 
          onSelectPlayer={onSelectPlayer} 
          onPlayersUpdated={onPlayersUpdated}
        />
      )}
    </div>
  );
};

export default PlayerSidebar; 