
from models.inference import query_mistral
from models.vector_store import get_top_k_docs

async def generate_response_with_rag(query: str) -> str:
    relevant_context = await get_top_k_docs(query)
    prompt = f"Context: {relevant_context}\n\nUser: {query}\n\nAI:"
    return await query_mistral(prompt)

# Utility to summarize a conversation and generate a title
async def summarize_conversation(conversation_history: list) -> dict:
    # Flatten messages for prompt
    history_text = "\n".join([
        f"{msg['sender']}: {msg['message']}" for msg in conversation_history
    ])
    prompt = f"Summarize the following conversation and suggest a short title.\n\nConversation:\n{history_text}\n\nSummary:"
    summary = await query_mistral(prompt)
    title_prompt = f"Suggest a short, descriptive title for this conversation.\n\nConversation:\n{history_text}\n\nTitle:"
    title = await query_mistral(title_prompt)
    return {"summary": summary, "title": title}