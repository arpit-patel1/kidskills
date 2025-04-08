import { useState, useEffect } from 'react';
import * as api from '../services/api';

export const QUESTIONS_PER_GAME = 100;

// Define mapping of subjects to sub-activities
const SUB_ACTIVITIES = {
  Math: ['Addition/Subtraction', 'Multiplication/Division', 'Word Problems', 'Mushroom Kingdom Calculations'],
  English: ['Opposites/Antonyms', 'Reading Comprehension', 'Nouns/Pronouns', 'Grammar Correction', 'Mushroom Kingdom Vocabulary']
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
    console.log("Updating settings:", { current: settings, new: newSettings });
    setSettings({ ...settings, ...newSettings });
  };
  
  // Start or restart the game
  const startGame = async (customSettings = null) => {
    try {
      // First set loading states before anything else
      setStartGameLoading(true);
      setLoading(true);
      setError('');
      
      // Use provided settings or current settings
      const gameSettings = customSettings || settings;
      console.log("Starting game with settings:", gameSettings);
      
      // Small delay to ensure loading state is visible before resetting
      await new Promise(resolve => setTimeout(resolve, 300));
      
      // Reset game state
      resetGameState();
      
      // But restore loading states that were cleared by resetGameState
      setStartGameLoading(true);
      setLoading(true);
      
      // Return early if no player selected
      if (!selectedPlayer) {
        setStartGameLoading(false);
        setLoading(false);
        return;
      }
      
      // Add a small delay to ensure state is completely cleared before fetching
      await new Promise(resolve => setTimeout(resolve, 300));
      
      console.log("After reset, using settings for API call:", gameSettings);
      
      // Now that we're sure state is reset, fetch the new question
      const question = await api.getQuestion(
        selectedPlayer.id,
        gameSettings.subject,
        gameSettings.sub_activity,
        gameSettings.difficulty
      );
      
      console.log("Question received for settings:", { 
        subject: gameSettings.subject, 
        sub_activity: gameSettings.sub_activity,
        questionSubject: question.subject,
        questionSubActivity: question.sub_activity
      });
      
      // Set current question after everything else is cleared
      setCurrentQuestion(question);
      
      // Add a small delay before removing loading states
      await new Promise(resolve => setTimeout(resolve, 300));
    } catch (err) {
      setError('Failed to load question. Please try again.');
      console.error(err);
    } finally {
      setStartGameLoading(false);
      setLoading(false);
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
        
        // Update score
        if (aiEvaluation.is_correct) {
          console.log('Correct answer! Updating score.');
          // Celebrate with confetti
          triggerConfetti();
          // Base points: 10 for correct answer
          setScore(score + 10);
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
        
        // Update score
        if (result.is_correct) {
          // Celebrate with confetti
          triggerConfetti();
          // Base points: 10 for correct answer
          setScore(score + 10);
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
    setLoadingNextQuestion(true);
    
    // Use a promise-based approach with proper state clearing
    setTimeout(async () => {
      try {
        setLoading(true);
        setError('');
        
        // First clear the old question state completely
        setFeedback(null);
        setSelectedAnswer(null);
        
        // Small delay to ensure state updates are processed
        await new Promise(resolve => setTimeout(resolve, 100));
        
        // Then fetch the new question
        const newQuestion = await api.getQuestion(
          selectedPlayer.id,
          settings.subject,
          settings.sub_activity,
          settings.difficulty
        );
        
        // Set the new question after state is cleared
        setCurrentQuestion(newQuestion);
      } catch (err) {
        setError('Failed to load question. Please try again.');
        console.error(err);
      } finally {
        setLoading(false);
        setLoadingNextQuestion(false);
      }
    }, 1000); // Reduced delay for better UX
  };
  
  // Toggle continuous mode - keeping function signature for compatibility
  // but it doesn't do anything now
  const toggleContinuousMode = () => {
    // Function kept for compatibility but does nothing
    return;
  };
  
  // Reset game state (but keep player)
  const resetGameState = () => {
    // Explicitly set each state to initial value to prevent lingering state
    setCurrentQuestion(null);
    setFeedback(null);
    setScore(0);
    setQuestionCount(0);
    setShowConfetti(false);
    setGameCompleted(false);
    setSelectedAnswer(null);
    setLoadingNextQuestion(false);
    setNextQuestionTimer(0);
    setError('');
    
    // Ensure we're not stuck in a loading state
    setLoading(false);
    setStartGameLoading(false);
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