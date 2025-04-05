import React, { useState } from 'react';
import { createPlayer } from '../services/api';

const PlayerCreation = ({ onPlayerCreated }) => {
  const [isCreating, setIsCreating] = useState(false);
  const [name, setName] = useState('');
  const [age, setAge] = useState('');
  const [grade, setGrade] = useState('2');
  const [avatar, setAvatar] = useState('girl1.png');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const avatarOptions = [
    { value: 'girl1.png', label: 'Girl 1' },
    { value: 'girl2.png', label: 'Girl 2' },
    { value: 'girl3.png', label: 'Girl 3' },
    { value: 'girl4.png', label: 'Girl 4' },
    { value: 'girl5.png', label: 'Girl 5' }
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    if (!name.trim()) {
      setError('Please enter a name');
      return;
    }
    
    if (!age || isNaN(age) || age < 5 || age > 12) {
      setError('Please enter a valid age (5-12)');
      return;
    }
    
    try {
      setLoading(true);
      
      const playerData = {
        name: name.trim(),
        age: Number(age),
        grade: Number(grade),
        avatar
      };
      
      const newPlayer = await createPlayer(playerData);
      
      setLoading(false);
      setIsCreating(false);
      setName('');
      setAge('');
      setGrade('2');
      setAvatar('girl1.png');
      
      onPlayerCreated(newPlayer);
    } catch (err) {
      setError(err.message || 'Failed to create player. Please try again.');
      setLoading(false);
    }
  };
  
  const renderForm = () => (
    <form onSubmit={handleSubmit} className="player-creation-form">
      <h3>Create New Player</h3>
      
      {error && <div className="error-message">{error}</div>}
      
      <div className="form-group">
        <label htmlFor="name">Name:</label>
        <input
          type="text"
          id="name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          disabled={loading}
          placeholder="Enter player name"
          required
        />
      </div>
      
      <div className="form-group">
        <label htmlFor="age">Age:</label>
        <input
          type="number"
          id="age"
          value={age}
          onChange={(e) => setAge(e.target.value)}
          disabled={loading}
          min="5"
          max="12"
          placeholder="Age"
          required
        />
      </div>
      
      <div className="form-group">
        <label htmlFor="grade">Grade:</label>
        <select 
          id="grade"
          value={grade}
          onChange={(e) => setGrade(e.target.value)}
          disabled={loading}
        >
          <option value="1">Grade 1</option>
          <option value="2">Grade 2</option>
          <option value="3">Grade 3</option>
          <option value="4">Grade 4</option>
          <option value="5">Grade 5</option>
        </select>
      </div>
      
      <div className="form-group">
        <label htmlFor="avatar">Avatar:</label>
        <select 
          id="avatar"
          value={avatar}
          onChange={(e) => setAvatar(e.target.value)}
          disabled={loading}
        >
          {avatarOptions.map(option => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>
      
      <div className="form-buttons">
        <button 
          type="button" 
          className="btn btn-secondary"
          onClick={() => setIsCreating(false)}
          disabled={loading}
        >
          Cancel
        </button>
        <button 
          type="submit" 
          className="btn btn-primary"
          disabled={loading}
        >
          {loading ? 'Creating...' : 'Create Player'}
        </button>
      </div>
    </form>
  );
  
  const renderCreateButton = () => (
    <div className="create-player-button">
      <button 
        className="btn btn-primary btn-lg" 
        onClick={() => setIsCreating(true)}
      >
        Create New Player
      </button>
    </div>
  );
  
  return (
    <div className="player-creation">
      {isCreating ? renderForm() : renderCreateButton()}
    </div>
  );
};

export default PlayerCreation; 