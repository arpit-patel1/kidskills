import axios from 'axios';

// Get the hostname of the current page
const hostname = window.location.hostname;
// Use the hostname to create a dynamic API URL that works across the network
const API_URL = `http://${hostname}:8000/api`;

// Create axios instance with base configuration
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Utility to debug response values and types
const debugResponseValues = (data) => {
  const result = {};
  for (const key in data) {
    const value = data[key];
    result[key] = {
      value,
      type: typeof value,
      stringValue: String(value)
    };
  }
  return result;
};

// Error handler
const handleError = (error) => {
  console.error('API Error:', error);
  
  if (error.response) {
    // Server responded with an error status
    throw new Error(error.response.data.detail || 'An error occurred with the server.');
  } else if (error.request) {
    // No response received
    throw new Error('No response from server. Please check your connection.');
  } else {
    // Error in request setup
    throw new Error('Error setting up the request: ' + error.message);
  }
};

// Get all players
export const getPlayers = async () => {
  try {
    const response = await api.get('/players');
    return response.data;
  } catch (error) {
    return handleError(error);
  }
};

// Get a challenge question
export const getQuestion = async (playerId, subject, sub_activity, difficulty) => {
  try {
    console.log("Getting question for player:", playerId, "Subject:", subject, "Sub-activity:", sub_activity, "Difficulty:", difficulty);
    
    // Determine question type based on sub_activity
    let question_type = 'multiple-choice';
    if (sub_activity === 'Grammar Correction') {
      question_type = 'direct-answer';
    } else if (sub_activity === 'Reading Comprehension') {
      question_type = 'reading-comprehension';
    }
    
    // Add a timestamp to ensure we don't get cached responses
    const timestamp = new Date().getTime();
    
    const response = await api.post('/challenges/generate', {
      player_id: playerId,
      subject,
      sub_activity,
      difficulty,
      question_type,
      timestamp
    });
    
    console.log("New question received:", response.data);
    console.log("Question debug info:", debugResponseValues(response.data));
    return response.data;
  } catch (error) {
    return handleError(error);
  }
};

// Submit an answer
export const submitAnswer = async (playerId, questionId, answer) => {
  try {
    console.log("Submitting to API - Player:", playerId, "Question:", questionId, "Answer:", answer);
    
    const response = await api.post('/challenges/submit', {
      player_id: playerId,
      question_id: questionId,
      answer
    });
    
    // Log the raw response
    console.log("Raw API response from submit:", response.data);
    console.log("Response debug info:", debugResponseValues(response.data));
    
    // Create a copy of the response.data and force is_correct to be a boolean
    const result = {
      ...response.data,
      is_correct: Boolean(response.data.is_correct)
    };
    
    console.log("Processed response with boolean conversion:", result);
    return result;
  } catch (error) {
    return handleError(error);
  }
};

// Create a new player
export const createPlayer = async (playerData) => {
  try {
    const response = await api.post('/players', playerData);
    return response.data;
  } catch (error) {
    return handleError(error);
  }
};

// Update player data
export const updatePlayer = async (playerId, playerData) => {
  try {
    const response = await api.put(`/players/${playerId}`, playerData);
    return response.data;
  } catch (error) {
    return handleError(error);
  }
};

// Get player stats
export const getPlayerStats = async (playerId) => {
  try {
    const response = await api.get(`/players/${playerId}/stats`);
    return response.data;
  } catch (error) {
    return handleError(error);
  }
};

// Delete a player
export const deletePlayer = async (playerId) => {
  try {
    await api.delete(`/players/${playerId}`);
    return true; // Successfully deleted
  } catch (error) {
    return handleError(error);
  }
};

// Get grammar feedback
export const getGrammarFeedback = async (question, userAnswer, correctAnswer, isCorrect) => {
  try {
    console.log("Getting grammar feedback for:", {
      question,
      user_answer: userAnswer,
      correct_answer: correctAnswer,
      is_correct: isCorrect
    });
    
    const response = await api.post('/grammar/feedback', {
      question,
      user_answer: userAnswer,
      correct_answer: correctAnswer,
      is_correct: isCorrect
    });
    
    console.log("Grammar feedback response:", response.data);
    return response.data;
  } catch (error) {
    console.error("Error getting grammar feedback:", error);
    // Provide fallback feedback
    return {
      feedback: isCorrect
        ? "Great job correcting the sentence!"
        : "Good try! Look at the sentence structure and try again."
    };
  }
};

// Evaluate grammar correction answer using AI
export const evaluateGrammarCorrection = async (question, userAnswer, correctAnswer, playerId) => {
  try {
    console.log("Evaluating grammar correction answer:", {
      question,
      user_answer: userAnswer,
      correct_answer: correctAnswer,
      player_id: playerId
    });
    
    const startTime = Date.now();
    
    // Create request payload 
    const payload = {
      question,
      user_answer: userAnswer,
      correct_answer: correctAnswer
    };
    
    // Only add player_id if it's not null or undefined
    if (playerId !== null && playerId !== undefined) {
      payload.player_id = playerId;
    }
    
    console.log("Sending request payload:", payload);
    
    // Add artificial delay of 1 second to make loading more visible
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    const response = await api.post('/grammar/evaluate', payload);
    
    const duration = Date.now() - startTime;
    console.log(`Grammar correction evaluation completed in ${duration}ms`);
    console.log("Grammar correction evaluation response:", response.data);
    return response.data;
  } catch (error) {
    console.error("Error evaluating grammar correction:", error);
    console.error("Error response:", error.response ? error.response.data : "No response data");
    console.error("Request details:", {
      question,
      user_answer: userAnswer,
      correct_answer: correctAnswer,
      player_id: playerId
    });
    
    // Provide fallback evaluation - simple string comparison
    const isCorrect = userAnswer.toLowerCase().trim() === correctAnswer.toLowerCase().trim();
    return {
      is_correct: isCorrect,
      feedback: isCorrect
        ? "Great job! You fixed the grammar error correctly."
        : "Good try! Check the sentence structure again."
    };
  }
};

// Evaluate reading comprehension answer using AI
export const evaluateReadingComprehension = async (passage, question, userAnswer, correctAnswer) => {
  try {
    console.log("Evaluating reading comprehension answer:", {
      passage,
      question,
      user_answer: userAnswer,
      correct_answer: correctAnswer
    });
    
    const response = await api.post('/reading/evaluate', {
      passage,
      question,
      user_answer: userAnswer,
      correct_answer: correctAnswer
    });
    
    console.log("Reading comprehension evaluation response:", response.data);
    return response.data;
  } catch (error) {
    console.error("Error evaluating reading comprehension:", error);
    // Provide fallback evaluation - simple string comparison
    const isCorrect = userAnswer.toLowerCase().trim() === correctAnswer.toLowerCase().trim();
    return {
      is_correct: isCorrect,
      feedback: isCorrect
        ? "Great job! Your answer shows good understanding of the passage."
        : "Good try! Re-read the passage carefully to find the correct answer."
    };
  }
};

export default api; 