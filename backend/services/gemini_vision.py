"""
Gemini Vision API integration for image analysis
"""
import google.generativeai as genai
import base64
import io
from PIL import Image
import logging

# Configure Gemini
GEMINI_API_KEY = "AIzaSyB5V3qgB25MFkv79JGaHUH75G047iQ5VIU"
genai.configure(api_key=GEMINI_API_KEY)

logger = logging.getLogger(__name__)

def analyze_image_with_gemini(pil_image, question=None):
    """
    Analyze image using Google Gemini Vision API with user-friendly responses
    """
    try:
        logger.info("Starting Gemini image analysis...")
        
        # Initialize Gemini model
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Prepare the prompt for natural, conversational responses
        if question and question.strip():
            prompt = f"""
You are a helpful AI assistant analyzing an image for a user. They asked: "{question}"

Please provide a friendly, natural response that:
1. Directly answers their question in a conversational way
2. Describes what you see in the image clearly and simply
3. Mentions any text or important details you notice
4. Keeps the tone warm and helpful

Write as if you're having a conversation with the user, not giving a technical report. Be specific but friendly.
"""
        else:
            prompt = """
You are a helpful AI assistant analyzing an image for a user. 

Please describe what you see in a friendly, conversational way. Imagine you're helping a friend understand the image:

1. Start with a warm greeting and overview of what the image shows
2. Describe the main elements in simple, clear language
3. Mention any text, colors, or interesting details you notice
4. End with an offer to help if they have specific questions

Keep it natural and engaging, like you're having a conversation!
"""
        
        # Generate response
        response = model.generate_content([prompt, pil_image])
        
        if response and response.text:
            logger.info("Gemini analysis completed successfully")
            return response.text.strip()
        else:
            logger.warning("Gemini returned empty response")
            return "I can see your image, but I'm having trouble analyzing it right now. Could you try asking a specific question about what you'd like to know?"
            
    except Exception as e:
        logger.error(f"Gemini analysis failed: {type(e).__name__}: {str(e)}")
        return f"I can see you've shared an image, but I'm having some technical difficulties analyzing it right now. Please try again in a moment!"

def process_image_with_gemini_and_ocr(pil_image, question=None, ocr_text=None):
    """
    Process image with both Gemini vision and OCR, combining results in a user-friendly format
    """
    try:
        logger.info("Processing image with Gemini + OCR...")
        
        # Get Gemini analysis
        gemini_analysis = analyze_image_with_gemini(pil_image, question)
        
        # Create a natural, friendly response format
        if ocr_text and ocr_text.strip() and ocr_text not in ["No text detected in the image.", "Failed to extract text from image."]:
            # When there's readable text, integrate it naturally
            if question and any(word in question.lower() for word in ['text', 'read', 'writing', 'written', 'says', 'word']):
                # User specifically asked about text
                combined_response = f"""{gemini_analysis}

📝 **Text I can read in the image:**
"{ocr_text.strip()}"

Hope this helps! Let me know if you'd like me to focus on any specific part of the image."""
            else:
                # General analysis with text included naturally
                combined_response = f"""{gemini_analysis}

I can also see there's some text in the image that reads: "{ocr_text.strip()}"

Feel free to ask if you'd like me to focus on any particular aspect!"""
        else:
            # No readable text found
            combined_response = f"""{gemini_analysis}

I don't see any readable text in this image, but I'm happy to answer any other questions about what I can see!"""
        
        logger.info("Gemini + OCR processing completed")
        return combined_response
        
    except Exception as e:
        logger.error(f"Combined processing failed: {e}")
        return f"I can see your image! While I had some technical issues with the detailed analysis, I'm here to help. Could you tell me what specifically you'd like to know about the image?"
