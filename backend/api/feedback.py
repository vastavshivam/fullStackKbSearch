# api/feedback.py
from fastapi import APIRouter, HTTPException, Depends
from models.schemas import FeedbackCreate
from db.crud import save_feedback
from pydantic import BaseModel
from typing import Optional
import logging

router = APIRouter()

# Setup logging
logger = logging.getLogger(__name__)

class MessageFeedback(BaseModel):
    message_id: str
    feedback_type: str  # 'up' or 'down'
    session_id: Optional[str] = None
    comment: Optional[str] = None

@router.post("/message-feedback")
async def submit_message_feedback(feedback: MessageFeedback):
    """Submit thumbs up/down feedback for a specific message"""
    try:
        # Validate feedback type
        if feedback.feedback_type not in ['up', 'down']:
            raise HTTPException(status_code=400, detail="Invalid feedback type. Must be 'up' or 'down'")
        
        # Save feedback to MongoDB
        result = save_feedback(feedback.message_id, feedback.feedback_type)
        
        logger.info(f"Feedback saved: {feedback.message_id} - {feedback.feedback_type}")
        
        return {
            "status": "success",
            "message": "Feedback submitted successfully",
            "feedback_id": feedback.message_id,
            "feedback_type": feedback.feedback_type
        }
        
    except Exception as e:
        logger.error(f"Failed to save feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save feedback: {str(e)}")

@router.get("/message-feedback/{message_id}")
async def get_message_feedback(message_id: str):
    """Get feedback for a specific message"""
    try:
        # This could be implemented to retrieve feedback from MongoDB
        # For now, return a placeholder response
        return {
            "message_id": message_id,
            "feedback_data": "Feedback retrieval not yet implemented"
        }
        
    except Exception as e:
        logger.error(f"Failed to retrieve feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve feedback: {str(e)}")

@router.get("/feedback-analytics")
async def get_feedback_analytics():
    """Get feedback analytics and statistics"""
    try:
        from mongo.models import feedback_logs_col
        
        # Count total feedback
        total_feedback = feedback_logs_col.count_documents({})
        
        # Count positive and negative feedback
        positive_feedback = feedback_logs_col.count_documents({"feedback": "up"})
        negative_feedback = feedback_logs_col.count_documents({"feedback": "down"})
        
        # Calculate satisfaction rate
        satisfaction_rate = (positive_feedback / total_feedback * 100) if total_feedback > 0 else 0
        
        return {
            "total_feedback": total_feedback,
            "positive_feedback": positive_feedback,
            "negative_feedback": negative_feedback,
            "satisfaction_rate": round(satisfaction_rate, 2),
            "message": "Feedback analytics retrieved successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to retrieve feedback analytics: {str(e)}")
        return {
            "total_feedback": 0,
            "positive_feedback": 0,
            "negative_feedback": 0,
            "satisfaction_rate": 0,
            "message": "Analytics currently unavailable"
        }
