# scripts/sentiment_trend.py

from pymongo import MongoClient
from datetime import datetime

MONGO_URI = "mongodb://localhost:27017"
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["chat_support"]
chat_logs_col = db["chat_logs"]

def get_daily_sentiment_trends():
    pipeline = [
        {
            "$group": {
                "_id": {
                    "date": {
                        "$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}
                    },
                    "sentiment": "$sentiment"
                },
                "count": {"$sum": 1}
            }
        },
        {
            "$sort": {"_id.date": 1}
        }
    ]

    results = chat_logs_col.aggregate(pipeline)

    trends = {}
    for doc in results:
        date = doc["_id"]["date"]
        sentiment = doc["_id"]["sentiment"]
        count = doc["count"]
        if date not in trends:
            trends[date] = {}
        trends[date][sentiment] = count

    return trends

if __name__ == "__main__":
    trends = get_daily_sentiment_trends()
    for date, sentiment_counts in trends.items():
        print(f"{date}: {sentiment_counts}")
