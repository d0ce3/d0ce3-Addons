import sys
import os

# Diagnóstico de importación de SQLite3
try:
    import sqlite3
    SQLITE_AVAILABLE = True
    SQLITE_VERSION = sqlite3.sqlite_version
    SQLITE_ERROR = None
except ImportError as e:
    SQLITE_AVAILABLE = False
    SQLITE_VERSION = None
    SQLITE_ERROR = str(e)
    # Imprimir solo una vez al cargar el módulo
    print(f"⚠️  discord_queue: SQLite3 no disponible - {e}")
    print(f"   Python: {sys.version}")
    print(f"   Executable: {sys.executable}")

import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import threading

class DiscordQueue:
    """
    Cola de eventos persistente para Discord
    Usa SQLite3 si está disponible, JSON como fallback
    """
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
        self.using_sqlite = SQLITE_AVAILABLE
        
        if SQLITE_AVAILABLE:
            self._init_sqlite_db()
        else:
            # Fallback a JSON
            self.db_path = db_path.replace('.db', '.json')
            self._init_json_db()
        
        self._initialized = True
    
    def _init_sqlite_db(self):
        """Inicializa base de datos SQLite"""
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
    
    def _init_json_db(self):
        """Inicializa almacenamiento JSON"""
        if not os.path.exists(self.db_path):
            self._save_json_data({
                'events': [],
                'next_id': 1
            })
    
    def _get_sqlite_connection(self):
        """Obtiene conexión SQLite"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _load_json_data(self):
        """Carga datos desde JSON"""
        try:
            with open(self.db_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {'events': [], 'next_id': 1}
    
    def _save_json_data(self, data):
        """Guarda datos en JSON"""
        with open(self.db_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def add_event(self, user_id: str, event_type: str, payload: dict) -> int:
        """Añade un evento a la cola"""
        if self.using_sqlite:
            return self._add_event_sqlite(user_id, event_type, payload)
        else:
            return self._add_event_json(user_id, event_type, payload)
    
    def _add_event_sqlite(self, user_id: str, event_type: str, payload: dict) -> int:
        conn = self._get_sqlite_connection()
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
    
    def _add_event_json(self, user_id: str, event_type: str, payload: dict) -> int:
        data = self._load_json_data()
        
        event_id = data['next_id']
        data['next_id'] += 1
        
        event = {
            'id': event_id,
            'user_id': user_id,
            'event_type': event_type,
            'payload': payload,
            'created_at': datetime.now().isoformat(),
            'processed': False,
            'attempts': 0,
            'last_attempt': None,
            'error_message': None
        }
        
        data['events'].append(event)
        self._save_json_data(data)
        
        return event_id
    
    def get_pending_events(self, max_attempts: int = 3, limit: int = 50) -> List[Dict]:
        """Obtiene eventos pendientes"""
        if self.using_sqlite:
            return self._get_pending_events_sqlite(max_attempts, limit)
        else:
            return self._get_pending_events_json(max_attempts, limit)
    
    def _get_pending_events_sqlite(self, max_attempts: int, limit: int) -> List[Dict]:
        conn = self._get_sqlite_connection()
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
    
    def _get_pending_events_json(self, max_attempts: int, limit: int) -> List[Dict]:
        data = self._load_json_data()
        
        events = [
            e for e in data['events']
            if not e['processed'] and e['attempts'] < max_attempts
        ]
        
        events.sort(key=lambda x: x['created_at'])
        return events[:limit]
    
    def mark_processed(self, event_id: int):
        """Marca un evento como procesado"""
        if self.using_sqlite:
            self._mark_processed_sqlite(event_id)
        else:
            self._mark_processed_json(event_id)
    
    def _mark_processed_sqlite(self, event_id: int):
        conn = self._get_sqlite_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE events
            SET processed = 1, last_attempt = ?
            WHERE id = ?
        """, (datetime.now().isoformat(), event_id))
        
        conn.commit()
        conn.close()
    
    def _mark_processed_json(self, event_id: int):
        data = self._load_json_data()
        
        for event in data['events']:
            if event['id'] == event_id:
                event['processed'] = True
                event['last_attempt'] = datetime.now().isoformat()
                break
        
        self._save_json_data(data)
    
    def mark_failed(self, event_id: int, error_message: str = None):
        """Marca un evento como fallido"""
        if self.using_sqlite:
            self._mark_failed_sqlite(event_id, error_message)
        else:
            self._mark_failed_json(event_id, error_message)
    
    def _mark_failed_sqlite(self, event_id: int, error_message: str):
        conn = self._get_sqlite_connection()
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
    
    def _mark_failed_json(self, event_id: int, error_message: str):
        data = self._load_json_data()
        
        for event in data['events']:
            if event['id'] == event_id:
                event['attempts'] += 1
                event['last_attempt'] = datetime.now().isoformat()
                event['error_message'] = error_message
                break
        
        self._save_json_data(data)
    
    def get_stats(self) -> Dict:
        """Obtiene estadísticas de la cola"""
        if self.using_sqlite:
            return self._get_stats_sqlite()
        else:
            return self._get_stats_json()
    
    def _get_stats_sqlite(self) -> Dict:
        conn = self._get_sqlite_connection()
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
    
    def _get_stats_json(self) -> Dict:
        data = self._load_json_data()
        events = data['events']
        
        total = len(events)
        pending = len([e for e in events if not e['processed']])
        processed = len([e for e in events if e['processed']])
        failed = len([e for e in events if not e['processed'] and e['attempts'] >= 3])
        
        return {
            'total': total,
            'pending': pending,
            'processed': processed,
            'failed': failed
        }
    
    def cleanup_old_events(self, days: int = 7):
        """Limpia eventos antiguos procesados"""
        if self.using_sqlite:
            return self._cleanup_old_events_sqlite(days)
        else:
            return self._cleanup_old_events_json(days)
    
    def _cleanup_old_events_sqlite(self, days: int):
        conn = self._get_sqlite_connection()
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
    
    def _cleanup_old_events_json(self, days: int):
        data = self._load_json_data()
        
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        original_count = len(data['events'])
        
        data['events'] = [
            e for e in data['events']
            if not (e['processed'] and e['created_at'] < cutoff_date)
        ]
        
        deleted = original_count - len(data['events'])
        
        self._save_json_data(data)
        return deleted
    
    def get_failed_events(self) -> List[Dict]:
        """Obtiene eventos fallidos"""
        if self.using_sqlite:
            return self._get_failed_events_sqlite()
        else:
            return self._get_failed_events_json()
    
    def _get_failed_events_sqlite(self) -> List[Dict]:
        conn = self._get_sqlite_connection()
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
    
    def _get_failed_events_json(self) -> List[Dict]:
        data = self._load_json_data()
        
        events = [
            e for e in data['events']
            if not e['processed'] and e['attempts'] >= 3
        ]
        
        events.sort(key=lambda x: x['created_at'], reverse=True)
        return events
    
    def retry_failed_event(self, event_id: int):
        """Reinicia un evento fallido"""
        if self.using_sqlite:
            self._retry_failed_event_sqlite(event_id)
        else:
            self._retry_failed_event_json(event_id)
    
    def _retry_failed_event_sqlite(self, event_id: int):
        conn = self._get_sqlite_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE events
            SET attempts = 0, error_message = NULL
            WHERE id = ?
        """, (event_id,))
        
        conn.commit()
        conn.close()
    
    def _retry_failed_event_json(self, event_id: int):
        data = self._load_json_data()
        
        for event in data['events']:
            if event['id'] == event_id:
                event['attempts'] = 0
                event['error_message'] = None
                break
        
        self._save_json_data(data)
    
    def delete_event(self, event_id: int):
        """Elimina un evento"""
        if self.using_sqlite:
            self._delete_event_sqlite(event_id)
        else:
            self._delete_event_json(event_id)
    
    def _delete_event_sqlite(self, event_id: int):
        conn = self._get_sqlite_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM events WHERE id = ?", (event_id,))
        
        conn.commit()
        conn.close()
    
    def _delete_event_json(self, event_id: int):
        data = self._load_json_data()
        data['events'] = [e for e in data['events'] if e['id'] != event_id]
        self._save_json_data(data)
    
    def get_backend_info(self) -> Dict:
        """Información sobre el backend usado"""
        return {
            'backend': 'SQLite3' if self.using_sqlite else 'JSON',
            'sqlite_available': SQLITE_AVAILABLE,
            'sqlite_version': SQLITE_VERSION,
            'sqlite_error': SQLITE_ERROR,
            'db_path': self.db_path
        }


# Instancia global
queue_instance = DiscordQueue()

__all__ = [
    'DiscordQueue',
    'queue_instance',
    'SQLITE_AVAILABLE',
    'SQLITE_VERSION'
]