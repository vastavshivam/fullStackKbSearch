#!/usr/bin/env python3

import pickle
from utils.embed_store import query_embeddings

# Debug the stored embeddings
with open("vector_stores/test_qa.json_chunks.pkl", "rb") as f:
    chunks = pickle.load(f)

print("Number of chunks:", len(chunks))
print("\nStored chunks:")
for i, chunk in enumerate(chunks):
    print(f"Chunk {i}:")
    print(repr(chunk))
    print("-" * 50)

# Test search functionality
print("\nTesting search queries:")
test_queries = [
    "How can I reset my password?",
    "Why is the app crashing on startup?",
    "What features does the premium plan offer?"
]

for query in test_queries:
    print(f"\nQuery: {query}")
    try:
        results = query_embeddings("test.json", query, top_k=1)
        print(f"Results: {results}")
    except Exception as e:
        print(f"Error: {e}")
