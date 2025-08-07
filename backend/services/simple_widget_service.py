"""
Simple Widget Service - SQLite-based persistence for widget configurations
"""
import sqlite3
import json
import os
from datetime import datetime
from typing import Optional, Dict, Any

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'widget_configs.db')

class SimpleWidgetService:
    """Simple SQLite-based widget service"""
    
    def __init__(self):
        """Initialize database"""
        self.init_db()
    
    def init_db(self):
        """Initialize SQLite database"""
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Create widget configurations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS widget_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id TEXT UNIQUE NOT NULL,
                user_email TEXT,
                config_data TEXT NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Add user_email column if it doesn't exist (for existing databases)
        try:
            cursor.execute('ALTER TABLE widget_configs ADD COLUMN user_email TEXT')
        except sqlite3.OperationalError:
            # Column already exists
            pass
        
        # Create knowledge base table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS widget_knowledge_base (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id TEXT NOT NULL,
                filename TEXT NOT NULL,
                content TEXT NOT NULL,
                file_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_widget_config(self, client_id: str, config_data: dict, user_email: str = None) -> bool:
        """Save widget configuration"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            config_json = json.dumps(config_data)
            is_active = config_data.get('is_active', True)
            
            # Insert or update configuration
            cursor.execute('''
                INSERT OR REPLACE INTO widget_configs 
                (client_id, user_email, config_data, is_active, updated_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (client_id, user_email, config_json, is_active, datetime.utcnow().isoformat()))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Error saving widget config: {e}")
            return False
    
    def get_widget_config(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Get widget configuration"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT config_data, is_active FROM widget_configs 
                WHERE client_id = ?
            ''', (client_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                config_data = json.loads(result[0])
                config_data['is_active'] = bool(result[1])
                return {
                    'config_data': config_data,
                    'client_id': client_id
                }
            
            return None
            
        except Exception as e:
            print(f"Error getting widget config: {e}")
            return None
    
    def delete_widget_config(self, client_id: str) -> bool:
        """Delete widget configuration"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM widget_configs WHERE client_id = ?', (client_id,))
            cursor.execute('DELETE FROM widget_knowledge_base WHERE client_id = ?', (client_id,))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Error deleting widget config: {e}")
            return False
    
    def save_knowledge_base_document(self, client_id: str, filename: str, content: str, file_type: str = 'text') -> bool:
        """Save knowledge base document"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO widget_knowledge_base 
                (client_id, filename, content, file_type)
                VALUES (?, ?, ?, ?)
            ''', (client_id, filename, content, file_type))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Error saving knowledge base document: {e}")
            return False
    
    def get_knowledge_base_documents(self, client_id: str) -> list:
        """Get all knowledge base documents for a client"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT filename, content, file_type FROM widget_knowledge_base 
                WHERE client_id = ?
            ''', (client_id,))
            
            results = cursor.fetchall()
            conn.close()
            
            return [
                {
                    'filename': row[0],
                    'content': row[1],
                    'file_type': row[2]
                }
                for row in results
            ]
            
        except Exception as e:
            print(f"Error getting knowledge base documents: {e}")
            return []

    def get_widgets_by_user(self, user_email: str) -> list:
        """Get all widgets for a specific user"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT client_id, config_data, is_active, created_at, updated_at 
                FROM widget_configs 
                WHERE user_email = ? 
                ORDER BY updated_at DESC
            ''', (user_email,))
            
            rows = cursor.fetchall()
            conn.close()
            
            widgets = []
            for row in rows:
                try:
                    config_data = json.loads(row[1])
                    widget = {
                        'client_id': row[0],
                        'user_email': user_email,
                        'config': config_data,
                        'is_active': bool(row[2]),
                        'created_at': row[3],
                        'updated_at': row[4]
                    }
                    widgets.append(widget)
                except json.JSONDecodeError:
                    continue
            
            return widgets
            
        except Exception as e:
            print(f"Error getting widgets by user: {e}")
            return []

    def get_all_widgets(self) -> list:
        """Get all widgets (for admin or backward compatibility)"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT client_id, user_email, config_data, is_active, created_at, updated_at 
                FROM widget_configs 
                ORDER BY updated_at DESC
            ''')
            
            rows = cursor.fetchall()
            conn.close()
            
            widgets = []
            for row in rows:
                try:
                    config_data = json.loads(row[2])
                    widget = {
                        'client_id': row[0],
                        'user_email': row[1],
                        'config': config_data,
                        'is_active': bool(row[3]),
                        'created_at': row[4],
                        'updated_at': row[5]
                    }
                    widgets.append(widget)
                except json.JSONDecodeError:
                    continue
            
            return widgets
            
        except Exception as e:
            print(f"Error getting all widgets: {e}")
            return []

# Global service instance
widget_service = SimpleWidgetService()
