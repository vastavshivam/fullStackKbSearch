# utils/embed_store.py

import os
import faiss
import pickle
from sentence_transformers import SentenceTransformer
from typing import List, Tuple
import numpy as np
import nltk
from nltk.tokenize import sent_tokenize

# Load embedding model
EMBED_MODEL = SentenceTransformer("all-MiniLM-L6-v2")

# Output directory
VECTOR_DIR = "vector_stores"
os.makedirs(VECTOR_DIR, exist_ok=True)

# ------------------------------
# Text Chunking using NLTK
# ------------------------------
def chunk_text(text: str, chunk_size=500) -> List[str]:
    """
    Split text into chunks using NLTK sentence tokenizer.
    Each chunk tries not to exceed the given chunk size.
    """
    sentences = sent_tokenize(text)
    chunks = []
    current = ""
    for sentence in sentences:
        if len(current) + len(sentence) <= chunk_size:
            current += sentence + " "
        else:
            chunks.append(current.strip())
            current = sentence + " "
    if current:
        chunks.append(current.strip())
    return chunks

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
