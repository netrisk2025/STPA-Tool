"""
Specific entity widgets for STPA Tool
Implements concrete entity management widgets for Interface, Asset, and other STPA entities.
"""

from typing import Dict, Any, List, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLineEdit, QTextEdit, QComboBox, QLabel, QPushButton,
    QTableWidgetItem, QHeaderView, QScrollArea, QSpinBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from .base_entity_widget import BaseEntityWidget
from .entity_dialogs import CriticalAttributesWidget
from ..database.entities import (
    Interface, Asset, Hazard, Loss, ControlStructure, 
    Controller, ControlledProcess, ControlAction, Feedback
)
from ..database.init import DatabaseInitializer
from ..config.constants import WORKING_BASELINE
from ..utils.hierarchy import HierarchyManager
from ..log_config.config import get_logger

logger = get_logger(__name__)


class InterfaceWidget(BaseEntityWidget):
    """
    Widget for managing Interface entities.
    """
    
    def __init__(self, database_initializer: DatabaseInitializer, parent=None):
        """Initialize Interface widget."""
        super().__init__(Interface, database_initializer, parent)
    
    def _setup_ui(self):
        """Setup the user interface."""
        self._setup_base_ui()
        
        # Configure table columns
        self.entity_table.setColumnCount(4)
        self.entity_table.setHorizontalHeaderLabels(["ID", "Name", "System", "Description"])
        
        header = self.entity_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setStretchLastSection(True)
    
    def _setup_validation(self):
        """Setup validation rules."""
        self.validator.add_rule(
            "interface_name",
            lambda x: x and len(x.strip()) > 0,
            "Interface name is required"
        )
        
        self.validator.add_rule(
            "interface_name",
            lambda x: len(x) <= 100 if x else True,
            "Interface name must be 100 characters or less"
        )
        
        self.validator.add_rule(
            "system_id",
            lambda x: x and x > 0,
            "Valid system must be selected"
        )
    
    def _setup_change_tracking(self):
        """Setup change tracking fields."""
        self.change_tracker.track_field("interface_name")
        self.change_tracker.track_field("interface_description")
        self.change_tracker.track_field("system_id")
    
    def _create_details_widget(self) -> QWidget:
        """Create the details/edit widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Scroll area for form
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Basic Information Group
        basic_group = QGroupBox("Basic Information")
        basic_layout = QFormLayout(basic_group)
        
        self.hierarchy_edit = QLineEdit()
        self.hierarchy_edit.setPlaceholderText("I-1, I-1.1, etc.")
        basic_layout.addRow("Hierarchical ID:", self.hierarchy_edit)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter interface name...")
        basic_layout.addRow("Interface Name*:", self.name_edit)
        
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Enter interface description...")
        self.description_edit.setMaximumHeight(100)
        basic_layout.addRow("Description:", self.description_edit)
        
        # System Association
        self.system_combo = QComboBox()
        self._load_systems()
        basic_layout.addRow("Associated System*:", self.system_combo)
        
        scroll_layout.addWidget(basic_group)
        
        # Critical Attributes
        self.critical_attrs = CriticalAttributesWidget()
        scroll_layout.addWidget(self.critical_attrs)
        
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_entity)
        self.save_btn.setEnabled(False)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.cancel_editing)
        self.cancel_btn.setEnabled(False)
        
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        # Connect change tracking
        self.name_edit.textChanged.connect(lambda: self.change_tracker.update_field("interface_name", self.name_edit.text()))
        self.description_edit.textChanged.connect(lambda: self.change_tracker.update_field("interface_description", self.description_edit.toPlainText()))
        self.system_combo.currentIndexChanged.connect(lambda: self.change_tracker.update_field("system_id", self.system_combo.currentData()))
        
        return widget
    
    def _load_systems(self):
        """Load available systems into combo box."""
        try:
            self.system_combo.clear()
            self.system_combo.addItem("Select System...", None)
            
            db_manager = self.database_initializer.get_database_manager()
            connection = db_manager.get_connection()
            
            systems = connection.fetchall(
                "SELECT id, system_hierarchy, system_name FROM systems WHERE baseline = ? ORDER BY system_hierarchy",
                (WORKING_BASELINE,)
            )
            
            for system in systems:
                display_text = f"{system['system_hierarchy']} - {system['system_name']}"
                self.system_combo.addItem(display_text, system['id'])
                
        except Exception as e:
            logger.error(f"Failed to load systems: {str(e)}")
    
    def _populate_table(self, entities: List[Interface]):
        """Populate table with interface data."""
        self.entity_table.setRowCount(len(entities))
        
        for row, interface in enumerate(entities):
            # Get system name
            system_name = self._get_system_name(interface.system_id)
            
            self.entity_table.setItem(row, 0, QTableWidgetItem(interface.get_hierarchical_id()))
            self.entity_table.setItem(row, 1, QTableWidgetItem(interface.interface_name))
            self.entity_table.setItem(row, 2, QTableWidgetItem(system_name))
            self.entity_table.setItem(row, 3, QTableWidgetItem(interface.interface_description or ""))
            
            # Store interface ID for selection
            self.entity_table.item(row, 0).setData(Qt.UserRole, interface.id)
    
    def _get_system_name(self, system_id: int) -> str:
        """Get system name by ID."""
        try:
            db_manager = self.database_initializer.get_database_manager()
            connection = db_manager.get_connection()
            
            system = connection.fetchone(
                "SELECT system_hierarchy, system_name FROM systems WHERE id = ?",
                (system_id,)
            )
            
            if system:
                return f"{system['system_hierarchy']} - {system['system_name']}"
            return f"System {system_id}"
            
        except Exception:
            return f"System {system_id}"
    
    def _populate_details(self, entity: Interface):
        """Populate details widget with interface data."""
        self.hierarchy_edit.setText(entity.get_hierarchical_id())
        self.name_edit.setText(entity.interface_name)
        self.description_edit.setPlainText(entity.interface_description or "")
        
        # Set system selection
        for i in range(self.system_combo.count()):
            if self.system_combo.itemData(i) == entity.system_id:
                self.system_combo.setCurrentIndex(i)
                break
        
        self.critical_attrs.set_values(entity)
        self.change_tracker.set_original_data(self._collect_form_data())
    
    def _collect_form_data(self) -> Dict[str, Any]:
        """Collect data from form fields."""
        # Parse hierarchical ID
        hierarchy_text = self.hierarchy_edit.text().strip()
        parsed_id = HierarchyManager.parse_hierarchical_id(hierarchy_text)
        
        data = {
            "type_identifier": parsed_id.type_identifier if parsed_id else "I",
            "level_identifier": parsed_id.level_identifier if parsed_id else 0,
            "sequential_identifier": parsed_id.sequential_identifier if parsed_id else 1,
            "system_hierarchy": hierarchy_text,
            "system_id": self.system_combo.currentData(),
            "interface_name": self.name_edit.text().strip(),
            "interface_description": self.description_edit.toPlainText().strip(),
            "baseline": WORKING_BASELINE
        }
        
        # Add critical attributes
        critical_values = self.critical_attrs.get_values()
        data.update(critical_values)
        
        return data
    
    def _clear_details(self):
        """Clear details form."""
        self.hierarchy_edit.setText("I-1")
        self.name_edit.clear()
        self.description_edit.clear()
        self.system_combo.setCurrentIndex(0)
        # Critical attributes will clear themselves
    
    def _set_editing_mode(self, enabled: bool):
        """Enable/disable editing mode."""
        self.hierarchy_edit.setEnabled(enabled and self.current_entity is None)  # Only enable for new entities
        self.name_edit.setEnabled(enabled)
        self.description_edit.setEnabled(enabled)
        self.system_combo.setEnabled(enabled)
        
        self.save_btn.setEnabled(enabled)
        self.cancel_btn.setEnabled(enabled)

    def add_entity(self):
        """Add a new interface."""
        try:
            # Clear details and set editing mode
            self._clear_details()
            self._set_editing_mode(True)
            
            # Set current system as selected if available
            if self.current_system_id is not None:
                # Find the current system in the combo box
                for i in range(self.system_combo.count()):
                    if self.system_combo.itemData(i) == self.current_system_id:
                        self.system_combo.setCurrentIndex(i)
                        break
            
            # Generate placeholder hierarchical ID
            if self.current_system_id is not None:
                # Get system hierarchy for ID generation
                db_manager = self.database_initializer.get_database_manager()
                connection = db_manager.get_connection()
                
                system_data = connection.fetchone(
                    "SELECT system_hierarchy FROM systems WHERE id = ?",
                    (self.current_system_id,)
                )
                
                if system_data:
                    system_hierarchy = system_data['system_hierarchy']
                    # Generate interface ID based on system hierarchy
                    self.hierarchy_edit.setText(f"{system_hierarchy}.I-?")
                else:
                    self.hierarchy_edit.setText("I-?")
            else:
                self.hierarchy_edit.setText("I-?")
            
            # Reset change tracker
            self.change_tracker.set_original_data({})
            
            logger.debug("Started adding new interface")
            
        except Exception as e:
            logger.error(f"Failed to start adding interface: {str(e)}")
            self._show_error("Add Failed", f"Failed to start adding interface:\n{str(e)}")
    
    def _collect_form_data(self) -> Dict[str, Any]:
        """Collect data from form fields."""
        data = {
            'type_identifier': 'I',
            'level_identifier': 0,
            'sequential_identifier': 1,
            'system_hierarchy': self.hierarchy_edit.text().strip(),
            'interface_name': self.name_edit.text().strip(),
            'interface_description': self.description_edit.toPlainText().strip(),
            'system_id': self.system_combo.currentData(),
            'baseline': WORKING_BASELINE
        }
        
        # Add critical attributes
        critical_values = self.critical_attrs.get_values()
        data.update(critical_values)
        
        # Set system_id to current system if not specified
        if data['system_id'] is None and self.current_system_id is not None:
            data['system_id'] = self.current_system_id
        
        return data


class AssetWidget(BaseEntityWidget):
    """
    Widget for managing Asset entities.
    """
    
    def __init__(self, database_initializer: DatabaseInitializer, parent=None):
        """Initialize Asset widget."""
        super().__init__(Asset, database_initializer, parent)
    
    def _setup_ui(self):
        """Setup the user interface."""
        self._setup_base_ui()
        
        # Configure table columns
        self.entity_table.setColumnCount(4)
        self.entity_table.setHorizontalHeaderLabels(["ID", "Name", "System", "Description"])
        
        header = self.entity_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setStretchLastSection(True)
    
    def _setup_validation(self):
        """Setup validation rules."""
        self.validator.add_rule(
            "asset_name",
            lambda x: x and len(x.strip()) > 0,
            "Asset name is required"
        )
        
        self.validator.add_rule(
            "asset_name",
            lambda x: len(x) <= 100 if x else True,
            "Asset name must be 100 characters or less"
        )
        
        self.validator.add_rule(
            "system_id",
            lambda x: x and x > 0,
            "Valid system must be selected"
        )
    
    def _setup_change_tracking(self):
        """Setup change tracking fields."""
        self.change_tracker.track_field("asset_name")
        self.change_tracker.track_field("asset_description")
        self.change_tracker.track_field("system_id")
    
    def _create_details_widget(self) -> QWidget:
        """Create the details/edit widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Scroll area for form
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Basic Information Group
        basic_group = QGroupBox("Basic Information")
        basic_layout = QFormLayout(basic_group)
        
        self.hierarchy_edit = QLineEdit()
        self.hierarchy_edit.setPlaceholderText("A-1, A-1.1, etc.")
        basic_layout.addRow("Hierarchical ID:", self.hierarchy_edit)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter asset name...")
        basic_layout.addRow("Asset Name*:", self.name_edit)
        
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Enter asset description...")
        self.description_edit.setMaximumHeight(100)
        basic_layout.addRow("Description:", self.description_edit)
        
        # System Association
        self.system_combo = QComboBox()
        self._load_systems()
        basic_layout.addRow("Associated System*:", self.system_combo)
        
        scroll_layout.addWidget(basic_group)
        
        # Critical Attributes
        self.critical_attrs = CriticalAttributesWidget()
        scroll_layout.addWidget(self.critical_attrs)
        
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_entity)
        self.save_btn.setEnabled(False)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.cancel_editing)
        self.cancel_btn.setEnabled(False)
        
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        # Connect change tracking
        self.name_edit.textChanged.connect(lambda: self.change_tracker.update_field("asset_name", self.name_edit.text()))
        self.description_edit.textChanged.connect(lambda: self.change_tracker.update_field("asset_description", self.description_edit.toPlainText()))
        self.system_combo.currentIndexChanged.connect(lambda: self.change_tracker.update_field("system_id", self.system_combo.currentData()))
        
        return widget
    
    def _load_systems(self):
        """Load available systems into combo box."""
        try:
            self.system_combo.clear()
            self.system_combo.addItem("Select System...", None)
            
            db_manager = self.database_initializer.get_database_manager()
            connection = db_manager.get_connection()
            
            systems = connection.fetchall(
                "SELECT id, system_hierarchy, system_name FROM systems WHERE baseline = ? ORDER BY system_hierarchy",
                (WORKING_BASELINE,)
            )
            
            for system in systems:
                display_text = f"{system['system_hierarchy']} - {system['system_name']}"
                self.system_combo.addItem(display_text, system['id'])
                
        except Exception as e:
            logger.error(f"Failed to load systems: {str(e)}")
    
    def _populate_table(self, entities: List[Asset]):
        """Populate table with asset data."""
        self.entity_table.setRowCount(len(entities))
        
        for row, asset in enumerate(entities):
            # Get system name
            system_name = self._get_system_name(asset.system_id)
            
            self.entity_table.setItem(row, 0, QTableWidgetItem(asset.get_hierarchical_id()))
            self.entity_table.setItem(row, 1, QTableWidgetItem(asset.asset_name))
            self.entity_table.setItem(row, 2, QTableWidgetItem(system_name))
            self.entity_table.setItem(row, 3, QTableWidgetItem(asset.asset_description or ""))
            
            # Store asset ID for selection
            self.entity_table.item(row, 0).setData(Qt.UserRole, asset.id)
    
    def _get_system_name(self, system_id: int) -> str:
        """Get system name by ID."""
        try:
            db_manager = self.database_initializer.get_database_manager()
            connection = db_manager.get_connection()
            
            system = connection.fetchone(
                "SELECT system_hierarchy, system_name FROM systems WHERE id = ?",
                (system_id,)
            )
            
            if system:
                return f"{system['system_hierarchy']} - {system['system_name']}"
            return f"System {system_id}"
            
        except Exception:
            return f"System {system_id}"
    
    def _populate_details(self, entity: Asset):
        """Populate details widget with asset data."""
        self.hierarchy_edit.setText(entity.get_hierarchical_id())
        self.name_edit.setText(entity.asset_name)
        self.description_edit.setPlainText(entity.asset_description or "")
        
        # Set system selection
        for i in range(self.system_combo.count()):
            if self.system_combo.itemData(i) == entity.system_id:
                self.system_combo.setCurrentIndex(i)
                break
        
        self.critical_attrs.set_values(entity)
        self.change_tracker.set_original_data(self._collect_form_data())
    
    def _collect_form_data(self) -> Dict[str, Any]:
        """Collect data from form fields."""
        # Parse hierarchical ID
        hierarchy_text = self.hierarchy_edit.text().strip()
        parsed_id = HierarchyManager.parse_hierarchical_id(hierarchy_text)
        
        data = {
            "type_identifier": parsed_id.type_identifier if parsed_id else "A",
            "level_identifier": parsed_id.level_identifier if parsed_id else 0,
            "sequential_identifier": parsed_id.sequential_identifier if parsed_id else 1,
            "system_hierarchy": hierarchy_text,
            "system_id": self.system_combo.currentData(),
            "asset_name": self.name_edit.text().strip(),
            "asset_description": self.description_edit.toPlainText().strip(),
            "baseline": WORKING_BASELINE
        }
        
        # Add critical attributes
        critical_values = self.critical_attrs.get_values()
        data.update(critical_values)
        
        return data
    
    def _clear_details(self):
        """Clear details form."""
        self.hierarchy_edit.setText("A-1")
        self.name_edit.clear()
        self.description_edit.clear()
        self.system_combo.setCurrentIndex(0)
        # Critical attributes will clear themselves
    
    def _set_editing_mode(self, enabled: bool):
        """Enable/disable editing mode."""
        self.hierarchy_edit.setEnabled(enabled and self.current_entity is None)
        self.name_edit.setEnabled(enabled)
        self.description_edit.setEnabled(enabled)
        self.system_combo.setEnabled(enabled)
        
        self.save_btn.setEnabled(enabled)
        self.cancel_btn.setEnabled(enabled)
    
    def add_entity(self):
        """Add a new asset."""
        try:
            # Clear details and set editing mode
            self._clear_details()
            self._set_editing_mode(True)
            
            # Set current system as selected if available
            if self.current_system_id is not None:
                # Find the current system in the combo box
                for i in range(self.system_combo.count()):
                    if self.system_combo.itemData(i) == self.current_system_id:
                        self.system_combo.setCurrentIndex(i)
                        break
            
            # Generate placeholder hierarchical ID
            if self.current_system_id is not None:
                # Get system hierarchy for ID generation
                db_manager = self.database_initializer.get_database_manager()
                connection = db_manager.get_connection()
                
                system_data = connection.fetchone(
                    "SELECT system_hierarchy FROM systems WHERE id = ?",
                    (self.current_system_id,)
                )
                
                if system_data:
                    system_hierarchy = system_data['system_hierarchy']
                    # Generate asset ID based on system hierarchy
                    self.hierarchy_edit.setText(f"{system_hierarchy}.A-?")
                else:
                    self.hierarchy_edit.setText("A-?")
            else:
                self.hierarchy_edit.setText("A-?")
            
            # Reset change tracker
            self.change_tracker.set_original_data({})
            
            logger.debug("Started adding new asset")
            
        except Exception as e:
            logger.error(f"Failed to start adding asset: {str(e)}")
            self._show_error("Add Failed", f"Failed to start adding asset:\n{str(e)}")
    
    def _collect_form_data(self) -> Dict[str, Any]:
        """Collect data from form fields."""
        data = {
            'type_identifier': 'A',
            'level_identifier': 0,
            'sequential_identifier': 1,
            'system_hierarchy': self.hierarchy_edit.text().strip(),
            'asset_name': self.name_edit.text().strip(),
            'asset_description': self.description_edit.toPlainText().strip(),
            'system_id': self.system_combo.currentData(),
            'baseline': WORKING_BASELINE
        }
        
        # Add critical attributes
        critical_values = self.critical_attrs.get_values()
        data.update(critical_values)
        
        # Set system_id to current system if not specified
        if data['system_id'] is None and self.current_system_id is not None:
            data['system_id'] = self.current_system_id
        
        return data


class HazardWidget(BaseEntityWidget):
    """
    Widget for managing Hazard entities.
    """
    
    def __init__(self, database_initializer: DatabaseInitializer, parent=None):
        """Initialize Hazard widget."""
        super().__init__(Hazard, database_initializer, parent)
    
    def _setup_ui(self):
        """Setup the user interface."""
        self._setup_base_ui()
        
        # Configure table columns
        self.entity_table.setColumnCount(5)
        self.entity_table.setHorizontalHeaderLabels(["ID", "Name", "System", "Asset", "Description"])
        
        header = self.entity_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setStretchLastSection(True)
    
    def _setup_validation(self):
        """Setup validation rules."""
        self.validator.add_rule(
            "h_name",
            lambda x: x and len(x.strip()) > 0,
            "Hazard name is required"
        )
    
    def _setup_change_tracking(self):
        """Setup change tracking fields."""
        self.change_tracker.track_field("h_name")
        self.change_tracker.track_field("h_description")
        self.change_tracker.track_field("system_id")
        self.change_tracker.track_field("asset_id")
    
    def _create_details_widget(self) -> QWidget:
        """Create the details/edit widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Scroll area for form
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Basic Information Group
        basic_group = QGroupBox("Basic Information")
        basic_layout = QFormLayout(basic_group)
        
        self.hierarchy_edit = QLineEdit()
        self.hierarchy_edit.setPlaceholderText("H-1, H-1.1, etc.")
        basic_layout.addRow("Hierarchical ID:", self.hierarchy_edit)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter hazard name...")
        basic_layout.addRow("Hazard Name*:", self.name_edit)
        
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Enter hazard description...")
        self.description_edit.setMaximumHeight(100)
        basic_layout.addRow("Description:", self.description_edit)
        
        # System Association
        self.system_combo = QComboBox()
        self._load_systems()
        basic_layout.addRow("Associated System:", self.system_combo)
        
        # Asset Association
        self.asset_combo = QComboBox()
        basic_layout.addRow("Associated Asset:", self.asset_combo)
        
        scroll_layout.addWidget(basic_group)
        
        # Critical Attributes
        self.critical_attrs = CriticalAttributesWidget()
        scroll_layout.addWidget(self.critical_attrs)
        
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_entity)
        self.save_btn.setEnabled(False)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.cancel_editing)
        self.cancel_btn.setEnabled(False)
        
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        # Connect signals
        self.system_combo.currentIndexChanged.connect(self._on_system_changed)
        
        # Connect change tracking
        self.name_edit.textChanged.connect(lambda: self.change_tracker.update_field("h_name", self.name_edit.text()))
        self.description_edit.textChanged.connect(lambda: self.change_tracker.update_field("h_description", self.description_edit.toPlainText()))
        self.system_combo.currentIndexChanged.connect(lambda: self.change_tracker.update_field("system_id", self.system_combo.currentData()))
        self.asset_combo.currentIndexChanged.connect(lambda: self.change_tracker.update_field("asset_id", self.asset_combo.currentData()))
        
        return widget
    
    def _load_systems(self):
        """Load available systems into combo box."""
        try:
            self.system_combo.clear()
            self.system_combo.addItem("Select System...", None)
            
            db_manager = self.database_initializer.get_database_manager()
            connection = db_manager.get_connection()
            
            systems = connection.fetchall(
                "SELECT id, system_hierarchy, system_name FROM systems WHERE baseline = ? ORDER BY system_hierarchy",
                (WORKING_BASELINE,)
            )
            
            for system in systems:
                display_text = f"{system['system_hierarchy']} - {system['system_name']}"
                self.system_combo.addItem(display_text, system['id'])
                
        except Exception as e:
            logger.error(f"Failed to load systems: {str(e)}")
    
    def _on_system_changed(self):
        """Handle system selection change to load associated assets."""
        system_id = self.system_combo.currentData()
        self._load_assets(system_id)
    
    def _load_assets(self, system_id: Optional[int]):
        """Load assets for selected system."""
        try:
            self.asset_combo.clear()
            self.asset_combo.addItem("No Asset", None)
            
            if not system_id:
                return
                
            db_manager = self.database_initializer.get_database_manager()
            connection = db_manager.get_connection()
            
            assets = connection.fetchall(
                "SELECT id, system_hierarchy, asset_name FROM assets WHERE system_id = ? AND baseline = ? ORDER BY system_hierarchy",
                (system_id, WORKING_BASELINE)
            )
            
            for asset in assets:
                display_text = f"{asset['system_hierarchy']} - {asset['asset_name']}"
                self.asset_combo.addItem(display_text, asset['id'])
                
        except Exception as e:
            logger.error(f"Failed to load assets: {str(e)}")
    
    def _populate_table(self, entities: List[Hazard]):
        """Populate table with hazard data."""
        self.entity_table.setRowCount(len(entities))
        
        for row, hazard in enumerate(entities):
            # Get system and asset names
            system_name = self._get_system_name(hazard.system_id)
            asset_name = self._get_asset_name(hazard.asset_id) if hazard.asset_id else ""
            
            self.entity_table.setItem(row, 0, QTableWidgetItem(hazard.get_hierarchical_id()))
            self.entity_table.setItem(row, 1, QTableWidgetItem(hazard.hazard_name))
            self.entity_table.setItem(row, 2, QTableWidgetItem(system_name))
            self.entity_table.setItem(row, 3, QTableWidgetItem(asset_name))
            self.entity_table.setItem(row, 4, QTableWidgetItem(hazard.hazard_description or ""))
            
            # Store hazard ID for selection
            self.entity_table.item(row, 0).setData(Qt.UserRole, hazard.id)
    
    def _get_system_name(self, system_id: int) -> str:
        """Get system name by ID."""
        try:
            db_manager = self.database_initializer.get_database_manager()
            connection = db_manager.get_connection()
            
            system = connection.fetchone(
                "SELECT system_hierarchy, system_name FROM systems WHERE id = ?",
                (system_id,)
            )
            
            if system:
                return f"{system['system_hierarchy']} - {system['system_name']}"
            return f"System {system_id}"
            
        except Exception:
            return f"System {system_id}"
    
    def _get_asset_name(self, asset_id: int) -> str:
        """Get asset name by ID."""
        try:
            db_manager = self.database_initializer.get_database_manager()
            connection = db_manager.get_connection()
            
            asset = connection.fetchone(
                "SELECT system_hierarchy, asset_name FROM assets WHERE id = ?",
                (asset_id,)
            )
            
            if asset:
                return f"{asset['system_hierarchy']} - {asset['asset_name']}"
            return f"Asset {asset_id}"
            
        except Exception:
            return f"Asset {asset_id}"
    
    def _populate_details(self, entity: Hazard):
        """Populate details widget with hazard data."""
        self.hierarchy_edit.setText(entity.get_hierarchical_id())
        self.name_edit.setText(entity.h_name)
        self.description_edit.setPlainText(entity.h_description or "")
        
        # Set system selection
        for i in range(self.system_combo.count()):
            if self.system_combo.itemData(i) == entity.system_id:
                self.system_combo.setCurrentIndex(i)
                break
        
        # Load assets for selected system and set selection
        self._load_assets(entity.system_id)
        for i in range(self.asset_combo.count()):
            if self.asset_combo.itemData(i) == entity.asset_id:
                self.asset_combo.setCurrentIndex(i)
                break
        
        self.critical_attrs.set_values(entity)
        self.change_tracker.set_original_data(self._collect_form_data())
    
    def _collect_form_data(self) -> Dict[str, Any]:
        """Collect data from form fields."""
        # Parse hierarchical ID
        hierarchy_text = self.hierarchy_edit.text().strip()
        parsed_id = HierarchyManager.parse_hierarchical_id(hierarchy_text)
        
        data = {
            "type_identifier": parsed_id.type_identifier if parsed_id else "H",
            "level_identifier": parsed_id.level_identifier if parsed_id else 0,
            "sequential_identifier": parsed_id.sequential_identifier if parsed_id else 1,
            "system_hierarchy": hierarchy_text,
            "system_id": self.system_combo.currentData(),
            "asset_id": self.asset_combo.currentData(),
            "h_name": self.name_edit.text().strip(),
            "h_description": self.description_edit.toPlainText().strip(),
            "baseline": WORKING_BASELINE
        }
        
        # Add critical attributes
        critical_values = self.critical_attrs.get_values()
        data.update(critical_values)
        
        return data
    
    def _clear_details(self):
        """Clear details form."""
        self.hierarchy_edit.setText("H-1")
        self.name_edit.clear()
        self.description_edit.clear()
        self.system_combo.setCurrentIndex(0)
        self.asset_combo.setCurrentIndex(0)
    
    def _set_editing_mode(self, enabled: bool):
        """Set editing mode."""
        self.name_edit.setEnabled(enabled)
        self.description_edit.setEnabled(enabled)
        self.system_combo.setEnabled(enabled)
        self.asset_combo.setEnabled(enabled)
        self.critical_attrs.setEnabled(enabled)
        self.save_btn.setEnabled(enabled)
        self.cancel_btn.setEnabled(enabled)
    
    def add_entity(self):
        """Add a new hazard."""
        try:
            # Clear details and set editing mode
            self._clear_details()
            self._set_editing_mode(True)
            
            # Set current system as selected if available
            if self.current_system_id is not None:
                # Find the current system in the combo box
                for i in range(self.system_combo.count()):
                    if self.system_combo.itemData(i) == self.current_system_id:
                        self.system_combo.setCurrentIndex(i)
                        break
                
                # Load assets for the current system
                self._load_assets(self.current_system_id)
            
            # Generate placeholder hierarchical ID
            if self.current_system_id is not None:
                # Get system hierarchy for ID generation
                db_manager = self.database_initializer.get_database_manager()
                connection = db_manager.get_connection()
                
                system_data = connection.fetchone(
                    "SELECT system_hierarchy FROM systems WHERE id = ?",
                    (self.current_system_id,)
                )
                
                if system_data:
                    system_hierarchy = system_data['system_hierarchy']
                    # Generate hazard ID based on system hierarchy
                    self.hierarchy_edit.setText(f"{system_hierarchy}.H-?")
                else:
                    self.hierarchy_edit.setText("H-?")
            else:
                self.hierarchy_edit.setText("H-?")
            
            # Reset change tracker
            self.change_tracker.set_original_data({})
            
            logger.debug("Started adding new hazard")
            
        except Exception as e:
            logger.error(f"Failed to start adding hazard: {str(e)}")
            self._show_error("Add Failed", f"Failed to start adding hazard:\n{str(e)}")
    
    def _collect_form_data(self) -> Dict[str, Any]:
        """Collect data from form fields."""
        data = {
            'type_identifier': 'H',
            'level_identifier': 0,
            'sequential_identifier': 1,
            'system_hierarchy': self.hierarchy_edit.text().strip(),
            'h_name': self.name_edit.text().strip(),
            'h_description': self.description_edit.toPlainText().strip(),
            'system_id': self.system_combo.currentData(),
            'asset_id': self.asset_combo.currentData(),
            'baseline': WORKING_BASELINE
        }
        
        # Add critical attributes
        critical_values = self.critical_attrs.get_values()
        data.update(critical_values)
        
        return data


class LossWidget(BaseEntityWidget):
    """
    Widget for managing Loss entities.
    """
    
    def __init__(self, database_initializer: DatabaseInitializer, parent=None):
        """Initialize Loss widget."""
        super().__init__(Loss, database_initializer, parent)
    
    def _setup_ui(self):
        """Setup the user interface."""
        self._setup_base_ui()
        
        # Configure table columns
        self.entity_table.setColumnCount(4)
        self.entity_table.setHorizontalHeaderLabels(["ID", "Name", "System", "Description"])
        
        header = self.entity_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setStretchLastSection(True)
    
    def _setup_validation(self):
        """Setup validation rules."""
        self.validator.add_rule(
            "loss_name",
            lambda x: x and len(x.strip()) > 0,
            "Loss name is required"
        )
    
    def _setup_change_tracking(self):
        """Setup change tracking fields."""
        self.change_tracker.track_field("loss_name")
        self.change_tracker.track_field("loss_description")
        self.change_tracker.track_field("asset_id")
    
    def _create_details_widget(self) -> QWidget:
        """Create the details/edit widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Scroll area for form
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Basic Information Group
        basic_group = QGroupBox("Basic Information")
        basic_layout = QFormLayout(basic_group)
        
        self.hierarchy_edit = QLineEdit()
        self.hierarchy_edit.setPlaceholderText("L-1, L-1.1, etc.")
        basic_layout.addRow("Hierarchical ID:", self.hierarchy_edit)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter loss name...")
        basic_layout.addRow("Loss Name*:", self.name_edit)
        
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Enter loss description...")
        self.description_edit.setMaximumHeight(100)
        basic_layout.addRow("Description:", self.description_edit)
        
        # System Association
        self.system_combo = QComboBox()
        self._load_systems()
        basic_layout.addRow("Associated System*:", self.system_combo)
        
        scroll_layout.addWidget(basic_group)
        
        # Critical Attributes
        self.critical_attrs = CriticalAttributesWidget()
        scroll_layout.addWidget(self.critical_attrs)
        
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_entity)
        self.save_btn.setEnabled(False)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.cancel_editing)
        self.cancel_btn.setEnabled(False)
        
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        # Connect change tracking
        self.name_edit.textChanged.connect(lambda: self.change_tracker.update_field("loss_name", self.name_edit.text()))
        self.description_edit.textChanged.connect(lambda: self.change_tracker.update_field("loss_description", self.description_edit.toPlainText()))
        self.system_combo.currentIndexChanged.connect(lambda: self.change_tracker.update_field("system_id", self.system_combo.currentData()))
        
        return widget
    
    def _load_systems(self):
        """Load available systems into combo box."""
        try:
            self.system_combo.clear()
            self.system_combo.addItem("Select System...", None)
            
            db_manager = self.database_initializer.get_database_manager()
            connection = db_manager.get_connection()
            
            systems = connection.fetchall(
                "SELECT id, system_hierarchy, system_name FROM systems WHERE baseline = ? ORDER BY system_hierarchy",
                (WORKING_BASELINE,)
            )
            
            for system in systems:
                display_text = f"{system['system_hierarchy']} - {system['system_name']}"
                self.system_combo.addItem(display_text, system['id'])
                
        except Exception as e:
            logger.error(f"Failed to load systems: {str(e)}")
    
    def _populate_table(self, entities: List[Loss]):
        """Populate table with loss data."""
        self.entity_table.setRowCount(len(entities))
        
        for row, loss in enumerate(entities):
            # Get system name
            system_name = self._get_system_name(loss.system_id)
            
            self.entity_table.setItem(row, 0, QTableWidgetItem(loss.get_hierarchical_id()))
            self.entity_table.setItem(row, 1, QTableWidgetItem(loss.loss_name))
            self.entity_table.setItem(row, 2, QTableWidgetItem(system_name))
            self.entity_table.setItem(row, 3, QTableWidgetItem(loss.loss_description or ""))
            
            # Store loss ID for selection
            self.entity_table.item(row, 0).setData(Qt.UserRole, loss.id)
    
    def _get_system_name(self, system_id: int) -> str:
        """Get system name by ID."""
        try:
            db_manager = self.database_initializer.get_database_manager()
            connection = db_manager.get_connection()
            
            system = connection.fetchone(
                "SELECT system_hierarchy, system_name FROM systems WHERE id = ?",
                (system_id,)
            )
            
            if system:
                return f"{system['system_hierarchy']} - {system['system_name']}"
            return f"System {system_id}"
            
        except Exception:
            return f"System {system_id}"
    
    def _populate_details(self, entity: Loss):
        """Populate details widget with loss data."""
        self.hierarchy_edit.setText(entity.get_hierarchical_id())
        self.name_edit.setText(entity.loss_name)
        self.description_edit.setPlainText(entity.loss_description or "")
        
        # Set system selection
        for i in range(self.system_combo.count()):
            if self.system_combo.itemData(i) == entity.system_id:
                self.system_combo.setCurrentIndex(i)
                break
        
        self.critical_attrs.set_values(entity)
        self.change_tracker.set_original_data(self._collect_form_data())
    
    def _collect_form_data(self) -> Dict[str, Any]:
        """Collect data from form fields."""
        # Parse hierarchical ID
        hierarchy_text = self.hierarchy_edit.text().strip()
        parsed_id = HierarchyManager.parse_hierarchical_id(hierarchy_text)
        
        data = {
            "type_identifier": parsed_id.type_identifier if parsed_id else "L",
            "level_identifier": parsed_id.level_identifier if parsed_id else 0,
            "sequential_identifier": parsed_id.sequential_identifier if parsed_id else 1,
            "system_hierarchy": hierarchy_text,
            "system_id": self.system_combo.currentData(),
            "loss_name": self.name_edit.text().strip(),
            "loss_description": self.description_edit.toPlainText().strip(),
            "baseline": WORKING_BASELINE
        }
        
        # Add critical attributes
        critical_values = self.critical_attrs.get_values()
        data.update(critical_values)
        
        return data
    
    def _clear_details(self):
        """Clear details form."""
        self.hierarchy_edit.setText("L-1")
        self.name_edit.clear()
        self.description_edit.clear()
        self.system_combo.setCurrentIndex(0)
    
    def _set_editing_mode(self, enabled: bool):
        """Set editing mode."""
        self.name_edit.setEnabled(enabled)
        self.description_edit.setEnabled(enabled)
        self.system_combo.setEnabled(enabled)
        self.critical_attrs.setEnabled(enabled)
        self.save_btn.setEnabled(enabled)
        self.cancel_btn.setEnabled(enabled)
    
    def add_entity(self):
        """Add a new loss."""
        try:
            # Clear details and set editing mode
            self._clear_details()
            self._set_editing_mode(True)
            
            # Set current system as selected if available
            if self.current_system_id is not None:
                # Find the current system in the combo box
                for i in range(self.system_combo.count()):
                    if self.system_combo.itemData(i) == self.current_system_id:
                        self.system_combo.setCurrentIndex(i)
                        break
                
                # Load assets for the current system
                self._load_assets(self.current_system_id)
            
            # Generate placeholder hierarchical ID
            if self.current_system_id is not None:
                # Get system hierarchy for ID generation
                db_manager = self.database_initializer.get_database_manager()
                connection = db_manager.get_connection()
                
                system_data = connection.fetchone(
                    "SELECT system_hierarchy FROM systems WHERE id = ?",
                    (self.current_system_id,)
                )
                
                if system_data:
                    system_hierarchy = system_data['system_hierarchy']
                    # Generate loss ID based on system hierarchy
                    self.hierarchy_edit.setText(f"{system_hierarchy}.L-?")
                else:
                    self.hierarchy_edit.setText("L-?")
            else:
                self.hierarchy_edit.setText("L-?")
            
            # Reset change tracker
            self.change_tracker.set_original_data({})
            
            logger.debug("Started adding new loss")
            
        except Exception as e:
            logger.error(f"Failed to start adding loss: {str(e)}")
            self._show_error("Add Failed", f"Failed to start adding loss:\n{str(e)}")
    
    def _collect_form_data(self) -> Dict[str, Any]:
        """Collect data from form fields."""
        data = {
            'type_identifier': 'L',
            'level_identifier': 0,
            'sequential_identifier': 1,
            'system_hierarchy': self.hierarchy_edit.text().strip(),
            'l_name': self.name_edit.text().strip(),
            'l_description': self.description_edit.toPlainText().strip(),
            'loss_description': self.loss_description_edit.toPlainText().strip(),
            'system_id': self.system_combo.currentData(),
            'asset_id': self.asset_combo.currentData(),
            'baseline': WORKING_BASELINE
        }
        
        # Add critical attributes
        critical_values = self.critical_attrs.get_values()
        data.update(critical_values)
        
        # Set system_id to current system if not specified
        if data['system_id'] is None and self.current_system_id is not None:
            data['system_id'] = self.current_system_id
        
        return data


class ControlStructureWidget(BaseEntityWidget):
    """
    Widget for managing Control Structure entities.
    """
    
    def __init__(self, database_initializer: DatabaseInitializer, parent=None):
        """Initialize Control Structure widget."""
        super().__init__(ControlStructure, database_initializer, parent)
    
    def _setup_ui(self):
        """Setup the user interface."""
        self._setup_base_ui()
        
        # Configure table columns
        self.entity_table.setColumnCount(4)
        self.entity_table.setHorizontalHeaderLabels(["ID", "Name", "System", "Description"])
        
        header = self.entity_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setStretchLastSection(True)
    
    def _setup_validation(self):
        """Setup validation rules."""
        self.validator.add_rule(
            "structure_name",
            lambda x: x and len(x.strip()) > 0,
            "Control structure name is required"
        )
        
        self.validator.add_rule(
            "system_id",
            lambda x: x and x > 0,
            "Valid system must be selected"
        )
    
    def _setup_change_tracking(self):
        """Setup change tracking fields."""
        self.change_tracker.track_field("structure_name")
        self.change_tracker.track_field("structure_description")
        self.change_tracker.track_field("system_id")
    
    def _create_details_widget(self) -> QWidget:
        """Create the details/edit widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Scroll area for form
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Basic Information Group
        basic_group = QGroupBox("Basic Information")
        basic_layout = QFormLayout(basic_group)
        
        self.hierarchy_edit = QLineEdit()
        self.hierarchy_edit.setPlaceholderText("CS-1, CS-1.1, etc.")
        basic_layout.addRow("Hierarchical ID:", self.hierarchy_edit)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter control structure name...")
        basic_layout.addRow("Structure Name*:", self.name_edit)
        
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Enter control structure description...")
        self.description_edit.setMaximumHeight(100)
        basic_layout.addRow("Description:", self.description_edit)
        
        # System Association
        self.system_combo = QComboBox()
        self._load_systems()
        basic_layout.addRow("Associated System*:", self.system_combo)
        
        # Diagram URL
        self.diagram_url_edit = QLineEdit()
        self.diagram_url_edit.setPlaceholderText("Enter diagram URL (optional)...")
        basic_layout.addRow("Diagram URL:", self.diagram_url_edit)
        
        scroll_layout.addWidget(basic_group)
        
        # Critical Attributes
        self.critical_attrs = CriticalAttributesWidget()
        scroll_layout.addWidget(self.critical_attrs)
        
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_entity)
        self.save_btn.setEnabled(False)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.cancel_editing)
        self.cancel_btn.setEnabled(False)
        
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        # Connect change tracking
        self.name_edit.textChanged.connect(lambda: self.change_tracker.update_field("structure_name", self.name_edit.text()))
        self.description_edit.textChanged.connect(lambda: self.change_tracker.update_field("structure_description", self.description_edit.toPlainText()))
        self.system_combo.currentIndexChanged.connect(lambda: self.change_tracker.update_field("system_id", self.system_combo.currentData()))
        
        return widget
    
    def _load_systems(self):
        """Load available systems into combo box."""
        try:
            self.system_combo.clear()
            self.system_combo.addItem("Select System...", None)
            
            db_manager = self.database_initializer.get_database_manager()
            connection = db_manager.get_connection()
            
            systems = connection.fetchall(
                "SELECT id, system_hierarchy, system_name FROM systems WHERE baseline = ? ORDER BY system_hierarchy",
                (WORKING_BASELINE,)
            )
            
            for system in systems:
                display_text = f"{system['system_hierarchy']} - {system['system_name']}"
                self.system_combo.addItem(display_text, system['id'])
                
        except Exception as e:
            logger.error(f"Failed to load systems: {str(e)}")
    
    def _populate_table(self, entities: List[ControlStructure]):
        """Populate table with control structure data."""
        self.entity_table.setRowCount(len(entities))
        
        for row, structure in enumerate(entities):
            # Get system name
            system_name = self._get_system_name(structure.system_id)
            
            self.entity_table.setItem(row, 0, QTableWidgetItem(structure.get_hierarchical_id()))
            self.entity_table.setItem(row, 1, QTableWidgetItem(structure.structure_name))
            self.entity_table.setItem(row, 2, QTableWidgetItem(system_name))
            self.entity_table.setItem(row, 3, QTableWidgetItem(structure.structure_description or ""))
            
            # Store structure ID for selection
            self.entity_table.item(row, 0).setData(Qt.UserRole, structure.id)
    
    def _get_system_name(self, system_id: int) -> str:
        """Get system name by ID."""
        try:
            db_manager = self.database_initializer.get_database_manager()
            connection = db_manager.get_connection()
            
            system = connection.fetchone(
                "SELECT system_hierarchy, system_name FROM systems WHERE id = ?",
                (system_id,)
            )
            
            if system:
                return f"{system['system_hierarchy']} - {system['system_name']}"
            return f"System {system_id}"
            
        except Exception:
            return f"System {system_id}"
    
    def _populate_details(self, entity: ControlStructure):
        """Populate details widget with control structure data."""
        self.hierarchy_edit.setText(entity.get_hierarchical_id())
        self.name_edit.setText(entity.structure_name)
        self.description_edit.setPlainText(entity.structure_description or "")
        self.diagram_url_edit.setText(entity.diagram_url or "")
        
        # Set system selection
        for i in range(self.system_combo.count()):
            if self.system_combo.itemData(i) == entity.system_id:
                self.system_combo.setCurrentIndex(i)
                break
        
        self.critical_attrs.set_values(entity)
        self.change_tracker.set_original_data(self._collect_form_data())
    
    def _collect_form_data(self) -> Dict[str, Any]:
        """Collect data from form fields."""
        # Parse hierarchical ID
        hierarchy_text = self.hierarchy_edit.text().strip()
        parsed_id = HierarchyManager.parse_hierarchical_id(hierarchy_text)
        
        data = {
            "type_identifier": parsed_id.type_identifier if parsed_id else "CS",
            "level_identifier": parsed_id.level_identifier if parsed_id else 0,
            "sequential_identifier": parsed_id.sequential_identifier if parsed_id else 1,
            "system_hierarchy": hierarchy_text,
            "system_id": self.system_combo.currentData(),
            "structure_name": self.name_edit.text().strip(),
            "structure_description": self.description_edit.toPlainText().strip(),
            "diagram_url": self.diagram_url_edit.text().strip(),
            "baseline": WORKING_BASELINE
        }
        
        # Add critical attributes
        critical_values = self.critical_attrs.get_values()
        data.update(critical_values)
        
        return data
    
    def _clear_details(self):
        """Clear details form."""
        self.hierarchy_edit.setText("CS-1")
        self.name_edit.clear()
        self.description_edit.clear()
        self.diagram_url_edit.clear()
        self.system_combo.setCurrentIndex(0)
    
    def _set_editing_mode(self, enabled: bool):
        """Enable/disable editing mode."""
        self.name_edit.setEnabled(enabled)
        self.description_edit.setEnabled(enabled)
        self.system_combo.setEnabled(enabled)
        self.critical_attrs.setEnabled(enabled)
        self.save_btn.setEnabled(enabled)
        self.cancel_btn.setEnabled(enabled)
    
    def add_entity(self):
        """Add a new control structure."""
        try:
            # Clear details and set editing mode
            self._clear_details()
            self._set_editing_mode(True)
            
            # Set current system as selected if available
            if self.current_system_id is not None:
                # Find the current system in the combo box
                for i in range(self.system_combo.count()):
                    if self.system_combo.itemData(i) == self.current_system_id:
                        self.system_combo.setCurrentIndex(i)
                        break
            
            # Generate placeholder hierarchical ID
            if self.current_system_id is not None:
                # Get system hierarchy for ID generation
                db_manager = self.database_initializer.get_database_manager()
                connection = db_manager.get_connection()
                
                system_data = connection.fetchone(
                    "SELECT system_hierarchy FROM systems WHERE id = ?",
                    (self.current_system_id,)
                )
                
                if system_data:
                    system_hierarchy = system_data['system_hierarchy']
                    # Generate control structure ID based on system hierarchy
                    self.hierarchy_edit.setText(f"{system_hierarchy}.CS-?")
                else:
                    self.hierarchy_edit.setText("CS-?")
            else:
                self.hierarchy_edit.setText("CS-?")
            
            # Reset change tracker
            self.change_tracker.set_original_data({})
            
            logger.debug("Started adding new control structure")
            
        except Exception as e:
            logger.error(f"Failed to start adding control structure: {str(e)}")
            self._show_error("Add Failed", f"Failed to start adding control structure:\n{str(e)}")
    
    def _collect_form_data(self) -> Dict[str, Any]:
        """Collect data from form fields."""
        data = {
            'type_identifier': 'CS',
            'level_identifier': 0,
            'sequential_identifier': 1,
            'system_hierarchy': self.hierarchy_edit.text().strip(),
            'structure_name': self.name_edit.text().strip(),
            'structure_description': self.description_edit.toPlainText().strip(),
            'system_id': self.system_combo.currentData(),
            'baseline': WORKING_BASELINE
        }
        
        # Add critical attributes
        critical_values = self.critical_attrs.get_values()
        data.update(critical_values)
        
        return data


class ControllerWidget(BaseEntityWidget):
    """
    Widget for managing Controller entities.
    """
    
    def __init__(self, database_initializer: DatabaseInitializer, parent=None):
        """Initialize Controller widget."""
        super().__init__(Controller, database_initializer, parent)
    
    def _setup_ui(self):
        """Setup the user interface."""
        self._setup_base_ui()
        
        # Configure table columns
        self.entity_table.setColumnCount(4)
        self.entity_table.setHorizontalHeaderLabels(["ID", "Name", "System", "Description"])
        
        header = self.entity_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setStretchLastSection(True)
    
    def _setup_validation(self):
        """Setup validation rules."""
        self.validator.add_rule(
            "controller_name",
            lambda x: x and len(x.strip()) > 0,
            "Controller name is required"
        )
        
        self.validator.add_rule(
            "controller_name",
            lambda x: len(x) <= 100 if x else True,
            "Controller name must be 100 characters or less"
        )
        
        self.validator.add_rule(
            "system_id",
            lambda x: x and x > 0,
            "Valid system must be selected"
        )
    
    def _setup_change_tracking(self):
        """Setup change tracking fields."""
        self.change_tracker.track_field("controller_name")
        self.change_tracker.track_field("controller_description")
        self.change_tracker.track_field("system_id")
    
    def _create_details_widget(self) -> QWidget:
        """Create the details/edit widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Scroll area for form
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Basic Information Group
        basic_group = QGroupBox("Basic Information")
        basic_layout = QFormLayout(basic_group)
        
        self.hierarchy_edit = QLineEdit()
        self.hierarchy_edit.setPlaceholderText("C-1, C-1.1, etc.")
        basic_layout.addRow("Hierarchical ID:", self.hierarchy_edit)
        
        self.short_id_edit = QLineEdit()
        self.short_id_edit.setPlaceholderText("Short text identifier...")
        basic_layout.addRow("Short ID:", self.short_id_edit)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter controller name...")
        basic_layout.addRow("Controller Name*:", self.name_edit)
        
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Enter controller description...")
        self.description_edit.setMaximumHeight(100)
        basic_layout.addRow("Description:", self.description_edit)
        
        # System Association
        self.system_combo = QComboBox()
        self._load_systems()
        basic_layout.addRow("Associated System*:", self.system_combo)
        
        scroll_layout.addWidget(basic_group)
        
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_entity)
        self.save_btn.setEnabled(False)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.cancel_editing)
        self.cancel_btn.setEnabled(False)
        
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        # Connect change tracking
        self.name_edit.textChanged.connect(lambda: self.change_tracker.update_field("controller_name", self.name_edit.text()))
        self.description_edit.textChanged.connect(lambda: self.change_tracker.update_field("controller_description", self.description_edit.toPlainText()))
        self.system_combo.currentIndexChanged.connect(lambda: self.change_tracker.update_field("system_id", self.system_combo.currentData()))
        
        return widget
    
    def _load_systems(self):
        """Load available systems into combo box."""
        try:
            self.system_combo.clear()
            self.system_combo.addItem("Select System...", None)
            
            db_manager = self.database_initializer.get_database_manager()
            connection = db_manager.get_connection()
            
            systems = connection.fetchall(
                "SELECT id, system_hierarchy, system_name FROM systems WHERE baseline = ? ORDER BY system_hierarchy",
                (WORKING_BASELINE,)
            )
            
            for system in systems:
                display_text = f"{system['system_hierarchy']} - {system['system_name']}"
                self.system_combo.addItem(display_text, system['id'])
                
        except Exception as e:
            logger.error(f"Failed to load systems: {str(e)}")
    
    def _populate_table(self, entities: List[Controller]):
        """Populate table with controller data."""
        self.entity_table.setRowCount(len(entities))
        
        for row, controller in enumerate(entities):
            # Get system name
            system_name = self._get_system_name(controller.system_id)
            
            self.entity_table.setItem(row, 0, QTableWidgetItem(controller.get_hierarchical_id()))
            self.entity_table.setItem(row, 1, QTableWidgetItem(controller.controller_name))
            self.entity_table.setItem(row, 2, QTableWidgetItem(system_name))
            self.entity_table.setItem(row, 3, QTableWidgetItem(controller.controller_description or ""))
            
            # Store controller ID for selection
            self.entity_table.item(row, 0).setData(Qt.UserRole, controller.id)
    
    def _get_system_name(self, system_id: int) -> str:
        """Get system name by ID."""
        try:
            db_manager = self.database_initializer.get_database_manager()
            connection = db_manager.get_connection()
            
            system = connection.fetchone(
                "SELECT system_hierarchy, system_name FROM systems WHERE id = ?",
                (system_id,)
            )
            
            if system:
                return f"{system['system_hierarchy']} - {system['system_name']}"
            return f"System {system_id}"
            
        except Exception:
            return f"System {system_id}"
    
    def _populate_details(self, entity: Controller):
        """Populate details widget with controller data."""
        self.hierarchy_edit.setText(entity.get_hierarchical_id())
        self.short_id_edit.setText(entity.short_text_identifier or "")
        self.name_edit.setText(entity.controller_name)
        self.description_edit.setPlainText(entity.controller_description or "")
        
        # Set system in combo box
        for i in range(self.system_combo.count()):
            if self.system_combo.itemData(i) == entity.system_id:
                self.system_combo.setCurrentIndex(i)
                break
    
    def _collect_form_data(self) -> Dict[str, Any]:
        """Collect data from form fields."""
        data = {
            'type_identifier': 'C',
            'level_identifier': 0,
            'sequential_identifier': 1,
            'system_hierarchy': self.hierarchy_edit.text().strip(),
            'short_text_identifier': self.short_id_edit.text().strip(),
            'controller_name': self.name_edit.text().strip(),
            'controller_description': self.description_edit.toPlainText().strip(),
            'system_id': self.system_combo.currentData(),
            'baseline': WORKING_BASELINE
        }
        
        return data
    
    def _clear_details(self):
        """Clear details widget."""
        self.hierarchy_edit.clear()
        self.short_id_edit.clear()
        self.name_edit.clear()
        self.description_edit.clear()
        self.system_combo.setCurrentIndex(0)
    
    def _set_editing_mode(self, enabled: bool):
        """Set editing mode."""
        self.name_edit.setEnabled(enabled)
        self.description_edit.setEnabled(enabled)
        self.system_combo.setEnabled(enabled)
        self.save_btn.setEnabled(enabled)
        self.cancel_btn.setEnabled(enabled)
    
    def add_entity(self):
        """Add a new controller."""
        try:
            # Clear details and set editing mode
            self._clear_details()
            self._set_editing_mode(True)
            
            # Set current system as selected if available
            if self.current_system_id is not None:
                # Find the current system in the combo box
                for i in range(self.system_combo.count()):
                    if self.system_combo.itemData(i) == self.current_system_id:
                        self.system_combo.setCurrentIndex(i)
                        break
            
            # Generate placeholder hierarchical ID
            if self.current_system_id is not None:
                # Get system hierarchy for ID generation
                db_manager = self.database_initializer.get_database_manager()
                connection = db_manager.get_connection()
                
                system_data = connection.fetchone(
                    "SELECT system_hierarchy FROM systems WHERE id = ?",
                    (self.current_system_id,)
                )
                
                if system_data:
                    system_hierarchy = system_data['system_hierarchy']
                    # Generate controller ID based on system hierarchy
                    self.hierarchy_edit.setText(f"{system_hierarchy}.C-?")
                else:
                    self.hierarchy_edit.setText("C-?")
            else:
                self.hierarchy_edit.setText("C-?")
            
            # Reset change tracker
            self.change_tracker.set_original_data({})
            
            logger.debug("Started adding new controller")
            
        except Exception as e:
            logger.error(f"Failed to start adding controller: {str(e)}")
            self._show_error("Add Failed", f"Failed to start adding controller:\n{str(e)}")