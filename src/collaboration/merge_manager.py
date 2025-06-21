"""
Merge management functionality for STPA Tool
Handles merging of branches and conflict resolution.
"""

import os
import json
import shutil
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Set
from enum import Enum

from ..database.connection import DatabaseConnection
from ..database.entities import System, EntityRepository
from ..config.constants import WORKING_BASELINE
from ..log_config.config import get_logger

logger = get_logger(__name__)


class ConflictType(Enum):
    """Types of merge conflicts."""
    HIERARCHICAL_ID = "hierarchical_id"
    DUPLICATE_ENTITY = "duplicate_entity"
    PARENT_MISSING = "parent_missing"
    REFERENCE_MISSING = "reference_missing"


class ConflictResolution(Enum):
    """Conflict resolution strategies."""
    KEEP_MAIN = "keep_main"
    KEEP_BRANCH = "keep_branch"
    MERGE_BOTH = "merge_both"
    MANUAL = "manual"


class MergeConflict:
    """Represents a merge conflict."""
    
    def __init__(self, conflict_type: ConflictType, table_name: str, entity_id: int, 
                 main_data: Dict[str, Any], branch_data: Dict[str, Any], description: str):
        self.conflict_type = conflict_type
        self.table_name = table_name
        self.entity_id = entity_id
        self.main_data = main_data
        self.branch_data = branch_data
        self.description = description
        self.resolution = None
        self.resolved_data = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert conflict to dictionary representation."""
        return {
            'conflict_type': self.conflict_type.value,
            'table_name': self.table_name,
            'entity_id': self.entity_id,
            'main_data': self.main_data,
            'branch_data': self.branch_data,
            'description': self.description,
            'resolution': self.resolution.value if self.resolution else None,
            'resolved_data': self.resolved_data
        }


class MergeManager:
    """Manages merging of project branches."""
    
    def __init__(self, db_connection: DatabaseConnection, working_directory: str):
        self.db_connection = db_connection
        self.working_directory = working_directory
    
    def analyze_merge(self, branch_path: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Analyze a branch for potential merge conflicts.
        
        Args:
            branch_path: Path to the branch to analyze
        
        Returns:
            Tuple of (can_auto_merge, analysis_results)
        """
        try:
            logger.info(f"Analyzing merge for branch at {branch_path}")
            
            # Validate branch
            if not self._validate_branch(branch_path):
                return False, {'error': 'Invalid branch structure'}
            
            # Load branch metadata
            metadata = self._load_branch_metadata(branch_path)
            if not metadata:
                return False, {'error': 'Branch metadata not found'}
            
            # Connect to branch database
            branch_db_path = os.path.join(branch_path, "stpa.db")
            branch_connection = self._connect_to_branch_db(branch_db_path)
            
            if not branch_connection:
                return False, {'error': 'Cannot connect to branch database'}
            
            try:
                # Analyze conflicts
                conflicts = self._detect_conflicts(branch_connection, metadata)
                
                # Analyze changes
                changes = self._analyze_changes(branch_connection, metadata)
                
                analysis = {
                    'branch_metadata': metadata,
                    'conflicts': [conflict.to_dict() for conflict in conflicts],
                    'changes': changes,
                    'can_auto_merge': len(conflicts) == 0,
                    'conflict_count': len(conflicts),
                    'change_count': sum(changes.values())
                }
                
                return len(conflicts) == 0, analysis
                
            finally:
                branch_connection.close()
                
        except Exception as e:
            logger.error(f"Failed to analyze merge: {str(e)}")
            return False, {'error': str(e)}
    
    def merge_branch(self, branch_path: str, conflict_resolutions: Optional[Dict[str, Any]] = None) -> Tuple[bool, str]:
        """
        Merge a branch into the main project.
        
        Args:
            branch_path: Path to the branch to merge
            conflict_resolutions: Dictionary of conflict resolutions
        
        Returns:
            Tuple of (success, message)
        """
        try:
            logger.info(f"Merging branch from {branch_path}")
            
            # Analyze merge first
            can_auto_merge, analysis = self.analyze_merge(branch_path)
            
            if not can_auto_merge and not conflict_resolutions:
                return False, f"Merge conflicts detected. {analysis['conflict_count']} conflicts must be resolved."
            
            # Load branch metadata
            metadata = analysis['branch_metadata']
            
            # Connect to branch database
            branch_db_path = os.path.join(branch_path, "stpa.db")
            branch_connection = self._connect_to_branch_db(branch_db_path)
            
            if not branch_connection:
                return False, "Cannot connect to branch database"
            
            try:
                # Start transaction on main database
                main_cursor = self.db_connection.get_cursor()
                main_cursor.execute("BEGIN TRANSACTION")
                
                try:
                    # Apply conflict resolutions if provided
                    if conflict_resolutions:
                        self._apply_conflict_resolutions(branch_connection, conflict_resolutions)
                    
                    # Perform the merge
                    merged_count = self._perform_merge(branch_connection, metadata)
                    
                    # Create merge log entry
                    self._create_merge_log(metadata, merged_count, conflict_resolutions)
                    
                    main_cursor.execute("COMMIT")
                    
                    logger.info(f"Branch merged successfully. {merged_count} records merged.")
                    return True, f"Branch merged successfully. {merged_count} records merged."
                    
                except Exception as e:
                    main_cursor.execute("ROLLBACK")
                    raise e
                    
            finally:
                branch_connection.close()
                
        except Exception as e:
            logger.error(f"Failed to merge branch: {str(e)}")
            return False, f"Failed to merge branch: {str(e)}"
    
    def _validate_branch(self, branch_path: str) -> bool:
        """Validate branch structure and files."""
        required_files = ['stpa.db', 'branch_metadata.json']
        
        for file_name in required_files:
            file_path = os.path.join(branch_path, file_name)
            if not os.path.exists(file_path):
                logger.error(f"Required file missing: {file_path}")
                return False
        
        return True
    
    def _load_branch_metadata(self, branch_path: str) -> Optional[Dict[str, Any]]:
        """Load branch metadata from file."""
        metadata_path = os.path.join(branch_path, "branch_metadata.json")
        try:
            with open(metadata_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load branch metadata: {str(e)}")
            return None
    
    def _connect_to_branch_db(self, db_path: str) -> Optional[DatabaseConnection]:
        """Connect to a branch database."""
        try:
            from ..database.connection import DatabaseManager
            db_manager = DatabaseManager(db_path)
            return db_manager.get_connection()
        except Exception as e:
            logger.error(f"Failed to connect to branch database: {str(e)}")
            return None
    
    def _detect_conflicts(self, branch_connection: DatabaseConnection, metadata: Dict[str, Any]) -> List[MergeConflict]:
        """Detect merge conflicts between branch and main database."""
        conflicts = []
        
        # Get tables to check
        mergeable_tables = self._get_mergeable_tables()
        
        for table_name in mergeable_tables:
            table_conflicts = self._detect_table_conflicts(branch_connection, table_name, metadata)
            conflicts.extend(table_conflicts)
        
        return conflicts
    
    def _detect_table_conflicts(self, branch_connection: DatabaseConnection, table_name: str, 
                               metadata: Dict[str, Any]) -> List[MergeConflict]:
        """Detect conflicts in a specific table."""
        conflicts = []
        
        try:
            # Get branch records
            branch_cursor = branch_connection.get_cursor()
            branch_cursor.execute(f"SELECT * FROM {table_name} WHERE baseline = ?", (WORKING_BASELINE,))
            branch_records = {row[0]: dict(zip([col[0] for col in branch_cursor.description], row)) 
                            for row in branch_cursor.fetchall()}
            
            # Get main records
            main_cursor = self.db_connection.get_cursor()
            main_cursor.execute(f"SELECT * FROM {table_name} WHERE baseline = ?", (WORKING_BASELINE,))
            main_records = {row[0]: dict(zip([col[0] for col in main_cursor.description], row)) 
                          for row in main_cursor.fetchall()}
            
            # Check for conflicts
            for entity_id, branch_record in branch_records.items():
                if entity_id in main_records:
                    main_record = main_records[entity_id]
                    
                    # Check for hierarchical ID conflicts
                    if 'hierarchical_id' in branch_record and 'hierarchical_id' in main_record:
                        if branch_record['hierarchical_id'] != main_record['hierarchical_id']:
                            conflicts.append(MergeConflict(
                                ConflictType.HIERARCHICAL_ID,
                                table_name,
                                entity_id,
                                main_record,
                                branch_record,
                                f"Hierarchical ID conflict: main='{main_record['hierarchical_id']}', branch='{branch_record['hierarchical_id']}'"
                            ))
                    
                    # Check for data conflicts (simplified - compare all fields)
                    if self._records_differ(main_record, branch_record):
                        conflicts.append(MergeConflict(
                            ConflictType.DUPLICATE_ENTITY,
                            table_name,
                            entity_id,
                            main_record,
                            branch_record,
                            f"Entity data conflicts detected for ID {entity_id}"
                        ))
            
        except Exception as e:
            logger.error(f"Error detecting conflicts in table {table_name}: {str(e)}")
        
        return conflicts
    
    def _records_differ(self, record1: Dict[str, Any], record2: Dict[str, Any]) -> bool:
        """Check if two records have significant differences."""
        # Skip certain fields that are expected to differ
        skip_fields = {'id', 'created_at', 'updated_at', 'baseline'}
        
        for key in record1:
            if key not in skip_fields and record1.get(key) != record2.get(key):
                return True
        
        return False
    
    def _analyze_changes(self, branch_connection: DatabaseConnection, metadata: Dict[str, Any]) -> Dict[str, int]:
        """Analyze changes in the branch compared to main."""
        changes = {
            'added': 0,
            'modified': 0,
            'deleted': 0
        }
        
        mergeable_tables = self._get_mergeable_tables()
        
        for table_name in mergeable_tables:
            try:
                # Get branch record IDs
                branch_cursor = branch_connection.get_cursor()
                branch_cursor.execute(f"SELECT id FROM {table_name} WHERE baseline = ?", (WORKING_BASELINE,))
                branch_ids = set(row[0] for row in branch_cursor.fetchall())
                
                # Get main record IDs  
                main_cursor = self.db_connection.get_cursor()
                main_cursor.execute(f"SELECT id FROM {table_name} WHERE baseline = ?", (WORKING_BASELINE,))
                main_ids = set(row[0] for row in main_cursor.fetchall())
                
                # Calculate changes
                changes['added'] += len(branch_ids - main_ids)
                # Note: We can't easily detect deletions without tracking the original branch state
                # For now, we'll only count additions and modifications
                
            except Exception as e:
                logger.error(f"Error analyzing changes in table {table_name}: {str(e)}")
        
        return changes
    
    def _get_mergeable_tables(self) -> List[str]:
        """Get list of tables that can be merged."""
        cursor = self.db_connection.get_cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            AND name NOT IN ('baseline_metadata', 'merge_log')
        """)
        
        mergeable_tables = []
        for (table_name,) in cursor.fetchall():
            # Check if table has baseline column
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in cursor.fetchall()]
            if 'baseline' in columns:
                mergeable_tables.append(table_name)
        
        return mergeable_tables
    
    def _apply_conflict_resolutions(self, branch_connection: DatabaseConnection, resolutions: Dict[str, Any]):
        """Apply conflict resolutions to branch data before merging."""
        # This would apply user-selected conflict resolutions
        # For now, we'll implement a basic version
        for conflict_id, resolution in resolutions.items():
            try:
                if resolution['action'] == 'keep_main':
                    # Remove conflicting record from branch
                    table = resolution['table_name']
                    entity_id = resolution['entity_id']
                    cursor = branch_connection.get_cursor()
                    cursor.execute(f"DELETE FROM {table} WHERE id = ?", (entity_id,))
                    
            except Exception as e:
                logger.error(f"Error applying conflict resolution {conflict_id}: {str(e)}")
    
    def _perform_merge(self, branch_connection: DatabaseConnection, metadata: Dict[str, Any]) -> int:
        """Perform the actual merge operation."""
        merged_count = 0
        mergeable_tables = self._get_mergeable_tables()
        
        for table_name in mergeable_tables:
            try:
                count = self._merge_table(branch_connection, table_name)
                merged_count += count
                logger.info(f"Merged {count} records from table {table_name}")
                
            except Exception as e:
                logger.error(f"Error merging table {table_name}: {str(e)}")
                raise
        
        return merged_count
    
    def _merge_table(self, branch_connection: DatabaseConnection, table_name: str) -> int:
        """Merge records from a specific table."""
        # Get table structure
        main_cursor = self.db_connection.get_cursor()
        main_cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [col[1] for col in main_cursor.fetchall() if col[1] != 'id']
        
        # Get branch records that don't exist in main
        branch_cursor = branch_connection.get_cursor()
        branch_cursor.execute(f"SELECT * FROM {table_name} WHERE baseline = ?", (WORKING_BASELINE,))
        
        merged_count = 0
        for row in branch_cursor.fetchall():
            branch_record = dict(zip([col[0] for col in branch_cursor.description], row))
            entity_id = branch_record['id']
            
            # Check if record exists in main database
            main_cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE id = ?", (entity_id,))
            exists_in_main = main_cursor.fetchone()[0] > 0
            
            if not exists_in_main:
                # Insert new record
                columns_str = ', '.join(columns)
                placeholders = ', '.join(['?' for _ in columns])
                values = [branch_record[col] for col in columns]
                
                main_cursor.execute(f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})", values)
                merged_count += 1
        
        return merged_count
    
    def _create_merge_log(self, metadata: Dict[str, Any], merged_count: int, resolutions: Optional[Dict[str, Any]]):
        """Create a log entry for the merge operation."""
        try:
            cursor = self.db_connection.get_cursor()
            
            # Ensure merge_log table exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS merge_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    merge_date TEXT NOT NULL,
                    branch_name TEXT NOT NULL,
                    branch_description TEXT,
                    root_system_id INTEGER,
                    merged_records INTEGER DEFAULT 0,
                    conflicts_resolved INTEGER DEFAULT 0,
                    merge_metadata TEXT
                )
            """)
            
            # Insert merge log entry
            cursor.execute("""
                INSERT INTO merge_log (merge_date, branch_name, branch_description, root_system_id, 
                                     merged_records, conflicts_resolved, merge_metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                metadata.get('branch_name', 'unknown'),
                metadata.get('description', ''),
                metadata.get('root_system_id'),
                merged_count,
                len(resolutions) if resolutions else 0,
                json.dumps(metadata)
            ))
            
        except Exception as e:
            logger.error(f"Failed to create merge log: {str(e)}")