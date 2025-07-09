// src/api.js
const API_BASE = "http://localhost:8000";

// POST login and return token
export async function loginUser(email, password) {
  const res = await fetch(`${API_BASE}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({ username: email, password }),
  });
  return res.json();
}

// Upload file
export async function uploadFile(file) {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_BASE}/api/files/upload`, {
    method: "POST",
    body: formData,
  });
  return res.json();
}

// Ask a question
export async function askQuestion(fileId, question) {
  const res = await fetch(`${API_BASE}/api/qa/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ file_id: fileId, question }),
  });
  return res.json();
}
