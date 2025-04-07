import { useState, useEffect } from 'react';
import * as api from '../services/api';

export const QUESTIONS_PER_GAME = 100;

// Define mapping of subjects to sub-activities
const SUB_ACTIVITIES = {
  Math: ['Addition/Subtraction', 'Multiplication/Division', 'Word Problems'],
  English: ['Opposites/Antonyms', 'Reading Comprehension', 'Nouns/Pronouns', 'Grammar Correction']
};

// Get default sub-activity for a subject
const getDefaultSubActivity = (subject) => {
  const subjectKey = subject.charAt(0).toUpperCase() + subject.slice(1).toLowerCase();
  return SUB_ACTIVITIES[subjectKey]?.[0] || 'Addition/Subtraction';
};

const useGameState = () => {
  // Player state
  const [players, setPlayers] = useState([]);
  const [selectedPlayer, setSelectedPlayer] = useState(null);
  
  // Game settings
  const [settings, setSettings] = useState({
    subject: 'Math',
    sub_activity: 'Addition/Subtraction',
    difficulty: 'Easy'
  });

  // Update sub-activity when subject changes
  useEffect(() => {
    if (settings.subject) {
      const defaultSubActivity = getDefaultSubActivity(settings.subject);
      if (settings.sub_activity !== defaultSubActivity && 
          !SUB_ACTIVITIES[settings.subject]?.includes(settings.sub_activity)) {
        setSettings(prev => ({
          ...prev,
          sub_activity: defaultSubActivity
        }));
      }
    }
  }, [settings.subject, settings.sub_activity]);
  
  // Game state
  const [currentQuestion, setCurrentQuestion] = useState(null);
  const [feedback, setFeedback] = useState(null);
  const [score, setScore] = useState(0);
  const [questionCount, setQuestionCount] = useState(0);
  const [streak, setStreak] = useState(0);
  const [showConfetti, setShowConfetti] = useState(false);
  const [gameCompleted, setGameCompleted] = useState(false);
  const [selectedAnswer, setSelectedAnswer] = useState(null);
  
  // UI state
  const [loading, setLoading] = useState(false);
  const [startGameLoading, setStartGameLoading] = useState(false);
  const [error, setError] = useState('');
  
  // Next question loading state
  const [loadingNextQuestion, setLoadingNextQuestion] = useState(false);
  const [nextQuestionTimer, setNextQuestionTimer] = useState(0);
  
  // Timer effect for next question loading animation
  useEffect(() => {
    let timerInterval;
    
    if (loadingNextQuestion) {
      timerInterval = setInterval(() => {
        setNextQuestionTimer(prev => prev + 1);
      }, 1000);
    } else {
      setNextQuestionTimer(0);
    }
    
    return () => {
      if (timerInterval) clearInterval(timerInterval);
    };
  }, [loadingNextQuestion]);
  
  // Fetch players on component mount
  useEffect(() => {
    fetchPlayers();
  }, []);
  
  // Fetch players function
  const fetchPlayers = async () => {
    try {
      const data = await api.getPlayers();
      setPlayers(data);
    } catch (err) {
      setError('Failed to load players. Please try again.');
      console.error(err);
    }
  };
  
  // Player selection
  const selectPlayer = (player) => {
    setSelectedPlayer(player);
    // Reset game state when player changes
    if (selectedPlayer !== player) {
      resetGameState();
    }
  };
  
  // Update game settings
  const updateSettings = (newSettings) => {
    setSettings({ ...settings, ...newSettings });
  };
  
  // Start or restart the game
  const startGame = async () => {
    resetGameState();
    
    if (!selectedPlayer) return;
    
    try {
      setStartGameLoading(true);
      setLoading(true); // Also set regular loading for MainContent indicator
      setError('');
      
      const question = await api.getQuestion(
        selectedPlayer.id,
        settings.subject,
        settings.sub_activity,
        settings.difficulty
      );
      
      setCurrentQuestion(question);
    } catch (err) {
      setError('Failed to load question. Please try again.');
      console.error(err);
    } finally {
      setStartGameLoading(false);
      setLoading(false); // Clear loading state
    }
  };
  
  // Fetch a new question
  // eslint-disable-next-line no-unused-vars
  const fetchQuestion = async () => {
    if (!selectedPlayer) return;
    
    try {
      setLoading(true);
      setError('');
      
      const question = await api.getQuestion(
        selectedPlayer.id,
        settings.subject,
        settings.sub_activity,
        settings.difficulty
      );
      
      setCurrentQuestion(question);
    } catch (err) {
      setError('Failed to load question. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
      setLoadingNextQuestion(false);
    }
  };
  
  // Function to show confetti for correct answers
  const triggerConfetti = () => {
    console.log('Showing confetti for correct answer');
    setShowConfetti(true);
    setTimeout(() => {
      setShowConfetti(false);
    }, 3000);
  };
  
  // Handle answer submission
  const handleAnswer = async (answer, aiEvaluation = null) => {
    if (!currentQuestion || !selectedPlayer) {
      console.error('Cannot submit answer: Missing currentQuestion or selectedPlayer');
      return;
    }
    
    console.log('handleAnswer called with:', { answer, hasAiEval: !!aiEvaluation });
    
    // Immediately mark as submitted
    setSelectedAnswer(answer);
    
    const isGrammarCorrection = currentQuestion.sub_activity === 'Grammar Correction';
    const isReadingComprehension = currentQuestion.sub_activity === 'Reading Comprehension';
    
    try {
      // If we have AI evaluation, use it directly instead of calling the API
      if ((isGrammarCorrection || isReadingComprehension) && aiEvaluation) {
        console.log('Using AI evaluation result:', aiEvaluation);
        
        // Create result with the AI evaluation
        const result = {
          is_correct: aiEvaluation.is_correct,
          correct_answer: currentQuestion.answer,
          ai_evaluated: true,
          feedback: aiEvaluation.feedback || (aiEvaluation.is_correct ? "Correct!" : "Incorrect")
        };
        
        // Store feedback
        setFeedback(result);
        
        // Update streak and score
        if (aiEvaluation.is_correct) {
          console.log('Correct answer! Updating score and streak.');
          setStreak(streak + 1);
          // Celebrate with confetti
          triggerConfetti();
          // Update score with enhanced streak bonuses for 1000-question game
          // Base points: 10 for correct answer
          // Enhanced bonus structure:
          // - 5 points for streaks of 3-4
          // - 10 points for streaks of 5-9
          // - 15 points for streaks of 10-14
          // - 20 points for streaks of 15+
          let streakBonus = 0;
          if (streak >= 2 && streak < 4) {
            streakBonus = 5;
          } else if (streak >= 4 && streak < 9) {
            streakBonus = 10;
          } else if (streak >= 9 && streak < 14) {
            streakBonus = 15;
          } else if (streak >= 14) {
            streakBonus = 20;
          }
          setScore(score + 10 + streakBonus);
        } else {
          console.log('Incorrect answer. Resetting streak.');
          setStreak(0);
        }
        
        // Update question count
        setQuestionCount(questionCount + 1);
        
        // Check if game is completed
        if (questionCount + 1 >= QUESTIONS_PER_GAME) {
          setGameCompleted(true);
        }
      } else {
        // For answers that didn't get AI evaluation, submit normally
        console.log('Submitting answer through API:', answer);
        setLoading(true);
        
        const result = await api.submitAnswer(
          selectedPlayer.id,
          currentQuestion.id,
          answer
        );
        
        console.log('API submission result:', result);
        
        // Store feedback
        setFeedback(result);
        
        // Update streak and score
        if (result.is_correct) {
          setStreak(streak + 1);
          // Celebrate with confetti
          triggerConfetti();
          // Update score with enhanced streak bonuses for 1000-question game
          // Base points: 10 for correct answer
          // Enhanced bonus structure:
          // - 5 points for streaks of 3-4
          // - 10 points for streaks of 5-9
          // - 15 points for streaks of 10-14
          // - 20 points for streaks of 15+
          let streakBonus = 0;
          if (streak >= 2 && streak < 4) {
            streakBonus = 5;
          } else if (streak >= 4 && streak < 9) {
            streakBonus = 10;
          } else if (streak >= 9 && streak < 14) {
            streakBonus = 15;
          } else if (streak >= 14) {
            streakBonus = 20;
          }
          setScore(score + 10 + streakBonus);
        } else {
          setStreak(0);
        }
        
        // Update question count
        setQuestionCount(questionCount + 1);
        
        // Check if game is completed
        if (questionCount + 1 >= QUESTIONS_PER_GAME) {
          setGameCompleted(true);
        }
      }
    } catch (error) {
      console.error('Error submitting answer:', error);
      setError('Failed to submit answer. Please try again.');
    } finally {
      setLoading(false);
    }
  };
  
  // Move to next question
  const nextQuestion = () => {
    setLoadingNextQuestion(true); // Show loading spinner with timer
    
    // Keep the current question and feedback visible but disabled
    // We'll fetch the new question after a delay, but don't clear the current question yet
    setTimeout(async () => {
      try {
        setLoading(true);
        setError('');
        
        const newQuestion = await api.getQuestion(
          selectedPlayer.id,
          settings.subject,
          settings.sub_activity,
          settings.difficulty
        );
        
        // Clear the old data and set the new question only after we have it
        setFeedback(null);
        setSelectedAnswer(null);
        setCurrentQuestion(newQuestion);
      } catch (err) {
        setError('Failed to load question. Please try again.');
        console.error(err);
      } finally {
        setLoading(false);
        setLoadingNextQuestion(false);
      }
    }, 2000);
  };
  
  // Toggle continuous mode - keeping function signature for compatibility
  // but it doesn't do anything now
  const toggleContinuousMode = () => {
    // Function kept for compatibility but does nothing
    return;
  };
  
  // Reset game state (but keep player)
  const resetGameState = () => {
    setCurrentQuestion(null);
    setFeedback(null);
    setScore(0);
    setQuestionCount(0);
    setStreak(0);
    setShowConfetti(false);
    setGameCompleted(false);
    setSelectedAnswer(null);
    setLoadingNextQuestion(false);
    setNextQuestionTimer(0);
    setError('');
  };
  
  // Reset entire game - modified to keep the selected player by default
  const resetGame = (resetPlayer = false) => {
    resetGameState();
    if (resetPlayer) {
      setSelectedPlayer(null);
    }
  };
  
  return {
    // State
    players,
    selectedPlayer,
    settings,
    currentQuestion,
    loading,
    startGameLoading,
    error,
    feedback,
    selectedAnswer,
    score,
    questionCount,
    streak,
    showConfetti,
    gameCompleted,
    loadingNextQuestion,
    nextQuestionTimer,
    
    // Actions
    selectPlayer,
    updateSettings,
    startGame,
    handleAnswer,
    nextQuestion,
    toggleContinuousMode,
    resetGameState,
    resetGame,
    fetchPlayers,
  };
};

export default useGameState; 