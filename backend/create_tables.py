import asyncio
from database.database import Base, engine
from models.db_models import (
    User, Ticket, UserFeedback, HumanEscalation, 
    WidgetConfig, WidgetKnowledgeBase, WidgetAnalytics,
    ChatLog, Item, ClientConfig, ChatHistory
)

async def create_tables():
    """Create all tables asynchronously"""
    print("Creating tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created successfully!")

if __name__ == "__main__":
    asyncio.run(create_tables())
