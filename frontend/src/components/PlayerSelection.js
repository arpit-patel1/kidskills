import React, { useState } from 'react';
import PlayerCreation from './PlayerCreation';
import { deletePlayer } from '../services/api';
import { Modal, Button } from 'react-bootstrap';

const PlayerSelection = ({ players, onSelectPlayer, onPlayersUpdated }) => {
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [playerToDelete, setPlayerToDelete] = useState(null);

  const handlePlayerCreated = (newPlayer) => {
    // Select the newly created player immediately
    onSelectPlayer(newPlayer);
  };

  const handleDeleteClick = (player, e) => {
    e.stopPropagation(); // Prevent player selection when clicking delete button
    setPlayerToDelete(player);
    setShowConfirmModal(true);
  };

  const handleConfirmDelete = async () => {
    if (playerToDelete) {
      try {
        await deletePlayer(playerToDelete.id);
        setShowConfirmModal(false);
        setPlayerToDelete(null);
        
        // Notify parent component to refresh player list
        if (onPlayersUpdated) {
          onPlayersUpdated();
        }
      } catch (error) {
        console.error("Error deleting player:", error);
        // Could show an error message here
      }
    }
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
                className="player-pill d-flex justify-content-between align-items-center"
                onClick={() => onSelectPlayer(player)}
              >
                <span>{player.name} (G{player.grade})</span>
                <button 
                  className="btn btn-sm btn-outline-danger ms-2" 
                  onClick={(e) => handleDeleteClick(player, e)}
                  aria-label={`Delete ${player.name}`}
                >
                  <i className="bi bi-trash"></i>
                </button>
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

      {/* Confirmation Modal */}
      <Modal show={showConfirmModal} onHide={() => setShowConfirmModal(false)} centered>
        <Modal.Header closeButton>
          <Modal.Title>Confirm Deletion</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          Are you sure you want to delete player "{playerToDelete?.name}"? 
          This will remove all their progress and cannot be undone.
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowConfirmModal(false)}>
            Cancel
          </Button>
          <Button variant="danger" onClick={handleConfirmDelete}>
            Delete
          </Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
};

export default PlayerSelection; 