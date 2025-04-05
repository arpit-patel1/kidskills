import React from 'react';

const GameSettings = ({ settings, onUpdateSettings }) => {
  const handleSubjectChange = (e) => {
    onUpdateSettings({ subject: e.target.value });
  };
  
  const handleDifficultyChange = (e) => {
    onUpdateSettings({ difficulty: e.target.value });
  };
  
  return (
    <div className="card game-settings">
      <div className="card-header">
        <i className="bi bi-sliders"></i> Game Settings
      </div>
      <div className="settings-container">
        <div className="settings-row">
          <label htmlFor="subject">
            <i className="bi bi-book"></i> Subject:
          </label>
          <select 
            id="subject" 
            value={settings.subject} 
            onChange={handleSubjectChange}
            className="form-control form-select-sm"
          >
            <option value="Math">Math</option>
            <option value="English">English</option>
          </select>
        </div>
        
        <div className="settings-row">
          <label htmlFor="difficulty">
            <i className="bi bi-bar-chart-fill"></i> Difficulty:
          </label>
          <select 
            id="difficulty" 
            value={settings.difficulty} 
            onChange={handleDifficultyChange}
            className="form-control form-select-sm"
          >
            <option value="Easy">Easy</option>
            <option value="Medium">Medium</option>
            <option value="Hard">Hard</option>
          </select>
        </div>
      </div>
    </div>
  );
};

export default GameSettings; 