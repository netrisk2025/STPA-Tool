"""
Branch management functionality for STPA Tool
Handles creation and management of project branches for collaboration.
"""

import os
import shutil
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from ..database.connection import DatabaseConnection
from ..database.entities import System, EntityRepository
from ..config.constants import WORKING_BASELINE
from ..log_config.config import get_logger

logger = get_logger(__name__)


class BranchManager:
    """Manages project branches for collaborative work."""
    
    def __init__(self, db_connection: DatabaseConnection, working_directory: str):
        self.db_connection = db_connection
        self.working_directory = working_directory
        self.branches_dir = os.path.join(working_directory, "branches")
        
        # Ensure branches directory exists
        os.makedirs(self.branches_dir, exist_ok=True)
    
    def create_branch(self, system_id: int, branch_name: str, description: str = "") -> Tuple[bool, str]:
        """
        Create a new branch containing a specific system and all its descendants.
        
        Args:
            system_id: The root system ID for the branch
            branch_name: Name for the new branch
            description: Description of the branch purpose
        
        Returns:
            Tuple of (success, branch_path_or_error_message)
        """
        try:
            # Validate branch name
            if not self._is_valid_branch_name(branch_name):
                return False, "Invalid branch name. Use only letters, numbers, underscores, and hyphens."
            
            # Check if branch already exists
            branch_path = os.path.join(self.branches_dir, branch_name)
            if os.path.exists(branch_path):
                return False, f"Branch '{branch_name}' already exists."
            
            # Get the system and validate it exists
            system_repo = EntityRepository(self.db_connection, System)
            root_system = system_repo.get_by_id(system_id)
            if not root_system:
                return False, f"System with ID {system_id} not found."
            
            logger.info(f"Creating branch '{branch_name}' for system {system_id} ({root_system.system_name})")
            
            # Create branch directory
            os.makedirs(branch_path, exist_ok=True)
            
            # Create new database for the branch
            branch_db_path = os.path.join(branch_path, "stpa.db")
            self._create_branch_database(system_id, branch_db_path)
            
            # Copy configuration file
            config_source = os.path.join(self.working_directory, "config.json")
            config_dest = os.path.join(branch_path, "config.json")
            if os.path.exists(config_source):
                shutil.copy2(config_source, config_dest)
                # Update config to point to branch database
                self._update_branch_config(config_dest, branch_db_path)
            
            # Create branch metadata
            self._create_branch_metadata(branch_path, {
                'branch_name': branch_name,
                'description': description,
                'root_system_id': system_id,
                'root_system_name': root_system.system_name,
                'root_system_hierarchy': root_system.system_hierarchy,
                'created_date': datetime.now().isoformat(),
                'parent_project': os.path.basename(self.working_directory),
                'created_from_baseline': WORKING_BASELINE
            })
            
            # Create subdirectories
            os.makedirs(os.path.join(branch_path, "diagrams"), exist_ok=True)
            os.makedirs(os.path.join(branch_path, "baselines"), exist_ok=True)
            os.makedirs(os.path.join(branch_path, "temp"), exist_ok=True)
            
            logger.info(f"Branch '{branch_name}' created successfully at {branch_path}")
            return True, branch_path
            
        except Exception as e:
            logger.error(f"Failed to create branch: {str(e)}")
            # Cleanup on failure
            branch_path = os.path.join(self.branches_dir, branch_name)
            if os.path.exists(branch_path):
                shutil.rmtree(branch_path, ignore_errors=True)
            return False, f"Failed to create branch: {str(e)}"
    
    def list_branches(self) -> List[Dict[str, Any]]:
        """
        List all available branches.
        
        Returns:
            List of branch information dictionaries
        """
        try:
            branches = []
            
            if not os.path.exists(self.branches_dir):
                return branches
            
            for branch_name in os.listdir(self.branches_dir):
                branch_path = os.path.join(self.branches_dir, branch_name)
                if os.path.isdir(branch_path):
                    metadata = self._load_branch_metadata(branch_path)
                    if metadata:
                        metadata['branch_path'] = branch_path
                        metadata['database_exists'] = os.path.exists(os.path.join(branch_path, "stpa.db"))
                        branches.append(metadata)
            
            # Sort by creation date (newest first)
            branches.sort(key=lambda x: x.get('created_date', ''), reverse=True)
            return branches
            
        except Exception as e:
            logger.error(f"Failed to list branches: {str(e)}")
            return []
    
    def delete_branch(self, branch_name: str) -> Tuple[bool, str]:
        """
        Delete a branch and all its files.
        
        Args:
            branch_name: Name of the branch to delete
        
        Returns:
            Tuple of (success, message)
        """
        try:
            branch_path = os.path.join(self.branches_dir, branch_name)
            
            if not os.path.exists(branch_path):
                return False, f"Branch '{branch_name}' does not exist."
            
            logger.info(f"Deleting branch '{branch_name}'")
            
            # Remove entire branch directory
            shutil.rmtree(branch_path)
            
            logger.info(f"Branch '{branch_name}' deleted successfully")
            return True, f"Branch '{branch_name}' deleted successfully."
            
        except Exception as e:
            logger.error(f"Failed to delete branch: {str(e)}")
            return False, f"Failed to delete branch: {str(e)}"
    
    def get_branch_info(self, branch_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific branch.
        
        Args:
            branch_name: Name of the branch
        
        Returns:
            Branch information dictionary or None if not found
        """
        try:
            branch_path = os.path.join(self.branches_dir, branch_name)
            
            if not os.path.exists(branch_path):
                return None
            
            metadata = self._load_branch_metadata(branch_path)
            if metadata:
                metadata['branch_path'] = branch_path
                metadata['database_exists'] = os.path.exists(os.path.join(branch_path, "stpa.db"))
                
                # Get database statistics if available
                db_path = os.path.join(branch_path, "stpa.db")
                if os.path.exists(db_path):
                    metadata['database_size'] = os.path.getsize(db_path)
                    metadata['database_stats'] = self._get_branch_database_stats(db_path)
                
                return metadata
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get branch info: {str(e)}")
            return None
    
    def _is_valid_branch_name(self, name: str) -> bool:
        """Validate branch name format."""
        import re
        return bool(re.match(r'^[a-zA-Z0-9_-]+$', name)) and len(name) <= 64
    
    def _create_branch_database(self, root_system_id: int, branch_db_path: str):
        """Create a new database for the branch containing only the specified system tree."""
        # Copy the main database structure
        main_db_path = self.db_connection.db_path
        shutil.copy2(main_db_path, branch_db_path)
        
        # Connect to the branch database
        from ..database.connection import DatabaseManager
        branch_db_manager = DatabaseManager(branch_db_path)
        branch_connection = branch_db_manager.get_connection()
        
        try:
            cursor = branch_connection.get_cursor()
            cursor.execute("BEGIN TRANSACTION")
            
            # Get all descendant systems
            descendant_ids = self._get_system_descendants(root_system_id)
            all_system_ids = descendant_ids + [root_system_id]
            
            # Create placeholders for IN clause
            placeholders = ','.join(['?' for _ in all_system_ids])
            
            # Get all tables with system_hierarchy column
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """)
            
            for (table_name,) in cursor.fetchall():
                # Check if table has system_hierarchy or system_id column
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = [col[1] for col in cursor.fetchall()]
                
                if 'system_hierarchy' in columns:
                    # Get system hierarchies for the selected systems
                    system_repo = EntityRepository(self.db_connection, System)
                    hierarchies = []
                    for sys_id in all_system_ids:
                        system = system_repo.get_by_id(sys_id)
                        if system:
                            hierarchies.append(system.system_hierarchy)
                    
                    if hierarchies:
                        hierarchy_placeholders = ','.join(['?' for _ in hierarchies])
                        # Keep only records that match our system hierarchies
                        cursor.execute(f"""
                            DELETE FROM {table_name} 
                            WHERE system_hierarchy NOT IN ({hierarchy_placeholders})
                        """, hierarchies)
                
                elif 'system_id' in columns:
                    # Keep only records that match our system IDs
                    cursor.execute(f"""
                        DELETE FROM {table_name} 
                        WHERE system_id NOT IN ({placeholders})
                    """, all_system_ids)
            
            cursor.execute("COMMIT")
            
        except Exception as e:
            cursor.execute("ROLLBACK")
            raise e
        finally:
            branch_connection.close()
    
    def _get_system_descendants(self, root_system_id: int) -> List[int]:
        """Get all descendant system IDs recursively."""
        cursor = self.db_connection.get_cursor()
        descendants = []
        
        def get_children(parent_id):
            cursor.execute("""
                SELECT id FROM systems 
                WHERE parent_system_id = ? AND baseline = ?
            """, (parent_id, WORKING_BASELINE))
            
            for (child_id,) in cursor.fetchall():
                descendants.append(child_id)
                get_children(child_id)  # Recursive call for grandchildren
        
        get_children(root_system_id)
        return descendants
    
    def _update_branch_config(self, config_path: str, db_path: str):
        """Update branch configuration to point to branch database."""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Update database path to be relative to branch directory
            config['database_path'] = os.path.basename(db_path)
            
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
                
        except Exception as e:
            logger.warning(f"Failed to update branch config: {str(e)}")
    
    def _create_branch_metadata(self, branch_path: str, metadata: Dict[str, Any]):
        """Create branch metadata file."""
        metadata_path = os.path.join(branch_path, "branch_metadata.json")
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def _load_branch_metadata(self, branch_path: str) -> Optional[Dict[str, Any]]:
        """Load branch metadata from file."""
        metadata_path = os.path.join(branch_path, "branch_metadata.json")
        try:
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load branch metadata from {metadata_path}: {str(e)}")
        return None
    
    def _get_branch_database_stats(self, db_path: str) -> Dict[str, int]:
        """Get basic statistics about a branch database."""
        try:
            from ..database.connection import DatabaseManager
            db_manager = DatabaseManager(db_path)
            connection = db_manager.get_connection()
            
            stats = {}
            cursor = connection.get_cursor()
            
            # Count records in main tables
            main_tables = ['systems', 'functions', 'requirements', 'interfaces', 'assets']
            
            for table in main_tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE baseline = ?", (WORKING_BASELINE,))
                    stats[table] = cursor.fetchone()[0]
                except:
                    stats[table] = 0
            
            connection.close()
            return stats
            
        except Exception as e:
            logger.warning(f"Failed to get database stats: {str(e)}")
            return {}