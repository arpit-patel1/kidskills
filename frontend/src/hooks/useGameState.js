import { useState, useEffect } from 'react';
import * as api from '../services/api';

const QUESTIONS_PER_GAME = 5;

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
  }, [settings.subject]);
  
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
    fetchQuestion();
  };
  
  // Fetch a new question
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
  
  // Handle answer submission
  const handleAnswer = async (answer) => {
    if (!currentQuestion || !selectedPlayer) return;
    
    // Store the selected answer
    setSelectedAnswer(answer);
    
    try {
      setLoading(true);
      setError('');
      
      console.log("Submitting answer:", answer);
      const result = await api.submitAnswer(
        selectedPlayer.id,
        currentQuestion.id,
        answer
      );
      console.log("API response:", result);
      
      // Update score and streak
      setQuestionCount(prevCount => prevCount + 1);
      
      // Make sure is_correct is a boolean
      const isCorrect = result.is_correct === true || result.is_correct === "true";
      
      // Only show confetti and update score/streak for correct answers
      if (isCorrect) {
        console.log("Answer is correct! Showing confetti.");
        setScore(prevScore => prevScore + 1);
        setStreak(prevStreak => prevStreak + 1);
        setShowConfetti(true);
        
        // Hide confetti after 5 seconds
        setTimeout(() => {
          setShowConfetti(false);
        }, 5000);
      } else {
        // For incorrect answers, reset streak and ensure NO confetti
        console.log("Answer is incorrect. No confetti.");
        setStreak(0);
        setShowConfetti(false);
      }
      
      // Set feedback but keep the current question displayed
      setFeedback(result);
      
      // Pre-fetch the next question in the background
      try {
        console.log("Pre-fetching next question...");
        await api.getQuestion(
          selectedPlayer.id,
          settings.subject,
          settings.sub_activity,
          settings.difficulty
        );
        console.log("Next question pre-fetched");
      } catch (err) {
        console.error("Failed to pre-fetch next question:", err);
      }
      
    } catch (err) {
      setError('Failed to submit answer. Please try again.');
      console.error(err);
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
  
  // Reset entire game
  const resetGame = () => {
    resetGameState();
    setSelectedPlayer(null);
  };
  
  return {
    // State
    players,
    selectedPlayer,
    settings,
    currentQuestion,
    feedback,
    selectedAnswer,
    score,
    questionCount,
    streak,
    showConfetti,
    gameCompleted,
    loading,
    error,
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