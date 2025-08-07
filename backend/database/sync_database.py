from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# SQLite database path
DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'widget_persistence.db')

# Create data directory if it doesn't exist
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# SQLite database URL
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Create synchronous engine for SQLite
sync_engine = create_engine(
    DATABASE_URL,
    echo=True,
    connect_args={"check_same_thread": False}  # Allow multiple threads for SQLite
)

# Synchronous session factory
SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

# Base model class
SyncBase = declarative_base()

def get_sync_db():
    """Get a synchronous database session"""
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_sync_tables():
    """Create all tables synchronously"""
    # Import models to register them
    from models.db_models import WidgetConfig, WidgetKnowledgeBase, WidgetAnalytics
    
    print(f"Creating tables in SQLite database: {DB_PATH}")
    SyncBase.metadata = declarative_base().metadata
    
    # Manually register the tables we need
    WidgetConfig.__table__.create(sync_engine, checkfirst=True)
    WidgetKnowledgeBase.__table__.create(sync_engine, checkfirst=True)
    WidgetAnalytics.__table__.create(sync_engine, checkfirst=True)
    
    print("Tables created successfully!")

if __name__ == "__main__":
    create_sync_tables()
