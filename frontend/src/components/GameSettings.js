import React, { useMemo } from 'react';

// Define mapping of subjects to sub-activities
const SUB_ACTIVITIES = {
  Math: ['Addition/Subtraction', 'Multiplication/Division', 'Word Problems'],
  English: ['Opposites/Antonyms', 'Reading Comprehension', 'Nouns/Pronouns']
};

const GameSettings = ({ settings, onUpdateSettings }) => {
  const handleSubjectChange = (e) => {
    const newSubject = e.target.value;
    onUpdateSettings({ 
      subject: newSubject,
      // Default to first sub-activity when subject changes
      sub_activity: SUB_ACTIVITIES[newSubject][0]
    });
  };
  
  const handleSubActivityChange = (e) => {
    onUpdateSettings({ sub_activity: e.target.value });
  };
  
  const handleDifficultyChange = (e) => {
    onUpdateSettings({ difficulty: e.target.value });
  };
  
  // Get appropriate sub-activities based on selected subject
  const availableSubActivities = useMemo(() => {
    return SUB_ACTIVITIES[settings.subject] || [];
  }, [settings.subject]);
  
  return (
    <div className="card game-settings">
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
          <label htmlFor="sub_activity">
            <i className="bi bi-lightning-fill"></i> Activity:
          </label>
          <select 
            id="sub_activity" 
            value={settings.sub_activity} 
            onChange={handleSubActivityChange}
            className="form-control form-select-sm"
          >
            {availableSubActivities.map(activity => (
              <option key={activity} value={activity}>
                {activity}
              </option>
            ))}
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