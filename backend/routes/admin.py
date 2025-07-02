# backend/routes/admin.py

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from fastapi.responses import JSONResponse
import os
from shutil import copyfileobj

admin_router = APIRouter()

UPLOAD_DIR = "uploaded_kbs"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@admin_router.post("/upload-kb")
async def upload_kb(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        copyfileobj(file.file, buffer)
    return {"status": "success", "filename": file.filename}



@admin_router.get("/analytics")
def get_analytics():
    return {
        "response_time": 450,
        "unresolved_count": 8,
        "sentiment_avg": "positive"
    }






