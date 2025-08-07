from typing import Text
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, DateTime, func, JSON
from sqlalchemy.orm import relationship
from database.database import Base
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
import uuid


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    role = Column(String, default="user")  # <-- add this line

    # these two must correspond to the other side’s back_populates
    items = relationship("Item", back_populates="owner")
    tickets = relationship("Ticket", back_populates="user")
    feedbacks = relationship(
        "UserFeedback",
        back_populates="user",
        cascade="all, delete-orphan"
    )


class Item(Base):
    __tablename__ = "items" 

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    description = Column(String, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="items")

class ChatLog(Base):
    __tablename__ = "chat_logs"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    user_input = Column(Text)
    bot_response = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)


class Ticket(Base):    
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(50), default="open")
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="tickets")   

class UserFeedback(Base):
    __tablename__ = "user_feedback"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    feedback_text = Column(Text, nullable=False)
    rating = Column(Integer, nullable=False)  # e.g., 1-5 scale
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="feedbacks")


class HumanEscalation(Base):
    __tablename__ = "human_escalations"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    reason = Column(Text)
    escalated_at = Column(DateTime, default=datetime.utcnow)

class ClientConfig(Base):
    __tablename__ = "client_config"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(String, nullable=False)
    sender = Column(String, nullable=False)  # e.g., 'user' or 'bot'
    user_number = Column(String, nullable=False)  # WhatsApp number
    message = Column(Text, nullable=False)
    message_type = Column(String, default="text")  # Optional: 'text', 'image', etc.
    direction = Column(String, nullable=False)  # 'incoming' or 'outgoing'
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(String, nullable=False)
    sender = Column(String, nullable=False)  # e.g., 'user' or 'bot'
    user_number = Column(String, nullable=False)  # WhatsApp number
    message = Column(Text, nullable=False)
    message_type = Column(String, default="text")  # Optional: 'text', 'image', etc.
    direction = Column(String, nullable=False)  # 'incoming' or 'outgoing'
    timestamp = Column(DateTime(timezone=True), server_default=func.now())


class WidgetConfig(Base):
    __tablename__ = "widget_configs"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Optional: link to user
    
    # Basic Widget Settings
    is_active = Column(Boolean, default=True)
    widget_name = Column(String, default="AI Assistant")
    domain = Column(String, nullable=True)
    
    # Configuration as JSON
    config_data = Column(JSON, nullable=False)  # Store all widget configuration
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", backref="widgets")
    knowledge_base_docs = relationship("WidgetKnowledgeBase", back_populates="widget", cascade="all, delete-orphan")


class WidgetKnowledgeBase(Base):
    __tablename__ = "widget_knowledge_base"

    id = Column(Integer, primary_key=True, index=True)
    widget_id = Column(Integer, ForeignKey("widget_configs.id"), nullable=False)
    
    # Document Information
    document_id = Column(String, unique=True, nullable=False)  # Hash-based ID
    filename = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    file_type = Column(String, nullable=False)
    size_mb = Column(String, nullable=True)
    
    # Metadata
    word_count = Column(Integer, default=0)
    char_count = Column(Integer, default=0)
    
    # Timestamps
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    widget = relationship("WidgetConfig", back_populates="knowledge_base_docs")


class WidgetAnalytics(Base):
    __tablename__ = "widget_analytics"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(String, nullable=False, index=True)
    
    # Event Information
    event_type = Column(String, nullable=False)  # chat_start, message_sent, etc.
    session_id = Column(String, nullable=False)
    user_id = Column(String, nullable=True)
    
    # Event Data
    event_data = Column(JSON, nullable=True)  # Flexible event metadata
    user_info = Column(JSON, nullable=True)  # User information
    conversation_data = Column(JSON, nullable=True)  # Conversation details
    
    # Analytics
    lead_score = Column(String, default="0.0")  # Store as string to avoid float issues
    
    # Timestamps
    timestamp = Column(DateTime, default=datetime.utcnow)
