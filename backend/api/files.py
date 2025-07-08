# ==========================================
# 💡 Support Assistant Project .gitignore
# For FastAPI + PostgreSQL + React + Docker
# Author: Shivam Srivastav
# ==========================================
# File: backend/api/files.py    
# ==========================================
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path
from utils.embed_store import chunk_text, save_embeddings
from models.schemas import KBEntryCreate, KBEntryResponse, KBEntriesListResponse
import shutil
import os

from utils.file_parser import parse_file, clean_json
from utils.email_notify import send_upload_notification

router = APIRouter()

UPLOAD_DIR = Path("uploads") 
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {".csv", ".json", ".xlsx" , ".txt", ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".bmp"}
MAX_FILE_SIZE_MB = 10

# In-memory storage for demo purposes (in production, use a database)
kb_entries = [
    {"id": 1, "question": "How to reset my password?", "answer": "Click on Forgot Password on the login page.", "created_at": "2024-01-01T10:00:00"},
    {"id": 2, "question": "How to contact support?", "answer": "Email us at support@example.com or call 1-800-SUPPORT.", "created_at": "2024-01-01T10:30:00"},
]
next_id = 3

@router.post("/upload", summary="Upload training/WhatsApp file")
async def upload_file(file: UploadFile = File(...)):
    # Validate extension
    ext = Path(file.filename).suffix.lower()
    print(f"File extension===============>: {ext}")
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"❌ Unsupported file type: {ext}")

    # Validate size
    contents = await file.read()
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(status_code=400, detail=f"❌ File too large (max {MAX_FILE_SIZE_MB}MB)")

    # Save file
    file_path = UPLOAD_DIR / file.filename
    print(f"File path===============>: {file_path}")
    with open(file_path, "wb") as f:
        f.write(contents)

    # Optional: parse and preview first rows
    try:
        preview = parse_file(file_path, limit=5)
        preview = clean_json(preview)  # Clean JSON data if needed
        print(f"Preview data===============>: {preview}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"❌ Failed to parse file: {str(e)}")
    
     # 🔁 Embed full content for retrieval
    try:  

        full_text = parse_file(file_path)  # No limit here
        chunks = chunk_text(full_text)
        save_embeddings(file_id=file.filename, chunks=chunks)
    except Exception as e:
        print(f"[Embedding Error]: {e}")  # or raise a warning log

    # Optional: send email/slack alert to admin
    send_upload_notification("vastavshivam@gmai.com", "uploaded successfully.", body="File uploaded ...")

    return JSONResponse(content={
        "message": f"✅ File {file.filename} uploaded successfully.",
        "filename": file.filename,
        "preview": preview  # Optional: parsed preview from CSV/JSON/XLSX
    })

@router.get("/kb/entries", response_model=KBEntriesListResponse, summary="Get all KB entries")
async def get_kb_entries():
    """Get all knowledge base entries"""
    return KBEntriesListResponse(entries=kb_entries, total=len(kb_entries))

@router.post("/kb/entries", response_model=KBEntryResponse, summary="Create new KB entry")
async def create_kb_entry(entry: KBEntryCreate):
    """Create a new knowledge base entry"""
    global next_id
    new_entry = {
        "id": next_id,
        "question": entry.question,
        "answer": entry.answer,
        "created_at": "2024-01-01T12:00:00"  # In production, use datetime.now()
    }
    kb_entries.append(new_entry)
    next_id += 1
    return KBEntryResponse(**new_entry)

@router.delete("/kb/entries/{entry_id}", summary="Delete KB entry")
async def delete_kb_entry(entry_id: int):
    """Delete a knowledge base entry"""
    global kb_entries
    kb_entries = [entry for entry in kb_entries if entry["id"] != entry_id]
    return {"message": f"Entry {entry_id} deleted successfully"}

@router.put("/kb/entries/{entry_id}", response_model=KBEntryResponse, summary="Update KB entry")
async def update_kb_entry(entry_id: int, entry: KBEntryCreate):
    """Update a knowledge base entry"""
    for kb_entry in kb_entries:
        if kb_entry["id"] == entry_id:
            kb_entry["question"] = entry.question
            kb_entry["answer"] = entry.answer
            return KBEntryResponse(**kb_entry)
    raise HTTPException(status_code=404, detail="Entry not found")
