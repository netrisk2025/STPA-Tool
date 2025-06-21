"""
Archive export functionality for STPA Tool
Creates ZIP archives of working directories for collaboration and backup.
"""

import os
import zipfile
import shutil
from pathlib import Path
from typing import List, Optional, Callable
from datetime import datetime

from ..log_config.config import get_logger

logger = get_logger(__name__)


class ArchiveExporter:
    """Handles ZIP archive creation for working directories."""
    
    def __init__(self):
        pass
    
    def export_working_directory(
        self, 
        working_dir: str, 
        output_path: str,
        exclude_patterns: Optional[List[str]] = None,
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> bool:
        """
        Export working directory as ZIP archive.
        
        Args:
            working_dir: Path to the working directory to export
            output_path: Path where to save the ZIP file
            exclude_patterns: List of file patterns to exclude
            progress_callback: Optional callback for progress updates
        
        Returns:
            True if export successful, False otherwise
        """
        logger.info(f"Starting working directory export: {working_dir} -> {output_path}")
        
        try:
            if not os.path.exists(working_dir):
                raise ValueError(f"Working directory does not exist: {working_dir}")
            
            # Default exclusions
            if exclude_patterns is None:
                exclude_patterns = [
                    '*.tmp', '*.log', '*~', '.DS_Store', 'Thumbs.db',
                    '*.bak', '*.swp', '*.swo', '__pycache__'
                ]
            
            # Get list of files to include
            files_to_include = self._get_files_to_include(working_dir, exclude_patterns)
            
            total_files = len(files_to_include)
            logger.info(f"Found {total_files} files to include in archive")
            
            # Create the ZIP archive
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for i, file_path in enumerate(files_to_include):
                    # Calculate relative path within working directory
                    rel_path = os.path.relpath(file_path, working_dir)
                    
                    # Add file to archive
                    zipf.write(file_path, rel_path)
                    
                    # Progress callback
                    if progress_callback:
                        progress_callback(i + 1, f"Adding {rel_path}")
                
                # Add metadata file
                metadata = self._create_archive_metadata(working_dir, total_files)
                zipf.writestr("STPA_EXPORT_METADATA.json", metadata)
            
            logger.info(f"Working directory export completed: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export working directory: {str(e)}")
            return False
    
    def _get_files_to_include(self, working_dir: str, exclude_patterns: List[str]) -> List[str]:
        """Get list of files to include in the archive."""
        import fnmatch
        
        files_to_include = []
        
        for root, dirs, files in os.walk(working_dir):
            # Filter directories to skip
            dirs[:] = [d for d in dirs if not any(fnmatch.fnmatch(d, pattern) for pattern in exclude_patterns)]
            
            for file in files:
                file_path = os.path.join(root, file)
                
                # Check if file matches any exclusion pattern
                if not any(fnmatch.fnmatch(file, pattern) for pattern in exclude_patterns):
                    files_to_include.append(file_path)
        
        return files_to_include
    
    def _create_archive_metadata(self, working_dir: str, file_count: int) -> str:
        """Create metadata JSON for the archive."""
        import json
        
        # Get database info if available
        db_path = os.path.join(working_dir, "stpa.db")
        db_size = 0
        db_exists = False
        
        if os.path.exists(db_path):
            db_exists = True
            db_size = os.path.getsize(db_path)
        
        metadata = {
            "export_info": {
                "export_timestamp": datetime.now().isoformat(),
                "stpa_tool_version": "1.0.0",
                "export_type": "Working Directory Archive",
                "source_directory": os.path.basename(working_dir)
            },
            "contents": {
                "total_files": file_count,
                "database_included": db_exists,
                "database_size_bytes": db_size,
                "includes_diagrams": os.path.exists(os.path.join(working_dir, "diagrams")),
                "includes_baselines": os.path.exists(os.path.join(working_dir, "baselines"))
            },
            "instructions": {
                "usage": "Extract this archive to create a new STPA Tool working directory",
                "requirements": "STPA Tool v1.0.0 or compatible",
                "notes": "Ensure extracted directory has proper read/write permissions"
            }
        }
        
        return json.dumps(metadata, indent=2)
    
    def extract_archive(
        self, 
        archive_path: str, 
        destination_dir: str,
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> bool:
        """
        Extract a STPA Tool archive to a destination directory.
        
        Args:
            archive_path: Path to the ZIP archive
            destination_dir: Directory where to extract files
            progress_callback: Optional callback for progress updates
        
        Returns:
            True if extraction successful, False otherwise
        """
        logger.info(f"Extracting archive: {archive_path} -> {destination_dir}")
        
        try:
            if not os.path.exists(archive_path):
                raise ValueError(f"Archive file does not exist: {archive_path}")
            
            # Create destination directory if it doesn't exist
            os.makedirs(destination_dir, exist_ok=True)
            
            with zipfile.ZipFile(archive_path, 'r') as zipf:
                file_list = zipf.namelist()
                total_files = len(file_list)
                
                for i, file_name in enumerate(file_list):
                    zipf.extract(file_name, destination_dir)
                    
                    if progress_callback:
                        progress_callback(i + 1, f"Extracting {file_name}")
            
            logger.info(f"Archive extraction completed: {destination_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to extract archive: {str(e)}")
            return False
    
    def validate_archive(self, archive_path: str) -> tuple[bool, List[str]]:
        """
        Validate a STPA Tool archive.
        
        Args:
            archive_path: Path to the ZIP archive to validate
        
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        logger.info(f"Validating archive: {archive_path}")
        
        issues = []
        is_valid = True
        
        try:
            if not os.path.exists(archive_path):
                issues.append("Archive file does not exist")
                return False, issues
            
            with zipfile.ZipFile(archive_path, 'r') as zipf:
                # Check if it's a valid ZIP file
                if zipf.testzip() is not None:
                    issues.append("Archive is corrupted")
                    is_valid = False
                
                file_list = zipf.namelist()
                
                # Check for essential files
                has_database = any('stpa.db' in f for f in file_list)
                has_config = any('config.json' in f or 'config.yaml' in f for f in file_list)
                has_metadata = 'STPA_EXPORT_METADATA.json' in file_list
                
                if not has_database:
                    issues.append("No database file (stpa.db) found in archive")
                    is_valid = False
                
                if not has_config:
                    issues.append("No configuration file found in archive")
                
                if not has_metadata:
                    issues.append("No export metadata found - may not be a STPA Tool archive")
                
                # Check metadata if present
                if has_metadata:
                    try:
                        metadata_content = zipf.read('STPA_EXPORT_METADATA.json')
                        import json
                        metadata = json.loads(metadata_content)
                        
                        if 'export_info' not in metadata:
                            issues.append("Invalid metadata format")
                        
                    except Exception as e:
                        issues.append(f"Could not read metadata: {str(e)}")
            
            logger.info(f"Archive validation completed: {'valid' if is_valid else 'invalid'}")
            return is_valid, issues
            
        except Exception as e:
            logger.error(f"Error validating archive: {str(e)}")
            return False, [f"Validation error: {str(e)}"]
    
    def get_archive_info(self, archive_path: str) -> Optional[dict]:
        """
        Get information about a STPA Tool archive.
        
        Args:
            archive_path: Path to the ZIP archive
        
        Returns:
            Dictionary with archive information or None if invalid
        """
        try:
            with zipfile.ZipFile(archive_path, 'r') as zipf:
                if 'STPA_EXPORT_METADATA.json' in zipf.namelist():
                    metadata_content = zipf.read('STPA_EXPORT_METADATA.json')
                    import json
                    return json.loads(metadata_content)
                else:
                    # Basic info without metadata
                    file_list = zipf.namelist()
                    return {
                        "export_info": {
                            "export_timestamp": "Unknown",
                            "export_type": "Legacy Archive",
                            "source_directory": "Unknown"
                        },
                        "contents": {
                            "total_files": len(file_list),
                            "database_included": any('stpa.db' in f for f in file_list)
                        }
                    }
                    
        except Exception as e:
            logger.error(f"Error reading archive info: {str(e)}")
            return None