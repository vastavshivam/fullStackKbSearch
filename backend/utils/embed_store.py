# utils/embed_store.py
import os
import faiss
import pickle
from sentence_transformers import SentenceTransformer
from typing import List, Tuple
import numpy as np

EMBED_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
VECTOR_DIR = "vector_stores"

os.makedirs(VECTOR_DIR, exist_ok=True)

def chunk_text(text: str, chunk_size=500) -> List[str]:
    sentences = str(text).split('.')
    chunks, current = [], ""
    for sentence in sentences:
        if len(current) + len(sentence) < chunk_size:
            current += sentence + "."
        else:  
            chunks.append(current.strip()) 
            current = sentence + "."
    if current:
        chunks.append(current.strip())
    return chunks

def save_embeddings(file_id: str, chunks: List[str]):
    embeddings = EMBED_MODEL.encode(chunks)
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)

    faiss.write_index(index, f"{VECTOR_DIR}/{file_id}.index")
    with open(f"{VECTOR_DIR}/{file_id}_chunks.pkl", "wb") as f:
        pickle.dump(chunks, f)

def load_index(file_id: str) -> Tuple[faiss.IndexFlatL2, List[str]]:
    index = faiss.read_index(f"{VECTOR_DIR}/{file_id}.index")
    with open(f"{VECTOR_DIR}/{file_id}_chunks.pkl", "rb") as f:
        chunks = pickle.load(f)
    return index, chunks

def embed_question(question: str) -> np.ndarray:
    return EMBED_MODEL.encode([question])

def query_embeddings(file_id, query, top_k=5):
    index_path = f"{VECTOR_DIR}/{file_id}.index"
    data_path = f"{VECTOR_DIR}/{file_id}_chunks.pkl"
    print(f"filepath: {index_path}, data_path: {data_path}")
    if not os.path.exists(index_path) or not os.path.exists(data_path):
        
        raise FileNotFoundError("Vector index or chunk file not found.")

    index = faiss.read_index(index_path)
    with open(data_path, "rb") as f:
        chunks = pickle.load(f)

    query_vector = EMBED_MODEL.encode([query])
    D, I = index.search(query_vector, top_k)
    return [chunks[i] for i in I[0]]
