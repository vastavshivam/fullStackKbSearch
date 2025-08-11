import os
import google.generativeai as genai
from models.vector_store import get_top_k_docs
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    print("Warning: GEMINI_API_KEY not found. Using fallback responses.")

async def generate_response_with_rag(query: str, client_id: Optional[str] = None) -> str:
    """
    Generate AI response using uploaded knowledge base + Gemini API
    """
    try:
        # Get relevant documents from uploaded knowledge base for the specific client
        relevant_docs = await get_top_k_docs(query, k=3, client_id=client_id)
        
        if not relevant_docs or not GEMINI_API_KEY:
            return "I don't have access to any knowledge base files yet. Please upload some documents to get started, or check if the API key is configured."
        
        # Format context from knowledge base
        context_parts = []
        for doc in relevant_docs:
            if doc.get('content'):
                source = doc.get('source', 'Unknown')
                context_parts.append(f"From {source}: {doc['content']}")
        
        context = "\n\n".join(context_parts)
        
        # Create a comprehensive prompt for Gemini
        prompt = f"""You are an AI assistant with access to uploaded knowledge base documents. Use the provided context to answer the user's question accurately and helpfully.

CONTEXT FROM KNOWLEDGE BASE:
{context}

USER QUESTION: {query}

INSTRUCTIONS:
- Answer based primarily on the provided context from the uploaded documents
- If the context contains relevant information, use it to provide a detailed and accurate response
- If the context doesn't contain enough information to fully answer the question, mention what you know from the context and explain what additional information might be needed
- Be conversational and helpful
- Cite which document or source the information comes from when relevant
- If the question is completely unrelated to the knowledge base, provide a helpful general response but mention that you have specific knowledge base content available

RESPONSE:"""

        # Generate response using Gemini
        if GEMINI_API_KEY:
            try:
                response = model.generate_content(prompt)
                return response.text
            except Exception as api_error:
                api_error_str = str(api_error)
                # Handle specific API errors gracefully
                if "quota" in api_error_str.lower() or "429" in api_error_str:
                    # Return knowledge base content directly when quota exceeded
                    if context_parts:
                        direct_response = f"Based on the knowledge base documents:\n\n"
                        for i, part in enumerate(context_parts[:2], 1):
                            direct_response += f"{i}. {part[:300]}...\n\n"
                        direct_response += f"(Note: Full AI processing temporarily unavailable due to quota limits)"
                        return direct_response
                    else:
                        return "I found relevant information but cannot process it fully right now due to API limits. Please try again later."
                else:
                    # Re-raise other errors
                    raise api_error
        else:
            return f"Based on the uploaded documents: {context[:500]}... (Please configure Gemini API key for full AI responses)"
            
    except Exception as e:
        print(f"Error in RAG generation: {e}")
        return "I'm having trouble accessing the knowledge base right now. Please try again or contact support."

async def generate_widget_response(query: str, client_id: str) -> str:
    """
    Generate response specifically for widget chat using client-specific knowledge base
    """
    try:
        # Get relevant documents from client-specific knowledge base
        from models.vector_store import get_widget_knowledge_base
        relevant_docs = await get_widget_knowledge_base(client_id, query, k=3)
        
        if not relevant_docs or not GEMINI_API_KEY:
            return "I don't have access to any knowledge base files for this widget yet. Please upload some documents to get started, or check if the API key is configured."
        
        # Format context from knowledge base
        context_parts = []
        for doc in relevant_docs:
            if doc.get('content'):
                source = doc.get('source', 'Unknown')
                context_parts.append(f"From {source}: {doc['content']}")
        
        context = "\n\n".join(context_parts)
        
        # Create a widget-specific prompt for Gemini
        prompt = f"""You are a helpful AI assistant for this website. You have access to the company's knowledge base and can answer questions about their products, services, policies, and information.

KNOWLEDGE BASE CONTEXT:
{context}

USER QUESTION: {query}

INSTRUCTIONS:
- Answer based on the provided company knowledge base
- Be helpful, friendly, and professional
- If the knowledge base contains relevant information, provide a detailed and accurate response
- If you need to reference specific policies or procedures, mention where the information comes from
- If the question is outside the knowledge base scope, politely explain what you can help with based on the available information
- Keep responses conversational and customer-focused
- Always aim to be helpful even if you don't have complete information

RESPONSE:"""

        # Generate response using Gemini
        if GEMINI_API_KEY:
            response = model.generate_content(prompt)
            return response.text
        else:
            return f"Based on the uploaded knowledge base: {context[:300]}... (Please configure Gemini API key for full AI responses)"
            
    except Exception as e:
        print(f"Error in widget RAG generation: {e}")
        return "I'm having trouble accessing the knowledge base right now. Please try again or contact support."