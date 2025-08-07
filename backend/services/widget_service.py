"""
Widget Service - Database operations for widget configurations
"""
from database.sync_database import SyncSessionLocal
from models.db_models import WidgetConfig as DBWidgetConfig, WidgetKnowledgeBase, WidgetAnalytics
from datetime import datetime
from typing import List, Dict, Optional
import json
import logging

logger = logging.getLogger(__name__)

class WidgetService:
    """Service class for widget database operations"""
    
    @staticmethod
    def save_widget_config(config: WidgetConfig, db: Session) -> DBWidgetConfig:
        """Save or update widget configuration in database"""
        try:
            # Check if widget already exists
            db_widget = db.query(DBWidgetConfig).filter(
                DBWidgetConfig.client_id == config.client_id
            ).first()
            
            # Convert config to dict
            config_dict = config.dict()
            
            if db_widget:
                # Update existing widget
                db_widget.config_data = config_dict
                db_widget.is_active = config.is_active
                db_widget.widget_name = config.chat_title or "AI Assistant"
                db_widget.domain = config.domain
                db_widget.updated_at = datetime.utcnow()
            else:
                # Create new widget
                db_widget = DBWidgetConfig(
                    client_id=config.client_id,
                    is_active=config.is_active,
                    widget_name=config.chat_title or "AI Assistant",
                    domain=config.domain,
                    config_data=config_dict,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(db_widget)
            
            db.commit()
            db.refresh(db_widget)
            return db_widget
            
        except Exception as e:
            logger.error(f"Failed to save widget config: {e}")
            db.rollback()
            raise

    @staticmethod
    def get_widget_config(client_id: str, db: Session) -> Optional[WidgetConfig]:
        """Get widget configuration from database"""
        try:
            db_widget = db.query(DBWidgetConfig).filter(
                DBWidgetConfig.client_id == client_id
            ).first()
            
            if not db_widget:
                return None
            
            # Convert stored config back to WidgetConfig object
            config_data = db_widget.config_data
            config_data["client_id"] = client_id  # Ensure client_id is set
            
            return WidgetConfig(**config_data)
            
        except Exception as e:
            logger.error(f"Failed to get widget config: {e}")
            return None

    @staticmethod
    def get_all_widget_configs(db: Session) -> List[Dict]:
        """Get all widget configurations"""
        try:
            db_widgets = db.query(DBWidgetConfig).all()
            
            widgets = []
            for db_widget in db_widgets:
                widget_data = {
                    "id": db_widget.id,
                    "client_id": db_widget.client_id,
                    "is_active": db_widget.is_active,
                    "widget_name": db_widget.widget_name,
                    "domain": db_widget.domain,
                    "created_at": db_widget.created_at.isoformat() if db_widget.created_at else None,
                    "updated_at": db_widget.updated_at.isoformat() if db_widget.updated_at else None,
                    "config": db_widget.config_data
                }
                widgets.append(widget_data)
            
            return widgets
            
        except Exception as e:
            logger.error(f"Failed to get all widget configs: {e}")
            return []

    @staticmethod
    def delete_widget_config(client_id: str, db: Session) -> bool:
        """Delete widget configuration"""
        try:
            db_widget = db.query(DBWidgetConfig).filter(
                DBWidgetConfig.client_id == client_id
            ).first()
            
            if db_widget:
                db.delete(db_widget)
                db.commit()
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete widget config: {e}")
            db.rollback()
            return False

    @staticmethod
    def delete_widget_config(self, client_id: str) -> bool:
        """Delete widget configuration"""
        try:
            config = self.db.query(WidgetConfig).filter(WidgetConfig.client_id == client_id).first()
            if config:
                self.db.delete(config)
                self.db.commit()
                return True
            return False
        except Exception as e:
            self.db.rollback()
            print(f"Error deleting widget config: {e}")
            return False

    def save_knowledge_base_document(self, client_id: str, document_data: dict) -> Optional[WidgetKnowledgeBase]:
        """Save knowledge base document to database"""
        try:
            # Get widget
            db_widget = db.query(DBWidgetConfig).filter(
                DBWidgetConfig.client_id == client_id
            ).first()
            
            if not db_widget:
                logger.error(f"Widget not found for client_id: {client_id}")
                return False
            
            # Check if document already exists
            existing_doc = db.query(WidgetKnowledgeBase).filter(
                WidgetKnowledgeBase.document_id == document["id"]
            ).first()
            
            if existing_doc:
                # Update existing document
                existing_doc.content = document["content"]
                existing_doc.word_count = document.get("word_count", 0)
                existing_doc.char_count = document.get("char_count", 0)
            else:
                # Create new document
                kb_doc = WidgetKnowledgeBase(
                    widget_id=db_widget.id,
                    document_id=document["id"],
                    filename=document["filename"],
                    content=document["content"],
                    file_type=document["type"],
                    size_mb=str(document.get("size_mb", 0)),
                    word_count=document.get("word_count", 0),
                    char_count=document.get("char_count", 0),
                    uploaded_at=datetime.fromisoformat(document["uploaded_at"]) if "uploaded_at" in document else datetime.utcnow()
                )
                db.add(kb_doc)
            
            db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Failed to save knowledge base document: {e}")
            db.rollback()
            return False

    @staticmethod
    def get_knowledge_base_documents(client_id: str, db: Session) -> List[Dict]:
        """Get all knowledge base documents for a widget"""
        try:
            db_widget = db.query(DBWidgetConfig).filter(
                DBWidgetConfig.client_id == client_id
            ).first()
            
            if not db_widget:
                return []
            
            kb_docs = db.query(WidgetKnowledgeBase).filter(
                WidgetKnowledgeBase.widget_id == db_widget.id
            ).all()
            
            documents = []
            for doc in kb_docs:
                documents.append({
                    "id": doc.document_id,
                    "filename": doc.filename,
                    "content": doc.content,
                    "type": doc.file_type,
                    "size_mb": float(doc.size_mb) if doc.size_mb else 0,
                    "word_count": doc.word_count,
                    "char_count": doc.char_count,
                    "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
                    "client_id": client_id
                })
            
            return documents
            
        except Exception as e:
            logger.error(f"Failed to get knowledge base documents: {e}")
            return []

    @staticmethod
    def clear_knowledge_base(client_id: str, db: Session) -> bool:
        """Clear all knowledge base documents for a widget"""
        try:
            db_widget = db.query(DBWidgetConfig).filter(
                DBWidgetConfig.client_id == client_id
            ).first()
            
            if not db_widget:
                return False
            
            # Delete all knowledge base documents
            db.query(WidgetKnowledgeBase).filter(
                WidgetKnowledgeBase.widget_id == db_widget.id
            ).delete()
            
            db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear knowledge base: {e}")
            db.rollback()
            return False

    @staticmethod
    def save_analytics_event(event: AnalyticsEvent, db: Session) -> bool:
        """Save analytics event to database"""
        try:
            analytics_record = WidgetAnalytics(
                client_id=event.client_id,
                event_type=event.event_type,
                session_id=event.session_id,
                user_id=event.user_id,
                event_data=event.metadata if event.metadata else {},
                user_info=event.user_info if event.user_info else {},
                conversation_data=event.conversation_data if event.conversation_data else {},
                lead_score=str(event.lead_score) if event.lead_score else "0.0",
                timestamp=event.timestamp
            )
            
            db.add(analytics_record)
            db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Failed to save analytics event: {e}")
            db.rollback()
            return False

# Utility function to get database session
def get_db_session():
    """Get database session"""
    db = next(get_db())
    try:
        return db
    finally:
        pass  # Don't close here, let the caller handle it
