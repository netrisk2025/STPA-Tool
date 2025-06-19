"""
Database connection management for STPA Tool
Handles SQLite database connections, initialization, and configuration.
"""

import sqlite3
import threading
from pathlib import Path
from typing import Optional, Any, Dict, List, Tuple
from contextlib import contextmanager

from ..config.constants import DB_TIMEOUT, DB_WAL_MODE
from ..log_config.config import get_logger
from .schema import get_full_schema_sql, SCHEMA_VERSION

logger = get_logger(__name__)


class DatabaseConnection:
    """
    Manages SQLite database connections with thread safety and connection pooling.
    """
    
    def __init__(self, db_path: Path):
        """
        Initialize database connection manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._local = threading.local()
        self._lock = threading.RLock()
        self._is_initialized = False
        
    def _get_connection(self) -> sqlite3.Connection:
        """
        Get thread-local database connection.
        
        Returns:
            SQLite connection for current thread
        """
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            logger.debug(f"Creating new database connection for thread {threading.current_thread().name}")
            
            # Create connection
            conn = sqlite3.connect(
                str(self.db_path),
                timeout=DB_TIMEOUT,
                check_same_thread=False
            )
            
            # Configure connection
            conn.row_factory = sqlite3.Row  # Enable column access by name
            conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
            
            if DB_WAL_MODE:
                conn.execute("PRAGMA journal_mode = WAL")  # Enable WAL mode
                
            # Enable automatic commits for most operations
            conn.isolation_level = None
            
            self._local.connection = conn
            
        return self._local.connection
    
    def close_connection(self) -> None:
        """Close thread-local connection."""
        if hasattr(self._local, 'connection') and self._local.connection:
            self._local.connection.close()
            self._local.connection = None
            logger.debug(f"Closed database connection for thread {threading.current_thread().name}")
    
    @contextmanager
    def get_cursor(self):
        """
        Context manager for database cursor.
        
        Yields:
            SQLite cursor
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
        finally:
            cursor.close()
    
    @contextmanager
    def transaction(self):
        """
        Context manager for database transactions.
        
        Yields:
            SQLite connection
        """
        conn = self._get_connection()
        try:
            conn.execute("BEGIN")
            yield conn
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise
    
    def execute(self, sql: str, parameters: Optional[Tuple] = None) -> sqlite3.Cursor:
        """
        Execute SQL statement.
        
        Args:
            sql: SQL statement
            parameters: SQL parameters (optional)
            
        Returns:
            Cursor with results
        """
        with self.get_cursor() as cursor:
            if parameters:
                return cursor.execute(sql, parameters)
            else:
                return cursor.execute(sql)
    
    def fetchone(self, sql: str, parameters: Optional[Tuple] = None) -> Optional[sqlite3.Row]:
        """
        Execute SQL and fetch one row.
        
        Args:
            sql: SQL statement
            parameters: SQL parameters (optional)
            
        Returns:
            Single row or None
        """
        with self.get_cursor() as cursor:
            if parameters:
                cursor.execute(sql, parameters)
            else:
                cursor.execute(sql)
            return cursor.fetchone()
    
    def fetchall(self, sql: str, parameters: Optional[Tuple] = None) -> List[sqlite3.Row]:
        """
        Execute SQL and fetch all rows.
        
        Args:
            sql: SQL statement
            parameters: SQL parameters (optional)
            
        Returns:
            List of rows
        """
        with self.get_cursor() as cursor:
            if parameters:
                cursor.execute(sql, parameters)
            else:
                cursor.execute(sql)
            return cursor.fetchall()
    
    def initialize_database(self) -> bool:
        """
        Initialize database with schema if it doesn't exist.
        
        Returns:
            True if initialization was successful
        """
        with self._lock:
            if self._is_initialized:
                return True
                
            try:
                # Check if database exists and has tables
                if self.db_path.exists():
                    # Check if database has proper schema
                    if self._verify_schema():
                        logger.info("Database schema verified")
                        self._is_initialized = True
                        return True
                    else:
                        logger.warning("Database schema verification failed, recreating")
                        self.db_path.unlink()  # Remove invalid database
                
                # Create new database
                logger.info(f"Creating new database at {self.db_path}")
                
                # Ensure parent directory exists
                self.db_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Execute schema creation
                schema_sql = get_full_schema_sql()
                
                # Use direct connection for schema creation (executescript doesn't work well in transactions)
                conn = self._get_connection()
                conn.executescript(schema_sql)
                
                logger.info("Database schema created successfully")
                self._is_initialized = True
                return True
                
            except Exception as e:
                logger.error(f"Failed to initialize database: {str(e)}")
                return False
    
    def _verify_schema(self) -> bool:
        """
        Verify that database has the expected schema.
        
        Returns:
            True if schema is valid
        """
        try:
            # Check if version table exists and has correct version
            version_row = self.fetchone(
                "SELECT version FROM db_version ORDER BY applied_at DESC LIMIT 1"
            )
            
            if not version_row:
                logger.warning("No version information found in database")
                return False
            
            if version_row['version'] != SCHEMA_VERSION:
                logger.warning(f"Database version mismatch: expected {SCHEMA_VERSION}, found {version_row['version']}")
                return False
            
            # Check if key tables exist
            required_tables = ['systems', 'functions', 'requirements', 'audit_log']
            
            for table in required_tables:
                result = self.fetchone(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    (table,)
                )
                if not result:
                    logger.warning(f"Required table '{table}' not found")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Schema verification failed: {str(e)}")
            return False
    
    def backup_database(self, backup_path: Path) -> bool:
        """
        Create a backup of the database.
        
        Args:
            backup_path: Path for backup file
            
        Returns:
            True if backup was successful
        """
        try:
            # Ensure backup directory exists
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Use SQLite backup API
            source_conn = self._get_connection()
            backup_conn = sqlite3.connect(str(backup_path))
            
            try:
                source_conn.backup(backup_conn)
                logger.info(f"Database backed up to {backup_path}")
                return True
            finally:
                backup_conn.close()
                
        except Exception as e:
            logger.error(f"Failed to backup database: {str(e)}")
            return False
    
    def get_database_info(self) -> Dict[str, Any]:
        """
        Get database information and statistics.
        
        Returns:
            Dictionary with database information
        """
        try:
            info = {
                'path': str(self.db_path),
                'size': self.db_path.stat().st_size if self.db_path.exists() else 0,
                'schema_version': None,
                'table_count': 0,
                'foreign_keys_enabled': False,
                'journal_mode': None
            }
            
            # Get version
            version_row = self.fetchone(
                "SELECT version FROM db_version ORDER BY applied_at DESC LIMIT 1"
            )
            if version_row:
                info['schema_version'] = version_row['version']
            
            # Get table count
            tables = self.fetchall(
                "SELECT COUNT(*) as count FROM sqlite_master WHERE type='table'"
            )
            if tables:
                info['table_count'] = tables[0]['count']
            
            # Get pragma settings
            fk_result = self.fetchone("PRAGMA foreign_keys")
            if fk_result:
                info['foreign_keys_enabled'] = bool(fk_result[0])
            
            journal_result = self.fetchone("PRAGMA journal_mode")
            if journal_result:
                info['journal_mode'] = journal_result[0]
            
            return info
            
        except Exception as e:
            logger.error(f"Failed to get database info: {str(e)}")
            return {'error': str(e)}
    
    def vacuum_database(self) -> bool:
        """
        Vacuum the database to optimize storage.
        
        Returns:
            True if vacuum was successful
        """
        try:
            with self.get_cursor() as cursor:
                cursor.execute("VACUUM")
            logger.info("Database vacuumed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to vacuum database: {str(e)}")
            return False


class DatabaseManager:
    """
    High-level database manager for STPA Tool.
    """
    
    def __init__(self, db_path: Path):
        """
        Initialize database manager.
        
        Args:
            db_path: Path to database file
        """
        self.db_path = db_path
        self.connection = DatabaseConnection(db_path)
        
    def initialize(self) -> bool:
        """
        Initialize the database.
        
        Returns:
            True if initialization was successful
        """
        logger.info(f"Initializing database at {self.db_path}")
        return self.connection.initialize_database()
    
    def get_connection(self) -> DatabaseConnection:
        """
        Get database connection.
        
        Returns:
            Database connection instance
        """
        return self.connection
    
    def close(self) -> None:
        """Close database connections."""
        self.connection.close_connection()
        logger.info("Database connections closed")
    
    def is_healthy(self) -> bool:
        """
        Check if database is healthy and accessible.
        
        Returns:
            True if database is healthy
        """
        try:
            # Simple query to check connectivity
            result = self.connection.fetchone("SELECT 1")
            return result is not None
            
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return False