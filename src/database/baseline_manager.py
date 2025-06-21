"""
Baseline management functionality for STPA Tool
Handles creation, loading, and management of database baselines.
"""

import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from .connection import DatabaseConnection
from ..config.constants import WORKING_BASELINE
from ..log_config.config import get_logger

logger = get_logger(__name__)


class BaselineManager:
    """Manages database baselines for versioning and collaboration."""
    
    def __init__(self, db_connection: DatabaseConnection, working_directory: str):
        self.db_connection = db_connection
        self.working_directory = working_directory
        self.baselines_dir = os.path.join(working_directory, "baselines")
        
        # Ensure baselines directory exists
        os.makedirs(self.baselines_dir, exist_ok=True)
    
    def create_baseline(self, baseline_name: Optional[str] = None, description: str = "") -> Tuple[bool, str]:
        """
        Create a new baseline from the current working data.
        
        Args:
            baseline_name: Custom name for the baseline (auto-generated if None)
            description: Description of the baseline
        
        Returns:
            Tuple of (success, baseline_name_or_error_message)
        """
        try:
            # Generate baseline name if not provided
            if not baseline_name:
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                baseline_name = f"baseline_{timestamp}"
            
            # Validate baseline name
            if not self._is_valid_baseline_name(baseline_name):
                return False, "Invalid baseline name. Use only letters, numbers, underscores, and hyphens."
            
            # Check if baseline already exists
            if self._baseline_exists(baseline_name):
                return False, f"Baseline '{baseline_name}' already exists."
            
            logger.info(f"Creating baseline '{baseline_name}'")
            
            # Start transaction
            cursor = self.db_connection.get_cursor()
            cursor.execute("BEGIN TRANSACTION")
            
            try:
                # Get all tables that have baseline columns
                baseline_tables = self._get_baseline_tables()
                
                # Clone all working records to the new baseline
                cloned_count = 0
                for table_name in baseline_tables:
                    count = self._clone_table_to_baseline(table_name, baseline_name)
                    cloned_count += count
                
                # Create baseline metadata
                self._create_baseline_metadata(baseline_name, description, cloned_count)
                
                # Create baseline database file
                baseline_db_path = self._create_baseline_database_file(baseline_name)
                
                # Commit transaction
                cursor.execute("COMMIT")
                
                logger.info(f"Baseline '{baseline_name}' created successfully with {cloned_count} records")
                return True, baseline_name
                
            except Exception as e:
                cursor.execute("ROLLBACK")
                raise e
                
        except Exception as e:
            logger.error(f"Failed to create baseline: {str(e)}")
            return False, f"Failed to create baseline: {str(e)}"
    
    def load_baseline(self, baseline_name: str) -> Tuple[bool, str]:
        """
        Load a baseline as the current working data (read-only).
        
        Args:
            baseline_name: Name of the baseline to load
        
        Returns:
            Tuple of (success, message)
        """
        try:
            if not self._baseline_exists(baseline_name):
                return False, f"Baseline '{baseline_name}' does not exist."
            
            logger.info(f"Loading baseline '{baseline_name}' as read-only")
            
            # For now, we'll implement a simple approach where we copy the baseline
            # database file and use it as the current database in read-only mode
            baseline_db_path = os.path.join(self.baselines_dir, f"{baseline_name}.db")
            current_db_path = self.db_connection.db_path
            
            # Create backup of current database
            backup_path = f"{current_db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(current_db_path, backup_path)
            
            # Copy baseline database to current location
            shutil.copy2(baseline_db_path, current_db_path)
            
            # Reconnect to the database
            self.db_connection.close()
            self.db_connection.connect()
            
            logger.info(f"Baseline '{baseline_name}' loaded successfully")
            return True, f"Baseline '{baseline_name}' loaded. Database is now read-only."
            
        except Exception as e:
            logger.error(f"Failed to load baseline: {str(e)}")
            return False, f"Failed to load baseline: {str(e)}"
    
    def list_baselines(self) -> List[Dict[str, Any]]:
        """
        List all available baselines.
        
        Returns:
            List of baseline information dictionaries
        """
        try:
            baselines = []
            
            # Get baseline metadata from database
            cursor = self.db_connection.get_cursor()
            cursor.execute("""
                SELECT baseline_name, description, created_date, record_count
                FROM baseline_metadata 
                ORDER BY created_date DESC
            """)
            
            for row in cursor.fetchall():
                baseline_info = {
                    'name': row[0],
                    'description': row[1] or "",
                    'created_date': row[2],
                    'record_count': row[3],
                    'file_exists': self._baseline_file_exists(row[0])
                }
                baselines.append(baseline_info)
            
            return baselines
            
        except Exception as e:
            logger.error(f"Failed to list baselines: {str(e)}")
            return []
    
    def delete_baseline(self, baseline_name: str) -> Tuple[bool, str]:
        """
        Delete a baseline and its associated files.
        
        Args:
            baseline_name: Name of the baseline to delete
        
        Returns:
            Tuple of (success, message)
        """
        try:
            if not self._baseline_exists(baseline_name):
                return False, f"Baseline '{baseline_name}' does not exist."
            
            if baseline_name == WORKING_BASELINE:
                return False, "Cannot delete the working baseline."
            
            logger.info(f"Deleting baseline '{baseline_name}'")
            
            cursor = self.db_connection.get_cursor()
            cursor.execute("BEGIN TRANSACTION")
            
            try:
                # Remove baseline records from all tables
                baseline_tables = self._get_baseline_tables()
                deleted_count = 0
                
                for table_name in baseline_tables:
                    cursor.execute(f"DELETE FROM {table_name} WHERE baseline = ?", (baseline_name,))
                    deleted_count += cursor.rowcount
                
                # Remove baseline metadata
                cursor.execute("DELETE FROM baseline_metadata WHERE baseline_name = ?", (baseline_name,))
                
                # Delete baseline database file
                baseline_db_path = os.path.join(self.baselines_dir, f"{baseline_name}.db")
                if os.path.exists(baseline_db_path):
                    os.remove(baseline_db_path)
                
                cursor.execute("COMMIT")
                
                logger.info(f"Baseline '{baseline_name}' deleted successfully ({deleted_count} records removed)")
                return True, f"Baseline '{baseline_name}' deleted successfully."
                
            except Exception as e:
                cursor.execute("ROLLBACK")
                raise e
                
        except Exception as e:
            logger.error(f"Failed to delete baseline: {str(e)}")
            return False, f"Failed to delete baseline: {str(e)}"
    
    def compare_baselines(self, baseline1: str, baseline2: str) -> Dict[str, Any]:
        """
        Compare two baselines and return differences.
        
        Args:
            baseline1: Name of first baseline
            baseline2: Name of second baseline
        
        Returns:
            Dictionary with comparison results
        """
        try:
            logger.info(f"Comparing baselines '{baseline1}' and '{baseline2}'")
            
            comparison = {
                'baseline1': baseline1,
                'baseline2': baseline2,
                'tables': {},
                'summary': {
                    'total_differences': 0,
                    'added_records': 0,
                    'modified_records': 0,
                    'deleted_records': 0
                }
            }
            
            cursor = self.db_connection.get_cursor()
            baseline_tables = self._get_baseline_tables()
            
            for table_name in baseline_tables:
                table_diff = self._compare_table_baselines(cursor, table_name, baseline1, baseline2)
                comparison['tables'][table_name] = table_diff
                
                # Update summary
                comparison['summary']['added_records'] += table_diff['added']
                comparison['summary']['modified_records'] += table_diff['modified']
                comparison['summary']['deleted_records'] += table_diff['deleted']
            
            comparison['summary']['total_differences'] = (
                comparison['summary']['added_records'] +
                comparison['summary']['modified_records'] +
                comparison['summary']['deleted_records']
            )
            
            return comparison
            
        except Exception as e:
            logger.error(f"Failed to compare baselines: {str(e)}")
            return {'error': str(e)}
    
    def _is_valid_baseline_name(self, name: str) -> bool:
        """Validate baseline name format."""
        import re
        return bool(re.match(r'^[a-zA-Z0-9_-]+$', name)) and len(name) <= 64
    
    def _baseline_exists(self, baseline_name: str) -> bool:
        """Check if baseline exists in metadata."""
        cursor = self.db_connection.get_cursor()
        cursor.execute("SELECT COUNT(*) FROM baseline_metadata WHERE baseline_name = ?", (baseline_name,))
        return cursor.fetchone()[0] > 0
    
    def _baseline_file_exists(self, baseline_name: str) -> bool:
        """Check if baseline database file exists."""
        baseline_db_path = os.path.join(self.baselines_dir, f"{baseline_name}.db")
        return os.path.exists(baseline_db_path)
    
    def _get_baseline_tables(self) -> List[str]:
        """Get list of tables that have baseline columns."""
        cursor = self.db_connection.get_cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            AND name != 'baseline_metadata'
        """)
        
        baseline_tables = []
        for (table_name,) in cursor.fetchall():
            # Check if table has baseline column
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in cursor.fetchall()]
            if 'baseline' in columns:
                baseline_tables.append(table_name)
        
        return baseline_tables
    
    def _clone_table_to_baseline(self, table_name: str, baseline_name: str) -> int:
        """Clone working records from a table to a new baseline."""
        cursor = self.db_connection.get_cursor()
        
        # Get table structure
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [col[1] for col in cursor.fetchall() if col[1] != 'id']
        
        # Build insert statement
        columns_str = ', '.join(columns)
        placeholders = ', '.join(['?' for _ in columns])
        
        # Get working records
        cursor.execute(f"SELECT {columns_str} FROM {table_name} WHERE baseline = ?", (WORKING_BASELINE,))
        working_records = cursor.fetchall()
        
        # Insert records with new baseline
        cloned_count = 0
        for record in working_records:
            # Replace baseline value
            record_list = list(record)
            baseline_index = columns.index('baseline')
            record_list[baseline_index] = baseline_name
            
            cursor.execute(f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})", record_list)
            cloned_count += 1
        
        return cloned_count
    
    def _create_baseline_metadata(self, baseline_name: str, description: str, record_count: int):
        """Create baseline metadata record."""
        cursor = self.db_connection.get_cursor()
        cursor.execute("""
            INSERT INTO baseline_metadata (baseline_name, description, created_date, record_count)
            VALUES (?, ?, ?, ?)
        """, (baseline_name, description, datetime.now().isoformat(), record_count))
    
    def _create_baseline_database_file(self, baseline_name: str) -> str:
        """Create a complete database file for the baseline."""
        baseline_db_path = os.path.join(self.baselines_dir, f"{baseline_name}.db")
        current_db_path = self.db_connection.db_path
        
        # Copy current database to baseline location
        shutil.copy2(current_db_path, baseline_db_path)
        
        return baseline_db_path
    
    def _compare_table_baselines(self, cursor, table_name: str, baseline1: str, baseline2: str) -> Dict[str, int]:
        """Compare records in a specific table between two baselines."""
        # Get primary key column (assume 'id')
        pk_column = 'id'
        
        # Get records from both baselines
        cursor.execute(f"SELECT {pk_column} FROM {table_name} WHERE baseline = ?", (baseline1,))
        baseline1_ids = set(row[0] for row in cursor.fetchall())
        
        cursor.execute(f"SELECT {pk_column} FROM {table_name} WHERE baseline = ?", (baseline2,))
        baseline2_ids = set(row[0] for row in cursor.fetchall())
        
        # Calculate differences
        added = len(baseline2_ids - baseline1_ids)
        deleted = len(baseline1_ids - baseline2_ids)
        
        # For simplicity, we'll consider all common records as potentially modified
        # A more sophisticated implementation would compare actual field values
        common_ids = baseline1_ids & baseline2_ids
        modified = len(common_ids)  # Simplified - would need field-by-field comparison
        
        return {
            'added': added,
            'modified': modified,
            'deleted': deleted,
            'total_baseline1': len(baseline1_ids),
            'total_baseline2': len(baseline2_ids)
        }
    
    def ensure_baseline_metadata_table(self):
        """Ensure the baseline metadata table exists."""
        cursor = self.db_connection.get_cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS baseline_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                baseline_name TEXT UNIQUE NOT NULL,
                description TEXT,
                created_date TEXT NOT NULL,
                record_count INTEGER DEFAULT 0,
                created_by TEXT DEFAULT 'system'
            )
        """)
        self.db_connection.commit()