from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.declarative import declarative_base
from api.qa import router as qa_router


from database import database  # Assuming you have a database module for initialization

from db import *
from api import auth, files, training, websocket, vchat, chat
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
    "http://localhost",
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
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(vchat.router, prefix="/api/vchat", tags=["VCHAT"])
app.include_router(files.router, prefix="/api/files", tags=["Files"])
app.include_router(qa_router, prefix="/api/qa", tags=["Q&A"])
app.include_router(training.router, prefix="/api/training", tags=["Training"])
# app.include_router(websocket.router,prefix="/", tags=["WebSocket"])
app.include_router(whatsapp.router, prefix="/whatsapp", tags=["whatsapp Integration"])
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


@app.on_event("startup")
async def startup_event():
    await database.init_db()
# from fastapi import FastAPI
# from routes import admin, token
# from fastapi.middleware.cors import CORSMiddleware

# app = FastAPI()

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# app.include_router(admin.admin_router, prefix="/api/admin")
# app.include_router(token.router)

# if __name__ == "__main__": 
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000) 


