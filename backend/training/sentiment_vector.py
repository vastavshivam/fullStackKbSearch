from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification, AutoModelForSeq2SeqLM
from sentence_transformers import SentenceTransformer, util
from pymongo import MongoClient
from pinecone import Pinecone, ServerlessSpec
import numpy as np
import uuid

# ------------------- Load Models -------------------
print("[🧠] Loading models...")

embedder = SentenceTransformer("all-MiniLM-L6-v2")

sentiment_model_name = "nlptown/bert-base-multilingual-uncased-sentiment"
sentiment_tokenizer = AutoTokenizer.from_pretrained(sentiment_model_name)
sentiment_model = AutoModelForSequenceClassification.from_pretrained(sentiment_model_name)
sentiment_pipeline = pipeline("sentiment-analysis", model=sentiment_model, tokenizer=sentiment_tokenizer)

summarizer_model_name = "facebook/bart-large-cnn"
summarizer_tokenizer = AutoTokenizer.from_pretrained(summarizer_model_name)
summarizer_model = AutoModelForSeq2SeqLM.from_pretrained(summarizer_model_name)

# ------------------- Knowledge Base -------------------
print("[📚] Encoding knowledge base articles...")

kb_articles = [
    "How to reset your password",
    "Steps to cancel your subscription",
    "How to update billing details",
    "Installation instructions for the mobile app",
    "How to connect to your smart device",
    "How are you?"
]
kb_embeddings = embedder.encode(kb_articles, convert_to_tensor=True)

# ------------------- MongoDB -------------------
print("[🔌] Connecting to MongoDB...")

client = MongoClient("mongodb+srv://RootAdmin:root@atlascluster.0ktshci.mongodb.net/?retryWrites=true&w=majority&appName=AtlasCluster")
collection = client["Portfolio"]["Portfolio-Website"]

# ------------------- Pinecone -------------------
print("[🌐] Connecting to Pinecone...")

pc = Pinecone(api_key="***")  # Replace with your actual API key
index_name = "pdf-rag-index"

if index_name not in pc.list_indexes().names():
    print(f"[📦] Index '{index_name}' not found. Creating...")
    pc.create_index(
        name=index_name,
        dimension=384,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )
else:
    print(f"[📦] Index '{index_name}' found.")

index = pc.Index(index_name)

# ------------------- Process Chat Sessions -------------------
print("[🚀] Starting chat session processing...")

for session in collection.find():
    session_id = str(session["_id"])
    chat = session.get("chat", [])

    if not chat:
        print(f"[⚠️] Skipping empty session: {session_id}")
        continue

    print(f"\n🔍 Processing session: {session_id}")
    chat_text = " ".join([msg["message"] for msg in chat])
    print(f"[💬] Chat text length: {len(chat_text)} characters")

    try:
        # 1. Knowledge Base Similarity
        chat_embedding_tensor = embedder.encode(chat_text, convert_to_tensor=True)
        kb_scores = util.cos_sim(chat_embedding_tensor, kb_embeddings)
        raw_score = float(kb_scores.max())
        best_kb_index = int(kb_scores.argmax())

        kb_threshold = 0.6
        if raw_score >= kb_threshold:
            is_kb = True
            kb_match_score = raw_score
            closest_kb_article = kb_articles[best_kb_index]
        else:
            is_kb = False
            kb_match_score = 0.0
            closest_kb_article = "None"

        print(f"[📌] KB match score: {kb_match_score:.4f} | is_kb: {is_kb} | article: {closest_kb_article}")

        # 2. Sentiment Analysis
        chunks = [chat_text[i:i+512] for i in range(0, len(chat_text), 512)]
        sentiments = [sentiment_pipeline(chunk)[0] for chunk in chunks]

        avg_score = float(np.mean([s["score"] for s in sentiments]))
        overall_label = max(set(s["label"] for s in sentiments), key=[s["label"] for s in sentiments].count)
        print(f"[❤️] Sentiment: {overall_label} | Avg Score: {avg_score:.2f}")

        # 3. Summary Generation
        print("[✍️] Generating summary...")
        inputs = summarizer_tokenizer([chat_text], max_length=1024, return_tensors="pt", truncation=True)
        summary_ids = summarizer_model.generate(
            inputs["input_ids"], max_length=150, min_length=30,
            length_penalty=2.0, num_beams=4, early_stopping=True
        )
        summary = summarizer_tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        print(f"[📝] Summary: {summary}")

        # 4. Update MongoDB
        collection.update_one(
            {"_id": session["_id"]},
            {"$set": {
                "is_kb_chat": is_kb,
                "kb_match_score": kb_match_score,
                "overall_sentiment": overall_label,
                "sentiment_score": avg_score,
                "chat_summary": summary,
                "closest_kb_article": closest_kb_article
            }}
        )
        print("[✅] MongoDB updated.")

        # 5. Pinecone Vector Indexing (Only if KB-related)
        if is_kb:
            vector_embedding = embedder.encode(summary).tolist()
            metadata = {
                "session_id": session_id,
                "summary": summary,
                "sentiment": overall_label,
                "sentiment_score": avg_score,
                "is_kb_chat": is_kb,
                "closest_kb_article": closest_kb_article
            }
            pinecone_id = str(uuid.uuid4())
            index.upsert([(pinecone_id, vector_embedding, metadata)])
            print(f"[📥] Stored in Pinecone with ID: {pinecone_id}")
        else:
            print(f"[⏭️] Skipped Pinecone upload for session {session_id} (not a KB chat)")

    except Exception as e:
        print(f"[❌] Error in session {session_id}: {e}")

print("\n[🏁] All chat sessions processed and indexed.")
