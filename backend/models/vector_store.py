# models/vector_store.py

from typing import List, Dict

async def get_top_k_docs(query: str, k: int = 3) -> List[Dict[str, str]]:
    """
    Mock function to return top-k similar documents.
    Replace this with actual vector DB search (e.g., FAISS, ChromaDB, Weaviate, etc.)
    """
    print(f"Searching vector store for query: {query}")
    return [
        {"title": "Doc 1", "content": f"Relevant content for '{query}' - doc 1"},
        {"title": "Doc 2", "content": f"Relevant content for '{query}' - doc 2"},
        {"title": "Doc 3", "content": f"Relevant content for '{query}' - doc 3"},
    ][:k]
