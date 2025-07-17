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

// Knowledge Base API functions
export const getKBEntries = () => {
  return axios.get(`${API_BASE}/api/files/kb/entries`);
};

export const createKBEntry = (question, answer) => {
  return axios.post(`${API_BASE}/api/files/kb/entries`, { question, answer });
};

export const updateKBEntry = (id, question, answer) => {
  return axios.put(`${API_BASE}/api/files/kb/entries/${id}`, { question, answer });
};

export const deleteKBEntry = (id) => {
  return axios.delete(`${API_BASE}/api/files/kb/entries/${id}`);
};

// Conversations API functions
export const saveConversation = (conversation) => {
  return axios.post(`${API_BASE}/api/conversations`, conversation);
};

export const getUserConversations = (userId) => {
  return axios.get(`${API_BASE}/api/conversations/${userId}`);
};

// WebSocket Chat API
export const connectWebSocketChat = () => {
  return new WebSocket(`${API_BASE}/ws/chat`);
};

// WhatsApp Configuration API
export const configureWhatsApp = (config) => {
  return axios.post(`${API_BASE}/whatsapp/configure-whatsapp`, config);
};

// WhatsApp Message Sending API
export const sendWhatsAppMessage = (message) => {
  return axios.post(`${API_BASE}/whatsapp/send-message`, message);
};
