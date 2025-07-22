from pymongo import MongoClient
import json
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

mongo_client = MongoClient("mongodb://localhost:27017")
db = mongo_client["chat_support"]
logs = list(db["chat_logs"].find())

analyzer = SentimentIntensityAnalyzer()
output_file = "training/data/fine_tune_reward.jsonl"

with open(output_file, "w") as f:
    for doc in logs:
        prompt = doc.get("user_message") or doc.get("prompt")
        response = doc.get("bot_reply") or doc.get("response")
        if not prompt or not response:
            continue

        sentiment_score = analyzer.polarity_scores(response)["compound"]
        if sentiment_score > 0.3:
            reward = 1.0
        elif sentiment_score < -0.3:
            reward = -1.0
        else:
            reward = 0.0

        record = {"prompt": prompt, "response": response, "reward": reward}
        json.dump(record, f)
        f.write("\n")

print("✅ JSONL exported from MongoDB")







