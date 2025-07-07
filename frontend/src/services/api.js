// src/services/api.js
import axios from 'axios';

// Use relative paths for proxy support
const API_BASE = '';

export const uploadFile = (formData) => {
  return axios.post(`${API_BASE}/api/files/upload`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
};

export const askQuestion = (question, fileId) => {
  return axios.post(`${API_BASE}/api/qa/ask`, { question, file_id: fileId });
};

export const generateToken = (userId) => {
  return axios.post(`${API_BASE}/api/auth/token`, { user_id: userId });
};

export const startTraining = () => {
  return axios.post(`${API_BASE}/api/training/start-training/`);
};
