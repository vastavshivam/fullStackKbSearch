# models/vector_store.py

from typing import List, Dict, Optional
import os
import glob
from utils.embed_store import query_embeddings

async def get_top_k_docs(query: str, k: int = 3, client_id: str = None) -> List[Dict[str, str]]:
    """
    Get top k most relevant documents from all knowledge bases or client-specific ones
    """
    vector_dir = "vector_stores"
    if not os.path.exists(vector_dir):
        return []
    
    all_results = []
    
    # Get client-specific pattern if client_id provided
    if client_id:
        pattern = f"{vector_dir}/{client_id}_*.index"
    else:
        pattern = f"{vector_dir}/*.index"
    
    index_files = glob.glob(pattern)
    
    for index_file in index_files:
        try:
            file_id = os.path.basename(index_file).replace('.index', '')
            docs = query_embeddings(file_id, query, k)
            
            for i, doc_content in enumerate(docs):
                all_results.append({
                    "title": file_id,
                    "content": doc_content,
                    "source": file_id,
                    "relevance_score": k - i,  # Simple scoring based on order
                    "file_id": file_id,
                    "client_id": client_id
                })
                
        except Exception as e:
            print(f"Error searching in {file_id}: {e}")
            continue
    
    # Sort by relevance and return top k results
    all_results.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
    return all_results[:k]

async def get_widget_knowledge_base(client_id: str, query: str, k: int = 3) -> List[Dict[str, str]]:
    """
    Get knowledge base results specifically for a widget client
    """
    return await get_top_k_docs(query, k=k, client_id=client_id)

def get_available_knowledge_bases() -> List[str]:
    """
    Get list of available knowledge base files
    """
    vector_dir = "vector_stores"
    if not os.path.exists(vector_dir):
        return []
    
    index_files = glob.glob(f"{vector_dir}/*.index")
    return [os.path.basename(f).replace('.index', '') for f in index_files]
