import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import declarative_base
from api.qa import router as qa_router
from api.auth import router as auth_router
from api.image_processing import router as image_router
from api.feedback import router as feedback_router
from api.voice import router as voice_router
from fastapi.responses import JSONResponse
import logging
from api import quote_parser

# Load environment variables
load_dotenv()

from database import database  # Assuming you have a database module for initialization

from db import *
from api import chat, auth, files, training, websocket, widget, dashboard, enhanced_widget_chat
from utils.email_notify import setup_email_notifications
from routes import whatsapp_routes as whatsapp
Base = declarative_base()

app = FastAPI(
    title="AppG Support Assistant API",
    description="AI-driven support assistant with chat, training, and vector search",
    version="1.0.0"
) 
 
# ✅ CORS configuration 
origins = [
    "http://localhost:3000",  # React frontend
    "http://127.0.0.1:3000",
    "http://localhost:3001",  # Current frontend port
    "http://127.0.0.1:3001",
    "http://localhost:8004",  # Backend port
    "http://127.0.0.1:8004",
    "http://localhost",
    "*",  # Allow all origins for widget embeds
]

# Allow CORS from frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)

# ✅ API routers 

app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(files.router, prefix="/api/files", tags=["Files"])
app.include_router(qa_router, prefix="/api/qa", tags=["Q&A"])
app.include_router(image_router, prefix="/api/image", tags=["Image Processing"])
app.include_router(feedback_router, prefix="/api/feedback", tags=["Feedback"])
app.include_router(voice_router, prefix="/api/voice", tags=["Voice Assistant"])
app.include_router(training.router, prefix="/api/training", tags=["Training"])
app.include_router(websocket.router, tags=["WebSocket"])
app.include_router(widget.router, prefix="/api/widget", tags=["Widget"])
app.include_router(enhanced_widget_chat.router, prefix="/api/enhanced-widget", tags=["Enhanced Widget Chat"])
app.include_router(dashboard.router, tags=["Dashboard"])
app.include_router(whatsapp.router, prefix="/whatsapp")
app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
app.include_router(quote_parser.router, prefix="/api")

# ✅ Static file serving (for uploaded images, previews, etc.)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# ✅ Startup/shutdown tasks
@app.on_event("startup")
async def startup():
    # await database.init_db()  # Commented out since using MongoDB
    setup_email_notifications()

@app.on_event("shutdown")
async def shutdown():
    pass  # Cleanup tasks (if any)

# ✅ Test endpoint for debugging file uploads
from fastapi import File, UploadFile, Form

@app.post("/test-upload", tags=["Testing"])
async def test_upload(image: UploadFile = File(None)):
    """Minimal test endpoint for file upload debugging"""
    try:
        if not image:
            return {"status": "no_file", "message": "No file provided"}
        
        # Just read the file bytes
        file_content = await image.read()
        
        return {
            "status": "success", 
            "filename": image.filename,
            "content_type": image.content_type,
            "size": len(file_content)
        }
        
    except Exception as e:
        return {"status": "error", "error": str(e)}

# ✅ Health check
@app.get("/", tags=["Health"])
def root():
    return {"message": "✅ Support Assistant API is live."}

# Exception handling
logging.basicConfig(level=logging.ERROR)

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logging.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"message": "An internal server error occurred."},
    )

# @app.on_event("startup")
# async def startup_event():
#     await database.init_db()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from api.auth import router as auth_router
except Exception as e:
    logger.error(f"Error during application startup: {e}")
    raise


