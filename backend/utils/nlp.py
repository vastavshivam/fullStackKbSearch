from random import choice
from sentence_transformers import SentenceTransformer

# Load BERT embedding model once
embed_model = SentenceTransformer('all-MiniLM-L6-v2')

def analyze_sentiment(text: str) -> str:
    # Replace this with actual sentiment model
    return choice(["positive", "neutral", "negative"])

def compute_embedding(text: str):
    return embed_model.encode(text).tolist()
