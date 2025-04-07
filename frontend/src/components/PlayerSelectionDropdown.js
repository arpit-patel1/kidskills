import React, { useState } from 'react';
import PlayerCreation from './PlayerCreation';

const PlayerSelectionDropdown = ({ 
  players,
  selectedPlayer,
  onSelectPlayer,
  onPlayersUpdated
}) => {
  const [showDropdown, setShowDropdown] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);

  const toggleDropdown = () => {
    setShowDropdown(prev => !prev);
    setShowCreateForm(false);
  };

  const handlePlayerSelect = (player) => {
    onSelectPlayer(player);
    setShowDropdown(false);
  };

  const handleAddNewClick = () => {
    setShowCreateForm(true);
    setShowDropdown(false);
  };

  return (
    <div className="player-dropdown-container">
      <button 
        className="player-dropdown-button" 
        onClick={toggleDropdown}
      >
        {selectedPlayer ? (
          <>
            <i className="bi bi-person-circle me-2"></i>
            {selectedPlayer.name} (Grade {selectedPlayer.grade})
          </>
        ) : (
          <>
            <i className="bi bi-person-plus me-2"></i>
            Select Player
          </>
        )}
        <i className={`bi bi-chevron-${showDropdown ? 'up' : 'down'} ms-2`}></i>
      </button>

      {showDropdown && (
        <div className="player-dropdown-menu">
          <div className="dropdown-header">
            <strong>Select Player</strong>
            <button 
              className="close-dropdown" 
              onClick={() => setShowDropdown(false)}
            >
              <i className="bi bi-x-lg"></i>
            </button>
          </div>
          
          {players.length > 0 ? (
            <div className="player-list">
              {players.map(player => (
                <div 
                  key={player.id}
                  className={`player-option ${selectedPlayer && player.id === selectedPlayer.id ? 'active' : ''}`}
                  onClick={() => handlePlayerSelect(player)}
                >
                  <i className="bi bi-person me-2"></i>
                  {player.name} (Grade {player.grade})
                </div>
              ))}
              <div className="dropdown-divider"></div>
              <div 
                className="player-option add-new"
                onClick={handleAddNewClick}
              >
                <i className="bi bi-plus-circle me-2"></i>
                Add New Player
              </div>
            </div>
          ) : (
            <div className="empty-player-list">
              <p>No players found</p>
              <button 
                className="btn btn-sm btn-primary"
                onClick={handleAddNewClick}
              >
                Add New Player
              </button>
            </div>
          )}
        </div>
      )}

      {showCreateForm && (
        <div className="player-form-modal">
          <div className="modal-content">
            <div className="modal-header">
              <h5>Create New Player</h5>
              <button 
                className="close-modal"
                onClick={() => setShowCreateForm(false)}
              >
                <i className="bi bi-x-lg"></i>
              </button>
            </div>
            <PlayerCreation 
              onPlayerCreated={(newPlayer) => {
                onPlayersUpdated();
                onSelectPlayer(newPlayer);
                setShowCreateForm(false);
              }}
              onCancel={() => setShowCreateForm(false)}
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default PlayerSelectionDropdown; 