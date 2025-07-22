from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.declarative import declarative_base
from api.qa import router as qa_router
from api.auth import router as auth_router
from fastapi.responses import JSONResponse
import logging

from database import database  # Assuming you have a database module for initialization

from db import *
from api import chat, auth, files, training, websocket
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
    "http://localhost:3001",  # React frontend (alternative port)
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
    "http://localhost",
    "*"  # Allow all origins for development (remove in production)
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ API routers 

app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(files.router, prefix="/api/files", tags=["Files"])
app.include_router(qa_router, prefix="/api/qa", tags=["Q&A"])
app.include_router(training.router, prefix="/api/training", tags=["Training"])
app.include_router(websocket.router, tags=["WebSocket"])
app.include_router(whatsapp.router, prefix="/whatsapp")
app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])

# ✅ Static file serving (for uploaded images, previews, etc.)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# ✅ Startup/shutdown tasks
@app.on_event("startup")
async def startup():
    await database.init_db()
    setup_email_notifications()

@app.on_event("shutdown")
async def shutdown():
    pass  # Cleanup tasks (if any)

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

@app.on_event("startup")
async def startup_event():
    await database.init_db()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from api.auth import router as auth_router
except Exception as e:
    logger.error(f"Error during application startup: {e}")
    raise


