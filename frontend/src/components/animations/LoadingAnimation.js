import React, { useState, useEffect } from 'react';

// Themed loading animations based on subject
const LoadingAnimation = ({ subject, isVisible, previousQuestion = null }) => {
  const [animationKey, setAnimationKey] = useState(0);
  
  // Randomly select a different animation each time it's shown
  useEffect(() => {
    if (isVisible) {
      setAnimationKey(Math.floor(Math.random() * 3)); // 0, 1, or 2
    }
  }, [isVisible]);
  
  if (!isVisible) return null;

  // Different animations based on subject
  const renderAnimation = () => {
    if (subject === 'Math') {
      return mathAnimations[animationKey];
    } else if (subject === 'English') {
      return englishAnimations(previousQuestion)[animationKey];
    } else if (subject === 'Mario') {
      return marioAnimations[animationKey];
    } else {
      return defaultAnimation;
    }
  };

  return (
    <div className="loading-animation-container">
      {renderAnimation()}
    </div>
  );
};

// Math animations
const mathAnimations = [
  // Animation 1: Dancing numbers
  <div key="math-1" className="math-animation numbers-dance">
    {[1, 2, 3, 4, 5, 6, 7, 8, 9].map((num, i) => (
      <div 
        key={i} 
        className="animated-number"
        style={{ 
          animationDelay: `${i * 0.1}s`,
          color: ['#FF9FD5', '#1E90FF', '#87CEEB'][i % 3]
        }}
      >
        {num}
      </div>
    ))}
  </div>,
  
  // Animation 2: Math symbols
  <div key="math-2" className="math-animation symbols-spin">
    {['+', '-', '×', '÷', '=', '%'].map((symbol, i) => (
      <div 
        key={i} 
        className="animated-symbol"
        style={{ 
          animationDelay: `${i * 0.2}s`,
          transform: `rotate(${i * 60}deg) translateX(50px)`,
          color: ['#FF9FD5', '#1E90FF', '#FFB6C1', '#87CEEB', '#B0E0E6', '#FFC0CB'][i]
        }}
      >
        {symbol}
      </div>
    ))}
    <div className="center-circle"></div>
  </div>,
  
  // Animation 3: Calculator
  <div key="math-3" className="math-animation calculator">
    <div className="calculator-display">
      <div className="calculator-digits">
        <span className="digit">1</span>
        <span className="digit">2</span>
        <span className="digit">3</span>
        <span className="digit">...</span>
      </div>
    </div>
    <div className="calculator-buttons">
      {[1, 2, 3, '+', 4, 5, 6, '-', 7, 8, 9, '×', 0, '=', 'C', '÷'].map((btn, i) => (
        <div key={i} className={`calculator-button ${typeof btn === 'string' && !['C', '='].includes(btn) ? 'operator' : ''}`}>
          {btn}
        </div>
      ))}
    </div>
  </div>
];

// English animations - converted to a function to accept previousQuestion
const englishAnimations = (previousQuestion) => [
  // Animation 1: Floating letters
  <div key="english-1" className="english-animation letters-float">
    {['A', 'B', 'C', 'D', 'E', 'F', 'G'].map((letter, i) => (
      <div 
        key={i} 
        className="animated-letter"
        style={{ 
          animationDelay: `${i * 0.15}s`,
          color: ['#FF9FD5', '#1E90FF', '#87CEEB', '#FFB6C1', '#B0E0E6', '#FFC0CB', '#ADD8E6'][i]
        }}
      >
        {letter}
      </div>
    ))}
  </div>,
  
  // Animation 2: Open book
  <div key="english-2" className="english-animation book">
    <div className="book-cover"></div>
    <div className="book-pages">
      <div className="book-page left-page">
        <div className="page-line"></div>
        <div className="page-line"></div>
        <div className="page-line"></div>
        <div className="page-line"></div>
      </div>
      <div className="book-page right-page">
        <div className="page-line"></div>
        <div className="page-line"></div>
        <div className="page-line"></div>
        <div className="page-line"></div>
      </div>
    </div>
  </div>,
  
  // Animation 3: Sentence building - uses words from the previous question if available
  <div key="english-3" className="english-animation sentence-build">
    {getAnimationWords(previousQuestion).map((word, i) => (
      <div 
        key={i} 
        className="word" 
        style={{ 
          animationDelay: `${i * 0.3}s`,
          backgroundColor: ['#ADD8E6', '#FFB6C1', '#B0E0E6', '#FFFFE0', '#E6E6FA', '#FFDAB9', '#E0FFFF', '#FFE4E1', '#F0FFF0', '#FFF0F5'][i % 10]
        }}
      >
        {word}
      </div>
    ))}
  </div>
];

// Helper function to extract words from the previous question
const getAnimationWords = (question) => {
  if (!question || !question.question) {
    // Fallback to default sentence
    return ["The", "quick", "fox", "jumps...", "over", "the", "lazy", "dog", "in", "style"];
  }

  // Split the question into words and filter out punctuation
  const words = question.question
    .split(/\s+/)
    .filter(word => word.length > 0)
    .map(word => word.replace(/[.,?!;:()]/g, ''));
  
  // Take up to 10 significant words (longer than 2 characters)
  const significantWords = words.filter(word => word.length > 2).slice(0, 10);
  
  // If we don't have enough significant words, use what we have
  // and fill remaining slots with words from the start of the question
  if (significantWords.length < 10 && words.length > significantWords.length) {
    const additionalWords = words
      .filter(word => !significantWords.includes(word))
      .slice(0, 10 - significantWords.length);
    return [...significantWords, ...additionalWords];
  }
  
  return significantWords.length >= 2 ? significantWords : words.slice(0, 10);
};

// Mario animations
const marioAnimations = [
  // Animation 1: Coin collection
  <div key="mario-1" className="mario-animation coins">
    {[...Array(8)].map((_, i) => (
      <div 
        key={i} 
        className="mario-coin"
        style={{ animationDelay: `${i * 0.2}s` }}
      >
        <div className="coin-inner">&#9733;</div>
      </div>
    ))}
  </div>,
  
  // Animation 2: Character jump
  <div key="mario-2" className="mario-animation character-jump">
    <div className="mario-character">M</div>
    <div className="mario-ground"></div>
  </div>,
  
  // Animation 3: Mushroom growth
  <div key="mario-3" className="mario-animation mushroom-grow">
    <div className="mushroom-cap"></div>
    <div className="mushroom-stem"></div>
  </div>
];

// Default animation for any other subject
const defaultAnimation = (
  <div key="default" className="default-animation">
    <div className="spinner"></div>
    <div className="loading-text">Checking answer...</div>
  </div>
);

export default LoadingAnimation; 