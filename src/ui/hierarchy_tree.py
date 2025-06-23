"""
Hierarchy tree widget for STPA Tool
Provides interactive system hierarchy navigation with database integration.
"""

from typing import Optional, Dict, List, Any
from PySide6.QtWidgets import (
    QTreeWidget, QTreeWidgetItem, QMenu, QMessageBox, QHeaderView, QDialog
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QAction, QIcon

from ..database.init import DatabaseInitializer
from ..database.entities import System, EntityFactory
from ..log_config.config import get_logger

logger = get_logger(__name__)


class SystemTreeItem(QTreeWidgetItem):
    """
    Custom tree widget item for system entities.
    """
    
    def __init__(self, system: System, parent=None):
        """
        Initialize system tree item.
        
        Args:
            system: System entity
            parent: Parent tree item
        """
        super().__init__(parent)
        self.system = system
        self._setup_item()
    
    def _setup_item(self):
        """Setup the tree item display."""
        # Column 0: Hierarchical ID and Name
        display_text = f"{self.system.get_hierarchical_id()} - {self.system.system_name}"
        self.setText(0, display_text)
        
        # Column 1: Description (truncated)
        description = self.system.system_description or ""
        if len(description) > 50:
            description = description[:47] + "..."
        self.setText(1, description)
        
        # Store system ID for easy retrieval
        self.setData(0, Qt.UserRole, self.system.id)
        
        # Set tooltip with full information
        tooltip = f"""System: {self.system.system_name}
ID: {self.system.get_hierarchical_id()}
Description: {self.system.system_description or 'No description'}
Baseline: {self.system.baseline}"""
        self.setToolTip(0, tooltip)
    
    def get_system_id(self) -> int:
        """Get the system ID."""
        return self.system.id
    
    def get_system(self) -> System:
        """Get the system entity."""
        return self.system
    
    def update_system(self, system: System):
        """Update the system entity and refresh display."""
        self.system = system
        self._setup_item()


class HierarchyTreeWidget(QTreeWidget):
    """
    Enhanced tree widget for system hierarchy with database integration.
    """
    
    # Signals
    system_selected = Signal(int)  # Emitted when a system is selected
    system_changed = Signal(int)   # Emitted when a system is modified
    refresh_requested = Signal()   # Emitted when refresh is requested
    
    def __init__(self, database_initializer: Optional[DatabaseInitializer] = None):
        """
        Initialize hierarchy tree widget.
        
        Args:
            database_initializer: Database initializer instance
        """
        super().__init__()
        
        self.database_initializer = database_initializer
        self._system_items: Dict[int, SystemTreeItem] = {}
        self._current_system_id: Optional[int] = None
        
        self._setup_ui()
        self._setup_connections()
        
        # Auto-refresh timer
        self._refresh_timer = QTimer()
        self._refresh_timer.timeout.connect(self._auto_refresh)
        self._refresh_timer.setSingleShot(True)
    
    def _setup_ui(self):
        """Setup the tree widget UI."""
        # Headers
        self.setHeaderLabels(["System Hierarchy", "Description"])
        
        # Header configuration
        header = self.header()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        
        # Tree configuration
        self.setRootIsDecorated(True)
        self.setAlternatingRowColors(True)
        self.setSelectionMode(QTreeWidget.SingleSelection)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        
        # Enable drag and drop for future reordering
        self.setDragDropMode(QTreeWidget.NoDragDrop)  # Disabled for now
    
    def _setup_connections(self):
        """Setup signal connections."""
        self.itemSelectionChanged.connect(self._on_selection_changed)
        self.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.customContextMenuRequested.connect(self._show_context_menu)
    
    def set_database_initializer(self, database_initializer: DatabaseInitializer):
        """Set the database initializer."""
        self.database_initializer = database_initializer
        self.refresh_from_database()
    
    def refresh_from_database(self):
        """Refresh tree content from database."""
        if not self.database_initializer:
            logger.warning("No database initializer set")
            return
        
        try:
            logger.debug("Refreshing hierarchy tree from database")
            
            # Clear existing items
            self.clear()
            self._system_items.clear()
            
            # Get database connection
            db_manager = self.database_initializer.get_database_manager()
            connection = db_manager.get_connection()
            system_repo = EntityFactory.get_repository(connection, System)
            
            # Get all systems ordered by hierarchy
            systems = connection.fetchall(
                "SELECT * FROM systems WHERE baseline = ? ORDER BY system_hierarchy",
                ("Working",)
            )
            
            if not systems:
                # Add placeholder item
                placeholder = QTreeWidgetItem(self)
                placeholder.setText(0, "No systems found")
                placeholder.setText(1, "Create a new system to get started")
                placeholder.setFlags(Qt.NoItemFlags)  # Make it non-selectable
                return
            
            # Convert to System entities
            system_entities = []
            for row in systems:
                row_dict = dict(row)
                system = System(**row_dict)
                system_entities.append(system)
            
            # Build tree structure
            self._build_tree_structure(system_entities)
            
            # Expand root items
            for i in range(self.topLevelItemCount()):
                item = self.topLevelItem(i)
                if item:
                    self.expandItem(item)
            
            logger.info(f"Loaded {len(system_entities)} systems into hierarchy tree")
            
        except Exception as e:
            logger.error(f"Failed to refresh hierarchy tree: {str(e)}")
            self._show_error("Failed to load system hierarchy", str(e))
    
    def _build_tree_structure(self, systems: List[System]):
        """
        Build tree structure from flat list of systems.
        
        Args:
            systems: List of system entities
        """
        # Create mapping of system ID to system
        system_map = {system.id: system for system in systems}
        
        # Create tree items for root systems first
        for system in systems:
            if system.parent_system_id is None:
                item = SystemTreeItem(system)
                self.addTopLevelItem(item)
                self._system_items[system.id] = item
        
        # Add child systems
        for system in systems:
            if system.parent_system_id is not None:
                parent_item = self._system_items.get(system.parent_system_id)
                if parent_item:
                    item = SystemTreeItem(system, parent_item)
                    self._system_items[system.id] = item
                else:
                    # Parent not found, add as root item
                    logger.warning(f"Parent system {system.parent_system_id} not found for system {system.id}")
                    item = SystemTreeItem(system)
                    self.addTopLevelItem(item)
                    self._system_items[system.id] = item
    
    def _on_selection_changed(self):
        """Handle selection change."""
        selected_items = self.selectedItems()
        if selected_items:
            item = selected_items[0]
            if isinstance(item, SystemTreeItem):
                system_id = item.get_system_id()
                if system_id != self._current_system_id:
                    self._current_system_id = system_id
                    logger.debug(f"System selected: {system_id}")
                    self.system_selected.emit(system_id)
        else:
            self._current_system_id = None
    
    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle item double-click."""
        if isinstance(item, SystemTreeItem):
            logger.debug(f"System double-clicked: {item.get_system_id()}")
            # TODO: Open system editor dialog
    
    def _show_context_menu(self, position):
        """Show context menu."""
        item = self.itemAt(position)
        menu = QMenu(self)
        
        if isinstance(item, SystemTreeItem):
            # System item context menu
            edit_action = QAction("Edit System", self)
            edit_action.triggered.connect(lambda: self._edit_system(item))
            menu.addAction(edit_action)
            
            menu.addSeparator()
            
            add_child_action = QAction("Add Child System", self)
            add_child_action.triggered.connect(lambda: self._add_child_system(item))
            menu.addAction(add_child_action)
            
            menu.addSeparator()
            
            delete_action = QAction("Delete System", self)
            delete_action.triggered.connect(lambda: self._delete_system(item))
            menu.addAction(delete_action)
        else:
            # Empty area context menu
            add_root_action = QAction("Add Root System", self)
            add_root_action.triggered.connect(self._add_root_system)
            menu.addAction(add_root_action)
        
        menu.addSeparator()
        
        refresh_action = QAction("Refresh", self)
        refresh_action.triggered.connect(self.refresh_from_database)
        menu.addAction(refresh_action)
        
        if not menu.isEmpty():
            menu.exec(self.mapToGlobal(position))
    
    def _edit_system(self, item: SystemTreeItem):
        """Edit system."""
        try:
            from .entity_dialogs import SystemEditDialog
            
            dialog = SystemEditDialog(system=item.get_system(), parent=self)
            if dialog.exec() == QDialog.Accepted:
                updated_system = dialog.get_system()
                if updated_system:
                    # Update in database
                    db_manager = self.database_initializer.get_database_manager()
                    connection = db_manager.get_connection()
                    system_repo = EntityFactory.get_repository(connection, System)
                    
                    if system_repo.update(updated_system):
                        # Update tree item
                        item.update_system(updated_system)
                        logger.info(f"Updated system: {updated_system.system_name}")
                        self.system_changed.emit(updated_system.id)
                    else:
                        self._show_error("Update Failed", "Failed to update system in database")
                        
        except Exception as e:
            logger.error(f"Failed to edit system: {str(e)}")
            self._show_error("Edit Failed", str(e))
    
    def _add_child_system(self, parent_item: SystemTreeItem):
        """Add child system."""
        try:
            from .entity_dialogs import SystemEditDialog
            
            parent_system = parent_item.get_system()
            dialog = SystemEditDialog(parent_system=parent_system, parent=self)
            
            if dialog.exec() == QDialog.Accepted:
                new_system = dialog.get_system()
                if new_system:
                    # The dialog should have already set parent_system_id and hierarchical ID
                    # Only override if the hierarchical ID is still a placeholder
                    if "?" in new_system.system_hierarchy:
                        # Generate hierarchical ID for child
                        from ..utils.hierarchy import HierarchyManager
                        parent_hierarchy = HierarchyManager.parse_hierarchical_id(parent_system.system_hierarchy)
                        if parent_hierarchy:
                            # Find next sequential ID for this level
                            db_manager = self.database_initializer.get_database_manager()
                            connection = db_manager.get_connection()
                            
                            # Get existing child systems of this parent
                            existing_children = connection.fetchall(
                                "SELECT system_hierarchy FROM systems WHERE parent_system_id = ? AND baseline = ?",
                                (parent_system.id, "Working")
                            )
                            
                            next_seq = len(existing_children) + 1
                            child_hierarchy = HierarchyManager.generate_child_id(parent_hierarchy, next_seq)
                            
                            if child_hierarchy:
                                new_system.system_hierarchy = str(child_hierarchy)
                                new_system.type_identifier = child_hierarchy.type_identifier
                                new_system.level_identifier = child_hierarchy.level_identifier
                                new_system.sequential_identifier = child_hierarchy.sequential_identifier
                    
                    # Save to database
                    db_manager = self.database_initializer.get_database_manager()
                    connection = db_manager.get_connection()
                    system_repo = EntityFactory.get_repository(connection, System)
                    new_id = system_repo.create(new_system)
                    
                    if new_id:
                        new_system.id = new_id
                        # Add to tree
                        self.add_system(new_system)
                        logger.info(f"Added child system: {new_system.system_name}")
                        self.system_changed.emit(new_id)
                    else:
                        self._show_error("Create Failed", "Failed to create system in database")
                        
        except Exception as e:
            logger.error(f"Failed to add child system: {str(e)}")
            self._show_error("Add Failed", str(e))
    
    def _add_root_system(self):
        """Add root system."""
        try:
            from .entity_dialogs import SystemEditDialog
            
            dialog = SystemEditDialog(parent=self)
            
            if dialog.exec() == QDialog.Accepted:
                new_system = dialog.get_system()
                if new_system:
                    # Only override if the hierarchical ID is still a placeholder
                    if "?" in new_system.system_hierarchy:
                        # Generate hierarchical ID for root system
                        from ..utils.hierarchy import HierarchyManager
                        
                        db_manager = self.database_initializer.get_database_manager()
                        connection = db_manager.get_connection()
                        
                        # Get existing root systems
                        existing_roots = connection.fetchall(
                            "SELECT system_hierarchy FROM systems WHERE parent_system_id IS NULL AND baseline = ?",
                            ("Working",)
                        )
                        
                        next_seq = len(existing_roots) + 1
                        root_hierarchy = HierarchyManager.HierarchicalID(
                            type_identifier="S",
                            level_identifier=0,
                            sequential_identifier=next_seq
                        )
                        
                        new_system.system_hierarchy = str(root_hierarchy)
                        new_system.type_identifier = root_hierarchy.type_identifier
                        new_system.level_identifier = root_hierarchy.level_identifier
                        new_system.sequential_identifier = root_hierarchy.sequential_identifier
                        new_system.parent_system_id = None
                    
                    # Save to database
                    db_manager = self.database_initializer.get_database_manager()
                    connection = db_manager.get_connection()
                    system_repo = EntityFactory.get_repository(connection, System)
                    new_id = system_repo.create(new_system)
                    
                    if new_id:
                        new_system.id = new_id
                        # Add to tree
                        self.add_system(new_system)
                        logger.info(f"Added root system: {new_system.system_name}")
                        self.system_changed.emit(new_id)
                    else:
                        self._show_error("Create Failed", "Failed to create system in database")
                        
        except Exception as e:
            logger.error(f"Failed to add root system: {str(e)}")
            self._show_error("Add Failed", str(e))
    
    def _delete_system(self, item: SystemTreeItem):
        """Delete system with confirmation."""
        system = item.get_system()
        
        # Confirmation dialog
        reply = QMessageBox.question(
            self,
            "Delete System",
            f"Are you sure you want to delete system '{system.system_name}'?\n\n"
            f"This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # Delete from database
                db_manager = self.database_initializer.get_database_manager()
                connection = db_manager.get_connection()
                system_repo = EntityFactory.get_repository(connection, System)
                
                if system_repo.delete(system.id):
                    # Remove from tree
                    if item.parent():
                        item.parent().removeChild(item)
                    else:
                        self.invisibleRootItem().removeChild(item)
                    
                    # Remove from mapping
                    if system.id in self._system_items:
                        del self._system_items[system.id]
                    
                    # Clear selection if this was selected
                    if self._current_system_id == system.id:
                        self._current_system_id = None
                    
                    logger.info(f"Deleted system: {system.system_name}")
                    self.system_changed.emit(system.id)
                else:
                    self._show_error("Delete Failed", "Failed to delete system from database")
                    
            except Exception as e:
                logger.error(f"Failed to delete system: {str(e)}")
                self._show_error("Delete Failed", str(e))
    
    def _show_error(self, title: str, message: str):
        """Show error message."""
        QMessageBox.critical(self, title, message)
    
    def get_selected_system_id(self) -> Optional[int]:
        """Get currently selected system ID."""
        return self._current_system_id
    
    def select_system(self, system_id: int):
        """Select system by ID."""
        item = self._system_items.get(system_id)
        if item:
            self.setCurrentItem(item)
            self.scrollToItem(item)
    
    def add_system(self, system: System):
        """Add a new system to the tree."""
        try:
            if system.parent_system_id:
                parent_item = self._system_items.get(system.parent_system_id)
                if parent_item:
                    item = SystemTreeItem(system, parent_item)
                    parent_item.setExpanded(True)
                else:
                    # Parent not found, add as root
                    item = SystemTreeItem(system)
                    self.addTopLevelItem(item)
            else:
                # Root system
                item = SystemTreeItem(system)
                self.addTopLevelItem(item)
            
            self._system_items[system.id] = item
            self.setCurrentItem(item)
            self.scrollToItem(item)
            
            logger.info(f"Added system to tree: {system.system_name}")
            
        except Exception as e:
            logger.error(f"Failed to add system to tree: {str(e)}")
    
    def update_system(self, system: System):
        """Update system in the tree."""
        item = self._system_items.get(system.id)
        if item:
            item.update_system(system)
            logger.debug(f"Updated system in tree: {system.system_name}")
    
    def _auto_refresh(self):
        """Auto-refresh after delay."""
        self.refresh_from_database()
    
    def schedule_refresh(self, delay_ms: int = 500):
        """Schedule refresh after delay."""
        self._refresh_timer.start(delay_ms)