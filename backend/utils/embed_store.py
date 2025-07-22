# utils/embed_store.py

import os
import faiss
import pickle
from sentence_transformers import SentenceTransformer
from typing import List, Tuple
import numpy as np
import re

# Load embedding model
EMBED_MODEL = SentenceTransformer("all-MiniLM-L6-v2")

# Output directory
VECTOR_DIR = "vector_stores"
os.makedirs(VECTOR_DIR, exist_ok=True)

# ------------------------------
# Text Chunking using simple sentence splitting
# ------------------------------
def chunk_text(text: str, chunk_size=500) -> List[str]:
    """
    Split text into chunks optimized for Q&A content and general text.
    Each chunk tries not to exceed the given chunk size.
    """
    # First, try to split by Q&A patterns if this looks like Q&A content
    if "Q:" in text and "A:" in text:
        # Split by Q&A pairs (separated by double newlines in our format)
        qa_pairs = text.split("\n\n")
        chunks = []
        for pair in qa_pairs:
            pair = pair.strip()
            if not pair:
                continue
                
            # If the pair is still too long, split it further
            if len(pair) > chunk_size:
                sentences = re.split(r'(?<=[.!?])\s+', pair)
                current_chunk = ""
                for sentence in sentences:
                    sentence = sentence.strip()
                    if not sentence:
                        continue
                    if len(current_chunk + sentence) + 1 <= chunk_size:
                        current_chunk += sentence + " "
                    else:
                        if current_chunk.strip():
                            chunks.append(current_chunk.strip())
                        current_chunk = sentence + " "
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
            else:
                chunks.append(pair)
        return [chunk for chunk in chunks if chunk.strip()]
    
    # For non-Q&A content, use the original sentence-based splitting
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    
    chunks = []
    current = ""
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
            
        if len(current) + len(sentence) + 1 <= chunk_size:
            current += sentence + " "
        else:
            if current.strip():
                chunks.append(current.strip())
            current = sentence + " "
    
    # Add the last chunk if it exists
    if current.strip():
        chunks.append(current.strip())
    
    # If no sentences were found, split by character limit
    if not chunks and text.strip():
        words = text.split()
        current = ""
        for word in words:
            if len(current) + len(word) + 1 <= chunk_size:
                current += word + " "
            else:
                if current.strip():
                    chunks.append(current.strip())
                current = word + " "
        if current.strip():
            chunks.append(current.strip())
    
    return chunks if chunks else [text.strip()] if text.strip() else []

# ------------------------------
# Save Embeddings
# ------------------------------
def save_embeddings(file_id: str, chunks: List[str]):
    """
    Compute and store embeddings using FAISS and pickle.
    """
    embeddings = EMBED_MODEL.encode(chunks)
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)

    # Save FAISS index
    faiss.write_index(index, f"{VECTOR_DIR}/{file_id}.index")

    # Save original chunks
    with open(f"{VECTOR_DIR}/{file_id}_chunks.pkl", "wb") as f:
        pickle.dump(chunks, f)

# ------------------------------
# Load Embeddings
# ------------------------------
def load_index(file_id: str) -> Tuple[faiss.IndexFlatL2, List[str]]:
    """
    Load FAISS index and corresponding text chunks.
    """
    index = faiss.read_index(f"{VECTOR_DIR}/{file_id}.index")
    with open(f"{VECTOR_DIR}/{file_id}_chunks.pkl", "rb") as f:
        chunks = pickle.load(f)
    return index, chunks

# ------------------------------
# Embed a Single Question
# ------------------------------
def embed_question(question: str) -> np.ndarray:
    """
    Convert a single question into its embedding.
    """
    return EMBED_MODEL.encode([question])

# ------------------------------
# Query Vector Store
# ------------------------------
def query_embeddings(file_id, query, top_k=5):
    """
    Search top-k most relevant text chunks for a query.
    """
    index_path = f"{VECTOR_DIR}/{file_id}.index"
    data_path = f"{VECTOR_DIR}/{file_id}_chunks.pkl"
    print(f"[🔍] Searching in: {index_path}")
    
    if not os.path.exists(index_path) or not os.path.exists(data_path):
        raise FileNotFoundError("Vector index or chunk file not found.")

    index = faiss.read_index(index_path)
    with open(data_path, "rb") as f:
        chunks = pickle.load(f)

    query_vector = EMBED_MODEL.encode([query])
    D, I = index.search(query_vector, top_k)

    return [chunks[i] for i in I[0]]
