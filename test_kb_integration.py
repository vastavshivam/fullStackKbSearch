#!/usr/bin/env python3
"""
Test script for Knowledge Base + Gemini Integration
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.append('/home/ishaan/Documents/fullStackKbSearch/backend')

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from services.rag import generate_widget_response, generate_response_with_rag

async def test_kb_integration():
    """Test the knowledge base integration with Gemini"""
    print("🧪 Testing Knowledge Base + Gemini Integration")
    print("=" * 50)
    
    # Test queries
    test_queries = [
        "What is your return policy?",
        "How do I track my order?", 
        "What products do you offer?",
        "How can I contact support?",
        "Tell me about pricing"
    ]
    
    test_client_id = "test_widget_123"
    
    for query in test_queries:
        print(f"\n🔍 Query: {query}")
        print("-" * 30)
        
        try:
            # Test widget-specific response
            response = await generate_widget_response(query, test_client_id)
            print(f"🤖 Response: {response}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("-" * 30)
    
    print("\n✅ Test completed!")

if __name__ == "__main__":
    asyncio.run(test_kb_integration())
