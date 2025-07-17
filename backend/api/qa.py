# api/qa.py
from fastapi import APIRouter, HTTPException, Depends
from models.schemas import AskRequest, AskResponse
# from utils.embed_store import load_index, embed_question,query_embeddings
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from rapidfuzz import fuzz
from sqlalchemy.orm import Session
from fastapi import Request

from utils.embed_store import VECTOR_DIR
from database.database import get_db
from models.db_models import ChatHistory, Conversation
import os
import json
from difflib import get_close_matches

router = APIRouter()

LLM_MODEL = "tiiuae/falcon-rw-1b"
# tokenizer = AutoTokenizer.from_pretrained(LLM_MODEL)
# model = AutoModelForCausalLM.from_pretrained(LLM_MODEL)

STATIC_DATA_PATHS = [
    os.path.join("training", "data", "fine_tune.jsonl"),
    os.path.join("training", "data", "train.jsonl"),
]

def load_static_qa():
    qa_pairs = []
    for path in STATIC_DATA_PATHS:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        item = json.loads(line)
                        qa_pairs.append({
                            "prompt": item.get("prompt", ""),
                            "response": item.get("response", "")
                        })
                    except Exception:
                        continue
    return qa_pairs

# @router.post("/ask", response_model=AskResponse)
# async def ask_question(data: AskRequest):
#     file_id = data.file_id
#     question = data.question
#
#     vector_path = os.path.join(VECTOR_DIR, f"{file_id}.index")
#     if not os.path.exists(vector_path):
#         raise HTTPException(status_code=404, detail="Vector index not found for this file")
#
#     index, chunks = load_index(file_id)
#     q_embedding = embed_question(question)
#     D, I = index.search(q_embedding, k=3)
#
#     retrieved = [chunks[i] for i in I[0]]
#     context = "\n".join(retrieved)
#     prompt = f"Context:\n{context}\n\nUser: {question}\nAI:"
#
#     inputs = tokenizer(prompt, return_tensors="pt")
#     output = model.generate(**inputs, max_new_tokens=150)
#     answer = tokenizer.decode(output[0], skip_special_tokens=True)
#
#     return AskResponse(answer=answer.split("AI:")[-1].strip())
#
#
# @router.post("/v1/ask", response_model=AskResponse)
# async def ask_question_v1(request: AskRequest):
#     try:
#         top_chunks = query_embeddings(request.file_id, request.question, top_k=5)
#         context = "\n".join(top_chunks)
#         prompt = f"Context:\n{context}\n\nUser: {request.question}\n\nAI:"
#
#         inputs = tokenizer(prompt, return_tensors="pt")
#         outputs = model.generate(**inputs, max_new_tokens=150, do_sample=True)
#         answer = tokenizer.decode(outputs[0], skip_special_tokens=True)
#
#         return {"answer": answer.split("AI:")[-1].strip()}
#     except FileNotFoundError as e:
#         raise HTTPException(status_code=404, detail=str(e))
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"❌ Failed: {str(e)}")

@router.post("/static-chat")
async def static_chat(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    question = data.get("question", "").strip()
    user_id = data.get("user_id")  # Assuming user_id is passed in the request

    if not user_id:
        raise HTTPException(status_code=400, detail="User ID is required")

    # Fetch conversation history for context
    conversation = db.query(Conversation).filter(Conversation.user_id == user_id).order_by(Conversation.created_at.desc()).first()
    conversation_history = []
    if conversation:
        conversation_history = json.loads(conversation.conversation_history)

    # Add user question to the history
    conversation_history.append({"sender": "user", "text": question})

    # Generate bot response (placeholder logic)
    bot_response = "This is a contextual response based on your question and history."

    # Add bot response to the history
    conversation_history.append({"sender": "bot", "text": bot_response})

    # Save updated conversation history
    if conversation:
        conversation.conversation_history = json.dumps(conversation_history)
        db.add(conversation)
    else:
        new_conversation = Conversation(
            user_id=user_id,
            conversation_history=json.dumps(conversation_history),
            summary=None  # Placeholder for summary generation
        )
        db.add(new_conversation)

    db.commit()

    # Return the bot response
    return {"answer": bot_response, "conversation_history": conversation_history}

    data = await request.json()
    question = data.get("question", "").strip().lower()
    
    # Hardcoded conversational responses
    greetings = {
        "hi": "Hello! How can I help you today?",
        "hello": "Hi there! How can I assist you?",
        "hey": "Hey! What can I do for you?",
        "bye": "Goodbye! Have a great day!",
        "goodbye": "Goodbye! If you need anything else, just ask!",
        "thanks": "You're welcome!",
        "thank you": "You're welcome!",
        "how are you": "I'm just a bot, but I'm here to help!",
        "who are you": "I'm FishAI, your assistant!",
        "what can you do": "I can answer your questions and help you with information from my knowledge base.",
        "help": "Sure! Ask me anything or tell me what you need help with.",
        "what is your name": "I'm FishAI, your virtual assistant.",
        "what is ai": "AI stands for Artificial Intelligence, which enables machines to mimic human intelligence.",
        "tell me a joke": "Why don't scientists trust atoms? Because they make up everything!",
        "what is the weather today": "I'm not connected to a weather service, but you can check your local forecast!",
        "how old are you": "I'm as old as the code that created me!",
        "what is your purpose": "My purpose is to assist you with your queries and provide helpful information.",
        "can you learn": "I don't learn on my own, but I can be updated by my developers.",
        "what is machine learning": "Machine learning is a subset of AI that allows systems to learn and improve from experience.",
        "what is deep learning": "Deep learning is a type of machine learning that uses neural networks to analyze data.",
        "what is python": "Python is a popular programming language known for its simplicity and versatility.",
        "what is fastapi": "FastAPI is a modern web framework for building APIs with Python.",
        "what is the time": "I don't have access to the current time, but you can check your device!",
        "what is your favorite color": "I don't have preferences, but I like the color of efficiency!",
        "can you help me": "Of course! Let me know what you need help with.",
        "what is the capital of france": "The capital of France is Paris.",
        "what is 2+2": "2+2 equals 4.",
        "what is the meaning of life": "The meaning of life is a philosophical question, but some say it's 42!",
        "can you tell me a story": "Once upon a time, there was a curious user who asked a bot for a story...",
        "what is the internet": "The internet is a global network that connects millions of private, public, academic, and business networks.",
        "what is cloud computing": "Cloud computing is the delivery of computing services over the internet.",
        "what is blockchain": "Blockchain is a decentralized ledger technology used for secure and transparent transactions.",
        "what is cryptocurrency": "Cryptocurrency is a digital or virtual currency that uses cryptography for security.",
        "what is bitcoin": "Bitcoin is a type of cryptocurrency, often referred to as digital gold.",
        "what is data science": "Data science is the field of study that combines domain expertise, programming, and statistics to extract insights from data.",
        "what is big data": "Big data refers to large and complex data sets that require advanced tools to process and analyze.",
        "what is artificial intelligence": "Artificial intelligence is the simulation of human intelligence in machines.",
        "what is a chatbot": "A chatbot is a software application designed to simulate human conversation.",
        "what is natural language processing": "Natural Language Processing (NLP) is a field of AI that focuses on the interaction between computers and humans using natural language.",
        "what is a neural network": "A neural network is a series of algorithms that mimic the operations of a human brain to recognize relationships in data.",
        "what is an algorithm": "An algorithm is a set of instructions designed to perform a specific task.",
        "what is programming": "Programming is the process of creating a set of instructions for a computer to perform specific tasks.",
        "what is software development": "Software development is the process of designing, creating, testing, and maintaining software applications.",
        "what is open source": "Open source refers to software with source code that anyone can inspect, modify, and enhance.",
        "what is github": "GitHub is a platform for version control and collaboration, allowing developers to work on projects together.",
        "what is version control": "Version control is a system that records changes to a file or set of files over time so that you can recall specific versions later.",
        "what is a database": "A database is an organized collection of data that can be accessed, managed, and updated.",
        "what is sql": "SQL stands for Structured Query Language, used for managing and manipulating databases.",
        "what is nosql": "NoSQL is a type of database that provides a mechanism for storage and retrieval of data that is modeled in means other than tabular relations.",
        "what is cloud storage": "Cloud storage is a service that allows you to save data by transferring it over the internet to an offsite storage system maintained by a third party.",
        "who am i": "You are whoever you want to be!",
        
    }
    
    # Fuzzy matching for greetings
    best_match = None
    best_score = 0
    for key, response in greetings.items():
        score = fuzz.ratio(question, key)
        if score > best_score and score >= 80:  # Threshold for similarity
            best_match = response
            best_score = score
    
    if best_match:
        return {"answer": best_match}
    
    qa_pairs = load_static_qa()
    prompts = [q["prompt"] for q in qa_pairs]
    match = get_close_matches(question, prompts, n=1, cutoff=0.5)
    if match:
        for q in qa_pairs:
            if q["prompt"] == match[0]:
                return {"answer": q["response"]}
    
    return {"answer": "Sorry, I couldn't find an answer to that question."}

@router.post("/static-chat/history")
async def fetch_conversation_history(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    user_id = data.get("user_id")

    if not user_id:
        raise HTTPException(status_code=400, detail="User ID is required")

    # Fetch the latest conversation for the user
    conversation = db.query(Conversation).filter(Conversation.user_id == user_id).order_by(Conversation.created_at.desc()).first()

    if not conversation:
        return {"conversation_history": []}

    # Return the conversation history
    return {"conversation_history": json.loads(conversation.conversation_history)}
