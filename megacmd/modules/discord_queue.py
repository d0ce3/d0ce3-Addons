import json
import os
import subprocess
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import threading
import logging

_logger = logging.getLogger('discord_queue')
_logger.setLevel(logging.INFO)
log_file = os.path.expanduser('~/.d0ce3_addons/.discord_queue.log')
try:
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    _logger.addHandler(file_handler)
except:
    pass

addon_logger = None
try:
    addon_logger = CloudModuleLoader.load_module("logger")
except:
    addon_logger = None

def _log(level, message):
    _logger.log(getattr(logging, level, logging.INFO), message)
    if addon_logger:
        try:
            msg = f"discord_queue: {message}"
            if level == "DEBUG":
                addon_logger.debug(msg)
            elif level == "INFO":
                addon_logger.info(msg)
            elif level == "WARNING":
                addon_logger.warning(msg)
            elif level == "ERROR":
                addon_logger.error(msg)
        except:
            pass

IS_PACKAGED = getattr(sys, 'frozen', False) or '.msx' in sys.executable
SYSTEM_PYTHON = '/usr/bin/python3'

try:
    import sqlite3
    CAN_USE_SQLITE_DIRECT = True
except ImportError:
    CAN_USE_SQLITE_DIRECT = False

if CAN_USE_SQLITE_DIRECT:
    USE_MODE = 'direct'
    _log("DEBUG", "Backend: SQLite3 directo")
elif IS_PACKAGED and os.path.exists(SYSTEM_PYTHON):
    USE_MODE = 'proxy'
    _log("INFO", "Backend: SQLite3 via proxy")
else:
    USE_MODE = 'json'
    _log("WARNING", "Backend: JSON fallback")


class SQLiteProxy:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.helper_script = self._create_helper_script()
        result = self.init_db()
        if not result.get("success"):
            _log("ERROR", f"No se pudo inicializar BD: {result.get('error')}")
    
    def _create_helper_script(self) -> str:
        script_path = '/tmp/discord_queue_helper.py'
        if os.path.exists(script_path):
            _log("DEBUG", "Reusando script helper")
            return script_path
        
        script_content = '''#!/usr/bin/env python3
import sqlite3
import json
import sys
from datetime import datetime, timedelta

def init_db(db_path):
    conn = sqlite3.connect(db_path)
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
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_processed ON events(processed, attempts)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_created ON events(created_at)")
    conn.commit()
    conn.close()
    print(json.dumps({"success": True}))

def add_event(db_path, user_id, event_type, payload):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO events (user_id, event_type, payload, created_at)
        VALUES (?, ?, ?, ?)
    """, (user_id, event_type, json.dumps(payload), datetime.now().isoformat()))
    event_id = cursor.lastrowid
    conn.commit()
    conn.close()
    print(json.dumps({"success": True, "event_id": event_id}))

def get_pending_events(db_path, max_attempts, limit):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM events
        WHERE processed = 0 AND attempts < ?
        ORDER BY created_at ASC
        LIMIT ?
    """, (max_attempts, limit))
    events = [dict(row) for row in cursor.fetchall()]
    conn.close()
    print(json.dumps({"success": True, "events": events}))

def mark_processed(db_path, event_id):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE events
        SET processed = 1, last_attempt = ?
        WHERE id = ?
    """, (datetime.now().isoformat(), event_id))
    conn.commit()
    conn.close()
    print(json.dumps({"success": True}))

def mark_failed(db_path, event_id, error_message):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE events
        SET attempts = attempts + 1, last_attempt = ?, error_message = ?
        WHERE id = ?
    """, (datetime.now().isoformat(), error_message, event_id))
    conn.commit()
    conn.close()
    print(json.dumps({"success": True}))

def get_stats(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as total FROM events")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM events WHERE processed = 0")
    pending = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM events WHERE processed = 1")
    processed = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM events WHERE processed = 0 AND attempts >= 3")
    failed = cursor.fetchone()[0]
    conn.close()
    print(json.dumps({
        "success": True,
        "stats": {
            "total": total,
            "pending": pending,
            "processed": processed,
            "failed": failed
        }
    }))

def cleanup_old_events(db_path, days):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
    cursor.execute("DELETE FROM events WHERE processed = 1 AND created_at < ?", (cutoff_date,))
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    print(json.dumps({"success": True, "deleted": deleted}))

def get_failed_events(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM events
        WHERE processed = 0 AND attempts >= 3
        ORDER BY created_at DESC
    """)
    events = [dict(row) for row in cursor.fetchall()]
    conn.close()
    print(json.dumps({"success": True, "events": events}))

def retry_failed_event(db_path, event_id):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("UPDATE events SET attempts = 0, error_message = NULL WHERE id = ?", (event_id,))
    conn.commit()
    conn.close()
    print(json.dumps({"success": True}))

def delete_event(db_path, event_id):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM events WHERE id = ?", (event_id,))
    conn.commit()
    conn.close()
    print(json.dumps({"success": True}))

if __name__ == "__main__":
    command = sys.argv[1]
    db_path = sys.argv[2]
    
    if command == "init":
        init_db(db_path)
    elif command == "add_event":
        user_id = sys.argv[3]
        event_type = sys.argv[4]
        payload = json.loads(sys.argv[5])
        add_event(db_path, user_id, event_type, payload)
    elif command == "get_pending":
        max_attempts = int(sys.argv[3])
        limit = int(sys.argv[4])
        get_pending_events(db_path, max_attempts, limit)
    elif command == "mark_processed":
        event_id = int(sys.argv[3])
        mark_processed(db_path, event_id)
    elif command == "mark_failed":
        event_id = int(sys.argv[3])
        error_message = sys.argv[4] if len(sys.argv) > 4 else None
        mark_failed(db_path, event_id, error_message)
    elif command == "get_stats":
        get_stats(db_path)
    elif command == "cleanup":
        days = int(sys.argv[3])
        cleanup_old_events(db_path, days)
    elif command == "get_failed":
        get_failed_events(db_path)
    elif command == "retry_failed":
        event_id = int(sys.argv[3])
        retry_failed_event(db_path, event_id)
    elif command == "delete":
        event_id = int(sys.argv[3])
        delete_event(db_path, event_id)
'''
        
        with open(script_path, 'w') as f:
            f.write(script_content)
        os.chmod(script_path, 0o755)
        _log("INFO", "Script helper creado")
        return script_path
    
    def _call_helper(self, *args) -> dict:
        try:
            result = subprocess.run(
                [SYSTEM_PYTHON, self.helper_script] + list(args),
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode != 0:
                _log("ERROR", f"Helper error: {result.stderr}")
                raise Exception(f"Helper error: {result.stderr}")
            return json.loads(result.stdout)
        except subprocess.TimeoutExpired:
            _log("ERROR", "Helper timeout")
            return {"success": False, "error": "Timeout"}
        except Exception as e:
            _log("ERROR", f"Helper call failed: {e}")
            return {"success": False, "error": str(e)}
    
    def init_db(self):
        return self._call_helper("init", self.db_path)
    
    def add_event(self, user_id: str, event_type: str, payload: dict) -> int:
        result = self._call_helper("add_event", self.db_path, user_id, event_type, json.dumps(payload))
        return result.get("event_id", 0) if result.get("success") else 0
    
    def get_pending_events(self, max_attempts: int = 3, limit: int = 50) -> List[Dict]:
        result = self._call_helper("get_pending", self.db_path, str(max_attempts), str(limit))
        if result.get("success"):
            events = result.get("events", [])
            for event in events:
                if isinstance(event.get('payload'), str):
                    event['payload'] = json.loads(event['payload'])
            return events
        return []
    
    def mark_processed(self, event_id: int):
        return self._call_helper("mark_processed", self.db_path, str(event_id))
    
    def mark_failed(self, event_id: int, error_message: str = None):
        args = ["mark_failed", self.db_path, str(event_id)]
        if error_message:
            args.append(error_message)
        return self._call_helper(*args)
    
    def get_stats(self) -> Dict:
        result = self._call_helper("get_stats", self.db_path)
        return result.get("stats", {}) if result.get("success") else {}
    
    def cleanup_old_events(self, days: int = 7) -> int:
        result = self._call_helper("cleanup", self.db_path, str(days))
        return result.get("deleted", 0) if result.get("success") else 0
    
    def get_failed_events(self) -> List[Dict]:
        result = self._call_helper("get_failed", self.db_path)
        if result.get("success"):
            events = result.get("events", [])
            for event in events:
                if isinstance(event.get('payload'), str):
                    event['payload'] = json.loads(event['payload'])
            return events
        return []
    
    def retry_failed_event(self, event_id: int):
        return self._call_helper("retry_failed", self.db_path, str(event_id))
    
    def delete_event(self, event_id: int):
        return self._call_helper("delete", self.db_path, str(event_id))


class DiscordQueueDirect:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()
    
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
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_processed ON events(processed, attempts)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_created ON events(created_at)")
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
        """, (user_id, event_type, json.dumps(payload), datetime.now().isoformat()))
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
        cursor.execute("UPDATE events SET processed = 1, last_attempt = ? WHERE id = ?",
                      (datetime.now().isoformat(), event_id))
        conn.commit()
        conn.close()
    
    def mark_failed(self, event_id: int, error_message: str = None):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE events SET attempts = attempts + 1, last_attempt = ?, error_message = ?
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
        cursor.execute("SELECT COUNT(*) as failed FROM events WHERE processed = 0 AND attempts >= 3")
        failed = cursor.fetchone()['failed']
        conn.close()
        return {'total': total, 'pending': pending, 'processed': processed, 'failed': failed}
    
    def cleanup_old_events(self, days: int = 7) -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        cursor.execute("DELETE FROM events WHERE processed = 1 AND created_at < ?", (cutoff_date,))
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
        cursor.execute("UPDATE events SET attempts = 0, error_message = NULL WHERE id = ?", (event_id,))
        conn.commit()
        conn.close()
    
    def delete_event(self, event_id: int):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM events WHERE id = ?", (event_id,))
        conn.commit()
        conn.close()


class DiscordQueueJSON:
    def __init__(self, db_path: str):
        self.db_path = db_path.replace('.db', '.json')
        self._lock = threading.Lock()
        self._init_db()
    
    def _init_db(self):
        if not os.path.exists(self.db_path):
            self._save_data({'events': [], 'next_id': 1})
    
    def _load_data(self):
        with self._lock:
            try:
                with open(self.db_path, 'r') as f:
                    return json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                return {'events': [], 'next_id': 1}
    
    def _save_data(self, data):
        with self._lock:
            with open(self.db_path, 'w') as f:
                json.dump(data, f, indent=2)
    
    def add_event(self, user_id: str, event_type: str, payload: dict) -> int:
        data = self._load_data()
        event_id = data['next_id']
        data['next_id'] += 1
        data['events'].append({
            'id': event_id,
            'user_id': user_id,
            'event_type': event_type,
            'payload': payload,
            'created_at': datetime.now().isoformat(),
            'processed': False,
            'attempts': 0,
            'last_attempt': None,
            'error_message': None
        })
        self._save_data(data)
        return event_id
    
    def get_pending_events(self, max_attempts: int = 3, limit: int = 50) -> List[Dict]:
        data = self._load_data()
        events = [e for e in data['events'] if not e['processed'] and e['attempts'] < max_attempts]
        events.sort(key=lambda x: x['created_at'])
        return events[:limit]
    
    def mark_processed(self, event_id: int):
        data = self._load_data()
        for event in data['events']:
            if event['id'] == event_id:
                event['processed'] = True
                event['last_attempt'] = datetime.now().isoformat()
                break
        self._save_data(data)
    
    def mark_failed(self, event_id: int, error_message: str = None):
        data = self._load_data()
        for event in data['events']:
            if event['id'] == event_id:
                event['attempts'] += 1
                event['last_attempt'] = datetime.now().isoformat()
                event['error_message'] = error_message
                break
        self._save_data(data)
    
    def get_stats(self) -> Dict:
        data = self._load_data()
        events = data['events']
        return {
            'total': len(events),
            'pending': len([e for e in events if not e['processed']]),
            'processed': len([e for e in events if e['processed']]),
            'failed': len([e for e in events if not e['processed'] and e['attempts'] >= 3])
        }
    
    def cleanup_old_events(self, days: int = 7) -> int:
        data = self._load_data()
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        original_count = len(data['events'])
        data['events'] = [
            e for e in data['events']
            if not (e['processed'] and e['created_at'] < cutoff_date)
        ]
        deleted = original_count - len(data['events'])
        self._save_data(data)
        return deleted
    
    def get_failed_events(self) -> List[Dict]:
        data = self._load_data()
        events = [e for e in data['events'] if not e['processed'] and e['attempts'] >= 3]
        events.sort(key=lambda x: x['created_at'], reverse=True)
        return events
    
    def retry_failed_event(self, event_id: int):
        data = self._load_data()
        for event in data['events']:
            if event['id'] == event_id:
                event['attempts'] = 0
                event['error_message'] = None
                break
        self._save_data(data)
    
    def delete_event(self, event_id: int):
        data = self._load_data()
        data['events'] = [e for e in data['events'] if e['id'] != event_id]
        self._save_data(data)


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
            db_path = os.path.expanduser('~/.d0ce3_addons/.discord_events.db')
        
        if USE_MODE == 'direct':
            self._impl = DiscordQueueDirect(db_path)
            self.backend = "SQLite3 (directo)"
        elif USE_MODE == 'proxy':
            self._impl = SQLiteProxy(db_path)
            self.backend = "SQLite3 (proxy)"
        else:
            self._impl = DiscordQueueJSON(db_path)
            self.backend = "JSON (fallback)"
        
        self._initialized = True
        _log("INFO", f"Backend: {self.backend}")
    
    def add_event(self, user_id: str, event_type: str, payload: dict) -> int:
        return self._impl.add_event(user_id, event_type, payload)
    
    def get_pending_events(self, max_attempts: int = 3, limit: int = 50) -> List[Dict]:
        return self._impl.get_pending_events(max_attempts, limit)
    
    def mark_processed(self, event_id: int):
        return self._impl.mark_processed(event_id)
    
    def mark_failed(self, event_id: int, error_message: str = None):
        return self._impl.mark_failed(event_id, error_message)
    
    def get_stats(self) -> Dict:
        return self._impl.get_stats()
    
    def cleanup_old_events(self, days: int = 7):
        return self._impl.cleanup_old_events(days)
    
    def get_failed_events(self) -> List[Dict]:
        return self._impl.get_failed_events()
    
    def retry_failed_event(self, event_id: int):
        return self._impl.retry_failed_event(event_id)
    
    def delete_event(self, event_id: int):
        return self._impl.delete_event(event_id)


queue_instance = DiscordQueue()

__all__ = ['DiscordQueue', 'queue_instance', 'USE_MODE']
