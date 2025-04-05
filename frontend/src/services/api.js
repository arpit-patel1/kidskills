import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

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
export const getQuestion = async (playerId, subject, difficulty) => {
  try {
    console.log("Getting question for player:", playerId, "Subject:", subject, "Difficulty:", difficulty);
    
    const response = await api.post('/challenges/generate', {
      player_id: playerId,
      subject,
      difficulty,
      question_type: 'multiple-choice'
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

export default api; 