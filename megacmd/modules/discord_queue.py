import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import threading

class DiscordQueue:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, db_path: str = None):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, db_path: str = None):
        if self._initialized:
            return
        
        if db_path is None:
            workspace = os.getenv("CODESPACE_VSCODE_FOLDER", "/workspace")
            db_path = os.path.join(workspace, ".discord_events.db")
        
        self.db_path = db_path
        self._init_db()
        self._initialized = True
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                payload TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                processed BOOLEAN DEFAULT 0,
                attempts INTEGER DEFAULT 0,
                last_attempt TIMESTAMP,
                error_message TEXT
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_processed 
            ON events(processed, attempts)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_created 
            ON events(created_at)
        """)
        
        conn.commit()
        conn.close()
    
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def add_event(self, user_id: str, event_type: str, payload: dict) -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO events (user_id, event_type, payload, created_at)
            VALUES (?, ?, ?, ?)
        """, (
            user_id,
            event_type,
            json.dumps(payload),
            datetime.now().isoformat()
        ))
        
        event_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return event_id
    
    def get_pending_events(self, max_attempts: int = 3, limit: int = 50) -> List[Dict]:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM events
            WHERE processed = 0 AND attempts < ?
            ORDER BY created_at ASC
            LIMIT ?
        """, (max_attempts, limit))
        
        events = []
        for row in cursor.fetchall():
            events.append({
                'id': row['id'],
                'user_id': row['user_id'],
                'event_type': row['event_type'],
                'payload': json.loads(row['payload']),
                'created_at': row['created_at'],
                'attempts': row['attempts'],
                'last_attempt': row['last_attempt'],
                'error_message': row['error_message']
            })
        
        conn.close()
        return events
    
    def mark_processed(self, event_id: int):
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE events
            SET processed = 1, last_attempt = ?
            WHERE id = ?
        """, (datetime.now().isoformat(), event_id))
        
        conn.commit()
        conn.close()
    
    def mark_failed(self, event_id: int, error_message: str = None):
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE events
            SET attempts = attempts + 1,
                last_attempt = ?,
                error_message = ?
            WHERE id = ?
        """, (datetime.now().isoformat(), error_message, event_id))
        
        conn.commit()
        conn.close()
    
    def get_stats(self) -> Dict:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as total FROM events")
        total = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as pending FROM events WHERE processed = 0")
        pending = cursor.fetchone()['pending']
        
        cursor.execute("SELECT COUNT(*) as processed FROM events WHERE processed = 1")
        processed = cursor.fetchone()['processed']
        
        cursor.execute("""
            SELECT COUNT(*) as failed 
            FROM events 
            WHERE processed = 0 AND attempts >= 3
        """)
        failed = cursor.fetchone()['failed']
        
        conn.close()
        
        return {
            'total': total,
            'pending': pending,
            'processed': processed,
            'failed': failed
        }
    
    def cleanup_old_events(self, days: int = 7):
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        cursor.execute("""
            DELETE FROM events
            WHERE processed = 1 AND created_at < ?
        """, (cutoff_date,))
        
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        
        return deleted
    
    def get_failed_events(self) -> List[Dict]:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM events
            WHERE processed = 0 AND attempts >= 3
            ORDER BY created_at DESC
        """)
        
        events = []
        for row in cursor.fetchall():
            events.append({
                'id': row['id'],
                'user_id': row['user_id'],
                'event_type': row['event_type'],
                'payload': json.loads(row['payload']),
                'created_at': row['created_at'],
                'attempts': row['attempts'],
                'error_message': row['error_message']
            })
        
        conn.close()
        return events
    
    def retry_failed_event(self, event_id: int):
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE events
            SET attempts = 0, error_message = NULL
            WHERE id = ?
        """, (event_id,))
        
        conn.commit()
        conn.close()
    
    def delete_event(self, event_id: int):
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM events WHERE id = ?", (event_id,))
        
        conn.commit()
        conn.close()

queue_instance = DiscordQueue()

__all__ = [
    'DiscordQueue',
    'queue_instance'
]
