import { useState, useEffect } from 'react';
import * as api from '../services/api';
import { SUB_ACTIVITIES, getDefaultSubActivity } from '../constants';

export const QUESTIONS_PER_GAME = 100;

const useGameState = (initialPlayer = null) => {
  // Player state
  const [players, setPlayers] = useState([]);
  const [selectedPlayer, setSelectedPlayer] = useState(initialPlayer);
  
  // Game settings
  const [settings, setSettings] = useState({
    subject: 'Math',
    sub_activity: 'Addition/Subtraction',
    difficulty: 'Easy'
  });

  // Update sub-activity when subject changes
  useEffect(() => {
    if (settings.subject) {
      // Get all valid activities for this subject
      const validSubActivities = SUB_ACTIVITIES[settings.subject] || [];
      
      // Check if current sub-activity is valid for the current subject
      const isSubActivityValid = validSubActivities.includes(settings.sub_activity);
      
      // Always log the current state for debugging
      console.log("Subject/Activity validation:", {
        subject: settings.subject, 
        subActivity: settings.sub_activity, 
        isValid: isSubActivityValid,
        validOptions: validSubActivities
      });
      
      // If not valid, set to the default sub-activity for this subject
      if (!isSubActivityValid) {
        const defaultSubActivity = getDefaultSubActivity(settings.subject);
        console.log(`Correcting invalid sub-activity "${settings.sub_activity}" to "${defaultSubActivity}" for subject "${settings.subject}"`);
        
        // Use setTimeout to ensure this runs after current render cycle
        setTimeout(() => {
          setSettings(prev => ({
            ...prev,
            sub_activity: defaultSubActivity
          }));
        }, 0);
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
      
      console.log("=== GAME START FLOW ===");
      console.log("1. Current state settings:", settings);
      console.log("2. Custom settings provided:", customSettings);
      console.log("3. Final gameSettings to use:", gameSettings);
      
      // Explicitly verify the subject and sub-activity are aligned
      const subActivitiesForSubject = SUB_ACTIVITIES[gameSettings.subject] || [];
      const isValidSubActivity = subActivitiesForSubject.includes(gameSettings.sub_activity);
      
      if (!isValidSubActivity) {
        console.warn(`MISMATCH: sub-activity "${gameSettings.sub_activity}" is not valid for subject "${gameSettings.subject}"`);
        console.warn("Valid activities for this subject are:", subActivitiesForSubject);
        
        // Force correction of the sub-activity
        const correctedSettings = {
          ...gameSettings,
          sub_activity: subActivitiesForSubject[0] || "Addition/Subtraction" // Fallback in case array is empty
        };
        
        console.log("4. CORRECTING SETTINGS to:", correctedSettings);
        
        // Update the state immediately
        setSettings(correctedSettings);
        
        // Use corrected settings for the game
        gameSettings.sub_activity = correctedSettings.sub_activity;
      } else {
        console.log("4. Subject and sub-activity are valid together");
      }
      
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
      
      console.log("5. After reset, using settings for API call:", gameSettings);
      
      // Check if the activity is Gujarati Letter Tracing
      const isGujaratiTracing = 
        gameSettings.subject === 'Gujarati' && 
        gameSettings.sub_activity === 'Letter Tracing';
        
      if (isGujaratiTracing) {
        console.log("6. Gujarati Tracing selected, skipping AI question fetch.");
        // For tracing, we don't fetch an AI question, MainContent handles rendering
        setCurrentQuestion(null); // Ensure no old question persists
      } else {
        console.log("6. Fetching new question for standard activity...");
        // Now that we're sure state is reset, fetch the new question
        const question = await api.getQuestion(
          selectedPlayer.id,
          gameSettings.subject,
          gameSettings.sub_activity,
          gameSettings.difficulty
        );
        
        console.log("7. Question received:", {
          questionId: question.id,
          subject: gameSettings.subject,
          sub_activity: gameSettings.sub_activity,
          questionSubject: question.subject,
          questionSubActivity: question.sub_activity,
          mismatch: (
            question.subject !== gameSettings.subject || 
            question.sub_activity !== gameSettings.sub_activity
          )
        });
        
        // Add player_id to the question object for later use
        question.player_id = selectedPlayer.id;
        
        // Set current question after everything else is cleared
        setCurrentQuestion(question);
      }
      
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
        console.log('Current question object:', currentQuestion);
        
        // Get the expected answer from all possible sources
        let expectedAnswer = aiEvaluation.correct_answer;
        if (!expectedAnswer && currentQuestion.answer) {
          expectedAnswer = currentQuestion.answer;
          console.log('Using currentQuestion.answer:', expectedAnswer);
        } else if (!expectedAnswer && currentQuestion.correct_answer) {
          expectedAnswer = currentQuestion.correct_answer;
          console.log('Using currentQuestion.correct_answer:', expectedAnswer);
        } else if (!expectedAnswer) {
          // For grammar correction, generate a default correct answer if all else fails
          if (isGrammarCorrection && currentQuestion.question) {
            // As a last resort, use a hardcoded correction for common issues
            const question = currentQuestion.question;
            if (question.includes(' was ') && (question.includes(' and ') || question.includes(','))) {
              expectedAnswer = question.replace(' was ', ' were ');
              console.log('Generated fallback answer for was/were:', expectedAnswer);
            } else if (question.includes(' see ')) {
              expectedAnswer = question.replace(' see ', ' sees ');
              console.log('Generated fallback answer for see/sees:', expectedAnswer);
            } else if (question.includes(' should of ')) {
              expectedAnswer = question.replace(' should of ', ' should have ');
              console.log('Generated fallback answer for should of/have:', expectedAnswer);
            } else {
              // If all else fails, just use the original question as the answer
              expectedAnswer = question;
              console.log('Using question as fallback answer:', expectedAnswer);
            }
          }
        }
        
        // Create result with the AI evaluation
        const result = {
          is_correct: aiEvaluation.is_correct,
          correct_answer: expectedAnswer,
          ai_evaluated: true,
          feedback: aiEvaluation.feedback || (aiEvaluation.is_correct ? "Correct!" : "Incorrect")
        };
        
        console.log('Final feedback result with correct_answer:', result);
        
        // Store feedback
        setFeedback(result);
        
        // Update score
        if (aiEvaluation.is_correct) {
          console.log('Correct answer! Updating score.');
          // Celebrate with confetti
          triggerConfetti();
          // Base points: 1 for correct answer
          setScore(score + 1);
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
          // Base points: 1 for correct answer
          setScore(score + 1);
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
    setShowConfetti(false); // Hide confetti when moving to next question
    
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
        
        // Add player_id to the question object for later use
        newQuestion.player_id = selectedPlayer.id;
        
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