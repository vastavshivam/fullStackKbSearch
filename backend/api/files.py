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
from utils.embed_store import chunk_text, save_embeddings
import shutil
import os
from training.fine_tune import fine_tune
from utils.file_parser import parse_file, clean_json, extract_full_text
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
        full_text = extract_full_text(file_path)  # Use new function for full text
        chunks = chunk_text(full_text)
        save_embeddings(file_id=file.filename, chunks=chunks)
        print(f"✅ Generated embeddings for {file.filename} with {len(chunks)} chunks")
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


# Knowledge Base Management Endpoints
@router.get("/kb/entries")
async def get_kb_entries():
    """Get all knowledge base entries"""
    try:
        # For now, return sample data - you can connect to database later
        kb_entries = []
        
        # Check if there are any uploaded JSON files in uploads directory
        upload_files = list(UPLOAD_DIR.glob("*.json"))
        for file_path in upload_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    import json
                    data = json.load(f)
                    if isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict) and 'question' in item and 'answer' in item:
                                kb_entries.append({
                                    "id": item.get('id', len(kb_entries) + 1),
                                    "question": item['question'],
                                    "answer": item['answer'],
                                    "category": item.get('category', 'General'),
                                    "source_file": file_path.name
                                })
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
                continue
                
        return {"entries": kb_entries}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load KB entries: {str(e)}")


@router.post("/kb/entries")
async def create_kb_entry(request: dict):
    """Create a new knowledge base entry"""
    try:
        question = request.get("question")
        answer = request.get("answer")
        category = request.get("category", "General")
        
        if not question or not answer:
            raise HTTPException(status_code=400, detail="Question and answer are required")
        
        # For demo, we'll just return success - you can add database storage later
        return {
            "message": "KB entry created successfully",
            "id": 1001,  # Mock ID
            "question": question,
            "answer": answer,
            "category": category
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create KB entry: {str(e)}")


@router.put("/kb/entries/{entry_id}")
async def update_kb_entry(entry_id: int, request: dict):
    """Update a knowledge base entry"""
    try:
        question = request.get("question")
        answer = request.get("answer")
        category = request.get("category", "General")
        
        if not question or not answer:
            raise HTTPException(status_code=400, detail="Question and answer are required")
        
        return {
            "message": "KB entry updated successfully",
            "id": entry_id,
            "question": question,
            "answer": answer,
            "category": category
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update KB entry: {str(e)}")


@router.delete("/kb/entries/{entry_id}")
async def delete_kb_entry(entry_id: int):
    """Delete a knowledge base entry"""
    try:
        return {"message": f"KB entry {entry_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete KB entry: {str(e)}")


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
