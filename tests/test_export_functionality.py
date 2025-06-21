"""
Unit tests for export functionality of the STPA Tool.
Tests JSON, Markdown, and archive export capabilities.
"""

import pytest
import tempfile
import json
import zipfile
from pathlib import Path
import sys
import os

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.export.json_exporter import JsonExporter
from src.export.markdown_exporter import MarkdownExporter
from src.export.archive_exporter import ArchiveExporter
from src.database.init import DatabaseInitializer
from src.database.entities import System, Function, Requirement, EntityFactory


@pytest.fixture
def temp_database():
    """Create temporary database with test data for export testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Initialize database
        db_init = DatabaseInitializer(temp_path)
        db_init.initialize()
        db_manager = db_init.get_database_manager()
        connection = db_manager.get_connection()
        
        # Add additional test data
        system_repo = EntityFactory.get_repository(connection, System)
        function_repo = EntityFactory.get_repository(connection, Function)
        requirement_repo = EntityFactory.get_repository(connection, Requirement)
        
        # Create test system
        test_system = System(
            type_identifier="S",
            level_identifier=0,
            sequential_identifier=100,
            system_hierarchy="S-100",
            system_name="Export Test System",
            system_description="System created for export testing"
        )
        system_id = system_repo.create(test_system)
        
        # Create test function
        test_function = Function(
            type_identifier="F",
            level_identifier=0,
            sequential_identifier=1,
            system_hierarchy="F-100.1",
            system_id=system_id,
            function_name="Export Test Function",
            function_description="Function for export testing"
        )
        function_repo.create(test_function)
        
        # Create test requirement
        test_requirement = Requirement(
            type_identifier="R",
            level_identifier=0,
            alphanumeric_identifier="REQ-100",
            system_hierarchy="R-100.1",
            system_id=system_id,
            requirement_text="The system shall support export functionality"
        )
        requirement_repo.create(test_requirement)
        
        yield db_init, system_id
        
        db_init.close()


class TestJsonExporter:
    """Test JSON export functionality."""
    
    def test_json_exporter_creation(self, temp_database):
        """Test JsonExporter creation."""
        db_init, system_id = temp_database
        connection = db_init.get_database_manager().get_connection()
        
        exporter = JsonExporter(connection)
        assert exporter is not None
    
    def test_export_system_data(self, temp_database):
        """Test exporting system data to JSON."""
        db_init, system_id = temp_database
        connection = db_init.get_database_manager().get_connection()
        
        exporter = JsonExporter(connection)
        
        # Export test system
        result = exporter.export_system_of_interest(system_id)
        
        assert result is not None
        assert 'system' in result
        assert 'functions' in result
        assert 'requirements' in result
        
        # Verify system data
        assert result['system']['system_name'] == "Export Test System"
        assert result['system']['system_hierarchy'] == "S-100"
        
        # Verify associated data
        assert len(result['functions']) >= 1
        assert len(result['requirements']) >= 1
        
        # Check function data
        function = result['functions'][0]
        assert function['function_name'] == "Export Test Function"
        
        # Check requirement data
        requirement = result['requirements'][0]
        assert requirement['requirement_text'] == "The system shall support export functionality"
    
    def test_export_to_file(self, temp_database):
        """Test exporting JSON data to file."""
        db_init, system_id = temp_database
        connection = db_init.get_database_manager().get_connection()
        
        exporter = JsonExporter(connection)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            output_path = Path(temp_file.name)
        
        try:
            # Export to file
            success = exporter.export_to_file(system_id, str(output_path))
            assert success is True
            assert output_path.exists()
            
            # Verify file contents
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            assert 'system' in data
            assert data['system']['system_name'] == "Export Test System"
            
        finally:
            if output_path.exists():
                output_path.unlink()
    
    def test_export_with_child_systems(self, temp_database):
        """Test exporting system with child systems."""
        db_init, parent_system_id = temp_database
        connection = db_init.get_database_manager().get_connection()
        system_repo = EntityFactory.get_repository(connection, System)
        
        # Create child system
        child_system = System(
            type_identifier="S",
            level_identifier=1,
            sequential_identifier=1,
            system_hierarchy="S-100.1",
            system_name="Child Export Test System",
            system_description="Child system for export testing",
            parent_system_id=parent_system_id
        )
        child_id = system_repo.create(child_system)
        
        exporter = JsonExporter(connection)
        
        # Export with child systems
        result = exporter.export_system_of_interest(parent_system_id, include_children=True)
        
        assert 'child_systems' in result
        assert len(result['child_systems']) >= 1
        
        child_data = result['child_systems'][0]
        assert child_data['system_name'] == "Child Export Test System"
        assert child_data['system_hierarchy'] == "S-100.1"


class TestMarkdownExporter:
    """Test Markdown export functionality."""
    
    def test_markdown_exporter_creation(self, temp_database):
        """Test MarkdownExporter creation."""
        db_init, system_id = temp_database
        connection = db_init.get_database_manager().get_connection()
        
        exporter = MarkdownExporter(connection)
        assert exporter is not None
    
    def test_export_system_specification(self, temp_database):
        """Test exporting system specification to Markdown."""
        db_init, system_id = temp_database
        connection = db_init.get_database_manager().get_connection()
        
        exporter = MarkdownExporter(connection)
        
        # Export system specification
        result = exporter.export_system_specification(system_id)
        
        assert result is not None
        assert isinstance(result, str)
        assert "Export Test System" in result
        assert "# Export Test System Specification" in result
        assert "The system shall support export functionality" in result
    
    def test_export_system_description(self, temp_database):
        """Test exporting system description to Markdown."""
        db_init, system_id = temp_database
        connection = db_init.get_database_manager().get_connection()
        
        exporter = MarkdownExporter(connection)
        
        # Export system description
        result = exporter.export_system_description(system_id)
        
        assert result is not None
        assert isinstance(result, str)
        assert "Export Test System" in result
        assert "System created for export testing" in result
        assert "Export Test Function" in result
    
    def test_export_to_file(self, temp_database):
        """Test exporting Markdown to file."""
        db_init, system_id = temp_database
        connection = db_init.get_database_manager().get_connection()
        
        exporter = MarkdownExporter(connection)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as temp_file:
            output_path = Path(temp_file.name)
        
        try:
            # Export specification to file
            success = exporter.export_specification_to_file(system_id, output_path)
            assert success is True
            assert output_path.exists()
            
            # Verify file contents
            with open(output_path, 'r') as f:
                content = f.read()
            
            assert "Export Test System" in content
            assert "The system shall support export functionality" in content
            
        finally:
            if output_path.exists():
                output_path.unlink()
    
    def test_markdown_formatting(self, temp_database):
        """Test Markdown formatting quality."""
        db_init, system_id = temp_database
        connection = db_init.get_database_manager().get_connection()
        
        exporter = MarkdownExporter(connection)
        
        # Export system specification
        result = exporter.export_system_specification(system_id)
        
        # Check for proper Markdown formatting
        assert result.startswith("#")  # Should start with header
        assert "##" in result  # Should have sub-headers
        assert "\n\n" in result  # Should have proper spacing
        
        # Check for requirement formatting
        lines = result.split('\n')
        requirement_lines = [line for line in lines if "R-" in line and "REQ" not in line]
        assert len(requirement_lines) > 0  # Should include requirement IDs


class TestArchiveExporter:
    """Test working directory archive export functionality."""
    
    def test_archive_exporter_creation(self):
        """Test ArchiveExporter creation."""
        exporter = ArchiveExporter()
        assert exporter is not None
    
    def test_create_archive(self, temp_database):
        """Test creating archive of working directory."""
        db_init, system_id = temp_database
        working_dir = db_init.working_directory
        
        exporter = ArchiveExporter()
        
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_file:
            archive_path = Path(temp_file.name)
        
        try:
            # Create archive
            success = exporter.export_working_directory(str(working_dir), str(archive_path))
            assert success is True
            assert archive_path.exists()
            
            # Verify archive contents
            with zipfile.ZipFile(archive_path, 'r') as zip_file:
                files = zip_file.namelist()
                
                # Should contain database file
                assert any('stpa.db' in f for f in files)
                
                # Should contain config file if it exists
                config_files = [f for f in files if 'config' in f.lower()]
                # May or may not have config file depending on setup
                
        finally:
            if archive_path.exists():
                archive_path.unlink()
    
    def test_archive_with_filters(self, temp_database):
        """Test creating archive with file filters."""
        db_init, system_id = temp_database
        working_dir = db_init.working_directory
        
        # Create some test files to filter
        test_file = working_dir / "test.tmp"
        test_file.write_text("temporary file")
        
        log_file = working_dir / "test.log"
        log_file.write_text("log file")
        
        exporter = ArchiveExporter()
        
        # Use exclusion patterns in the export call
        
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_file:
            archive_path = Path(temp_file.name)
        
        try:
            # Create archive with filters
            success = exporter.export_working_directory(
                str(working_dir), 
                str(archive_path),
                exclude_patterns=['*.tmp', '*.log']
            )
            assert success is True
            
            # Verify filtered files are excluded
            with zipfile.ZipFile(archive_path, 'r') as zip_file:
                files = zip_file.namelist()
                
                # Should not contain filtered files
                assert not any('test.tmp' in f for f in files)
                assert not any('test.log' in f for f in files)
                
                # Should still contain database
                assert any('stpa.db' in f for f in files)
                
        finally:
            if archive_path.exists():
                archive_path.unlink()
            if test_file.exists():
                test_file.unlink()
            if log_file.exists():
                log_file.unlink()
    
    def test_validate_archive(self, temp_database):
        """Test archive validation functionality."""
        db_init, system_id = temp_database
        working_dir = db_init.working_directory
        
        exporter = ArchiveExporter()
        
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_file:
            archive_path = Path(temp_file.name)
        
        try:
            # Create archive
            exporter.export_working_directory(str(working_dir), str(archive_path))
            
            # Validate archive
            is_valid, issues = exporter.validate_archive(str(archive_path))
            assert is_valid is True
            assert isinstance(issues, list)
            
        finally:
            if archive_path.exists():
                archive_path.unlink()
    
    def test_get_archive_info(self, temp_database):
        """Test getting archive information."""
        db_init, system_id = temp_database
        working_dir = db_init.working_directory
        
        exporter = ArchiveExporter()
        
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_file:
            archive_path = Path(temp_file.name)
        
        try:
            # Create archive
            exporter.export_working_directory(str(working_dir), str(archive_path))
            
            # Get archive info
            info = exporter.get_archive_info(str(archive_path))
            
            assert info is not None
            assert 'contents' in info
            assert 'export_info' in info  
            assert 'instructions' in info
            
            # Check the contents structure
            assert info['contents']['database_included'] is True
            
        finally:
            if archive_path.exists():
                archive_path.unlink()


class TestExportIntegration:
    """Test integration between different export components."""
    
    def test_export_workflow(self, temp_database):
        """Test complete export workflow."""
        db_init, system_id = temp_database
        connection = db_init.get_database_manager().get_connection()
        working_dir = db_init.working_directory
        
        # Export JSON
        json_exporter = JsonExporter(connection)
        json_path = working_dir / "export_test.json"
        json_success = json_exporter.export_to_file(system_id, json_path)
        assert json_success is True
        assert json_path.exists()
        
        # Export Markdown
        md_exporter = MarkdownExporter(connection)
        md_path = working_dir / "export_test.md"
        md_success = md_exporter.export_specification_to_file(system_id, md_path)
        assert md_success is True
        assert md_path.exists()
        
        # Create archive including exported files
        archive_exporter = ArchiveExporter()
        archive_path = working_dir / "complete_export.zip"
        
        try:
            archive_success = archive_exporter.export_working_directory(str(working_dir), str(archive_path))
            assert archive_success is True
            assert archive_path.exists()
            
            # Verify archive contains exported files
            with zipfile.ZipFile(archive_path, 'r') as zip_file:
                files = zip_file.namelist()
                assert any('export_test.json' in f for f in files)
                assert any('export_test.md' in f for f in files)
                assert any('stpa.db' in f for f in files)
        
        finally:
            # Cleanup
            for file_path in [json_path, md_path, archive_path]:
                if file_path.exists():
                    file_path.unlink()


class TestExportErrorHandling:
    """Test export error handling and edge cases."""
    
    def test_json_export_invalid_system(self, temp_database):
        """Test JSON export with invalid system ID."""
        db_init, system_id = temp_database
        connection = db_init.get_database_manager().get_connection()
        
        exporter = JsonExporter(connection)
        
        # Try to export non-existent system
        result = exporter.export_system_of_interest(999999)
        assert result is None
    
    def test_markdown_export_invalid_system(self, temp_database):
        """Test Markdown export with invalid system ID."""
        db_init, system_id = temp_database
        connection = db_init.get_database_manager().get_connection()
        
        exporter = MarkdownExporter(connection)
        
        # Try to export non-existent system
        result = exporter.export_system_specification(999999)
        assert result is None or result == ""
    
    def test_archive_invalid_directory(self):
        """Test archive creation with invalid directory."""
        invalid_dir = Path("/nonexistent/directory")
        
        exporter = ArchiveExporter()
        
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_file:
            archive_path = Path(temp_file.name)
        
        try:
            # Should handle gracefully
            success = exporter.export_working_directory(str(invalid_dir), str(archive_path))
            assert success is False
            
        finally:
            if archive_path.exists():
                archive_path.unlink()
    
    def test_export_file_permissions(self, temp_database):
        """Test export with file permission issues."""
        db_init, system_id = temp_database
        connection = db_init.get_database_manager().get_connection()
        
        exporter = JsonExporter(connection)
        
        # Try to export to read-only directory (if possible)
        try:
            readonly_dir = Path("/tmp/readonly_test")
            readonly_dir.mkdir(exist_ok=True)
            readonly_dir.chmod(0o444)  # Read-only
            
            readonly_file = readonly_dir / "test.json"
            
            # Should handle permission error gracefully
            success = exporter.export_to_file(system_id, readonly_file)
            # May succeed or fail depending on system, but shouldn't crash
            assert isinstance(success, bool)
            
        except (PermissionError, OSError):
            # Expected on some systems
            pass
        finally:
            # Cleanup
            try:
                readonly_dir.chmod(0o755)
                readonly_dir.rmdir()
            except (PermissionError, OSError, FileNotFoundError):
                pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])