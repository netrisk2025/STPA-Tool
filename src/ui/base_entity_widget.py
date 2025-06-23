"""
Base entity widget classes for STPA Tool
Provides common functionality for all entity management widgets.
"""

from abc import ABC, abstractmethod, ABCMeta
from typing import Optional, Dict, Any, List, Type, Callable
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QLabel, QLineEdit, QTextEdit,
    QComboBox, QCheckBox, QSpinBox, QHeaderView, QMessageBox,
    QToolBar, QSplitter, QGroupBox, QScrollArea
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QIcon, QFont, QAction

from ..database.entities import BaseEntity, EntityFactory
from ..database.init import DatabaseInitializer
from ..log_config.config import get_logger

logger = get_logger(__name__)


class EntityValidator:
    """
    Validation framework for entity data.
    """
    
    def __init__(self):
        """Initialize validator."""
        self.validation_rules: Dict[str, List[Callable]] = {}
        self.validation_messages: Dict[str, str] = {}
    
    def add_rule(self, field_name: str, validator_func: Callable, message: str):
        """
        Add validation rule for a field.
        
        Args:
            field_name: Name of the field to validate
            validator_func: Function that returns True if valid
            message: Error message if validation fails
        """
        if field_name not in self.validation_rules:
            self.validation_rules[field_name] = []
        
        self.validation_rules[field_name].append(validator_func)
        self.validation_messages[f"{field_name}_{len(self.validation_rules[field_name])}"] = message
    
    def validate(self, data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate data against all rules.
        
        Args:
            data: Dictionary of field data to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        for field_name, validators in self.validation_rules.items():
            field_value = data.get(field_name)
            
            for i, validator in enumerate(validators):
                try:
                    if not validator(field_value):
                        key = f"{field_name}_{i+1}"
                        errors.append(self.validation_messages.get(key, f"Validation failed for {field_name}"))
                except Exception as e:
                    errors.append(f"Validation error for {field_name}: {str(e)}")
        
        return len(errors) == 0, errors


class EntityChangeTracker:
    """
    Tracks changes to entity data for dirty state management.
    """
    
    def __init__(self):
        """Initialize change tracker."""
        self.original_data: Dict[str, Any] = {}
        self.current_data: Dict[str, Any] = {}
        self.tracked_fields: set = set()
    
    def set_original_data(self, data: Dict[str, Any]):
        """Set the original data state."""
        self.original_data = data.copy()
        self.current_data = data.copy()
    
    def track_field(self, field_name: str):
        """Add field to tracking."""
        self.tracked_fields.add(field_name)
    
    def update_field(self, field_name: str, value: Any):
        """Update tracked field value."""
        if field_name in self.tracked_fields:
            self.current_data[field_name] = value
    
    def is_dirty(self) -> bool:
        """Check if any tracked fields have changed."""
        for field_name in self.tracked_fields:
            if self.original_data.get(field_name) != self.current_data.get(field_name):
                return True
        return False
    
    def get_changes(self) -> Dict[str, tuple[Any, Any]]:
        """Get dictionary of changed fields with (old, new) values."""
        changes = {}
        for field_name in self.tracked_fields:
            old_value = self.original_data.get(field_name)
            new_value = self.current_data.get(field_name)
            if old_value != new_value:
                changes[field_name] = (old_value, new_value)
        return changes
    
    def reset(self):
        """Reset to current state as original."""
        self.original_data = self.current_data.copy()


class BaseEntityWidget(QWidget):
    """
    Abstract base class for entity management widgets.
    Provides common functionality for CRUD operations, validation, and change tracking.
    """
    
    # Signals
    entity_created = Signal(object)  # Emitted when entity is created
    entity_updated = Signal(object)  # Emitted when entity is updated
    entity_deleted = Signal(int)     # Emitted when entity is deleted
    selection_changed = Signal(object)  # Emitted when selection changes
    
    def __init__(self, entity_class: Type[BaseEntity], database_initializer: DatabaseInitializer, parent=None):
        """
        Initialize base entity widget.
        
        Args:
            entity_class: The entity class this widget manages
            database_initializer: Database initializer instance
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.entity_class = entity_class
        self.database_initializer = database_initializer
        self.current_entity: Optional[BaseEntity] = None
        self.selected_entity_id: Optional[int] = None
        self.current_system_id: Optional[int] = None  # Track current system for filtering
        
        # Framework components
        self.validator = EntityValidator()
        self.change_tracker = EntityChangeTracker()
        
        # UI components will be set by subclasses
        self.entity_table: Optional[QTableWidget] = None
        self.toolbar: Optional[QToolBar] = None
        self.details_widget: Optional[QWidget] = None
        
        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._auto_refresh)
        self.refresh_timer.setSingleShot(True)
        
        self._setup_ui()
        self._setup_validation()
        self._setup_change_tracking()
        self._load_entities()
        
        logger.info(f"Initialized {entity_class.__name__} entity widget")
    
    @abstractmethod
    def _setup_ui(self):
        """Setup the user interface. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def _setup_validation(self):
        """Setup validation rules. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def _setup_change_tracking(self):
        """Setup change tracking fields. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def _create_details_widget(self) -> QWidget:
        """Create the details/edit widget. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def _populate_details(self, entity: BaseEntity):
        """Populate details widget with entity data. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def _collect_form_data(self) -> Dict[str, Any]:
        """Collect data from form fields. Must be implemented by subclasses."""
        pass
    
    def _setup_base_ui(self):
        """Setup base UI layout common to all entity widgets."""
        layout = QVBoxLayout(self)
        
        # Create toolbar
        self.toolbar = QToolBar("Entity Actions")
        self.toolbar.setMovable(False)
        
        # Add common actions
        self.add_action = QAction("Add", self)
        self.add_action.setIcon(QIcon.fromTheme("list-add"))
        self.add_action.triggered.connect(self.add_entity)
        self.toolbar.addAction(self.add_action)
        
        self.edit_action = QAction("Edit", self)
        self.edit_action.setIcon(QIcon.fromTheme("document-edit"))
        self.edit_action.setEnabled(False)
        self.edit_action.triggered.connect(self.edit_entity)
        self.toolbar.addAction(self.edit_action)
        
        self.delete_action = QAction("Delete", self)
        self.delete_action.setIcon(QIcon.fromTheme("edit-delete"))
        self.delete_action.setEnabled(False)
        self.delete_action.triggered.connect(self.delete_entity)
        self.toolbar.addAction(self.delete_action)
        
        self.toolbar.addSeparator()
        
        self.refresh_action = QAction("Refresh", self)
        self.refresh_action.setIcon(QIcon.fromTheme("view-refresh"))
        self.refresh_action.triggered.connect(self.refresh_entities)
        self.toolbar.addAction(self.refresh_action)
        
        layout.addWidget(self.toolbar)
        
        # Create splitter for table and details
        splitter = QSplitter(Qt.Horizontal)
        
        # Entity table
        self.entity_table = QTableWidget()
        self.entity_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.entity_table.setSelectionMode(QTableWidget.SingleSelection)
        self.entity_table.setAlternatingRowColors(True)
        self.entity_table.itemSelectionChanged.connect(self._on_selection_changed)
        self.entity_table.doubleClicked.connect(self.edit_entity)
        
        splitter.addWidget(self.entity_table)
        
        # Details widget (to be created by subclass)
        self.details_widget = self._create_details_widget()
        if self.details_widget:
            splitter.addWidget(self.details_widget)
        
        # Set splitter sizes (70% table, 30% details)
        splitter.setSizes([700, 300])
        
        layout.addWidget(splitter)
    
    def set_current_system_id(self, system_id: Optional[int]):
        """Set the current system ID for filtering entities."""
        self.current_system_id = system_id
        logger.debug(f"Set current system ID to {system_id} for {self.entity_class.__name__} widget")
    
    def _load_entities(self):
        """Load entities from database."""
        try:
            if not self.database_initializer:
                logger.warning("No database initializer available")
                return
            
            db_manager = self.database_initializer.get_database_manager()
            connection = db_manager.get_connection()
            entity_repo = EntityFactory.get_repository(connection, self.entity_class)
            
            # Load entities, filtered by system if specified
            if self.current_system_id is not None:
                entities = entity_repo.find_by_system_id(self.current_system_id)
                logger.debug(f"Loaded {len(entities)} {self.entity_class.__name__} entities for system {self.current_system_id}")
            else:
                entities = entity_repo.list()
                logger.debug(f"Loaded {len(entities)} {self.entity_class.__name__} entities (all systems)")
            
            # Populate table
            self._populate_table(entities)
            
            # Clear selection
            self.selected_entity_id = None
            self.current_entity = None
            self._clear_details()
            
        except Exception as e:
            logger.error(f"Failed to load {self.entity_class.__name__} entities: {str(e)}")
            self._show_error("Load Failed", f"Failed to load {self.entity_class.__name__} entities:\n{str(e)}")
    
    def _get_table_name(self) -> str:
        """Get database table name from entity class."""
        # Convert CamelCase to snake_case and pluralize
        class_name = self.entity_class.__name__
        table_name = ""
        for i, char in enumerate(class_name):
            if char.isupper() and i > 0:
                table_name += "_"
            table_name += char.lower()
        
        # Simple pluralization
        if table_name.endswith('y'):
            table_name = table_name[:-1] + "ies"
        elif table_name.endswith(('s', 'sh', 'ch', 'x', 'z')):
            table_name += "es"
        else:
            table_name += "s"
        
        return table_name
    
    @abstractmethod
    def _populate_table(self, entities: List[BaseEntity]):
        """Populate table with entity data. Must be implemented by subclasses."""
        pass
    
    def _on_selection_changed(self):
        """Handle selection change in entity table."""
        selected_items = self.entity_table.selectedItems()
        
        if selected_items:
            row = selected_items[0].row()
            entity_id = self.entity_table.item(row, 0).data(Qt.UserRole)
            
            if entity_id != self.selected_entity_id:
                self.selected_entity_id = entity_id
                self._load_entity_details(entity_id)
                
                # Enable edit/delete actions
                self.edit_action.setEnabled(True)
                self.delete_action.setEnabled(True)
        else:
            self.selected_entity_id = None
            self.current_entity = None
            self.edit_action.setEnabled(False)
            self.delete_action.setEnabled(False)
    
    def _load_entity_details(self, entity_id: int):
        """Load entity details for display/editing."""
        try:
            db_manager = self.database_initializer.get_database_manager()
            connection = db_manager.get_connection()
            
            table_name = self._get_table_name()
            entity_data = connection.fetchone(
                f"SELECT * FROM {table_name} WHERE id = ?",
                (entity_id,)
            )
            
            if entity_data:
                entity_dict = dict(entity_data)
                self.current_entity = self.entity_class(**entity_dict)
                self._populate_details(self.current_entity)
                self.selection_changed.emit(self.current_entity)
                
        except Exception as e:
            logger.error(f"Failed to load entity details: {str(e)}")
    
    def add_entity(self):
        """Add new entity."""
        self.current_entity = None
        self.selected_entity_id = None
        
        # Clear details form for new entity
        if self.details_widget:
            self._clear_details()
        
        # Enable editing
        self._set_editing_mode(True)
    
    def edit_entity(self):
        """Edit selected entity."""
        if not self.current_entity:
            QMessageBox.warning(self, "No Selection", "Please select an entity to edit.")
            return
        
        self._set_editing_mode(True)
    
    def delete_entity(self):
        """Delete selected entity with confirmation."""
        if not self.current_entity:
            return
        
        # Confirmation dialog
        reply = QMessageBox.question(
            self,
            "Delete Entity",
            f"Are you sure you want to delete this {self.entity_class.__name__}?\\n\\n"
            f"This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                db_manager = self.database_initializer.get_database_manager()
                connection = db_manager.get_connection()
                entity_repo = EntityFactory.get_repository(connection, self.entity_class)
                
                if entity_repo.delete(self.current_entity.id):
                    self.entity_deleted.emit(self.current_entity.id)
                    self.refresh_entities()
                    logger.info(f"Deleted {self.entity_class.__name__} with ID {self.current_entity.id}")
                else:
                    self._show_error("Delete Failed", "Failed to delete entity from database")
                    
            except Exception as e:
                logger.error(f"Failed to delete entity: {str(e)}")
                self._show_error("Delete Failed", str(e))
    
    def save_entity(self):
        """Save current entity."""
        try:
            # Collect form data
            form_data = self._collect_form_data()
            
            # Validate data
            is_valid, errors = self.validator.validate(form_data)
            if not is_valid:
                self._show_validation_errors(errors)
                return False
            
            db_manager = self.database_initializer.get_database_manager()
            connection = db_manager.get_connection()
            entity_repo = EntityFactory.get_repository(connection, self.entity_class)
            
            if self.current_entity is None:
                # Create new entity
                entity = self.entity_class(**form_data)
                saved_entity = entity_repo.create(entity)
                
                if saved_entity:
                    self.current_entity = saved_entity
                    self.entity_created.emit(saved_entity)
                    self.refresh_entities()
                    self._set_editing_mode(False)
                    logger.info(f"Created new {self.entity_class.__name__}")
                    return True
            else:
                # Update existing entity
                for key, value in form_data.items():
                    if hasattr(self.current_entity, key):
                        setattr(self.current_entity, key, value)
                
                if entity_repo.update(self.current_entity):
                    self.entity_updated.emit(self.current_entity)
                    self.refresh_entities()
                    self._set_editing_mode(False)
                    logger.info(f"Updated {self.entity_class.__name__} with ID {self.current_entity.id}")
                    return True
            
            self._show_error("Save Failed", "Failed to save entity to database")
            return False
            
        except Exception as e:
            logger.error(f"Failed to save entity: {str(e)}")
            self._show_error("Save Failed", str(e))
            return False
    
    def cancel_editing(self):
        """Cancel editing and revert changes."""
        if self.change_tracker.is_dirty():
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Are you sure you want to cancel?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                return
        
        # Revert to original state
        if self.current_entity:
            self._populate_details(self.current_entity)
        else:
            self._clear_details()
        
        self._set_editing_mode(False)
        self.change_tracker.reset()
    
    def refresh_entities(self):
        """Refresh entity list from database."""
        self._load_entities()
    
    def schedule_refresh(self, delay_ms: int = 500):
        """Schedule refresh after delay."""
        self.refresh_timer.start(delay_ms)
    
    def _auto_refresh(self):
        """Auto-refresh entities."""
        self.refresh_entities()
    
    @abstractmethod
    def _clear_details(self):
        """Clear details form. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def _set_editing_mode(self, enabled: bool):
        """Enable/disable editing mode. Must be implemented by subclasses."""
        pass
    
    def _show_error(self, title: str, message: str):
        """Show error message dialog."""
        QMessageBox.critical(self, title, message)
    
    def _show_validation_errors(self, errors: List[str]):
        """Show validation errors dialog."""
        error_text = "\\n".join(f"• {error}" for error in errors)
        QMessageBox.warning(
            self,
            "Validation Errors",
            f"Please correct the following errors:\\n\\n{error_text}"
        )
    
    def get_selected_entity(self) -> Optional[BaseEntity]:
        """Get currently selected entity."""
        return self.current_entity
    
    def select_entity(self, entity_id: int):
        """Select entity by ID."""
        for row in range(self.entity_table.rowCount()):
            item = self.entity_table.item(row, 0)
            if item and item.data(Qt.UserRole) == entity_id:
                self.entity_table.selectRow(row)
                break


class EntityManagementWidget(QWidget):
    """
    Container widget that manages multiple entity types with tabbed interface.
    """
    
    def __init__(self, database_initializer: DatabaseInitializer, parent=None):
        """
        Initialize entity management widget.
        
        Args:
            database_initializer: Database initializer instance
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.database_initializer = database_initializer
        self.entity_widgets: Dict[str, BaseEntityWidget] = {}
        
        self._setup_ui()
        
        logger.info("Initialized entity management widget")
    
    def _setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("Entity Management")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Placeholder for entity widgets (will be added by specific implementations)
        self.content_layout = QVBoxLayout()
        layout.addLayout(self.content_layout)
    
    def add_entity_widget(self, name: str, widget: BaseEntityWidget):
        """
        Add entity widget to management interface.
        
        Args:
            name: Display name for the entity type
            widget: Entity widget instance
        """
        self.entity_widgets[name] = widget
        self.content_layout.addWidget(widget)
        
        logger.debug(f"Added entity widget: {name}")
    
    def get_entity_widget(self, name: str) -> Optional[BaseEntityWidget]:
        """Get entity widget by name."""
        return self.entity_widgets.get(name)
    
    def refresh_all(self):
        """Refresh all entity widgets."""
        for widget in self.entity_widgets.values():
            widget.refresh_entities()