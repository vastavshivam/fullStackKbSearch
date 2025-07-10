from models.inference import query_mistral
from models.vector_store import get_top_k_docs

async def generate_response_with_rag(query: str) -> str:
    relevant_context = await  get_top_k_docs(query)
    prompt = f"Context: {relevant_context}\n\nUser: {query}\n\nAI:"
    return await query_mistral(prompt)