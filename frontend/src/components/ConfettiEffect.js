import React from 'react';
import ReactConfetti from 'react-confetti';

const ConfettiEffect = ({ show, continuous = false }) => {
  if (!show) {
    return null;
  }
  
  return (
    <div className="confetti-container">
      <ReactConfetti
        width={window.innerWidth}
        height={window.innerHeight}
        numberOfPieces={1500}
        recycle={continuous}
        tweenDuration={4000}
        gravity={0.1}
        initialVelocityY={10}
        friction={0.97}
        colors={['#FF9FD5', '#ADD8E6', '#87CEEB', '#FFB6C1', '#B0E0E6', '#FFC0CB', '#1E90FF']}
      />
    </div>
  );
};

export default ConfettiEffect; 