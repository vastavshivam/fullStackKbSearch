# 🤖 AI Support Assistant

A full-stack AI-powered support assistant platform, inspired by Bird.com, that allows users to:

- Upload support files (.csv, .json, .txt)
- Automatically fine-tune and embed document data
- Chat with an AI assistant in real time using WebSocket
- Perform semantic search using vector similarity
- Manage authentication and training logs

---

## 📁 Project Structure
├── backend/ # FastAPI + Transformers + Vector DB
│ ├── api/
│ │ ├── files.py # File upload and preview
│ │ ├── qa.py # /ask question route
│ ├── utils/
│ │ ├── file_parser.py # File content parsing
│ │ ├── embed_store.py # FAISS/Chroma vector storage
│ │ └── email_notify.py # Training complete notification
│ └── main.py # FastAPI app entry
│
├── frontend/ # React + WebSocket + Tailwind UI
│ ├── src/
│ │ ├── components/ # Chat, Upload, Dashboard UI
│ │ ├── pages/ # Home, Login, Admin routes
│ │ ├── services/ # Axios + WebSocket services
│ │ ├── context/ # AuthContext for JWT
│ │ └── App.jsx # Routing + Layout


---

## 🚀 Features

- ✅ JWT-based login (FastAPI + React)
- ✅ File upload + preview (`.csv`, `.json`, `.txt`)
- ✅ File-to-chunks + embeddings via SentenceTransformers
- ✅ Store embeddings in FAISS or ChromaDB
- ✅ Real-time WebSocket chat (`/ws/chat`)
- ✅ Context-aware AI replies (Falcon, Mistral, etc.)
- ✅ Training trigger + email notification
- ✅ TailwindCSS-based responsive UI

---

## ⚙️ Setup Instructions

### 1. Backend (FastAPI)

```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn main:app --reload
MODEL_NAME=tiiuae/falcon-rw-1b
REDIS_URL=redis://localhost:6379
JWT_SECRET=your-secret-key

2. Frontend (React)
cd frontend
npm install
npm start

Environment file .env.local:

VITE_API_BASE=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws/chat

📬 API Overview
🔐 Auth


POST /auth/token
{ "user_id": "shivam" }
📤 File Upload


POST /upload
form-data: file

💬 Chat WebSocket
/ws/chat?token=<JWT_TOKEN>
❓ Ask a Question

POST /ask
{
  "question": "How to reset my order?",
  "file_id": "faq.csv"
}
🧠 Model & Tools
HuggingFace: Falcon, Mistral (via Transformers)

SentenceTransformers: For embedding chunks

ChromaDB / FAISS: Local vector search

LangChain: Memory for chat sessions

WebSocket: Streaming chat via FastAPI + React

📸 UI Preview

👨‍💻 Developed By
Shivam Srivastav
AI Engineer & Full Stack Developer
Email: shivam.s@appgallop.com
