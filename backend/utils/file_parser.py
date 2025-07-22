import pandas as pd
import json
from pathlib import Path
import PyPDF2
import base64
from PIL import Image
from io import BytesIO
import math
import numpy as np

# ==========================================
# 💡 Support Assistant Project .gitignore
# For FastAPI + PostgreSQL + React + Docker
# Author: Shivam Srivastav
# ==========================================
# File: backend/api/files.py    
# ==========================================

def clean_json(obj):
        if isinstance(obj, dict):
            return {k: clean_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [clean_json(item) for item in obj]
        elif isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
            return None
        elif isinstance(obj, np.floating) and (np.isnan(obj) or np.isinf(obj)):
            return None
        else:
            return obj

def parse_file(file_path: Path, limit: int = 10):
    """
    Parses files (.csv, .xlsx, .json, .txt, .pdf, image) and returns a preview of first `limit` records or metadata.
    author: 
        shivam srivastav
        date: 2025-07-01
    Args:
        file_path (Path): Path to the uploaded file
        limit (int): Max number of records or preview lines

    Returns:
        dict: {
            "filename": str,
            "type": str,
            "preview": list or dict (depends on type)
        }
    """
    ext = file_path.suffix.lower()

    try:
        if ext == ".csv":
            df = pd.read_csv(file_path)
            preview_data = df.head(limit).to_dict(orient="records")

        elif ext == ".xlsx":
            df = pd.read_excel(file_path)
            preview_data = df.head(limit).to_dict(orient="records")

        elif ext == ".json":
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    preview_data = data[:limit]
                elif isinstance(data, dict):
                    preview_data = [{k: data[k]} for k in list(data.keys())[:limit]]
                else:
                    raise ValueError("Unsupported JSON structure")

        elif ext == ".txt":
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                preview_data = [{"line": line.strip()} for line in lines[:limit]]

        elif ext == ".pdf":
            preview_data = []
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page_num in range(min(limit, len(reader.pages))):
                    page = reader.pages[page_num]
                    text = page.extract_text()
                    preview_data.append({
                        "page": page_num + 1,
                        "text": text.strip() if text else "[Empty]"
                    })

        elif ext in [".png", ".jpg", ".jpeg", ".gif", ".bmp"]:
            with Image.open(file_path) as img:
                buffered = BytesIO()
                img.save(buffered, format=img.format)
                encoded_image = base64.b64encode(buffered.getvalue()).decode("utf-8")
                preview_data = {
                    "format": img.format,
                    "mode": img.mode,
                    "size": img.size,
                    "preview_base64": f"data:image/{img.format.lower()};base64,{encoded_image}"
                }

        else:
            raise ValueError(f"Unsupported file type: {ext}")

        return {
            "filename": file_path.name,
            "type": ext[1:],  # e.g. jpg
            "preview": clean_json(preview_data)
        }

    except Exception as e:
        raise RuntimeError(f"❌ Failed to parse file: {str(e)}")


def extract_text_content(file_path: Path) -> str:
    """
    Extract full text content from various file types for embedding purposes.
    Returns the complete text content as a single string.
    """
    ext = file_path.suffix.lower()
    
    try:
        if ext == ".csv":
            df = pd.read_csv(file_path)
            # Convert all columns to text and join
            text_content = ""
            for _, row in df.iterrows():
                text_content += " ".join([str(val) for val in row.values if pd.notna(val)]) + "\n"
            return text_content.strip()

        elif ext == ".xlsx":
            df = pd.read_excel(file_path)
            # Convert all columns to text and join
            text_content = ""
            for _, row in df.iterrows():
                text_content += " ".join([str(val) for val in row.values if pd.notna(val)]) + "\n"
            return text_content.strip()

        elif ext == ".json":
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            # Extract text from JSON structure - create better chunks for Q&A pairs
            def extract_json_text(obj):
                if isinstance(obj, dict):
                    # If this looks like a Q&A pair, format it for KB
                    if "prompt" in obj and "response" in obj:
                        sentiment = obj.get("sentiment", "neutral")
                        return f"prompt: {obj['prompt']} response: {obj['response']} sentiment: {sentiment}"
                    else:
                        texts = []
                        for key, value in obj.items():
                            if isinstance(value, (str, int, float)):
                                texts.append(f"{key}: {value}")
                            elif isinstance(value, (dict, list)):
                                texts.append(extract_json_text(value))
                        return " ".join(texts)
                elif isinstance(obj, list):
                    # For lists, separate each item with double newlines for better chunking
                    return "\n\n".join([extract_json_text(item) for item in obj])
                else:
                    return str(obj)
            
            return extract_json_text(data)

        elif ext == ".txt":
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()

        elif ext == ".pdf":
            text_content = ""
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        text_content += text + "\n"
            return text_content.strip()

        else:
            # For unsupported formats, return empty string
            return ""

    except Exception as e:
        print(f"Error extracting text from {file_path}: {str(e)}")
        return ""
