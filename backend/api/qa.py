# api/qa.py
from fastapi import APIRouter, HTTPException
from models.schemas import AskRequest, AskResponse
from utils.embed_store import load_index, embed_question, query_embeddings
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import os
import re
from difflib import SequenceMatcher

from utils.embed_store import VECTOR_DIR

router = APIRouter()

LLM_MODEL = "tiiuae/falcon-rw-1b"
tokenizer = AutoTokenizer.from_pretrained(LLM_MODEL)
model = AutoModelForCausalLM.from_pretrained(LLM_MODEL)

# Comprehensive conversation patterns with responses
CONVERSATION_PATTERNS = {
    # Greetings and casual interactions
    "greetings": {
        "patterns": ["hi", "hello", "hey", "hola", "greetings", "good morning", "good afternoon", "good evening", "good night", "howdy", "what's up", "sup", "yo", "hiya", "salutations"],
        "responses": [
            "Hello! 👋 I'm your AppGallop AI assistant. How can I help you today?",
            "Hi there! 😊 Great to see you! What can I do for you?",
            "Hey! Welcome to AppGallop! I'm here to help with any questions you have.",
            "Hello! Hope you're having a wonderful day! How may I assist you?",
            "Hi! I'm your friendly AI assistant. What would you like to know?"
        ]
    },
    
    # How are you variations
    "wellbeing": {
        "patterns": ["how are you", "how are you doing", "how's it going", "how do you feel", "are you okay", "are you well", "how have you been", "what's your status", "how are things"],
        "responses": [
            "I'm doing great, thank you for asking! I'm here and ready to assist you. What would you like to know?",
            "I'm fantastic! Always ready to help. How are you doing today?",
            "I'm doing wonderful! Thanks for asking. How can I help you today?",
            "I'm excellent and fully operational! What can I help you with?",
            "I'm doing amazing! Hope you're having a great day too. What's on your mind?"
        ]
    },
    
    # Capabilities and help
    "capabilities": {
        "patterns": ["what can you do", "what are your capabilities", "help", "help me", "what do you know", "what are you good at", "what's your purpose", "how can you help", "what services do you offer"],
        "responses": [
            "I can help you with various tasks! I can answer questions, provide information, assist with problem-solving, and have conversations. Feel free to upload a knowledge base for more specific domain expertise. What would you like help with?",
            "I'm here to assist with answering questions, providing information, helping solve problems, and having meaningful conversations. I work best when you upload knowledge bases for specific topics!",
            "I can help with questions, provide support, assist with research, and chat about various topics. Upload a knowledge base for specialized help in your domain!",
            "My capabilities include answering questions, providing assistance, problem-solving, and engaging conversations. I become even more powerful with uploaded knowledge bases!"
        ]
    },
    
    # Identity questions
    "identity": {
        "patterns": ["who are you", "what are you", "tell me about yourself", "introduce yourself", "what's your name", "are you human", "are you a bot", "are you ai", "are you real"],
        "responses": [
            "I'm AppGallop's AI assistant! I'm designed to help answer questions, provide support, and assist with various tasks. I can work with uploaded knowledge bases to give you specific information about your business or topics of interest.",
            "I'm your friendly AI assistant from AppGallop! I'm here to help with questions, provide information, and make your experience smoother.",
            "I'm an AI assistant created by AppGallop to help users like you! I can answer questions, provide assistance, and work with knowledge bases for specialized support.",
            "I'm AppGallop's intelligent assistant! I'm designed to be helpful, informative, and friendly while assisting with your queries and tasks."
        ]
    },
    
    # Gratitude
    "gratitude": {
        "patterns": ["thank you", "thanks", "thank you so much", "appreciate it", "thanks a lot", "much appreciated", "grateful", "cheers", "thx", "ty"],
        "responses": [
            "You're very welcome! I'm happy to help. Is there anything else you'd like to know or discuss?",
            "My pleasure! Always glad to assist. What else can I help you with?",
            "You're welcome! I'm here whenever you need help. Anything else on your mind?",
            "Happy to help! Feel free to ask if you have more questions.",
            "You're most welcome! I'm always here to assist. What else would you like to know?"
        ]
    },
    
    # Farewells
    "farewells": {
        "patterns": ["bye", "goodbye", "see you later", "farewell", "see ya", "catch you later", "until next time", "take care", "have a good day", "talk to you later"],
        "responses": [
            "Goodbye! It was great chatting with you. Feel free to come back anytime if you need help! 👋",
            "See you later! Thanks for the great conversation. Come back anytime!",
            "Farewell! Hope to chat with you again soon. Take care! 😊",
            "Bye! It was wonderful helping you today. Don't hesitate to return if you need assistance!",
            "Take care! Thanks for visiting. I'll be here whenever you need help! 👋"
        ]
    },
    
    # Compliments and praise
    "compliments": {
        "patterns": ["you're great", "you're awesome", "good job", "well done", "you're helpful", "you're smart", "you're amazing", "love you", "you rock", "fantastic work"],
        "responses": [
            "Thank you so much! That really makes my day. I'm here to help whenever you need it! 😊",
            "Aww, thank you! I really appreciate that. Is there anything else I can help you with?",
            "You're too kind! I'm just doing what I love - helping people like you!",
            "Thank you for the kind words! It motivates me to keep being helpful. What else can I do for you?",
            "That's so nice of you to say! I'm glad I could be helpful. Anything else you'd like to discuss?"
        ]
    },
    
    # Questions about time, weather, location
    "external_info": {
        "patterns": ["what time is it", "what's the weather", "where am i", "what's the date", "what day is it", "current time", "today's weather", "temperature outside"],
        "responses": [
            "I don't have access to real-time information like current time or weather, but you can check your device for that info! Is there something else I can help you with?",
            "I wish I could tell you the current time/weather, but I don't have access to real-time data. Check your device for that! What else can I assist with?",
            "I don't have access to live data like time or weather updates. Your device can give you that info! How else can I help you today?"
        ]
    },
    
    # Fun and casual questions
    "fun_questions": {
        "patterns": ["tell me a joke", "make me laugh", "something funny", "entertain me", "tell me something interesting", "surprise me", "what's new", "anything exciting"],
        "responses": [
            "Here's one for you: Why don't scientists trust atoms? Because they make up everything! 😄 What else can I help you with?",
            "How about this: I told my computer a joke about UDP, but it didn't get it! 😂 Need help with anything else?",
            "Fun fact: The word 'set' has the most different meanings in English! Pretty interesting, right? What would you like to know more about?",
            "Here's something cool: Honey never spoils! Archaeologists have found edible honey in ancient Egyptian tombs. Amazing, isn't it? What else interests you?",
            "Did you know? A group of flamingos is called a 'flamboyance'! 🦩 What other topics would you like to explore?"
        ]
    },
    
    # Emotional support
    "emotional_support": {
        "patterns": ["i'm sad", "i'm tired", "i'm stressed", "i'm worried", "i'm anxious", "i'm confused", "i'm frustrated", "i need help", "i'm lost", "i don't know"],
        "responses": [
            "I'm sorry you're feeling that way. I'm here to help however I can. Would you like to talk about what's bothering you?",
            "That sounds tough. I'm here to listen and help in any way possible. What's on your mind?",
            "I understand that can be difficult. I'm here to support you. Would you like to share what's causing these feelings?",
            "I'm here for you. Sometimes talking things through can help. What would you like to discuss?",
            "That must be challenging. I'm here to help and support you through this. How can I assist you today?"
        ]
    },
    
    # Learning and education
    "learning": {
        "patterns": ["teach me", "i want to learn", "explain", "how does this work", "i don't understand", "can you show me", "educate me", "i'm curious about"],
        "responses": [
            "I'd love to help you learn! What topic are you interested in? I can explain things or point you in the right direction.",
            "Learning is fantastic! What would you like to know more about? I'm here to help explain things clearly.",
            "Great attitude! I'm here to help you understand. What subject or topic interests you?",
            "I'm excited to help you learn! What area would you like to explore? I'll do my best to explain it clearly.",
            "Learning new things is wonderful! What topic has caught your curiosity? I'm here to help!"
        ]
    },
    
    # Work and productivity
    "work_productivity": {
        "patterns": ["i'm working on", "need help with work", "productivity tips", "how to be more efficient", "work advice", "career guidance", "job help"],
        "responses": [
            "I'd be happy to help with work-related questions! What specific area are you working on? I can provide guidance and suggestions.",
            "Work can be challenging! I'm here to help with productivity tips, problem-solving, or any work-related questions you have.",
            "Great that you're focused on work! What aspect would you like help with? I can offer advice and support.",
            "I'm here to help with work matters! Whether it's productivity, problem-solving, or guidance, what do you need assistance with?"
        ]
    },
    
    # Technology questions
    "technology": {
        "patterns": ["computer problem", "tech help", "software issue", "app not working", "technical support", "it problem", "bug", "error", "crash"],
        "responses": [
            "I can try to help with tech issues! What specific problem are you experiencing? Describe what's happening and I'll do my best to assist.",
            "Tech problems can be frustrating! Tell me more about what's going wrong and I'll help troubleshoot the issue.",
            "I'm here to help with technical issues! What device or software is giving you trouble? Let's work through it together.",
            "Technical support is one of my strengths! Describe the problem you're facing and I'll guide you through potential solutions."
        ]
    },
    
    # Random conversation starters
    "random_conversation": {
        "patterns": ["i'm bored", "let's chat", "talk to me", "i'm lonely", "keep me company", "what should we discuss", "random question", "tell me something"],
        "responses": [
            "I'm here to chat! What's on your mind today? We could talk about hobbies, interests, current events, or anything else you'd like!",
            "I'd love to keep you company! What would you like to talk about? I'm interested in hearing about your day or any topics you enjoy.",
            "Great! I enjoy good conversations. What interests you? We could discuss books, movies, science, travel, or whatever you're passionate about!",
            "I'm happy to chat with you! What's something that's been on your mind lately? Or is there a topic you'd like to explore together?",
            "Perfect timing for a chat! What would make for an interesting conversation today? I'm all ears!"
        ]
    }
}

def similarity_score(a, b):
    """Calculate similarity between two strings using SequenceMatcher"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def find_best_match(user_input, patterns, threshold=0.6):
    """Find the best matching pattern for user input with similarity threshold"""
    user_input = user_input.lower().strip()
    best_match = None
    best_score = 0
    
    for category, data in patterns.items():
        for pattern in data["patterns"]:
            # Direct substring match (higher priority)
            if pattern in user_input or user_input in pattern:
                score = 0.9
            else:
                # Fuzzy matching
                score = similarity_score(user_input, pattern)
            
            if score > best_score and score >= threshold:
                best_score = score
                best_match = category
    
    return best_match, best_score

import random

@router.post("/ask", response_model=AskResponse)
async def ask_question(data: AskRequest):
    file_id = data.file_id
    question = data.question

    vector_path = os.path.join(VECTOR_DIR, f"{file_id}.index")
    if not os.path.exists(vector_path):
        raise HTTPException(status_code=404, detail="Vector index not found for this file")

    index, chunks = load_index(file_id)
    q_embedding = embed_question(question)
    D, I = index.search(q_embedding, k=3)

    retrieved = [chunks[i] for i in I[0]]
    joined_context = "\n".join(retrieved)
    prompt = f"Context:\n{joined_context}\n\nUser: {question}\nAI:"

    inputs = tokenizer(prompt, return_tensors="pt")
    output = model.generate(**inputs, max_new_tokens=150)
    answer = tokenizer.decode(output[0], skip_special_tokens=True)

    clean_answer = answer.split("AI:")[-1].lstrip().strip()
    return AskResponse(answer=clean_answer)


@router.post("/v1/ask", response_model=AskResponse)
async def ask_question(request: AskRequest):
    try:
        top_chunks = query_embeddings(request.file_id, request.question, top_k=5)
        context = "\n".join(top_chunks)
        prompt = f"Context:\n{context}\n\nUser: {request.question}\n\nAI:"

        inputs = tokenizer(prompt, return_tensors="pt")
        outputs = model.generate(**inputs, max_new_tokens=150, do_sample=True)
        answer = tokenizer.decode(outputs[0], skip_special_tokens=True)

        clean_answer = answer.split("AI:")[-1].lstrip().strip()
        return {"answer": clean_answer}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"❌ Failed: {str(e)}")


@router.post("/static-chat")
async def static_chat(request: dict):
    """Advanced conversational AI with fuzzy matching and extensive conversation patterns"""
    try:
        question = request.get("question", "").strip()
        if not question:
            raise HTTPException(status_code=400, detail="Question is required")
        
        # Find the best matching conversation pattern
        best_match, confidence = find_best_match(question, CONVERSATION_PATTERNS)
        
        if best_match and confidence > 0.6:
            # Get a random response from the matched category
            responses = CONVERSATION_PATTERNS[best_match]["responses"]
            response = random.choice(responses)
            return {"answer": response}
        
        # Handle specific keywords with fuzzy matching
        question_lower = question.lower()
        
        # Business/AppGallop related questions
        if any(word in question_lower for word in ["appgallop", "company", "business", "service", "product"]):
            return {"answer": "AppGallop is focused on providing excellent AI-powered solutions! I'm here to help you with any questions about our services. What would you like to know more about?"}
        
        # Programming/Development questions
        if any(word in question_lower for word in ["code", "programming", "development", "api", "software", "bug", "debug"]):
            return {"answer": "I can help with programming and development questions! While I'd need a relevant knowledge base for specific technical details, I'm happy to discuss general concepts. What are you working on?"}
        
        # General knowledge questions
        if any(word in question_lower for word in ["what is", "how does", "why", "when", "where", "explain"]):
            return {"answer": f"That's a great question about '{question}'! While I can discuss general topics, I'd be much more helpful with a relevant knowledge base uploaded. For now, I can try to help with what I know - what specific aspect interests you most?"}
        
        # Problem-solving requests
        if any(word in question_lower for word in ["problem", "issue", "trouble", "fix", "solve", "broken", "not working"]):
            return {"answer": "I'm here to help solve problems! Could you tell me more details about what's not working or what issue you're facing? The more specific you can be, the better I can assist you."}
        
        # Learning requests
        if any(word in question_lower for word in ["learn", "study", "understand", "tutorial", "guide", "how to"]):
            return {"answer": "I love helping people learn! What subject or skill are you interested in? While I can provide general guidance, uploading a relevant knowledge base would give you much more detailed and specific information."}
        
        # Personal questions about user
        if any(word in question_lower for word in ["my", "i am", "i'm", "i have", "i need", "i want"]):
            return {"answer": "I'd be happy to help with whatever you need! Could you tell me more about your situation or what you're looking for? I'm here to assist in any way I can."}
        
        # Questions with numbers or data
        if re.search(r'\d+', question):
            return {"answer": "I see you're asking about something with specific numbers or data. While I can discuss general concepts, for precise calculations or data-specific questions, a relevant knowledge base would be most helpful. What can I help you understand about this topic?"}
        
        # Default response for unmatched questions
        return {"answer": f"That's an interesting question! While I'd love to give you a detailed answer about '{question}', I work best when you upload a knowledge base with specific information on the topic. For now, I'm here to chat and help with general questions. Could you tell me more about what you're looking for, or would you like to discuss something else?"}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"❌ Failed: {str(e)}")
