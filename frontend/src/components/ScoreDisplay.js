import React from 'react';

const ScoreDisplay = ({ score, questionCount, streak }) => {
  // Show score only if at least one question has been answered
  if (questionCount === 0) {
    return null;
  }
  
  // Generate star emojis based on streak
  const stars = Array(Math.min(streak, 5)).fill('⭐').join(' ');
  
  // Determine if we should show a special achievement badge
  const showStreakBadge = streak >= 3;
  
  // Get achievement badge text
  const getAchievementText = (streak) => {
    if (streak >= 10) return '🏆 Champion!';
    if (streak >= 5) return '🥇 Expert!';
    if (streak >= 3) return '🎖️ Great job!';
    return '';
  };
  
  return (
    <div className="score-display">
      <div className="score-item">
        <span>Score: </span>
        <strong>{score} / {questionCount}</strong>
      </div>
      
      {streak > 0 && (
        <div className="score-item">
          <span>Streak: </span>
          <strong>
            <span className="emoji">{stars}</span> ({streak})
          </strong>
          
          {showStreakBadge && (
            <span className="streak-badge">
              {getAchievementText(streak)}
            </span>
          )}
        </div>
      )}
    </div>
  );
};

export default ScoreDisplay; 