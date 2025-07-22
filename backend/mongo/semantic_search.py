# semantic_search.py
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from bson import ObjectId
from pymongo import MongoClient

# Load embedder
embedder = SentenceTransformer("all-MiniLM-L6-v2")

# Mongo
MONGO_URI = "mongodb://localhost:27017"
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["chat_support"]
chat_logs_col = db["chat_logs"]

# FAISS index
embedding_dim = 384
index = faiss.IndexFlatL2(embedding_dim)
id_map = []

def build_faiss_index():
    """
    Load all embeddings into FAISS index.
    """
    global id_map
    embeddings = []
    cursor = chat_logs_col.find({"embedding": {"$exists": True}})
    for doc in cursor:
        emb = np.array(doc["embedding"], dtype=np.float32)
        embeddings.append(emb)
        id_map.append(str(doc["_id"]))
    if embeddings:
        index.add(np.vstack(embeddings))
    print(f"FAISS index loaded with {len(id_map)} vectors.")

def find_similar_messages(query_text, top_k=3):
    """
    Search top-k similar messages.
    """
    query_emb = embedder.encode([query_text])[0].astype(np.float32).reshape(1, -1)
    if index.ntotal == 0:
        return []
    distances, indices = index.search(query_emb, top_k)
    results = []
    for i, idx in enumerate(indices[0]):
        mongo_id = id_map[idx]
        doc = chat_logs_col.find_one({"_id": ObjectId(mongo_id)})
        results.append({
            "message": doc["message"],
            "sender": doc["sender"],
            "session_id": doc["session_id"],
            "distance": float(distances[0][i])
        })
    return results

if __name__ == "__main__":
    build_faiss_index()
    query = "I forgot my password"
    matches = find_similar_messages(query)
    for m in matches:
        print(m)
