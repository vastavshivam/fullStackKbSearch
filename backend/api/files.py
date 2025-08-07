# ==========================================
# 💡 Support Assistant Project .gitignore
# For FastAPI + PostgreSQL + React + Docker
# Author: Shivam Srivastav
# ==========================================
# File: backend/api/files.py    
# ==========================================
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from pathlib import Path
from utils.embed_store import chunk_text, save_embeddings
import shutil
import os
import time
from datetime import datetime
from typing import List
from training.fine_tune import fine_tune
from utils.file_parser import parse_file, clean_json, extract_full_text
from utils.email_notify import send_upload_notification

router = APIRouter()

UPLOAD_DIR = Path("uploads") 
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {".csv", ".json", ".xlsx" , ".txt", ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".bmp"}
MAX_FILE_SIZE_MB = 10

@router.post("/upload", summary="Upload knowledge base files")
async def upload_file(background_tasks: BackgroundTasks, files: List[UploadFile] = File(...)):
    """
    Upload multiple files to create knowledge base.
    Supports: PDF, TXT, JSON, CSV, XLSX files
    """
    uploaded_files = []
    all_documents = []
    
    for file in files:
        try:
            # Validate extension
            if not file.filename:
                continue
                
            ext = Path(file.filename).suffix.lower()
            print(f"Processing file: {file.filename} with extension: {ext}")
            
            if ext not in ALLOWED_EXTENSIONS:
                uploaded_files.append({
                    "filename": file.filename,
                    "status": "error",
                    "error": f"Unsupported file type: {ext}"
                })
                continue

            # Read file content as binary
            file_content = await file.read()
            size_mb = len(file_content) / (1024 * 1024)
            
            # Validate size
            if size_mb > MAX_FILE_SIZE_MB:
                uploaded_files.append({
                    "filename": file.filename,
                    "status": "error", 
                    "error": f"File too large (max {MAX_FILE_SIZE_MB}MB)"
                })
                continue

            # Save file with binary write
            file_path = UPLOAD_DIR / file.filename
            print(f"Saving file to: {file_path}")
            
            try:
                with open(file_path, "wb") as f:
                    f.write(file_content)
                print(f"✅ File saved successfully: {file_path}")
            except Exception as save_error:
                print(f"❌ Failed to save file {file.filename}: {save_error}")
                uploaded_files.append({
                    "filename": file.filename,
                    "status": "error",
                    "error": f"Failed to save file: {str(save_error)}"
                })
                continue

            # Extract full text content for knowledge base
            try:
                full_text = extract_full_text(file_path)
                print(f"✅ Extracted {len(full_text)} characters from {file.filename}")
                
                # Store in knowledge base
                from services.simple_widget_service import SimpleWidgetService
                widget_service = SimpleWidgetService()
                
                # Create document entry for knowledge base
                document = {
                    "id": str(hash(file.filename + str(time.time()))),
                    "filename": file.filename,
                    "content": full_text,
                    "type": ext[1:],  # Remove the dot
                    "size_mb": round(size_mb, 2),
                    "uploaded_at": datetime.now().isoformat(),
                    "word_count": len(full_text.split()),
                    "char_count": len(full_text)
                }
                all_documents.append(document)
                
                # Save to knowledge base database
                widget_service.save_knowledge_base_document(
                    client_id="global",  # Global knowledge base
                    filename=file.filename,
                    content=full_text,
                    file_type=ext[1:]
                )
                
                # Generate embeddings for semantic search
                try:
                    chunks = chunk_text(full_text)
                    save_embeddings(file_id=file.filename, chunks=chunks)
                    print(f"✅ Generated embeddings for {file.filename} with {len(chunks)} chunks")
                except Exception as embed_error:
                    print(f"⚠️ Embedding generation failed for {file.filename}: {embed_error}")
                
            except Exception as extraction_error:
                print(f"❌ Text extraction failed for {file.filename}: {extraction_error}")
                uploaded_files.append({
                    "filename": file.filename,
                    "status": "error",
                    "error": f"Failed to extract text: {str(extraction_error)}"
                })
                continue

            # Parse for preview (optional)
            try:
                preview = parse_file(file_path, limit=3)
                preview = clean_json(preview)
                uploaded_files.append({
                    "filename": file.filename,
                    "status": "success",
                    "preview": preview,
                    "size_mb": round(size_mb, 2),
                    "type": ext[1:],
                    "word_count": len(full_text.split()) if 'full_text' in locals() else 0,
                    "char_count": len(full_text) if 'full_text' in locals() else 0
                })
            except Exception as preview_error:
                print(f"⚠️ Preview generation failed for {file.filename}: {preview_error}")
                uploaded_files.append({
                    "filename": file.filename,
                    "status": "success",
                    "size_mb": round(size_mb, 2),
                    "type": ext[1:],
                    "word_count": len(full_text.split()) if 'full_text' in locals() else 0,
                    "char_count": len(full_text) if 'full_text' in locals() else 0,
                    "preview_error": str(preview_error)
                })
                
        except Exception as file_error:
            print(f"❌ Unexpected error processing {file.filename if file.filename else 'unknown file'}: {file_error}")
            uploaded_files.append({
                "filename": file.filename if file.filename else "unknown",
                "status": "error",
                "error": str(file_error)
            })

    # ✅ Start training automatically after successful uploads
    successful_uploads = [f for f in uploaded_files if f.get("status") == "success"]
    if successful_uploads:
        try:
            background_tasks.add_task(fine_tune)
            print(f"✅ Training task scheduled for {len(successful_uploads)} files")
        except Exception as train_error:
            print(f"⚠️ Failed to schedule training: {train_error}")

    # Optional: send notification
    try:
        send_upload_notification("vastavshivam@gmail.com", f"{len(successful_uploads)} files uploaded", body="Knowledge base updated")
    except Exception as notify_error:
        print(f"⚠️ Notification failed: {notify_error}")

    return JSONResponse(content={
        "message": f"✅ Processed {len(uploaded_files)} files - {len(successful_uploads)} successful, {len(uploaded_files) - len(successful_uploads)} failed.",
        "files": uploaded_files,
        "knowledge_base": {
            "total_documents": len(all_documents),
            "total_content_length": sum(len(doc["content"]) for doc in all_documents) if all_documents else 0,
            "document_types": list(set(doc["type"] for doc in all_documents)) if all_documents else [],
            "successful_uploads": len(successful_uploads),
            "failed_uploads": len(uploaded_files) - len(successful_uploads)
        }
    })


# Simple test endpoint for debugging
@router.get("/widget/test/{client_id}")
async def test_widget_endpoint(client_id: str):
    """Test endpoint to verify routing is working"""
    return {
        "message": f"Widget endpoint is working for client: {client_id}",
        "client_id": client_id,
        "timestamp": datetime.now().isoformat()
    }


# Specialized Widget KB Upload - Proper Binary Handling
@router.post("/widget/upload/{client_id}")
async def upload_widget_kb(client_id: str, files: List[UploadFile] = File(...)):
    """
    Upload knowledge base files for a specific widget client.
    Properly handles binary files like PDFs.
    """
    print(f"🚀 KB Upload request received for client: {client_id}")
    print(f"📁 Number of files received: {len(files)}")
    
    uploaded_files = []
    all_documents = []
    
    # Import widget service
    from services.simple_widget_service import SimpleWidgetService
    widget_service = SimpleWidgetService()
    
    for file in files:
        try:
            if not file.filename:
                continue
                
            # Validate extension
            ext = Path(file.filename).suffix.lower()
            print(f"🔄 Processing file: {file.filename} with extension: {ext}")
            
            if ext not in ALLOWED_EXTENSIONS:
                uploaded_files.append({
                    "filename": file.filename,
                    "status": "error",
                    "error": f"Unsupported file type: {ext}"
                })
                continue

            # Read file content as binary (crucial for PDFs)
            file_content = await file.read()
            size_mb = len(file_content) / (1024 * 1024)
            
            # Validate size
            if size_mb > MAX_FILE_SIZE_MB:
                uploaded_files.append({
                    "filename": file.filename,
                    "status": "error",
                    "error": f"File too large (max {MAX_FILE_SIZE_MB}MB)"
                })
                continue

            # Create client-specific upload directory
            client_upload_dir = UPLOAD_DIR / client_id
            client_upload_dir.mkdir(exist_ok=True)
            
            # Save file with binary write mode
            file_path = client_upload_dir / file.filename
            print(f"💾 Saving file to: {file_path}")
            
            try:
                with open(file_path, "wb") as f:
                    f.write(file_content)
                print(f"✅ File saved successfully: {file_path}")
            except Exception as save_error:
                print(f"❌ Failed to save file {file.filename}: {save_error}")
                uploaded_files.append({
                    "filename": file.filename,
                    "status": "error",
                    "error": f"Failed to save file: {str(save_error)}"
                })
                continue

            # Extract text content for knowledge base
            try:
                full_text = extract_full_text(file_path)
                print(f"✅ Extracted {len(full_text)} characters from {file.filename}")
                
                # Create document entry
                document = {
                    "id": str(hash(f"{client_id}_{file.filename}_{time.time()}")),
                    "filename": file.filename,
                    "content": full_text,
                    "type": ext[1:],
                    "size_mb": round(size_mb, 2),
                    "client_id": client_id,
                    "uploaded_at": datetime.now().isoformat(),
                    "word_count": len(full_text.split()),
                    "char_count": len(full_text)
                }
                all_documents.append(document)
                
                # Save to widget-specific knowledge base
                widget_service.save_knowledge_base_document(
                    client_id=client_id,
                    filename=file.filename,
                    content=full_text,
                    file_type=ext[1:]
                )
                print(f"✅ Saved document to knowledge base for client: {client_id}")
                
                # Generate embeddings for semantic search
                try:
                    chunks = chunk_text(full_text)
                    save_embeddings(file_id=f"{client_id}_{file.filename}", chunks=chunks)
                    print(f"✅ Generated embeddings with {len(chunks)} chunks")
                except Exception as embed_error:
                    print(f"⚠️ Embedding generation failed: {embed_error}")
                
                uploaded_files.append({
                    "filename": file.filename,
                    "status": "success",
                    "size_mb": round(size_mb, 2),
                    "type": ext[1:],
                    "word_count": len(full_text.split()),
                    "char_count": len(full_text),
                    "client_id": client_id
                })
                
            except Exception as extraction_error:
                print(f"❌ Text extraction failed for {file.filename}: {extraction_error}")
                uploaded_files.append({
                    "filename": file.filename,
                    "status": "error",
                    "error": f"Failed to extract text: {str(extraction_error)}"
                })
                continue
                
        except Exception as file_error:
            print(f"❌ Unexpected error processing {file.filename if file.filename else 'unknown file'}: {file_error}")
            uploaded_files.append({
                "filename": file.filename if file.filename else "unknown",
                "status": "error",
                "error": str(file_error)
            })

    # Count successful uploads
    successful_uploads = [f for f in uploaded_files if f.get("status") == "success"]
    failed_uploads = len(uploaded_files) - len(successful_uploads)

    return JSONResponse(content={
        "message": f"✅ Processed {len(uploaded_files)} files for client {client_id} - {len(successful_uploads)} successful, {failed_uploads} failed.",
        "client_id": client_id,
        "files": uploaded_files,
        "knowledge_base": {
            "total_documents": len(all_documents),
            "total_content_length": sum(len(doc["content"]) for doc in all_documents) if all_documents else 0,
            "document_types": list(set(doc["type"] for doc in all_documents)) if all_documents else [],
            "successful_uploads": len(successful_uploads),
            "failed_uploads": failed_uploads
        }
    })

# Knowledge Base Retrieval Endpoint
@router.get("/widget/kb/{client_id}")
async def get_widget_knowledge_base(client_id: str):
    """Get knowledge base documents for a specific widget client"""
    try:
        from services.simple_widget_service import SimpleWidgetService
        widget_service = SimpleWidgetService()
        
        documents = widget_service.get_knowledge_base_documents(client_id)
        
        return JSONResponse(content={
            "client_id": client_id,
            "documents": documents,
            "total_documents": len(documents),
            "total_content_length": sum(len(doc.get("content", "")) for doc in documents)
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve knowledge base: {str(e)}")


# Clear Knowledge Base Endpoint
@router.delete("/widget/kb/{client_id}")
async def clear_widget_knowledge_base(client_id: str):
    """Clear all knowledge base documents for a specific widget client"""
    try:
        from services.simple_widget_service import SimpleWidgetService
        widget_service = SimpleWidgetService()
        
        deleted_count = widget_service.clear_knowledge_base(client_id)
        
        return JSONResponse(content={
            "message": f"✅ Cleared knowledge base for client {client_id}",
            "client_id": client_id,
            "deleted_documents": deleted_count
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear knowledge base: {str(e)}")


# Test Upload Endpoint
@router.post("/test-upload")
async def test_upload(file: UploadFile = File(...)):
    """Simple test endpoint to debug file upload issues"""
    try:
        print(f"📤 Test upload received: {file.filename}")
        print(f"📋 Content type: {file.content_type}")
        print(f"📋 Headers: {file.headers}")
        
        # Read file content as binary
        content = await file.read()
        print(f"📊 File size: {len(content)} bytes")
        print(f"📊 First 100 bytes: {content[:100]}")
        
        # Try to save file
        test_path = UPLOAD_DIR / f"test_{file.filename}"
        with open(test_path, "wb") as f:
            f.write(content)
        
        print(f"✅ Test file saved to: {test_path}")
        
        # Try to extract text if PDF
        if file.filename and file.filename.lower().endswith('.pdf'):
            try:
                full_text = extract_full_text(test_path)
                print(f"✅ PDF text extraction successful: {len(full_text)} characters")
                
                return JSONResponse(content={
                    "message": "✅ Test upload successful",
                    "filename": file.filename,
                    "size_bytes": len(content),
                    "content_type": file.content_type,
                    "text_extracted": True,
                    "text_length": len(full_text),
                    "text_preview": full_text[:200] if full_text else None
                })
            except Exception as extract_error:
                print(f"❌ PDF text extraction failed: {extract_error}")
                return JSONResponse(content={
                    "message": "⚠️ File uploaded but text extraction failed",
                    "filename": file.filename,
                    "size_bytes": len(content),
                    "content_type": file.content_type,
                    "text_extracted": False,
                    "extraction_error": str(extract_error)
                })
        
        return JSONResponse(content={
            "message": "✅ Test upload successful",
            "filename": file.filename,
            "size_bytes": len(content),
            "content_type": file.content_type,
            "text_extracted": False,
            "note": "Not a PDF file"
        })
        
    except Exception as e:
        print(f"❌ Test upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Test upload failed: {str(e)}")


# Sample fallback endpoints (keep existing functionality)
@router.get("/entries")
async def get_entries():
    """Get all knowledge base entries"""
    try:
        entries = []
        upload_files = list(UPLOAD_DIR.glob("*.json"))
        
        for file_path in upload_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    import json
                    data = json.load(f)
                    if isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict) and 'question' in item and 'answer' in item:
                                entries.append({
                                    "id": item.get('id', len(entries) + 1),
                                    "question": item['question'],
                                    "answer": item['answer'],
                                    "category": item.get('category', 'General'),
                                    "source_file": file_path.name
                                })
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
                continue
                
        return {"entries": entries}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load entries: {str(e)}")
