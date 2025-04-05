import React from 'react';
import PlayerCreation from './PlayerCreation';

const PlayerSelection = ({ players, onSelectPlayer }) => {
  const handlePlayerCreated = (newPlayer) => {
    // Select the newly created player immediately
    onSelectPlayer(newPlayer);
  };

  return (
    <div className="player-selection">
      <h4>Select a Player</h4>
      
      {players.length === 0 ? (
        <div className="no-players">
          <p>No players available. Please create a new player.</p>
          <PlayerCreation onPlayerCreated={handlePlayerCreated} />
        </div>
      ) : (
        <>
          <div className="player-pills-container">
            {players.map(player => (
              <div 
                key={player.id} 
                className="player-pill"
                onClick={() => onSelectPlayer(player)}
              >
                {player.name} (G{player.grade})
              </div>
            ))}
          </div>
          
          <div className="player-creation-section">
            <button 
              className="btn btn-sm btn-outline-primary d-flex align-items-center mx-auto"
              onClick={() => document.getElementById('playerCreationForm').classList.toggle('d-none')}
            >
              Add New Player
            </button>
            <div id="playerCreationForm" className="mt-3 d-none">
              <PlayerCreation onPlayerCreated={handlePlayerCreated} />
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default PlayerSelection; 