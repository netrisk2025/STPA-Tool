"""
Database initialization and setup for STPA Tool
Handles database creation, migration, and initial data seeding.
"""

from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from ..config.constants import DEFAULT_DB_NAME, WORKING_BASELINE
from ..log_config.config import get_logger
from .connection import DatabaseManager
from .schema import SCHEMA_VERSION
from .entities import System, EntityFactory

logger = get_logger(__name__)


class DatabaseInitializer:
    """
    Handles database initialization and setup.
    """
    
    def __init__(self, working_directory: Path):
        """
        Initialize database initializer.
        
        Args:
            working_directory: Working directory for database
        """
        self.working_directory = working_directory
        self.db_path = working_directory / DEFAULT_DB_NAME
        self.db_manager = DatabaseManager(self.db_path)
    
    def initialize(self) -> bool:
        """
        Initialize database with schema and initial data.
        
        Returns:
            True if initialization was successful
        """
        try:
            logger.info("Starting database initialization")
            
            # Initialize database schema
            if not self.db_manager.initialize():
                logger.error("Failed to initialize database schema")
                return False
            
            # Verify database health
            if not self.db_manager.is_healthy():
                logger.error("Database health check failed")
                return False
            
            # Seed initial data if needed
            if self._is_empty_database():
                logger.info("Database is empty, seeding initial data")
                if not self._seed_initial_data():
                    logger.warning("Failed to seed initial data, but database is functional")
            
            logger.info("Database initialization completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Database initialization failed: {str(e)}")
            return False
    
    def get_database_manager(self) -> DatabaseManager:
        """
        Get the database manager instance.
        
        Returns:
            Database manager
        """
        return self.db_manager
    
    def _is_empty_database(self) -> bool:
        """
        Check if database is empty (no user data).
        
        Returns:
            True if database has no user data
        """
        try:
            connection = self.db_manager.get_connection()
            
            # Check if there are any systems
            systems_count = connection.fetchone("SELECT COUNT(*) as count FROM systems")
            if systems_count and systems_count['count'] > 0:
                return False
            
            # Check if there are any requirements
            requirements_count = connection.fetchone("SELECT COUNT(*) as count FROM requirements")
            if requirements_count and requirements_count['count'] > 0:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to check if database is empty: {str(e)}")
            return False
    
    def _seed_initial_data(self) -> bool:
        """
        Seed database with initial example data.
        
        Returns:
            True if seeding was successful
        """
        try:
            connection = self.db_manager.get_connection()
            system_repo = EntityFactory.get_repository(connection, System)
            
            # Create root system
            root_system = System(
                type_identifier="S",
                level_identifier=0,
                sequential_identifier=1,
                system_hierarchy="S-1",
                system_name="Example STPA System",
                system_description="This is an example system created during initial setup. You can modify or delete this system and create your own."
            )
            
            root_id = system_repo.create(root_system)
            if root_id:
                logger.info(f"Created example root system with ID {root_id}")
                
                # Create example subsystem
                subsystem = System(
                    type_identifier="S", 
                    level_identifier=1,
                    sequential_identifier=1,
                    system_hierarchy="S-1.1",
                    parent_system_id=root_id,
                    system_name="Example Subsystem",
                    system_description="This is an example subsystem showing hierarchical system organization."
                )
                
                subsystem_id = system_repo.create(subsystem)
                if subsystem_id:
                    logger.info(f"Created example subsystem with ID {subsystem_id}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to seed initial data: {str(e)}")
            return False
    
    def get_database_info(self) -> Dict[str, Any]:
        """
        Get comprehensive database information.
        
        Returns:
            Dictionary with database information
        """
        try:
            connection = self.db_manager.get_connection()
            info = connection.get_database_info()
            
            # Add additional statistics
            tables_info = self._get_table_statistics()
            info['tables'] = tables_info
            
            return info
            
        except Exception as e:
            logger.error(f"Failed to get database info: {str(e)}")
            return {'error': str(e)}
    
    def _get_table_statistics(self) -> Dict[str, int]:
        """
        Get row counts for all main tables.
        
        Returns:
            Dictionary with table names and row counts
        """
        try:
            connection = self.db_manager.get_connection()
            
            tables = [
                'systems', 'functions', 'interfaces', 'assets',
                'constraints', 'requirements', 'environments', 'hazards',
                'losses', 'control_structures', 'controllers',
                'control_algorithms', 'process_models', 'controlled_processes',
                'control_actions', 'feedback', 'state_diagrams', 'states',
                'in_transitions', 'out_transitions', 'safety_security_controls'
            ]
            
            stats = {}
            for table in tables:
                try:
                    result = connection.fetchone(f"SELECT COUNT(*) as count FROM {table}")
                    stats[table] = result['count'] if result else 0
                except Exception:
                    stats[table] = 0  # Table might not exist in older schemas
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get table statistics: {str(e)}")
            return {}
    
    def backup_database(self, backup_name: Optional[str] = None) -> Optional[Path]:
        """
        Create a backup of the database.
        
        Args:
            backup_name: Custom backup name (optional)
            
        Returns:
            Path to backup file or None if failed
        """
        try:
            if not backup_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"stpa_backup_{timestamp}.db"
            
            backup_path = self.working_directory / "backups" / backup_name
            backup_path.parent.mkdir(exist_ok=True)
            
            connection = self.db_manager.get_connection()
            if connection.backup_database(backup_path):
                logger.info(f"Database backed up to {backup_path}")
                return backup_path
            else:
                logger.error("Database backup failed")
                return None
                
        except Exception as e:
            logger.error(f"Failed to backup database: {str(e)}")
            return None
    
    def verify_database_integrity(self) -> bool:
        """
        Verify database integrity and consistency.
        
        Returns:
            True if database integrity is good
        """
        try:
            connection = self.db_manager.get_connection()
            
            # Run SQLite integrity check
            integrity_result = connection.fetchone("PRAGMA integrity_check")
            if not integrity_result or integrity_result[0] != "ok":
                logger.error(f"Database integrity check failed: {integrity_result}")
                return False
            
            # Check foreign key constraints
            fk_result = connection.fetchone("PRAGMA foreign_key_check")
            if fk_result:
                logger.error(f"Foreign key constraint violations found: {fk_result}")
                return False
            
            # Verify schema version
            version_result = connection.fetchone(
                "SELECT version FROM db_version ORDER BY applied_at DESC LIMIT 1"
            )
            if not version_result or version_result['version'] != SCHEMA_VERSION:
                logger.error(f"Schema version mismatch: expected {SCHEMA_VERSION}")
                return False
            
            logger.info("Database integrity verification passed")
            return True
            
        except Exception as e:
            logger.error(f"Database integrity verification failed: {str(e)}")
            return False
    
    def close(self) -> None:
        """Close database connections."""
        if self.db_manager:
            self.db_manager.close()


def initialize_database(working_directory: Path) -> Optional[DatabaseInitializer]:
    """
    Convenience function to initialize database.
    
    Args:
        working_directory: Working directory for database
        
    Returns:
        DatabaseInitializer instance or None if failed
    """
    try:
        initializer = DatabaseInitializer(working_directory)
        
        if initializer.initialize():
            return initializer
        else:
            return None
            
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        return None