"""
Unit tests for UI components of the STPA Tool.
Tests widgets, dialogs, and main window functionality.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import os
import sys

# Set environment for headless testing
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

from src.ui.main_window import MainWindow
from src.ui.dialogs import DirectorySelectionDialog, ErrorDialog, ConfirmationDialog
from src.ui.entity_dialogs import SystemEditDialog, FunctionEditDialog, RequirementEditDialog
from src.ui.hierarchy_tree import HierarchyTreeWidget
from src.database.entities import System, Function, Requirement
from src.config.settings import ConfigManager
from src.database.init import DatabaseInitializer


@pytest.fixture(scope="session")
def qapp():
    """Create QApplication instance for testing."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(['test'])
    yield app
    # Don't quit here as it might be used by other tests


@pytest.fixture
def temp_database():
    """Create temporary database for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Initialize database
        db_init = DatabaseInitializer(temp_path)
        db_init.initialize()
        
        yield db_init
        
        db_init.close()


class TestDialogs:
    """Test dialog functionality."""
    
    def test_directory_selection_dialog(self, qapp):
        """Test directory selection dialog creation."""
        dialog = DirectorySelectionDialog()
        
        assert dialog is not None
        assert dialog.windowTitle() == "Select Working Directory"
        
        # Test with initial directory
        with tempfile.TemporaryDirectory() as temp_dir:
            dialog_with_dir = DirectorySelectionDialog(Path(temp_dir))
            assert dialog_with_dir is not None
    
    def test_error_dialog(self, qapp):
        """Test error dialog creation and display."""
        dialog = ErrorDialog("Test Error", "This is a test error message")
        
        assert dialog is not None
        assert "Test Error" in dialog.windowTitle()
        
        # Test that dialog can be created without showing
        dialog.close()
    
    def test_confirmation_dialog(self, qapp):
        """Test confirmation dialog creation."""
        dialog = ConfirmationDialog("Test Confirmation", "Are you sure?")
        
        assert dialog is not None
        assert "Test Confirmation" in dialog.windowTitle()
        
        dialog.close()


class TestEntityDialogs:
    """Test entity editing dialogs."""
    
    def test_system_edit_dialog_creation(self, qapp, temp_database):
        """Test SystemEditDialog creation."""
        db_manager = temp_database.get_database_manager()
        
        # Test new system dialog
        dialog = SystemEditDialog(db_manager.get_connection())
        assert dialog is not None
        assert dialog.windowTitle() == "Add System"
        
        # Create test system for editing
        system = System(
            type_identifier="S",
            level_identifier=0,
            sequential_identifier=1,
            system_hierarchy="S-1",
            system_name="Test System",
            system_description="A test system"
        )
        
        # Test edit system dialog
        edit_dialog = SystemEditDialog(db_manager.get_connection(), system)
        assert edit_dialog is not None
        assert edit_dialog.windowTitle() == "Edit System"
        
        dialog.close()
        edit_dialog.close()
    
    def test_function_edit_dialog_creation(self, qapp, temp_database):
        """Test FunctionEditDialog creation."""
        db_manager = temp_database.get_database_manager()
        
        dialog = FunctionEditDialog(db_manager.get_connection(), system_id=1)
        assert dialog is not None
        assert dialog.windowTitle() == "Add Function"
        
        dialog.close()
    
    def test_requirement_edit_dialog_creation(self, qapp, temp_database):
        """Test RequirementEditDialog creation."""
        db_manager = temp_database.get_database_manager()
        
        dialog = RequirementEditDialog(db_manager.get_connection(), system_id=1)
        assert dialog is not None
        assert dialog.windowTitle() == "Add Requirement"
        
        dialog.close()


class TestHierarchyTree:
    """Test hierarchy tree widget."""
    
    def test_hierarchy_tree_creation(self, qapp):
        """Test hierarchy tree widget creation."""
        tree = HierarchyTreeWidget()
        
        assert tree is not None
        assert tree.columnCount() == 1
        assert tree.headerItem().text(0) == "System Hierarchy"
    
    def test_hierarchy_tree_population(self, qapp, temp_database):
        """Test populating hierarchy tree with database data."""
        db_manager = temp_database.get_database_manager()
        tree = HierarchyTreeWidget()
        
        # Load systems from database
        tree.load_systems(db_manager.get_connection())
        
        # Should have at least the example systems
        assert tree.topLevelItemCount() > 0
        
        # Check that top-level items exist
        root_item = tree.topLevelItem(0)
        assert root_item is not None
        assert root_item.text(0) is not None


class TestMainWindow:
    """Test main window functionality."""
    
    def test_main_window_creation(self, qapp):
        """Test main window creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create config manager
            config_manager = ConfigManager(temp_path)
            
            # Initialize database
            db_init = DatabaseInitializer(temp_path)
            db_init.initialize()
            
            try:
                # Create main window
                main_window = MainWindow(config_manager, db_init.get_database_manager())
                
                assert main_window is not None
                assert main_window.windowTitle() == "STPA Tool v1.0.0"
                
                # Test that main components exist
                assert main_window.hierarchy_tree is not None
                assert main_window.content_tabs is not None
                assert main_window.status_bar is not None
                
                main_window.close()
                
            finally:
                db_init.close()
    
    def test_main_window_menu_creation(self, qapp):
        """Test main window menu bar creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            config_manager = ConfigManager(temp_path)
            db_init = DatabaseInitializer(temp_path)
            db_init.initialize()
            
            try:
                main_window = MainWindow(config_manager, db_init.get_database_manager())
                
                # Check menu bar exists
                menu_bar = main_window.menuBar()
                assert menu_bar is not None
                
                # Check for expected menus
                menu_titles = [action.text() for action in menu_bar.actions()]
                expected_menus = ["&File", "&Edit", "&View", "&Tools", "&Collaboration", "&Help"]
                
                for expected_menu in expected_menus:
                    assert expected_menu in menu_titles
                
                main_window.close()
                
            finally:
                db_init.close()
    
    def test_system_selection_functionality(self, qapp):
        """Test system selection in main window."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            config_manager = ConfigManager(temp_path)
            db_init = DatabaseInitializer(temp_path)
            db_init.initialize()
            
            try:
                main_window = MainWindow(config_manager, db_init.get_database_manager())
                
                # Test system selection
                # Get first system from hierarchy tree
                if main_window.hierarchy_tree.topLevelItemCount() > 0:
                    first_item = main_window.hierarchy_tree.topLevelItem(0)
                    main_window.hierarchy_tree.setCurrentItem(first_item)
                    
                    # Should trigger system selection
                    assert main_window.current_system_id is not None
                
                main_window.close()
                
            finally:
                db_init.close()


class TestUIIntegration:
    """Test UI component integration."""
    
    def test_entity_dialog_integration(self, qapp, temp_database):
        """Test integration between entity dialogs and database."""
        db_manager = temp_database.get_database_manager()
        connection = db_manager.get_connection()
        
        # Create system dialog
        dialog = SystemEditDialog(connection)
        
        # Test validation (should fail for empty required fields)
        assert not dialog.validate_form()
        
        dialog.close()
    
    def test_hierarchy_tree_refresh(self, qapp, temp_database):
        """Test hierarchy tree refresh after database changes."""
        db_manager = temp_database.get_database_manager()
        connection = db_manager.get_connection()
        
        tree = HierarchyTreeWidget()
        tree.load_systems(connection)
        
        initial_count = tree.topLevelItemCount()
        
        # Add new system to database
        from src.database.entities import EntityFactory
        system_repo = EntityFactory.get_repository(connection, System)
        
        new_system = System(
            type_identifier="S",
            level_identifier=0,
            sequential_identifier=999,
            system_hierarchy="S-999",
            system_name="UI Test System",
            system_description="System created for UI testing"
        )
        
        system_repo.create(new_system)
        
        # Refresh tree
        tree.load_systems(connection)
        
        # Should have one more item
        assert tree.topLevelItemCount() == initial_count + 1


class TestUIErrorHandling:
    """Test UI error handling and edge cases."""
    
    def test_dialog_with_invalid_database(self, qapp):
        """Test dialog behavior with invalid database connection."""
        # Create mock connection that raises errors
        mock_connection = Mock()
        mock_connection.fetchall.side_effect = Exception("Database error")
        
        # Should handle gracefully
        dialog = SystemEditDialog(mock_connection)
        assert dialog is not None
        dialog.close()
    
    def test_hierarchy_tree_with_empty_database(self, qapp):
        """Test hierarchy tree with empty database."""
        # Create mock connection with no systems
        mock_connection = Mock()
        mock_connection.fetchall.return_value = []
        
        tree = HierarchyTreeWidget()
        tree.load_systems(mock_connection)
        
        # Should handle empty result gracefully
        assert tree.topLevelItemCount() == 0
    
    def test_main_window_with_database_error(self, qapp):
        """Test main window behavior when database initialization fails."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            config_manager = ConfigManager(temp_path)
            
            # Create mock database manager that fails
            mock_db_manager = Mock()
            mock_db_manager.is_healthy.return_value = False
            mock_db_manager.get_connection.side_effect = Exception("Database connection failed")
            
            # Should handle database errors gracefully
            try:
                main_window = MainWindow(config_manager, mock_db_manager)
                assert main_window is not None
                main_window.close()
            except Exception as e:
                # If it raises an exception, it should be handled gracefully
                assert "Database connection failed" in str(e)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])