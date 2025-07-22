# ==========================================
# 💡 Support Assistant Project .gitignore
# For FastAPI + PostgreSQL + React + Docker
# Author: Shivam Srivastav
# ==========================================
# File: backend/api/files.py    
# ==========================================
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pathlib import Path
from utils.embed_store import chunk_text, save_embeddings, VECTOR_DIR
import shutil
import os
import json
from training.fine_tune import fine_tune
from utils.file_parser import parse_file, clean_json, extract_text_content
from utils.email_notify import send_upload_notification

router = APIRouter()

UPLOAD_DIR = Path("uploads") 
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {".csv", ".json", ".xlsx" , ".txt", ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".bmp"}
MAX_FILE_SIZE_MB = 10

@router.post("/upload", summary="Upload training/WhatsApp file")
async def upload_file(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
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
        # Extract full text content from the file
        full_text = extract_text_content(file_path)
        if full_text:
            chunks = chunk_text(full_text)
            save_embeddings(file_id=file.filename, chunks=chunks)
            print(f"✅ Created embeddings for {file.filename} with {len(chunks)} chunks")
        else:
            print(f"⚠️ No text content extracted from {file.filename}")
    except Exception as e:
        print(f"[Embedding Error]: {e}")  # or raise a warning log

    # ✅ Start training automatically after embeddings
    background_tasks.add_task(fine_tune)

    # Optional: send email/slack alert to admin
    send_upload_notification("vastavshivam@gmai.com", "uploaded successfully.", body="File uploaded ...")

    return JSONResponse(content={
        "message": f"✅ File {file.filename} uploaded successfully.",
        "filename": file.filename,
        "preview": preview  # Optional: parsed preview from CSV/JSON/XLSX
    })

@router.get("/kb/entries", summary="List knowledge base entries")
async def list_kb_entries():
    """List all uploaded knowledge base files with their metadata"""
    try:
        entries = []
        
        # Check upload directory
        if UPLOAD_DIR.exists():
            for file_path in UPLOAD_DIR.iterdir():
                if file_path.is_file():
                    # Check if vector embeddings exist
                    vector_file = Path(VECTOR_DIR) / f"{file_path.name}.index"
                    chunks_file = Path(VECTOR_DIR) / f"{file_path.name}_chunks.pkl"
                    
                    entry = {
                        "filename": file_path.name,
                        "size": file_path.stat().st_size,
                        "created_at": file_path.stat().st_mtime,
                        "has_embeddings": vector_file.exists() and chunks_file.exists(),
                        "file_type": file_path.suffix.lower()
                    }
                    entries.append(entry)
        
        return JSONResponse(content={
            "entries": entries,
            "total": len(entries)
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list knowledge base entries: {str(e)}")

# async def upload_file(file: UploadFile = File(...)):
#     # Validate extension
#     ext = Path(file.filename).suffix.lower()
#     if ext not in ALLOWED_EXTENSIONS:
#         raise HTTPException(status_code=400, detail=f"❌ Unsupported file type: {ext}")

#     # Validate size
#     contents = await file.read()
#     size_mb = len(contents) / (1024 * 1024)
#     if size_mb > MAX_FILE_SIZE_MB:
#         raise HTTPException(status_code=400, detail=f"❌ File too large (max {MAX_FILE_SIZE_MB}MB)")

#     # Save file
#     file_path = UPLOAD_DIR / file.filename
#     with open(file_path, "wb") as f:
#         f.write(contents)

#     # Optional: parse and preview first rows
#     try:
#         preview = parse_file(file_path, limit=5)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"❌ Failed to parse file: {str(e)}")

#     # Optional: send email/slack alert to admin
#     send_upload_notification('vastavshivam@gmai.com', "uploaded successfully.", body="File uploaded ...")

#     return JSONResponse(content={
#     "message": f"✅ File {file.filename} uploaded successfully.",
#     "filename": file.filename,
#     "preview": preview  # Optional: parsed preview from CSV/JSON/XLSX
# })
