# 🧠 Knowledge Base + Gemini AI Integration

## Overview
Your AI assistant now uses uploaded documents as its knowledge base and responds using Google's Gemini API. When users chat with the widget, the system:

1. **Searches uploaded documents** using vector embeddings
2. **Finds relevant content** using semantic similarity 
3. **Generates responses** using Gemini AI based on the found context
4. **Provides accurate, contextual answers** based on your uploaded files

---

## 🚀 How It Works

### 1. **Document Upload Process**
```
PDF/TXT/CSV/JSON Files → Text Extraction → Chunking → Vector Embeddings → FAISS Index
```

When you upload files through the admin dashboard:
- Files are saved in client-specific folders (`uploads/{client_id}/`)
- Text content is extracted from all file types
- Content is split into searchable chunks
- Vector embeddings are generated using SentenceTransformers
- Embeddings are stored in FAISS index files (`vector_stores/{client_id}_{filename}.index`)

### 2. **Chat Response Process**
```
User Question → Vector Search → Relevant Context → Gemini AI → Response
```

When a user asks a question:
- The question is converted to a vector embedding
- System searches through uploaded documents for similar content
- Top 3 most relevant document chunks are found
- Context + question is sent to Gemini AI
- Gemini generates a natural response based on your documents

---

## 🔧 Technical Implementation

### **Backend Changes Made:**

1. **Enhanced RAG Service** (`services/rag.py`)
   - Integrated Google Gemini API for response generation
   - Client-specific knowledge base search
   - Proper context formatting for AI prompts

2. **Improved Vector Store** (`models/vector_store.py`)
   - Client-specific document search
   - Better error handling and logging
   - Relevance scoring for search results

3. **Updated Chat API** (`api/chat.py`)
   - Widget-specific response generation
   - Improved error handling
   - Better integration with knowledge base

4. **File Upload Enhancement** (`api/files.py`)
   - Client-specific file storage and embeddings
   - Support for multiple file formats
   - Automatic vector index generation

### **Configuration:**
- **Gemini API Key**: Set in `backend/.env` file
- **Vector Storage**: FAISS indexes in `vector_stores/` directory
- **File Storage**: Client-specific folders in `uploads/` directory

---

## 📝 API Endpoints

### **Upload Knowledge Base**
```
POST /api/files/widget/upload/{client_id}
```
Upload documents for a specific widget client.

### **Widget Chat**
```
POST /api/chat/widget
```
Send chat messages that use the uploaded knowledge base.

---

## 🎯 User Experience

### **For Administrators:**
1. **Upload Documents**: Use the Knowledge Base tab in the admin dashboard
2. **Train Examples**: Add Q&A examples to improve response quality
3. **Test Search**: Use semantic search to verify document understanding
4. **Monitor Status**: View processed files and embedding status

### **For End Users:**
1. **Natural Conversations**: Ask questions in plain language
2. **Accurate Responses**: Get answers based on your uploaded documents
3. **Source Attribution**: Responses indicate which documents were used
4. **Fallback Handling**: Graceful responses when information isn't available

---

## 🔍 Testing the Integration

### **1. Upload Test Documents**
- Navigate to admin dashboard → Knowledge Base tab
- Upload a few PDF/TXT files with relevant information
- Verify files show as "processed" with embeddings generated

### **2. Test Chat Widget**
- Open the demo website with embedded chat widget
- Ask questions related to uploaded documents
- Verify responses reference the uploaded content

### **3. Debug Logging**
Check backend logs for:
```
🔄 Processing file: document.pdf
✅ Generated embeddings with 15 chunks
🔍 Searching vector store for query: What is your return policy?
🤖 Generated response using Gemini API
```

---

## ⚙️ Configuration Guide

### **Environment Variables (.env)**
```bash
GEMINI_API_KEY=your_gemini_api_key_here
DATABASE_URL=sqlite:///./fullstack_kb.db
JWT_SECRET_KEY=your-secret-key-here
```

### **Required Dependencies**
```bash
pip install python-dotenv==1.0.0
pip install google-generativeai==0.3.2
```

### **Directory Structure**
```
backend/
├── vector_stores/           # FAISS embedding indexes
├── uploads/                 # Uploaded documents
│   └── {client_id}/         # Client-specific files
├── services/rag.py          # AI response generation
├── models/vector_store.py   # Vector search functionality
└── .env                     # Environment configuration
```

---

## 🐛 Troubleshooting

### **Common Issues:**

1. **"No knowledge base files found"**
   - Upload documents through admin dashboard
   - Check `vector_stores/` directory for .index files
   - Verify file upload was successful

2. **"API key not configured"**
   - Add `GEMINI_API_KEY` to `backend/.env` file
   - Restart the backend server
   - Check API key is valid on Google AI Studio

3. **Poor response quality**
   - Add more Q&A training examples
   - Upload more comprehensive documents
   - Test semantic search to verify document understanding

4. **Vector search errors**
   - Check `uploads/` directory has files
   - Verify FAISS indexes exist in `vector_stores/`
   - Check backend logs for embedding generation errors

### **Debug Commands:**
```bash
# Test knowledge base integration
python test_kb_integration.py

# Check uploaded files
ls -la uploads/

# Check vector indexes
ls -la vector_stores/

# View backend logs
tail -f backend.log
```

---

## 🚀 Next Steps

### **Enhancement Opportunities:**
1. **Advanced Search**: Implement hybrid search (vector + keyword)
2. **Multi-Language**: Add support for multiple languages
3. **Document Types**: Support for more file formats (DOCX, PPTX)
4. **Analytics**: Track which documents are most useful
5. **Fine-Tuning**: Custom model training on specific domains

### **Scaling Considerations:**
1. **Vector Database**: Migrate to Pinecone/Weaviate for larger datasets
2. **Caching**: Implement response caching for common queries
3. **Load Balancing**: Distribute AI requests across multiple endpoints
4. **Monitoring**: Add comprehensive performance monitoring

---

## ✅ Success Criteria

Your knowledge base integration is working correctly when:

- ✅ Documents upload successfully and generate embeddings
- ✅ Chat responses reference uploaded content
- ✅ Semantic search finds relevant information
- ✅ AI responses are contextual and accurate
- ✅ Different clients have separate knowledge bases
- ✅ Backend logs show successful vector searches and API calls

---

**🎉 Congratulations! Your AI assistant now has a brain powered by your documents and Gemini AI!**
