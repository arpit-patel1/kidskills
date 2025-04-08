import React from 'react';
import '../styles/animations.css';
import { FaStar, FaCheck, FaBolt, FaMagic, FaCrown, FaHeart, FaSparkles } from 'react-icons/fa';

const ThemedLoader = ({ message = "Getting the next question ready..." }) => {
  return (
    <div className="loading-animation-container">
      <div className="theme-spinner" style={{ width: '80px', height: '80px', margin: '0 auto 30px' }}></div>
      
      <div className="floating-icons" style={{ position: 'relative', width: '300px', height: '100px' }}>
        <div className="icon" style={{ color: 'var(--theme-pink)', fontSize: '32px' }}><FaStar /></div>
        <div className="icon" style={{ color: 'var(--theme-powder-blue)', fontSize: '32px' }}><FaCheck /></div>
        <div className="icon" style={{ color: 'var(--theme-darker-pink)', fontSize: '32px' }}><FaBolt /></div>
        <div className="icon" style={{ color: 'var(--theme-darker-blue)', fontSize: '32px' }}><FaMagic /></div>
        <div className="icon" style={{ color: 'var(--theme-pink)', fontSize: '32px' }}><FaCrown /></div>
      </div>
      
      <div className="loading-message" style={{ 
        fontSize: '1.8rem', 
        background: 'linear-gradient(45deg, var(--theme-pink), var(--theme-powder-blue))',
        backgroundSize: '200% auto',
        WebkitBackgroundClip: 'text',
        WebkitTextFillColor: 'transparent',
        animation: 'text-shine 2s linear infinite',
        fontWeight: 'bold',
        marginTop: '20px',
        filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.3))'
      }}>
        {message}
      </div>
    </div>
  );
};

export default ThemedLoader; 