// src/services/api.js
import axios from "axios";

const API_BASE = "http://localhost:8000"; // FastAPI base URL

export const uploadFile = (formData) => {
  return axios.post(`${API_BASE}/api/files/upload`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
};

export const askQuestion = (question, fileId) => {
  return axios.post(`${API_BASE}/api/qa/ask`, { question, file_id: fileId });
};

export const generateToken = (userId) => {
  return axios.post(`${API_BASE}/auth/token`, { user_id: userId });
};

export const startTraining = () => {
  return axios.post(`${API_BASE}/start-training/`);
};

// Dummy Knowledge Base API functions to resolve import errors
export const getKBEntries = () => Promise.resolve([]);
export const updateKBEntry = () => Promise.resolve();
export const createKBEntry = () => Promise.resolve();
export const deleteKBEntry = () => Promise.resolve();
