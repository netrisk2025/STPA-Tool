"""
Comprehensive database tests for STPA Tool
Tests database schema, connections, entities, and operations.
"""

import pytest
import tempfile
import sqlite3
from pathlib import Path
from datetime import datetime

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.database.connection import DatabaseConnection, DatabaseManager
from src.database.schema import get_full_schema_sql, SCHEMA_VERSION
from src.database.entities import System, Function, Requirement, EntityRepository, EntityFactory
from src.database.init import DatabaseInitializer
from src.utils.hierarchy import HierarchyManager, HierarchicalID


class TestDatabaseSchema:
    """Test database schema creation and validation."""
    
    def test_schema_generation(self):
        """Test that schema SQL is generated correctly."""
        schema_sql = get_full_schema_sql()
        
        assert schema_sql is not None
        assert len(schema_sql) > 0
        assert "CREATE TABLE" in schema_sql
        assert "systems" in schema_sql
        assert "requirements" in schema_sql
        assert "audit_log" in schema_sql
        assert SCHEMA_VERSION in schema_sql
    
    def test_schema_creation(self):
        """Test that schema can be created in SQLite."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=True) as temp_file:
            temp_path = Path(temp_file.name)
            temp_file.close()  # Close so SQLite can use it
            
            # Create database with schema
            conn = sqlite3.connect(str(temp_path))
            schema_sql = get_full_schema_sql()
            conn.executescript(schema_sql)
            conn.close()
            
            # Verify tables were created
            conn = sqlite3.connect(str(temp_path))
            cursor = conn.cursor()
            
            # Check that key tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            required_tables = ['systems', 'functions', 'requirements', 'audit_log', 'db_version']
            for table in required_tables:
                assert table in tables
            
            conn.close()


class TestDatabaseConnection:
    """Test database connection management."""
    
    def test_database_connection_creation(self):
        """Test database connection creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            
            # Create connection
            db_conn = DatabaseConnection(db_path)
            
            # Test basic operations
            result = db_conn.fetchone("SELECT 1 as test")
            assert result is not None
            assert result['test'] == 1
            
            db_conn.close_connection()
    
    def test_database_manager_initialization(self):
        """Test database manager initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            
            # Create and initialize database manager
            db_manager = DatabaseManager(db_path)
            
            assert db_manager.initialize() is True
            assert db_manager.is_healthy() is True
            
            # Check database info
            info = db_manager.get_connection().get_database_info()
            assert info['schema_version'] == SCHEMA_VERSION
            assert info['foreign_keys_enabled'] is True
            
            db_manager.close()
    
    def test_database_transaction(self):
        """Test database transaction handling."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            
            db_manager = DatabaseManager(db_path)
            db_manager.initialize()
            
            connection = db_manager.get_connection()
            
            # Test successful transaction
            with connection.transaction():
                connection.execute(
                    "INSERT INTO systems (type_identifier, level_identifier, sequential_identifier, system_hierarchy, system_name) VALUES (?, ?, ?, ?, ?)",
                    ("S", 0, 1, "S-1", "Test System")
                )
            
            # Verify data was committed
            result = connection.fetchone("SELECT system_name FROM systems WHERE system_hierarchy = 'S-1'")
            assert result is not None
            assert result['system_name'] == "Test System"
            
            # Test transaction rollback
            try:
                with connection.transaction():
                    connection.execute(
                        "INSERT INTO systems (type_identifier, level_identifier, sequential_identifier, system_hierarchy, system_name) VALUES (?, ?, ?, ?, ?)",
                        ("S", 0, 2, "S-2", "Test System 2")
                    )
                    # Force an error to trigger rollback
                    raise Exception("Test error")
            except Exception:
                pass
            
            # Verify data was rolled back
            result = connection.fetchone("SELECT system_name FROM systems WHERE system_hierarchy = 'S-2'")
            assert result is None
            
            db_manager.close()


class TestDatabaseEntities:
    """Test database entity classes and operations."""
    
    def test_system_entity_creation(self):
        """Test System entity creation and properties."""
        system = System(
            type_identifier="S",
            level_identifier=0,
            sequential_identifier=1,
            system_hierarchy="S-1",
            system_name="Test System",
            system_description="A test system"
        )
        
        assert system.get_table_name() == "systems"
        assert system.get_hierarchical_id() == "S-1"
        
        # Test dictionary conversion
        system_dict = system.to_dict()
        assert system_dict['system_name'] == "Test System"
        assert system_dict['type_identifier'] == "S"
    
    def test_entity_repository_crud(self):
        """Test entity repository CRUD operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            
            # Initialize database
            db_manager = DatabaseManager(db_path)
            db_manager.initialize()
            connection = db_manager.get_connection()
            
            # Get repository
            system_repo = EntityFactory.get_repository(connection, System)
            
            # Test CREATE
            system = System(
                type_identifier="S",
                level_identifier=0,
                sequential_identifier=1,
                system_hierarchy="S-1",
                system_name="Test System",
                system_description="A test system for CRUD operations"
            )
            
            system_id = system_repo.create(system)
            assert system_id is not None
            assert system_id > 0
            
            # Test READ
            retrieved_system = system_repo.read(system_id)
            assert retrieved_system is not None
            assert retrieved_system.system_name == "Test System"
            assert retrieved_system.id == system_id
            
            # Test UPDATE
            retrieved_system.system_description = "Updated description"
            update_success = system_repo.update(retrieved_system)
            assert update_success is True
            
            # Verify update
            updated_system = system_repo.read(system_id)
            assert updated_system.system_description == "Updated description"
            
            # Test DELETE
            delete_success = system_repo.delete(system_id)
            assert delete_success is True
            
            # Verify deletion
            deleted_system = system_repo.read(system_id)
            assert deleted_system is None
            
            db_manager.close()
    
    def test_entity_relationships(self):
        """Test entity relationships and foreign keys."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            
            # Initialize database
            db_manager = DatabaseManager(db_path)
            db_manager.initialize()
            connection = db_manager.get_connection()
            
            # Create repositories
            system_repo = EntityFactory.get_repository(connection, System)
            function_repo = EntityFactory.get_repository(connection, Function)
            
            # Create parent system
            parent_system = System(
                type_identifier="S",
                level_identifier=0,
                sequential_identifier=1,
                system_hierarchy="S-1",
                system_name="Parent System"
            )
            parent_id = system_repo.create(parent_system)
            assert parent_id is not None
            
            # Create child system
            child_system = System(
                type_identifier="S",
                level_identifier=1,
                sequential_identifier=1,
                system_hierarchy="S-1.1",
                system_name="Child System",
                parent_system_id=parent_id
            )
            child_id = system_repo.create(child_system)
            assert child_id is not None
            
            # Create function for system
            function = Function(
                type_identifier="F",
                level_identifier=0,
                sequential_identifier=1,
                system_hierarchy="F-1",
                system_id=parent_id,
                function_name="Test Function",
                function_description="A test function"
            )
            function_id = function_repo.create(function)
            assert function_id is not None
            
            # Test querying by system
            functions = function_repo.list_by_system(parent_id)
            assert len(functions) == 1
            assert functions[0].function_name == "Test Function"
            
            db_manager.close()


class TestHierarchicalIDs:
    """Test hierarchical ID management."""
    
    def test_hierarchical_id_parsing(self):
        """Test parsing of hierarchical ID strings."""
        # Test simple ID (root level)
        id1 = HierarchyManager.parse_hierarchical_id("S-1")
        assert id1 is not None
        assert id1.type_identifier == "S"
        assert id1.level_identifier == 0  # Root level
        assert id1.sequential_identifier == 1
        
        # Test complex ID (nested level)
        id2 = HierarchyManager.parse_hierarchical_id("S-1.2")
        assert id2 is not None
        assert id2.type_identifier == "S"
        assert id2.level_identifier == 1  # First sub-level
        assert id2.sequential_identifier == 2
        
        # Test invalid ID
        id3 = HierarchyManager.parse_hierarchical_id("INVALID")
        assert id3 is None
    
    def test_hierarchical_id_validation(self):
        """Test hierarchical ID validation."""
        # Valid ID
        valid_id = HierarchicalID("S", 1, 1)
        is_valid, error = HierarchyManager.validate_hierarchical_id(valid_id)
        assert is_valid is True
        assert error is None
        
        # Invalid type
        invalid_type = HierarchicalID("INVALID", 1, 1)
        is_valid, error = HierarchyManager.validate_hierarchical_id(invalid_type)
        assert is_valid is False
        assert "Invalid type identifier" in error
    
    def test_hierarchical_id_sorting(self):
        """Test sorting of hierarchical IDs."""
        ids = ["S-2", "S-1.1", "S-1", "S-1.2", "R-1"]
        sorted_ids = HierarchyManager.sort_hierarchical_ids(ids)
        
        # R should come after S, and within S, proper hierarchical order
        # Root level items (S-1, S-2) should be sorted by sequential_identifier
        # Sub-level items (S-1.1, S-1.2) should be sorted by level then sequential
        expected = ["R-1", "S-1", "S-2", "S-1.1", "S-1.2"]
        assert sorted_ids == expected
    
    def test_find_next_sequential_id(self):
        """Test finding next sequential ID."""
        existing_ids = ["S-1", "S-1.1", "S-1.2", "S-2"]
        
        # Next sequential for level 1
        next_id = HierarchyManager.find_next_sequential_id(existing_ids, "S", 1)
        assert next_id == 3  # S-1.3
        
        # Next sequential for level 0
        next_root = HierarchyManager.find_next_sequential_id(existing_ids, "S", 0)
        assert next_root == 3  # S-3


class TestDatabaseInitializer:
    """Test database initialization and setup."""
    
    def test_database_initialization(self):
        """Test complete database initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Initialize database
            initializer = DatabaseInitializer(temp_path)
            assert initializer.initialize() is True
            
            # Check database info
            info = initializer.get_database_info()
            assert info['schema_version'] == SCHEMA_VERSION
            assert 'tables' in info
            
            # Should have created example data
            assert info['tables']['systems'] > 0
            
            initializer.close()
    
    def test_database_backup(self):
        """Test database backup functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Initialize database
            initializer = DatabaseInitializer(temp_path)
            initializer.initialize()
            
            # Create backup
            backup_path = initializer.backup_database("test_backup.db")
            assert backup_path is not None
            assert backup_path.exists()
            
            # Verify backup is valid SQLite database
            backup_conn = sqlite3.connect(str(backup_path))
            result = backup_conn.execute("SELECT COUNT(*) FROM systems").fetchone()
            assert result[0] > 0  # Should have example data
            backup_conn.close()
            
            initializer.close()
    
    def test_database_integrity_verification(self):
        """Test database integrity verification."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Initialize database
            initializer = DatabaseInitializer(temp_path)
            initializer.initialize()
            
            # Verify integrity
            assert initializer.verify_database_integrity() is True
            
            initializer.close()


# Test fixtures and utilities
@pytest.fixture
def temp_database():
    """Fixture providing a temporary database for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        
        db_manager = DatabaseManager(db_path)
        db_manager.initialize()
        
        yield db_manager
        
        db_manager.close()


def test_audit_trail_functionality(temp_database):
    """Test audit trail logging functionality."""
    connection = temp_database.get_connection()
    system_repo = EntityFactory.get_repository(connection, System)
    
    # Create system (should log INSERT)
    system = System(
        type_identifier="S",
        level_identifier=0,
        sequential_identifier=1,
        system_hierarchy="S-1",
        system_name="Audit Test System"
    )
    system_id = system_repo.create(system)
    
    # Check audit log
    audit_records = connection.fetchall(
        "SELECT * FROM audit_log WHERE table_name = 'systems' AND row_id = ?",
        (system_id,)
    )
    assert len(audit_records) == 1
    assert audit_records[0]['operation'] == 'INSERT'
    
    # Update system (should log UPDATE)
    system.system_name = "Updated Audit Test System"
    system.id = system_id
    system_repo.update(system)
    
    # Check for UPDATE record
    audit_records = connection.fetchall(
        "SELECT * FROM audit_log WHERE table_name = 'systems' AND row_id = ? ORDER BY timestamp",
        (system_id,)
    )
    assert len(audit_records) == 2
    assert audit_records[1]['operation'] == 'UPDATE'
    
    # Delete system (should log DELETE)
    system_repo.delete(system_id)
    
    # Check for DELETE record
    audit_records = connection.fetchall(
        "SELECT * FROM audit_log WHERE table_name = 'systems' AND row_id = ? ORDER BY timestamp",
        (system_id,)
    )
    assert len(audit_records) == 3
    assert audit_records[2]['operation'] == 'DELETE'


if __name__ == "__main__":
    # Run tests when script is executed directly
    pytest.main([__file__, "-v"])