"""
Working directory management utilities for STPA Tool
Handles directory validation, initialization, and management.
"""

import os
import shutil
from pathlib import Path
from typing import Optional, List

from ..config.constants import (
    DEFAULT_DB_NAME, DIAGRAMS_DIR, BASELINES_DIR, TEMP_DIR,
    CONFIG_FILE_JSON, DEFAULT_DIR_PERMISSIONS
)
from ..logging.config import get_logger

logger = get_logger(__name__)


class DirectoryManager:
    """
    Manages working directory operations for the STPA Tool.
    """
    
    def __init__(self, working_directory: Optional[Path] = None):
        """
        Initialize directory manager.
        
        Args:
            working_directory: Path to working directory
        """
        self.working_directory = working_directory
    
    def validate_directory(self, directory_path: Path) -> tuple[bool, Optional[str]]:
        """
        Validate a directory for use as working directory.
        
        Args:
            directory_path: Path to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check if path exists
            if not directory_path.exists():
                return False, "Directory does not exist"
            
            # Check if it's actually a directory
            if not directory_path.is_dir():
                return False, "Path is not a directory"
            
            # Check read permissions
            if not os.access(directory_path, os.R_OK):
                return False, "No read permission for directory"
            
            # Check write permissions
            if not os.access(directory_path, os.W_OK):
                return False, "No write permission for directory"
            
            # Check if directory is writable by creating a test file
            test_file = directory_path / ".stpa_tool_test"
            try:
                test_file.touch()
                test_file.unlink()
            except Exception:
                return False, "Cannot write to directory"
            
            return True, None
            
        except Exception as e:
            return False, f"Error validating directory: {str(e)}"
    
    def initialize_directory(self, directory_path: Path) -> tuple[bool, Optional[str]]:
        """
        Initialize a directory for use with STPA Tool.
        
        Args:
            directory_path: Path to initialize
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Validate directory first
            is_valid, error_msg = self.validate_directory(directory_path)
            if not is_valid:
                return False, error_msg
            
            # Create subdirectories
            subdirs = [DIAGRAMS_DIR, BASELINES_DIR, TEMP_DIR]
            for subdir in subdirs:
                subdir_path = directory_path / subdir
                subdir_path.mkdir(exist_ok=True, parents=True)
                
                # Set permissions
                try:
                    subdir_path.chmod(DEFAULT_DIR_PERMISSIONS)
                except Exception:
                    # Permissions might not be supported on all systems
                    pass
            
            # Update working directory
            self.working_directory = directory_path
            
            logger.info(f"Initialized working directory: {directory_path}")
            return True, None
            
        except Exception as e:
            error_msg = f"Error initializing directory: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def get_database_path(self) -> Optional[Path]:
        """
        Get path to database file in working directory.
        
        Returns:
            Path to database file or None if no working directory set
        """
        if not self.working_directory:
            return None
        
        return self.working_directory / DEFAULT_DB_NAME
    
    def get_config_path(self) -> Optional[Path]:
        """
        Get path to configuration file in working directory.
        
        Returns:
            Path to configuration file or None if no working directory set
        """
        if not self.working_directory:
            return None
        
        return self.working_directory / CONFIG_FILE_JSON
    
    def get_diagrams_path(self) -> Optional[Path]:
        """
        Get path to diagrams directory.
        
        Returns:
            Path to diagrams directory or None if no working directory set
        """
        if not self.working_directory:
            return None
        
        return self.working_directory / DIAGRAMS_DIR
    
    def get_baselines_path(self) -> Optional[Path]:
        """
        Get path to baselines directory.
        
        Returns:
            Path to baselines directory or None if no working directory set
        """
        if not self.working_directory:
            return None
        
        return self.working_directory / BASELINES_DIR
    
    def get_temp_path(self) -> Optional[Path]:
        """
        Get path to temporary files directory.
        
        Returns:
            Path to temp directory or None if no working directory set
        """
        if not self.working_directory:
            return None
        
        return self.working_directory / TEMP_DIR
    
    def list_existing_files(self) -> List[str]:
        """
        List existing STPA Tool files in working directory.
        
        Returns:
            List of existing file names
        """
        if not self.working_directory:
            return []
        
        existing_files = []
        
        # Check for database
        db_path = self.get_database_path()
        if db_path and db_path.exists():
            existing_files.append(db_path.name)
        
        # Check for config file
        config_path = self.get_config_path()
        if config_path and config_path.exists():
            existing_files.append(config_path.name)
        
        # Check for directories
        for dir_name in [DIAGRAMS_DIR, BASELINES_DIR, TEMP_DIR]:
            dir_path = self.working_directory / dir_name
            if dir_path.exists() and dir_path.is_dir():
                existing_files.append(f"{dir_name}/")
        
        return existing_files
    
    def cleanup_temp_files(self) -> bool:
        """
        Clean up temporary files in working directory.
        
        Returns:
            True if cleanup was successful
        """
        try:
            temp_path = self.get_temp_path()
            if not temp_path or not temp_path.exists():
                return True
            
            # Remove all files in temp directory
            for item in temp_path.iterdir():
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
            
            logger.info("Cleaned up temporary files")
            return True
            
        except Exception as e:
            logger.error(f"Error cleaning up temp files: {str(e)}")
            return False
    
    def backup_database(self, backup_name: Optional[str] = None) -> tuple[bool, Optional[str]]:
        """
        Create a backup of the database file.
        
        Args:
            backup_name: Custom backup name (optional)
            
        Returns:
            Tuple of (success, backup_path or error_message)
        """
        try:
            db_path = self.get_database_path()
            if not db_path or not db_path.exists():
                return False, "Database file not found"
            
            # Generate backup name if not provided
            if not backup_name:
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"stpa_backup_{timestamp}.db"
            
            backup_path = self.working_directory / backup_name
            
            # Copy database file
            shutil.copy2(db_path, backup_path)
            
            logger.info(f"Created database backup: {backup_path}")
            return True, str(backup_path)
            
        except Exception as e:
            error_msg = f"Error creating database backup: {str(e)}"
            logger.error(error_msg)
            return False, error_msg