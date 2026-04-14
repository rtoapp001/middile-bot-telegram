import sqlite3
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional

logger = logging.getLogger(__name__)

# Database path
DB_PATH = "bot_database.db"

# Database timeout in seconds
DB_TIMEOUT = 30

class Database:
    def __init__(self):
        self._init_sqlite()
        self.init_db()
    
    def _init_sqlite(self):
        """Initialize SQLite with proper settings for concurrent access"""
        try:
            conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
            cursor = conn.cursor()
            # Enable WAL mode for better concurrency
            cursor.execute("PRAGMA journal_mode=WAL")
            # Increase busy timeout
            cursor.execute(f"PRAGMA busy_timeout={DB_TIMEOUT * 1000}")
            # Enable concurrent access
            cursor.execute("PRAGMA synchronous=NORMAL")
            conn.close()
            logger.info("✅ SQLite initialized with WAL mode")
        except Exception as e:
            logger.error(f"❌ Error initializing SQLite: {e}")
    
    def _get_connection(self):
        """Get a database connection with proper timeout settings"""
        conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT, check_same_thread=False)
        return conn
    
    def init_db(self):
        """Initialize database with tables"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_downloads INTEGER DEFAULT 0,
                    is_blocked INTEGER DEFAULT 0,
                    last_request_at TIMESTAMP
                )
            """)
            
            # Requests table (track each APK request)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS requests (
                    request_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    code TEXT NOT NULL,
                    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'pending',
                    queue_position INTEGER,
                    completed_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            
            # Queue tracking table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS queue_status (
                    request_id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    queue_message TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (request_id) REFERENCES requests(request_id)
                )
            """)
            
            # Analytics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_type TEXT,
                    metric_value TEXT,
                    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            conn.close()
            logger.info("✅ Database initialized")
        except Exception as e:
            logger.error(f"❌ Database init error: {e}")
    
    def add_user(self, user_id: int, username: str, first_name: str, last_name: str = ""):
        """Add or update user"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR IGNORE INTO users (user_id, username, first_name, last_name)
                VALUES (?, ?, ?, ?)
            """, (user_id, username, first_name, last_name))
            
            conn.commit()
            conn.close()
            logger.info(f"✅ User {user_id} added/updated")
        except Exception as e:
            logger.error(f"❌ Error adding user: {e}")
    
    def create_request(self, user_id: int, code: str) -> int:
        """Create new APK request, return request_id"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO requests (user_id, code)
                VALUES (?, ?)
            """, (user_id, code))
            
            conn.commit()
            request_id = cursor.lastrowid
            conn.close()
            
            logger.info(f"✅ Request {request_id} created for user {user_id}")
            return request_id
        except Exception as e:
            logger.error(f"❌ Error creating request: {e}")
            return None
    
    def update_request_status(self, request_id: int, status: str, queue_message: str = None):
        """Update request status"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE requests SET status = ? WHERE request_id = ?
            """, (status, request_id))
            
            if queue_message:
                cursor.execute("""
                    UPDATE queue_status SET queue_message = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE request_id = ?
                """, (queue_message, request_id))
            
            conn.commit()
            conn.close()
            logger.info(f"✅ Request {request_id} status updated to {status}")
        except Exception as e:
            logger.error(f"❌ Error updating request: {e}")
    
    def complete_request(self, request_id: int):
        """Mark request as completed"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Get user_id
            cursor.execute("SELECT user_id FROM requests WHERE request_id = ?", (request_id,))
            result = cursor.fetchone()
            
            if result:
                user_id = result[0]
                
                # Update request
                cursor.execute("""
                    UPDATE requests 
                    SET status = 'completed', completed_at = CURRENT_TIMESTAMP 
                    WHERE request_id = ?
                """, (request_id,))
                
                # Update user stats
                cursor.execute("""
                    UPDATE users 
                    SET total_downloads = total_downloads + 1 
                    WHERE user_id = ?
                """, (user_id,))
                
                conn.commit()
                logger.info(f"✅ Request {request_id} completed")
            
            conn.close()
        except Exception as e:
            logger.error(f"❌ Error completing request: {e}")
    
    def get_user_stats(self, user_id: int) -> Dict:
        """Get user statistics"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    total_downloads,
                    (SELECT COUNT(*) FROM requests WHERE user_id = ?) as total_requests,
                    (SELECT COUNT(*) FROM requests WHERE user_id = ? AND status = 'completed') as completed,
                    joined_at
                FROM users WHERE user_id = ?
            """, (user_id, user_id, user_id))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'downloads': result[0],
                    'total_requests': result[1],
                    'completed': result[2],
                    'joined_at': result[3]
                }
            return None
        except Exception as e:
            logger.error(f"❌ Error getting user stats: {e}")
            return None
    
    def get_all_users_count(self) -> int:
        """Get total number of users"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM users")
            result = cursor.fetchone()
            conn.close()
            
            return result[0] if result else 0
        except Exception as e:
            logger.error(f"❌ Error getting users count: {e}")
            return 0
    
    def get_pending_requests_count(self) -> int:
        """Get number of pending requests"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM requests WHERE status = 'pending'")
            result = cursor.fetchone()
            conn.close()
            
            return result[0] if result else 0
        except Exception as e:
            logger.error(f"❌ Error getting pending count: {e}")
            return 0
    
    def get_last_request_time(self, user_id: int) -> Optional[datetime]:
        """Get last request time for rate limiting"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT requested_at FROM requests 
                WHERE user_id = ? 
                ORDER BY requested_at DESC 
                LIMIT 1
            """, (user_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return datetime.fromisoformat(result[0])
            return None
        except Exception as e:
            logger.error(f"❌ Error getting last request: {e}")
            return None
    
    def is_user_blocked(self, user_id: int) -> bool:
        """Check if user is blocked"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT is_blocked FROM users WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            conn.close()
            
            return result[0] == 1 if result else False
        except Exception as e:
            logger.error(f"❌ Error checking block status: {e}")
            return False
    
    def block_user(self, user_id: int):
        """Block a user"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("UPDATE users SET is_blocked = 1 WHERE user_id = ?", (user_id,))
            conn.commit()
            conn.close()
            
            logger.info(f"✅ User {user_id} blocked")
        except Exception as e:
            logger.error(f"❌ Error blocking user: {e}")
    
    def get_admin_stats(self) -> Dict:
        """Get overall bot statistics"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM users")
            total_users = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM requests WHERE status = 'completed'")
            total_downloads = cursor.fetchone()[0]
            
            cursor.execute("SELECT AVG(CAST((julianday(completed_at) - julianday(requested_at)) * 24 * 60 AS INTEGER)) FROM requests WHERE status = 'completed'")
            avg_time = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM requests WHERE status = 'pending'")
            pending = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'total_users': total_users,
                'total_downloads': total_downloads,
                'avg_time_minutes': round(avg_time) if avg_time else 0,
                'pending_requests': pending
            }
        except Exception as e:
            logger.error(f"❌ Error getting admin stats: {e}")
            return {}


# Initialize database
db = Database()
