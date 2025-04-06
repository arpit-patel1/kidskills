import React from 'react';

const ScoreDisplay = ({ score, questionCount, streak }) => {
  // Show score only if at least one question has been answered
  if (questionCount === 0) {
    return null;
  }
  
  // Generate star emojis based on streak (max 5 stars)
  const stars = Array(Math.min(streak, 5)).fill('⭐').join(' ');
  
  // Determine if we should show a special achievement badge
  const showStreakBadge = streak >= 3;
  
  // Get achievement badge text with enhanced achievements for 1000-question game
  const getAchievementText = (streak) => {
    if (streak >= 20) return '🔥 Legendary!';
    if (streak >= 15) return '👑 Master!';
    if (streak >= 10) return '🏆 Champion!';
    if (streak >= 7) return '🥇 Expert!';
    if (streak >= 5) return '🥈 Pro!';
    if (streak >= 3) return '🎖️ Great job!';
    return '';
  };
  
  // Get bonus points text based on current streak
  const getBonusPointsText = (streak) => {
    if (streak >= 15) return '+20 bonus per answer';
    if (streak >= 10) return '+15 bonus per answer';
    if (streak >= 5) return '+10 bonus per answer';
    if (streak >= 3) return '+5 bonus per answer';
    return '';
  };
  
  return (
    <div className="score-display">
      <div className="score-item">
        <span>Score: </span>
        <strong>{score}</strong>
        <div className="small text-muted">Question: {questionCount}/1000</div>
      </div>
      
      {streak > 0 && (
        <div className="score-item">
          <span>Streak: </span>
          <strong>
            <span className="emoji">{stars}</span> ({streak})
          </strong>
          
          {showStreakBadge && (
            <div className="streak-badges">
              <span className="streak-badge">
                {getAchievementText(streak)}
              </span>
              <span className="streak-bonus small text-success">
                {getBonusPointsText(streak)}
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ScoreDisplay; 