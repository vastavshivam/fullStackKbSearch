# api/qa.py
from fastapi import APIRouter, HTTPException
from models.schemas import AskRequest, AskResponse
from utils.embed_store import load_index, embed_question, query_embeddings, VECTOR_DIR
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import os
from pathlib import Path

router = APIRouter()

# Model variables for file-based Q&A
LLM_MODEL = "distilgpt2"
tokenizer = None
model = None

def load_qa_model():
    """Load model only for file-based Q&A"""
    global tokenizer, model
    if tokenizer is None or model is None:
        tokenizer = AutoTokenizer.from_pretrained(LLM_MODEL)
        model = AutoModelForCausalLM.from_pretrained(LLM_MODEL)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

def get_conversational_response(question: str) -> str:
    """
    Returns hardcoded conversational responses for common questions and topics
    """
    question_lower = question.lower()
    
    # Greetings & Basic Interactions
    if any(word in question_lower for word in ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening']):
        return "Hello! I'm here to help you with any questions you have. What can I assist you with today?"
    elif any(word in question_lower for word in ['how are you', 'how do you do', 'what\'s up']):
        return "I'm doing great, thank you for asking! I'm here and ready to help with whatever you need. How are you doing?"
    elif any(word in question_lower for word in ['goodbye', 'bye', 'see you later', 'farewell']):
        return "Goodbye! It was great chatting with you. Feel free to come back anytime if you need help. Have a wonderful day!"
    
    # About the Assistant
    elif any(phrase in question_lower for phrase in ['who are you', 'what are you', 'tell me about yourself']):
        return "I'm an AI assistant designed to help answer your questions and have meaningful conversations. I can discuss a wide variety of topics and I'm here to be helpful, informative, and engaging!"
    elif any(phrase in question_lower for phrase in ['what can you do', 'your capabilities', 'how can you help']):
        return "I can help with many things! I can answer questions, explain concepts, help with problem-solving, have conversations on various topics, provide information, and assist with learning. What would you like help with?"
    elif any(phrase in question_lower for phrase in ['your name', 'what should I call you']):
        return "You can call me your AI Assistant! I'm here to help and chat with you. What would you like to talk about?"
    
    # Compliments & Politeness
    elif any(phrase in question_lower for phrase in ['thank you', 'thanks', 'appreciate it']):
        return "You're very welcome! I'm happy I could help. Is there anything else you'd like to know or discuss?"
    elif any(phrase in question_lower for phrase in ['please', 'could you', 'would you mind']):
        return "Of course! I'd be happy to help. What do you need assistance with?"
    elif any(phrase in question_lower for phrase in ['sorry', 'apologize', 'my bad']):
        return "No worries at all! There's no need to apologize. How can I help you today?"
    
    # Knowledge & Learning
    elif any(phrase in question_lower for phrase in ['i don\'t know', 'not sure', 'confused', 'don\'t understand']):
        return "That's completely okay! Learning is a process, and it's normal to feel confused sometimes. I'm here to help explain things. What specific topic or concept would you like me to clarify?"
    elif any(phrase in question_lower for phrase in ['teach me', 'explain', 'how does', 'what is', 'define']):
        return "I'd be happy to explain! I love helping people learn new things. What topic would you like me to teach you about or explain in more detail?"
    elif any(phrase in question_lower for phrase in ['interesting', 'fascinating', 'cool', 'wow']):
        return "I'm glad you find it interesting! There's so much fascinating information out there. Is there a particular aspect you'd like to explore further, or would you like to learn about something related?"
    
    # Problem Solving & Support
    elif any(phrase in question_lower for phrase in ['problem', 'issue', 'trouble', 'difficulty', 'challenge']):
        return "I understand you're facing a challenge. I'm here to help! Can you tell me more details about the specific problem you're experiencing so I can provide the best assistance?"
    elif any(phrase in question_lower for phrase in ['help me', 'assist me', 'support', 'guidance']):
        return "Absolutely! I'm here to provide support and guidance. What do you need help with? The more details you can share, the better I can assist you."
    elif any(phrase in question_lower for phrase in ['stuck', 'lost', 'overwhelmed']):
        return "I understand that feeling! When we're stuck or overwhelmed, breaking things down into smaller steps can really help. Let's work through this together - what's the main thing you're trying to accomplish?"
    
    # Technology & Digital Life
    elif any(phrase in question_lower for phrase in ['computer', 'technology', 'digital', 'internet', 'software']):
        return "Technology can be really exciting and sometimes overwhelming! I'd be happy to discuss tech topics with you. What specific aspect of technology interests you or what would you like to know more about?"
    elif any(phrase in question_lower for phrase in ['AI', 'artificial intelligence', 'machine learning', 'robots']):
        return "AI and machine learning are fascinating fields that are rapidly evolving! There's so much to explore, from how AI works to its applications and implications. What aspect of AI would you like to discuss?"
    elif any(phrase in question_lower for phrase in ['social media', 'facebook', 'twitter', 'instagram', 'online']):
        return "Social media and online platforms have really transformed how we connect and share information! There are both benefits and challenges to consider. What's your experience with social media, or what would you like to discuss about online interactions?"
    
    # Learning & Education
    elif any(phrase in question_lower for phrase in ['study', 'learning', 'education', 'school', 'university', 'college']):
        return "Education and learning are so important for personal growth! Whether it's formal education or self-directed learning, there are many effective strategies. Are you looking for study tips, learning strategies, or want to discuss educational topics?"
    elif any(phrase in question_lower for phrase in ['book', 'reading', 'literature', 'novel']):
        return "Books and reading are wonderful! There's nothing quite like getting lost in a good story or learning something new from a great book. What types of books do you enjoy, or are you looking for reading recommendations?"
    elif any(phrase in question_lower for phrase in ['history', 'science', 'math', 'language', 'art']):
        return "Those are all fascinating subjects! Each field has so much depth and interesting connections to explore. Which area interests you most, or is there a specific topic within any of these fields you'd like to discuss?"
    
    # Creativity & Hobbies
    elif any(phrase in question_lower for phrase in ['creative', 'creativity', 'art', 'music', 'writing', 'drawing']):
        return "Creativity is such a wonderful part of human expression! Whether it's visual arts, music, writing, or any other creative pursuit, it's all about exploring and expressing ideas. What creative activities interest you or what would you like to explore?"
    elif any(phrase in question_lower for phrase in ['hobby', 'hobbies', 'interests', 'passion', 'free time']):
        return "Hobbies and personal interests add so much richness to life! They're great for relaxation, learning, and personal fulfillment. What hobbies do you enjoy, or are you looking to explore new interests?"
    elif any(phrase in question_lower for phrase in ['game', 'gaming', 'play', 'entertainment', 'fun']):
        return "Games and entertainment are great ways to have fun and unwind! There are so many different types - video games, board games, sports, puzzles, and more. What kinds of games or entertainment do you enjoy?"
    
    # Health & Wellbeing
    elif any(phrase in question_lower for phrase in ['health', 'wellness', 'fitness', 'exercise', 'wellbeing']):
        return "Health and wellness are so important for overall quality of life! There are many aspects to consider - physical health, mental health, nutrition, exercise, and more. What aspect of health and wellness would you like to discuss?"
    elif any(phrase in question_lower for phrase in ['stress', 'anxiety', 'worried', 'nervous', 'overwhelmed']):
        return "It's completely normal to feel stressed or anxious sometimes - you're not alone in feeling this way. While I can't provide medical advice, I can share that talking about concerns, practicing relaxation techniques, and seeking support can be helpful. Is there something specific on your mind?"
    elif any(phrase in question_lower for phrase in ['happy', 'joy', 'excited', 'celebration', 'good news']):
        return "That's wonderful to hear! Happiness and positive emotions are so important for our wellbeing. It's great that you're experiencing joy. What's making you feel happy or excited?"
    
    # Work & Career
    elif any(phrase in question_lower for phrase in ['work', 'job', 'career', 'professional', 'workplace']):
        return "Work and career are big parts of many people's lives! Whether it's finding the right career path, developing skills, dealing with workplace challenges, or achieving work-life balance, there's a lot to consider. What aspects of work or career would you like to discuss?"
    elif any(phrase in question_lower for phrase in ['interview', 'resume', 'job search', 'employment']):
        return "Job searching and career development can be both exciting and challenging! There are many strategies for resumes, interviews, networking, and finding the right opportunities. What specific aspect of job searching or career development would you like to discuss?"
    
    # Relationships & Social
    elif any(phrase in question_lower for phrase in ['friend', 'friendship', 'relationship', 'social', 'people']):
        return "Relationships and social connections are so valuable! Whether it's making new friends, maintaining existing relationships, or navigating social situations, human connections enrich our lives. What aspects of relationships or social interactions would you like to talk about?"
    elif any(phrase in question_lower for phrase in ['family', 'parents', 'siblings', 'relatives']):
        return "Family relationships can be both rewarding and complex! Every family is unique, with its own dynamics, traditions, and challenges. Family connections often shape who we are. What aspects of family life would you like to discuss?"
    
    # Travel & Culture
    elif any(phrase in question_lower for phrase in ['travel', 'vacation', 'trip', 'adventure', 'explore']):
        return "Travel and exploration are amazing ways to experience new places, cultures, and perspectives! Whether it's planning a trip, sharing travel experiences, or dreaming about future adventures, there's so much to discover. What interests you about travel?"
    elif any(phrase in question_lower for phrase in ['culture', 'tradition', 'customs', 'diversity', 'heritage']):
        return "Culture and traditions are fascinating! They shape how we see the world and connect us to our communities and heritage. There's so much diversity in human cultures around the world. What aspects of culture or traditions interest you?"
    
    # Food & Cooking
    elif any(phrase in question_lower for phrase in ['food', 'cooking', 'recipe', 'meal', 'cuisine']):
        return "Food and cooking are wonderful topics! There's something special about preparing and sharing meals - it brings people together and lets us explore different flavors and cultures. Do you enjoy cooking, or are there particular cuisines you're interested in?"
    elif any(phrase in question_lower for phrase in ['restaurant', 'dining', 'eat out', 'chef']):
        return "Dining experiences can be so enjoyable! Whether it's trying new restaurants, exploring different cuisines, or appreciating culinary artistry, food culture is rich and diverse. What kinds of dining experiences do you enjoy?"
    
    # Nature & Environment
    elif any(phrase in question_lower for phrase in ['nature', 'environment', 'outdoors', 'wildlife', 'animals']):
        return "Nature and the environment are incredible! There's so much beauty and complexity in the natural world - from wildlife and ecosystems to landscapes and environmental conservation. What aspects of nature interest you most?"
    elif any(phrase in question_lower for phrase in ['weather', 'rain', 'sunny', 'cloudy']):
        return "I don't have access to current weather data, but you can check your local weather app or website! Weather certainly affects our mood and activities. How's the weather treating you today?"
    
    # Philosophy & Life
    elif any(phrase in question_lower for phrase in ['meaning of life', 'philosophy', 'purpose', 'existence']):
        return "Deep philosophical questions have fascinated humanity for centuries! Many find meaning through relationships, personal growth, helping others, creative expression, or spiritual beliefs. What gives your life meaning?"
    elif any(phrase in question_lower for phrase in ['happiness', 'joy', 'contentment']):
        return "Happiness often comes from appreciating what we have, meaningful connections, pursuing growth, and contributing to others' well-being. Small daily joys matter too! What brings you happiness?"
    
    # Motivational & Inspirational
    elif any(phrase in question_lower for phrase in ['inspiration', 'motivation', 'encourage']):
        return "Remember that every expert was once a beginner, every journey starts with a single step, and growth happens outside your comfort zone. You have unique potential - believe in yourself and keep moving forward!"
    elif any(phrase in question_lower for phrase in ['give up', 'difficult', 'hard', 'struggle']):
        return "Challenges are tough, but they often lead to growth and strength. Take breaks when needed, ask for help, break big problems into smaller steps, and remember that setbacks are part of the journey. You're stronger than you know!"
    
    # Compliments & Appreciation
    elif any(phrase in question_lower for phrase in ['thank you', 'thanks', 'appreciate']):
        return "You're very welcome! I'm glad I could help. It's my pleasure to assist you. Is there anything else you'd like to know or discuss?"
    elif any(phrase in question_lower for phrase in ['good job', 'well done', 'excellent']):
        return "Thank you so much! I really appreciate your kind words. I'm here whenever you need assistance or just want to chat!"
    
    # Default response for unmatched questions
    else:
        return "That's an interesting question! While I'd love to give you a detailed answer, I might not have specific information on that topic. Could you tell me more about what you're looking for, or perhaps ask about something else I can help with?"

@router.post("/static-chat")
async def static_chat(request: dict):
    """
    Endpoint for static chat with hardcoded conversational responses
    Enhanced with knowledge base search when available
    """
    print(f"[DEBUG] static_chat called with request: {request}")
    try:
        question = request.get("question", "")
        if not question:
            raise HTTPException(status_code=400, detail="Question is required")
        
        # First try to search knowledge base if available
        try:
            # Check if any knowledge base files exist
            vector_dir = Path(VECTOR_DIR)
            if vector_dir.exists():
                vector_files = list(vector_dir.glob("*.index"))
                
                if vector_files:
                    # Use the first available knowledge base
                    vector_file = vector_files[0]
                    file_id = vector_file.stem  # Remove .index extension
                    
                    # Search for relevant context
                    relevant_chunks = query_embeddings(file_id, question, top_k=3)
                    
                    if relevant_chunks and len(relevant_chunks) > 0:
                        print(f"[DEBUG] Found {len(relevant_chunks)} relevant chunks")
                        # Parse the chunks to find matching Q&A pairs
                        best_match = None
                        highest_relevance = -1
                        
                        for i, chunk in enumerate(relevant_chunks):
                            print(f"[DEBUG] Processing chunk {i}: {chunk[:200]}...")
                            
                            # Handle the actual format: "prompt: ... response: ... sentiment: ..."
                            if "prompt:" in chunk.lower() and "response:" in chunk.lower():
                                # Find all prompt-response pairs in the chunk
                                parts = chunk.split("prompt:")
                                for part in parts[1:]:  # Skip first empty part
                                    if "response:" in part:
                                        try:
                                            prompt_part = part.split("response:")[0].strip()
                                            response_part = part.split("response:")[1].split("sentiment:")[0].strip()
                                            
                                            print(f"[DEBUG] Extracted prompt: {prompt_part[:50]}...")
                                            print(f"[DEBUG] Extracted response: {response_part[:50]}...")
                                            
                                            # Simple matching
                                            question_lower = question.lower()
                                            prompt_lower = prompt_part.lower()
                                            
                                            question_words = set(question_lower.split())
                                            prompt_words = set(prompt_lower.split())
                                            match_count = len(question_words.intersection(prompt_words))
                                            
                                            print(f"[DEBUG] Match count: {match_count}")
                                            
                                            if match_count > highest_relevance:
                                                highest_relevance = match_count
                                                best_match = response_part
                                                print(f"[DEBUG] New best match with score {match_count}")
                                        except Exception as parse_error:
                                            print(f"[DEBUG] Parse error: {parse_error}")
                                            continue
                        
                        print(f"[DEBUG] Final best match: {best_match if best_match else 'None'}")
                        print(f"[DEBUG] Highest relevance: {highest_relevance}")
                        
                        # If we found a good match, return it
                        if best_match and highest_relevance > 0:
                            # Clean up the response
                            clean_response = best_match.strip()
                            # Remove quotes if present
                            if clean_response.startswith('"') and clean_response.endswith('"'):
                                clean_response = clean_response[1:-1]
                            
                            print(f"[DEBUG] Returning KB response: {clean_response}")
                            return {"answer": clean_response}
        
        except Exception as e:
            print(f"Knowledge base search failed: {e}")
            # Continue to hardcoded responses if KB search fails
        
        # Fall back to hardcoded conversational response
        print(f"[DEBUG] Falling back to hardcoded response")
        ai_response = get_conversational_response(question)
        
        return {"answer": ai_response}
        
    except Exception as e:
        print(f"[DEBUG] Error in static_chat: {e}")
        return {"answer": "Sorry, there was an error processing your request. Please try again."}


@router.post("/static-chat/history")
async def get_static_chat_history(request: dict):
    """
    Endpoint to get chat history (placeholder implementation)
    """
    user_id = request.get("user_id", "default")
    # For now, return empty history - in production you'd fetch from database
    return {"conversation_history": []}
