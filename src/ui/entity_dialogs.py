"""
Entity editing dialogs for STPA Tool
Provides forms for creating and editing STPA entities.
"""

from typing import Optional, Dict, Any
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGridLayout,
    QLineEdit, QTextEdit, QComboBox, QCheckBox, QLabel, QPushButton,
    QDialogButtonBox, QGroupBox, QScrollArea, QWidget, QMessageBox,
    QSpinBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from ..database.entities import System, Function, Requirement, Interface, Asset, Hazard, Loss, ControlStructure, Controller, BaseEntity
from ..config.constants import (
    CRITICALITY_LEVELS, VERIFICATION_METHODS, IMPERATIVES,
    WORKING_BASELINE
)
from ..utils.hierarchy import HierarchyManager
from ..log_config.config import get_logger

logger = get_logger(__name__)


class CriticalAttributesWidget(QWidget):
    """
    Widget for editing critical attributes common to many entities.
    """
    
    def __init__(self):
        """Initialize critical attributes widget."""
        super().__init__()
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the critical attributes UI."""
        layout = QVBoxLayout(self)
        
        # Critical Attributes Group
        critical_group = QGroupBox("Critical Attributes")
        critical_layout = QGridLayout(critical_group)
        
        # Criticality
        critical_layout.addWidget(QLabel("Criticality:"), 0, 0)
        self.criticality_combo = QComboBox()
        self.criticality_combo.addItems(CRITICALITY_LEVELS)
        critical_layout.addWidget(self.criticality_combo, 0, 1)
        
        # Security attributes with descriptions
        row = 1
        self.security_widgets = {}
        
        security_attributes = [
            ("confidentiality", "Confidentiality"),
            ("integrity", "Integrity"), 
            ("availability", "Availability"),
            ("authenticity", "Authenticity"),
            ("non_repudiation", "Non-Repudiation"),
            ("assurance", "Assurance"),
            ("trustworthy", "Trustworthy"),
            ("privacy", "Privacy")
        ]
        
        for attr_name, attr_label in security_attributes:
            # Checkbox
            checkbox = QCheckBox(attr_label)
            critical_layout.addWidget(checkbox, row, 0)
            
            # Description field
            desc_edit = QLineEdit()
            desc_edit.setPlaceholderText(f"{attr_label} description...")
            desc_edit.setEnabled(False)  # Initially disabled
            critical_layout.addWidget(desc_edit, row, 1)
            
            # Enable description when checkbox is checked
            checkbox.toggled.connect(desc_edit.setEnabled)
            
            self.security_widgets[attr_name] = {
                'checkbox': checkbox,
                'description': desc_edit
            }
            
            row += 1
        
        layout.addWidget(critical_group)
    
    def set_values(self, entity: BaseEntity):
        """Set values from entity."""
        if hasattr(entity, 'criticality'):
            index = self.criticality_combo.findText(entity.criticality)
            if index >= 0:
                self.criticality_combo.setCurrentIndex(index)
        
        for attr_name, widgets in self.security_widgets.items():
            if hasattr(entity, attr_name):
                checkbox_value = getattr(entity, attr_name, False)
                widgets['checkbox'].setChecked(checkbox_value)
                
                desc_attr = f"{attr_name}_description"
                if hasattr(entity, desc_attr):
                    desc_value = getattr(entity, desc_attr, "")
                    widgets['description'].setText(desc_value)
    
    def get_values(self) -> Dict[str, Any]:
        """Get values as dictionary."""
        values = {
            'criticality': self.criticality_combo.currentText()
        }
        
        for attr_name, widgets in self.security_widgets.items():
            values[attr_name] = widgets['checkbox'].isChecked()
            values[f"{attr_name}_description"] = widgets['description'].text()
        
        return values


class SystemEditDialog(QDialog):
    """
    Dialog for editing system entities.
    """
    
    system_saved = Signal(object)  # Emitted when system is saved
    
    def __init__(self, system: Optional[System] = None, parent_system: Optional[System] = None, parent_id: Optional[int] = None, parent=None):
        """
        Initialize system edit dialog.
        
        Args:
            system: System to edit (None for new system)
            parent_system: Parent system for new child systems
            parent_id: Parent system ID for new child systems
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.system = system
        self.parent_system = parent_system
        self.parent_id = parent_id if parent_id else (parent_system.id if parent_system else None)
        self.is_new = system is None
        
        if self.is_new:
            self.setWindowTitle("New System")
        else:
            self.setWindowTitle(f"Edit System - {system.system_name}")
        
        self.setModal(True)
        self.resize(600, 700)
        
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        """Setup the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Scroll area for long forms
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Basic Information Group
        basic_group = QGroupBox("Basic Information")
        basic_layout = QFormLayout(basic_group)
        
        # Hierarchical ID (auto-generated, read-only)
        self.hierarchy_edit = QLineEdit()
        self.hierarchy_edit.setReadOnly(True)
        self.hierarchy_edit.setPlaceholderText("Auto-generated on save")
        basic_layout.addRow("Hierarchical ID:", self.hierarchy_edit)
        
        # System Name
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter system name...")
        basic_layout.addRow("System Name*:", self.name_edit)
        
        # System Description
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Enter system description...")
        self.description_edit.setMaximumHeight(100)
        basic_layout.addRow("Description:", self.description_edit)
        
        # Parent System (for new systems)
        if self.is_new:
            self.parent_label = QLabel()
            if self.parent_system:
                self.parent_label.setText(f"{self.parent_system.get_hierarchical_id()} - {self.parent_system.system_name}")
            else:
                self.parent_label.setText("Root System")
            basic_layout.addRow("Parent System:", self.parent_label)
        
        scroll_layout.addWidget(basic_group)
        
        # Critical Attributes
        self.critical_attrs = CriticalAttributesWidget()
        scroll_layout.addWidget(self.critical_attrs)
        
        # Baseline Information (for existing systems)
        if not self.is_new:
            baseline_group = QGroupBox("Baseline Information")
            baseline_layout = QFormLayout(baseline_group)
            
            self.baseline_label = QLabel()
            baseline_layout.addRow("Baseline:", self.baseline_label)
            
            scroll_layout.addWidget(baseline_group)
        
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        # Buttons
        button_box = QDialogButtonBox()
        
        if self.is_new:
            button_box.setStandardButtons(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        else:
            button_box.setStandardButtons(QDialogButtonBox.Save | QDialogButtonBox.Cancel | QDialogButtonBox.Reset)
        
        button_box.accepted.connect(self._save_system)
        button_box.rejected.connect(self.reject)
        
        if not self.is_new:
            reset_button = button_box.button(QDialogButtonBox.Reset)
            reset_button.clicked.connect(self._load_data)
        
        layout.addWidget(button_box)
        
        # Validation
        self.name_edit.textChanged.connect(self._validate_form)
        self.hierarchy_edit.textChanged.connect(self._validate_form)
        
        self._validate_form()
    
    def _load_data(self):
        """Load data from system entity."""
        if self.system:
            self.hierarchy_edit.setText(self.system.get_hierarchical_id())
            self.name_edit.setText(self.system.system_name)
            self.description_edit.setPlainText(self.system.system_description or "")
            self.critical_attrs.set_values(self.system)
            
            if hasattr(self, 'baseline_label'):
                self.baseline_label.setText(self.system.baseline)
        else:
            # Generate next hierarchical ID for new system
            if self.parent_system:
                # Generate child ID based on parent
                parent_hierarchy = HierarchyManager.parse_hierarchical_id(self.parent_system.system_hierarchy)
                if parent_hierarchy:
                    # For now, show placeholder - actual ID will be generated on save
                    if parent_hierarchy.level_identifier == 0:
                        self.hierarchy_edit.setText(f"{parent_hierarchy.type_identifier}-{parent_hierarchy.sequential_identifier}.?")
                    else:
                        self.hierarchy_edit.setText(f"{parent_hierarchy.type_identifier}-{parent_hierarchy.level_identifier}.{parent_hierarchy.sequential_identifier}.?")
                else:
                    self.hierarchy_edit.setText("S-?.?")
            else:
                # Generate root ID placeholder
                self.hierarchy_edit.setText("S-?")
    
    def _validate_form(self):
        """Validate form and enable/disable save button."""
        is_valid = True
        
        # Check required fields (only system name is required now)
        if not self.name_edit.text().strip():
            is_valid = False
        
        # Enable/disable save button
        button_box = self.findChild(QDialogButtonBox)
        if button_box:
            save_button = button_box.button(QDialogButtonBox.Save)
            if save_button:
                save_button.setEnabled(is_valid)
    
    def _save_system(self):
        """Save the system."""
        try:
            # Create or update system
            if self.is_new:
                self.system = System(
                    system_name=self.name_edit.text().strip(),
                    system_description=self.description_edit.toPlainText().strip(),
                    parent_system_id=self.parent_id,
                    baseline=WORKING_BASELINE
                )
                # Note: hierarchical ID will be auto-generated in the repository
            else:
                self.system.system_name = self.name_edit.text().strip()
                self.system.system_description = self.description_edit.toPlainText().strip()
            
            # Apply critical attributes
            critical_values = self.critical_attrs.get_values()
            for key, value in critical_values.items():
                setattr(self.system, key, value)
            
            # Emit signal
            self.system_saved.emit(self.system)
            
            logger.info(f"System {'created' if self.is_new else 'updated'}: {self.system.system_name}")
            self.accept()
            
        except Exception as e:
            logger.error(f"Failed to save system: {str(e)}")
            QMessageBox.critical(self, "Save Failed", f"Failed to save system:\n{str(e)}")
    
    def get_system(self) -> Optional[System]:
        """Get the system entity."""
        return self.system


class FunctionEditDialog(QDialog):
    """
    Dialog for editing function entities.
    """
    
    function_saved = Signal(object)  # Emitted when function is saved
    
    def __init__(self, function: Optional[Function] = None, system_id: Optional[int] = None, parent=None):
        """
        Initialize function edit dialog.
        
        Args:
            function: Function to edit (None for new function)
            system_id: Associated system ID for new functions
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.function = function
        self.system_id = system_id
        self.is_new = function is None
        
        if self.is_new:
            self.setWindowTitle("New Function")
        else:
            self.setWindowTitle(f"Edit Function - {function.function_name}")
        
        self.setModal(True)
        self.resize(500, 600)
        
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        """Setup the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Scroll area
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Basic Information
        basic_group = QGroupBox("Basic Information")
        basic_layout = QFormLayout(basic_group)
        
        self.hierarchy_edit = QLineEdit()
        self.hierarchy_edit.setReadOnly(True)
        self.hierarchy_edit.setPlaceholderText("Auto-generated on save")
        basic_layout.addRow("Hierarchical ID:", self.hierarchy_edit)
        
        self.short_id_edit = QLineEdit()
        self.short_id_edit.setPlaceholderText("Short text identifier...")
        basic_layout.addRow("Short ID:", self.short_id_edit)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter function name...")
        basic_layout.addRow("Function Name*:", self.name_edit)
        
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Enter function description...")
        self.description_edit.setMaximumHeight(100)
        basic_layout.addRow("Description:", self.description_edit)
        
        scroll_layout.addWidget(basic_group)
        
        # Critical Attributes
        self.critical_attrs = CriticalAttributesWidget()
        scroll_layout.addWidget(self.critical_attrs)
        
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self._save_function)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(button_box)
        
        # Validation
        self.name_edit.textChanged.connect(self._validate_form)
        self._validate_form()
    
    def _load_data(self):
        """Load data from function entity."""
        if self.function:
            self.hierarchy_edit.setText(self.function.get_hierarchical_id())
            self.short_id_edit.setText(self.function.short_text_identifier or "")
            self.name_edit.setText(self.function.function_name)
            self.description_edit.setPlainText(self.function.function_description or "")
            self.critical_attrs.set_values(self.function)
        else:
            # Show placeholder for auto-generated ID
            self.hierarchy_edit.setPlaceholderText("Auto-generated on save")
    
    def _validate_form(self):
        """Validate form."""
        is_valid = bool(self.name_edit.text().strip())
        
        button_box = self.findChild(QDialogButtonBox)
        if button_box:
            save_button = button_box.button(QDialogButtonBox.Save)
            if save_button:
                save_button.setEnabled(is_valid)
    
    def _save_function(self):
        """Save the function."""
        try:
            if self.is_new:
                function = Function(
                    system_id=self.system_id,
                    short_text_identifier=self.short_id_edit.text().strip(),
                    function_name=self.name_edit.text().strip(),
                    function_description=self.description_edit.toPlainText().strip(),
                    baseline=WORKING_BASELINE
                )
                # Note: hierarchical ID will be auto-generated in the repository
            else:
                function = self.function
                function.short_text_identifier = self.short_id_edit.text().strip()
                function.function_name = self.name_edit.text().strip()
                function.function_description = self.description_edit.toPlainText().strip()
            
            # Apply critical attributes
            critical_values = self.critical_attrs.get_values()
            for key, value in critical_values.items():
                setattr(function, key, value)
            
            self.function_saved.emit(function)
            
            logger.info(f"Function {'created' if self.is_new else 'updated'}: {function.function_name}")
            self.accept()
            
        except Exception as e:
            logger.error(f"Failed to save function: {str(e)}")
            QMessageBox.critical(self, "Save Failed", f"Failed to save function:\n{str(e)}")
    
    def get_function(self) -> Optional[Function]:
        """Get the function entity."""
        return self.function


class RequirementEditDialog(QDialog):
    """
    Dialog for editing requirement entities.
    """
    
    requirement_saved = Signal(object)  # Emitted when requirement is saved
    
    def __init__(self, requirement: Optional[Requirement] = None, system_id: Optional[int] = None, parent=None):
        """
        Initialize requirement edit dialog.
        
        Args:
            requirement: Requirement to edit (None for new requirement)
            system_id: Associated system ID for new requirements
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.requirement = requirement
        self.system_id = system_id
        self.is_new = requirement is None
        
        if self.is_new:
            self.setWindowTitle("New Requirement")
        else:
            self.setWindowTitle(f"Edit Requirement - {requirement.alphanumeric_identifier}")
        
        self.setModal(True)
        self.resize(600, 700)
        
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        """Setup the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Scroll area
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Basic Information
        basic_group = QGroupBox("Basic Information")
        basic_layout = QFormLayout(basic_group)
        
        self.hierarchy_edit = QLineEdit()
        self.hierarchy_edit.setReadOnly(True)
        self.hierarchy_edit.setPlaceholderText("Auto-generated on save")
        basic_layout.addRow("Hierarchical ID:", self.hierarchy_edit)
        
        self.alphanumeric_edit = QLineEdit()
        self.alphanumeric_edit.setPlaceholderText("e.g., REQ-001")
        basic_layout.addRow("Alphanumeric ID:", self.alphanumeric_edit)
        
        self.short_id_edit = QLineEdit()
        self.short_id_edit.setPlaceholderText("Short text identifier...")
        basic_layout.addRow("Short ID:", self.short_id_edit)
        
        self.requirement_text_edit = QTextEdit()
        self.requirement_text_edit.setPlaceholderText("Enter requirement text...")
        self.requirement_text_edit.setMaximumHeight(100)
        basic_layout.addRow("Requirement Text*:", self.requirement_text_edit)
        
        # Verification and imperative
        self.verification_combo = QComboBox()
        self.verification_combo.addItems(["Inspection", "Analysis", "Demonstration", "Test"])
        basic_layout.addRow("Verification Method:", self.verification_combo)
        
        self.imperative_combo = QComboBox()
        self.imperative_combo.addItems(["Shall", "Should", "May", "Will"])
        basic_layout.addRow("Imperative:", self.imperative_combo)
        
        self.actor_edit = QLineEdit()
        self.actor_edit.setPlaceholderText("Actor (optional)")
        basic_layout.addRow("Actor:", self.actor_edit)
        
        self.action_edit = QLineEdit()
        self.action_edit.setPlaceholderText("Action (optional)")
        basic_layout.addRow("Action:", self.action_edit)
        
        scroll_layout.addWidget(basic_group)
        
        # Critical Attributes
        self.critical_attrs = CriticalAttributesWidget()
        scroll_layout.addWidget(self.critical_attrs)
        
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self._save_requirement)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(button_box)
        
        # Validation
        self.requirement_text_edit.textChanged.connect(self._validate_form)
        self._validate_form()
    
    def _load_data(self):
        """Load data from requirement entity."""
        if self.requirement:
            self.hierarchy_edit.setText(self.requirement.get_hierarchical_id())
            self.alphanumeric_edit.setText(self.requirement.alphanumeric_identifier or "")
            self.short_id_edit.setText(self.requirement.short_text_identifier or "")
            self.requirement_text_edit.setPlainText(self.requirement.requirement_text)
            self.verification_combo.setCurrentText(self.requirement.verification_method or "Inspection")
            self.imperative_combo.setCurrentText(self.requirement.imperative or "Shall")
            self.actor_edit.setText(self.requirement.actor or "")
            self.action_edit.setText(self.requirement.action or "")
            self.critical_attrs.set_values(self.requirement)
        else:
            # Generate placeholder ID
            self.hierarchy_edit.setText("R-?")
    
    def _validate_form(self):
        """Validate form."""
        is_valid = bool(self.requirement_text_edit.toPlainText().strip())
        
        button_box = self.findChild(QDialogButtonBox)
        if button_box:
            save_button = button_box.button(QDialogButtonBox.Save)
            if save_button:
                save_button.setEnabled(is_valid)
    
    def _save_requirement(self):
        """Save the requirement."""
        try:
            if self.is_new:
                requirement = Requirement(
                    system_id=self.system_id,
                    alphanumeric_identifier=self.alphanumeric_edit.text().strip(),
                    short_text_identifier=self.short_id_edit.text().strip(),
                    requirement_text=self.requirement_text_edit.toPlainText().strip(),
                    verification_method=self.verification_combo.currentText(),
                    imperative=self.imperative_combo.currentText(),
                    actor=self.actor_edit.text().strip(),
                    action=self.action_edit.text().strip(),
                    baseline=WORKING_BASELINE
                )
                # Note: hierarchical ID will be auto-generated in the repository
            else:
                requirement = self.requirement
                requirement.alphanumeric_identifier = self.alphanumeric_edit.text().strip()
                requirement.short_text_identifier = self.short_id_edit.text().strip()
                requirement.requirement_text = self.requirement_text_edit.toPlainText().strip()
                requirement.verification_method = self.verification_combo.currentText()
                requirement.imperative = self.imperative_combo.currentText()
                requirement.actor = self.actor_edit.text().strip()
                requirement.action = self.action_edit.text().strip()
            
            # Apply critical attributes
            critical_values = self.critical_attrs.get_values()
            for key, value in critical_values.items():
                setattr(requirement, key, value)
            
            self.requirement_saved.emit(requirement)
            
            logger.info(f"Requirement {'created' if self.is_new else 'updated'}: {requirement.alphanumeric_identifier}")
            self.accept()
            
        except Exception as e:
            logger.error(f"Failed to save requirement: {str(e)}")
            QMessageBox.critical(self, "Save Failed", f"Failed to save requirement:\n{str(e)}")
    
    def get_requirement(self) -> Optional[Requirement]:
        """Get the requirement entity."""
        return self.requirement


class InterfaceEditDialog(QDialog):
    """
    Dialog for editing interface entities.
    """
    
    interface_saved = Signal(object)  # Emitted when interface is saved
    
    def __init__(self, interface: Optional[Interface] = None, system_id: Optional[int] = None, parent=None):
        """
        Initialize interface edit dialog.
        
        Args:
            interface: Interface to edit (None for new interface)
            system_id: Associated system ID for new interfaces
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.interface = interface
        self.system_id = system_id
        self.is_new = interface is None
        
        if self.is_new:
            self.setWindowTitle("New Interface")
        else:
            self.setWindowTitle(f"Edit Interface - {interface.interface_name}")
        
        self.setModal(True)
        self.resize(500, 600)
        
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        """Setup the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Scroll area
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Basic Information
        basic_group = QGroupBox("Basic Information")
        basic_layout = QFormLayout(basic_group)
        
        self.hierarchy_edit = QLineEdit()
        self.hierarchy_edit.setReadOnly(True)
        self.hierarchy_edit.setPlaceholderText("Auto-generated on save")
        basic_layout.addRow("Hierarchical ID:", self.hierarchy_edit)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter interface name...")
        basic_layout.addRow("Interface Name*:", self.name_edit)
        
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Enter interface description...")
        self.description_edit.setMaximumHeight(100)
        basic_layout.addRow("Description:", self.description_edit)
        
        scroll_layout.addWidget(basic_group)
        
        # Critical Attributes
        self.critical_attrs = CriticalAttributesWidget()
        scroll_layout.addWidget(self.critical_attrs)
        
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self._save_interface)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(button_box)
        
        # Validation
        self.name_edit.textChanged.connect(self._validate_form)
        self._validate_form()
    
    def _load_data(self):
        """Load data from interface entity."""
        if self.interface:
            self.hierarchy_edit.setText(self.interface.get_hierarchical_id())
            self.name_edit.setText(self.interface.interface_name)
            self.description_edit.setPlainText(self.interface.interface_description or "")
            self.critical_attrs.set_values(self.interface)
        else:
            # Generate placeholder ID
            self.hierarchy_edit.setText("I-?")
    
    def _validate_form(self):
        """Validate form."""
        is_valid = bool(self.name_edit.text().strip())
        
        button_box = self.findChild(QDialogButtonBox)
        if button_box:
            save_button = button_box.button(QDialogButtonBox.Save)
            if save_button:
                save_button.setEnabled(is_valid)
    
    def _save_interface(self):
        """Save the interface."""
        try:
            if self.is_new:
                interface = Interface(
                    system_id=self.system_id,
                    interface_name=self.name_edit.text().strip(),
                    interface_description=self.description_edit.toPlainText().strip(),
                    baseline=WORKING_BASELINE
                )
                # Note: hierarchical ID will be auto-generated in the repository
            else:
                interface = self.interface
                interface.interface_name = self.name_edit.text().strip()
                interface.interface_description = self.description_edit.toPlainText().strip()
            
            # Apply critical attributes
            critical_values = self.critical_attrs.get_values()
            for key, value in critical_values.items():
                setattr(interface, key, value)
            
            self.interface_saved.emit(interface)
            
            logger.info(f"Interface {'created' if self.is_new else 'updated'}: {interface.interface_name}")
            self.accept()
            
        except Exception as e:
            logger.error(f"Failed to save interface: {str(e)}")
            QMessageBox.critical(self, "Save Failed", f"Failed to save interface:\n{str(e)}")
    
    def get_interface(self) -> Optional[Interface]:
        """Get the interface entity."""
        return self.interface


class AssetEditDialog(QDialog):
    """
    Dialog for editing asset entities.
    """
    
    asset_saved = Signal(object)  # Emitted when asset is saved
    
    def __init__(self, asset: Optional[Asset] = None, system_id: Optional[int] = None, parent=None):
        """
        Initialize asset edit dialog.
        
        Args:
            asset: Asset to edit (None for new asset)
            system_id: Associated system ID for new assets
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.asset = asset
        self.system_id = system_id
        self.is_new = asset is None
        
        if self.is_new:
            self.setWindowTitle("New Asset")
        else:
            self.setWindowTitle(f"Edit Asset - {asset.asset_name}")
        
        self.setModal(True)
        self.resize(500, 600)
        
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        """Setup the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Scroll area
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Basic Information
        basic_group = QGroupBox("Basic Information")
        basic_layout = QFormLayout(basic_group)
        
        self.hierarchy_edit = QLineEdit()
        self.hierarchy_edit.setReadOnly(True)
        self.hierarchy_edit.setPlaceholderText("Auto-generated on save")
        basic_layout.addRow("Hierarchical ID:", self.hierarchy_edit)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter asset name...")
        basic_layout.addRow("Asset Name*:", self.name_edit)
        
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Enter asset description...")
        self.description_edit.setMaximumHeight(100)
        basic_layout.addRow("Description:", self.description_edit)
        
        scroll_layout.addWidget(basic_group)
        
        # Critical Attributes
        self.critical_attrs = CriticalAttributesWidget()
        scroll_layout.addWidget(self.critical_attrs)
        
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self._save_asset)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(button_box)
        
        # Validation
        self.name_edit.textChanged.connect(self._validate_form)
        self._validate_form()
    
    def _load_data(self):
        """Load data from asset entity."""
        if self.asset:
            self.hierarchy_edit.setText(self.asset.get_hierarchical_id())
            self.name_edit.setText(self.asset.asset_name)
            self.description_edit.setPlainText(self.asset.asset_description or "")
            self.critical_attrs.set_values(self.asset)
        else:
            # Generate placeholder ID
            self.hierarchy_edit.setText("A-?")
    
    def _validate_form(self):
        """Validate form."""
        is_valid = bool(self.name_edit.text().strip())
        
        button_box = self.findChild(QDialogButtonBox)
        if button_box:
            save_button = button_box.button(QDialogButtonBox.Save)
            if save_button:
                save_button.setEnabled(is_valid)
    
    def _save_asset(self):
        """Save the asset."""
        try:
            if self.is_new:
                asset = Asset(
                    system_id=self.system_id,
                    asset_name=self.name_edit.text().strip(),
                    asset_description=self.description_edit.toPlainText().strip(),
                    baseline=WORKING_BASELINE
                )
                # Note: hierarchical ID will be auto-generated in the repository
            else:
                asset = self.asset
                asset.asset_name = self.name_edit.text().strip()
                asset.asset_description = self.description_edit.toPlainText().strip()
            
            # Apply critical attributes
            critical_values = self.critical_attrs.get_values()
            for key, value in critical_values.items():
                setattr(asset, key, value)
            
            self.asset_saved.emit(asset)
            
            logger.info(f"Asset {'created' if self.is_new else 'updated'}: {asset.asset_name}")
            self.accept()
            
        except Exception as e:
            logger.error(f"Failed to save asset: {str(e)}")
            QMessageBox.critical(self, "Save Failed", f"Failed to save asset:\n{str(e)}")
    
    def get_asset(self) -> Optional[Asset]:
        """Get the asset entity."""
        return self.asset


class HazardEditDialog(QDialog):
    """
    Dialog for editing hazard entities.
    """
    
    hazard_saved = Signal(object)  # Emitted when hazard is saved
    
    def __init__(self, hazard: Optional[Hazard] = None, system_id: Optional[int] = None, parent=None):
        """
        Initialize hazard edit dialog.
        
        Args:
            hazard: Hazard to edit (None for new hazard)
            system_id: Associated system ID for new hazards
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.hazard = hazard
        self.system_id = system_id
        self.is_new = hazard is None
        
        if self.is_new:
            self.setWindowTitle("New Hazard")
        else:
            self.setWindowTitle(f"Edit Hazard - {hazard.hazard_name}")
        
        self.setModal(True)
        self.resize(500, 600)
        
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        """Setup the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Scroll area
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Basic Information
        basic_group = QGroupBox("Basic Information")
        basic_layout = QFormLayout(basic_group)
        
        self.hierarchy_edit = QLineEdit()
        self.hierarchy_edit.setReadOnly(True)
        self.hierarchy_edit.setPlaceholderText("Auto-generated on save")
        basic_layout.addRow("Hierarchical ID:", self.hierarchy_edit)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter hazard name...")
        basic_layout.addRow("Hazard Name*:", self.name_edit)
        
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Enter hazard description...")
        self.description_edit.setMaximumHeight(100)
        basic_layout.addRow("Description:", self.description_edit)
        
        scroll_layout.addWidget(basic_group)
        
        # Critical Attributes
        self.critical_attrs = CriticalAttributesWidget()
        scroll_layout.addWidget(self.critical_attrs)
        
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self._save_hazard)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(button_box)
        
        # Validation
        self.name_edit.textChanged.connect(self._validate_form)
        self._validate_form()
    
    def _load_data(self):
        """Load data from hazard entity."""
        if self.hazard:
            self.hierarchy_edit.setText(self.hazard.get_hierarchical_id())
            self.name_edit.setText(self.hazard.hazard_name)
            self.description_edit.setPlainText(self.hazard.hazard_description or "")
            self.critical_attrs.set_values(self.hazard)
        else:
            # Generate placeholder ID
            self.hierarchy_edit.setText("H-?")
    
    def _validate_form(self):
        """Validate form."""
        is_valid = bool(self.name_edit.text().strip())
        
        button_box = self.findChild(QDialogButtonBox)
        if button_box:
            save_button = button_box.button(QDialogButtonBox.Save)
            if save_button:
                save_button.setEnabled(is_valid)
    
    def _save_hazard(self):
        """Save the hazard."""
        try:
            hierarchy_text = self.hierarchy_edit.text().strip()
            parsed_id = HierarchyManager.parse_hierarchical_id(hierarchy_text)
            
            if not parsed_id:
                QMessageBox.warning(self, "Invalid ID", "Please enter a valid hierarchical ID")
                return
            
            if self.is_new:
                hazard = Hazard(
                    type_identifier=parsed_id.type_identifier,
                    level_identifier=parsed_id.level_identifier,
                    sequential_identifier=parsed_id.sequential_identifier,
                    system_hierarchy=hierarchy_text,
                    h_name=self.name_edit.text().strip(),
                    h_description=self.description_edit.toPlainText().strip(),
                    baseline=WORKING_BASELINE
                )
            else:
                hazard = self.hazard
                hazard.h_name = self.name_edit.text().strip()
                hazard.h_description = self.description_edit.toPlainText().strip()
            
            # Apply critical attributes
            critical_values = self.critical_attrs.get_values()
            for key, value in critical_values.items():
                setattr(hazard, key, value)
            
            self.hazard_saved.emit(hazard)
            
            logger.info(f"Hazard {'created' if self.is_new else 'updated'}: {hazard.hazard_name}")
            self.accept()
            
        except Exception as e:
            logger.error(f"Failed to save hazard: {str(e)}")
            QMessageBox.critical(self, "Save Failed", f"Failed to save hazard:\n{str(e)}")
    
    def get_hazard(self) -> Optional[Hazard]:
        """Get the hazard entity."""
        return self.hazard


class LossEditDialog(QDialog):
    """
    Dialog for editing loss entities.
    """
    
    loss_saved = Signal(object)  # Emitted when loss is saved
    
    def __init__(self, loss: Optional[Loss] = None, system_id: Optional[int] = None, parent=None):
        """
        Initialize loss edit dialog.
        
        Args:
            loss: Loss to edit (None for new loss)
            system_id: Associated system ID for new losses
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.loss = loss
        self.system_id = system_id
        self.is_new = loss is None
        
        if self.is_new:
            self.setWindowTitle("New Loss")
        else:
            self.setWindowTitle(f"Edit Loss - {loss.loss_name}")
        
        self.setModal(True)
        self.resize(500, 600)
        
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        """Setup the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Scroll area
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Basic Information
        basic_group = QGroupBox("Basic Information")
        basic_layout = QFormLayout(basic_group)
        
        self.hierarchy_edit = QLineEdit()
        self.hierarchy_edit.setReadOnly(True)
        self.hierarchy_edit.setPlaceholderText("Auto-generated on save")
        basic_layout.addRow("Hierarchical ID:", self.hierarchy_edit)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter loss name...")
        basic_layout.addRow("Loss Name*:", self.name_edit)
        
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Enter loss description...")
        self.description_edit.setMaximumHeight(100)
        basic_layout.addRow("Description:", self.description_edit)
        
        scroll_layout.addWidget(basic_group)
        
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self._save_loss)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(button_box)
        
        # Validation
        self.name_edit.textChanged.connect(self._validate_form)
        self._validate_form()
    
    def _load_data(self):
        """Load data from loss entity."""
        if self.loss:
            self.hierarchy_edit.setText(self.loss.get_hierarchical_id())
            self.name_edit.setText(self.loss.loss_name)
            self.description_edit.setPlainText(self.loss.loss_description or "")
        else:
            # Generate placeholder ID
            self.hierarchy_edit.setText("L-?")
    
    def _validate_form(self):
        """Validate form."""
        is_valid = bool(self.name_edit.text().strip())
        
        button_box = self.findChild(QDialogButtonBox)
        if button_box:
            save_button = button_box.button(QDialogButtonBox.Save)
            if save_button:
                save_button.setEnabled(is_valid)
    
    def _save_loss(self):
        """Save the loss."""
        try:
            hierarchy_text = self.hierarchy_edit.text().strip()
            parsed_id = HierarchyManager.parse_hierarchical_id(hierarchy_text)
            
            if not parsed_id:
                QMessageBox.warning(self, "Invalid ID", "Please enter a valid hierarchical ID")
                return
            
            if self.is_new:
                loss = Loss(
                    type_identifier=parsed_id.type_identifier,
                    level_identifier=parsed_id.level_identifier,
                    sequential_identifier=parsed_id.sequential_identifier,
                    system_hierarchy=hierarchy_text,
                    l_name=self.name_edit.text().strip(),
                    l_description=self.description_edit.toPlainText().strip(),
                    loss_description=self.description_edit.toPlainText().strip(),
                    baseline=WORKING_BASELINE
                )
            else:
                loss = self.loss
                loss.l_name = self.name_edit.text().strip()
                loss.l_description = self.description_edit.toPlainText().strip()
                loss.loss_description = self.description_edit.toPlainText().strip()
            
            self.loss_saved.emit(loss)
            
            logger.info(f"Loss {'created' if self.is_new else 'updated'}: {loss.loss_name}")
            self.accept()
            
        except Exception as e:
            logger.error(f"Failed to save loss: {str(e)}")
            QMessageBox.critical(self, "Save Failed", f"Failed to save loss:\n{str(e)}")
    
    def get_loss(self) -> Optional[Loss]:
        """Get the loss entity."""
        return self.loss


class ControlStructureEditDialog(QDialog):
    """
    Dialog for editing control structure entities.
    """
    
    control_structure_saved = Signal(object)  # Emitted when control structure is saved
    
    def __init__(self, control_structure: Optional[ControlStructure] = None, system_id: Optional[int] = None, parent=None):
        """
        Initialize control structure edit dialog.
        
        Args:
            control_structure: Control structure to edit (None for new control structure)
            system_id: Associated system ID for new control structures
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.control_structure = control_structure
        self.system_id = system_id
        self.is_new = control_structure is None
        
        if self.is_new:
            self.setWindowTitle("New Control Structure")
        else:
            self.setWindowTitle(f"Edit Control Structure - {control_structure.structure_name}")
        
        self.setModal(True)
        self.resize(500, 600)
        
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        """Setup the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Scroll area
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Basic Information
        basic_group = QGroupBox("Basic Information")
        basic_layout = QFormLayout(basic_group)
        
        self.hierarchy_edit = QLineEdit()
        self.hierarchy_edit.setReadOnly(True)
        self.hierarchy_edit.setPlaceholderText("Auto-generated on save")
        basic_layout.addRow("Hierarchical ID:", self.hierarchy_edit)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter control structure name...")
        basic_layout.addRow("Structure Name*:", self.name_edit)
        
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Enter control structure description...")
        self.description_edit.setMaximumHeight(100)
        basic_layout.addRow("Description:", self.description_edit)
        
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
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self._save_control_structure)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(button_box)
        
        # Validation
        self.name_edit.textChanged.connect(self._validate_form)
        self._validate_form()
    
    def _load_data(self):
        """Load data from control structure entity."""
        if self.control_structure:
            self.hierarchy_edit.setText(self.control_structure.get_hierarchical_id())
            self.name_edit.setText(self.control_structure.structure_name)
            self.description_edit.setPlainText(self.control_structure.structure_description or "")
            self.diagram_url_edit.setText(self.control_structure.diagram_url or "")
            self.critical_attrs.set_values(self.control_structure)
        else:
            # Generate placeholder ID
            self.hierarchy_edit.setText("CS-?")
    
    def _validate_form(self):
        """Validate form."""
        is_valid = bool(self.name_edit.text().strip())
        
        button_box = self.findChild(QDialogButtonBox)
        if button_box:
            save_button = button_box.button(QDialogButtonBox.Save)
            if save_button:
                save_button.setEnabled(is_valid)
    
    def _save_control_structure(self):
        """Save the control structure."""
        try:
            if self.is_new:
                control_structure = ControlStructure(
                    system_id=self.system_id,
                    structure_name=self.name_edit.text().strip(),
                    structure_description=self.description_edit.toPlainText().strip(),
                    diagram_url=self.diagram_url_edit.text().strip(),
                    baseline=WORKING_BASELINE
                )
                # Note: hierarchical ID will be auto-generated in the repository
            else:
                control_structure = self.control_structure
                control_structure.structure_name = self.name_edit.text().strip()
                control_structure.structure_description = self.description_edit.toPlainText().strip()
                control_structure.diagram_url = self.diagram_url_edit.text().strip()
            
            # Apply critical attributes
            critical_values = self.critical_attrs.get_values()
            for key, value in critical_values.items():
                setattr(control_structure, key, value)
            
            self.control_structure_saved.emit(control_structure)
            
            logger.info(f"Control Structure {'created' if self.is_new else 'updated'}: {control_structure.structure_name}")
            self.accept()
            
        except Exception as e:
            logger.error(f"Failed to save control structure: {str(e)}")
            QMessageBox.critical(self, "Save Failed", f"Failed to save control structure:\n{str(e)}")
    
    def get_control_structure(self) -> Optional[ControlStructure]:
        """Get the control structure entity."""
        return self.control_structure


class ControllerEditDialog(QDialog):
    """
    Dialog for editing controller entities.
    """
    
    controller_saved = Signal(object)  # Emitted when controller is saved
    
    def __init__(self, controller: Optional[Controller] = None, system_id: Optional[int] = None, parent=None):
        """
        Initialize controller edit dialog.
        
        Args:
            controller: Controller to edit (None for new controller)
            system_id: Associated system ID for new controllers
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.controller = controller
        self.system_id = system_id
        self.is_new = controller is None
        
        if self.is_new:
            self.setWindowTitle("New Controller")
        else:
            self.setWindowTitle(f"Edit Controller - {controller.controller_name}")
        
        self.setModal(True)
        self.resize(500, 600)
        
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        """Setup the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Scroll area
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Basic Information
        basic_group = QGroupBox("Basic Information")
        basic_layout = QFormLayout(basic_group)
        
        self.hierarchy_edit = QLineEdit()
        self.hierarchy_edit.setReadOnly(True)
        self.hierarchy_edit.setPlaceholderText("Auto-generated on save")
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
        
        scroll_layout.addWidget(basic_group)
        
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self._save_controller)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(button_box)
        
        # Validation
        self.name_edit.textChanged.connect(self._validate_form)
        self._validate_form()
    
    def _load_data(self):
        """Load data from controller entity."""
        if self.controller:
            self.hierarchy_edit.setText(self.controller.get_hierarchical_id())
            self.short_id_edit.setText(self.controller.short_text_identifier or "")
            self.name_edit.setText(self.controller.controller_name)
            self.description_edit.setPlainText(self.controller.controller_description or "")
        else:
            # Generate placeholder ID
            self.hierarchy_edit.setText("C-?")
    
    def _validate_form(self):
        """Validate form."""
        is_valid = bool(self.name_edit.text().strip())
        
        button_box = self.findChild(QDialogButtonBox)
        if button_box:
            save_button = button_box.button(QDialogButtonBox.Save)
            if save_button:
                save_button.setEnabled(is_valid)
    
    def _save_controller(self):
        """Save the controller."""
        try:
            if self.is_new:
                controller = Controller(
                    system_id=self.system_id,
                    short_text_identifier=self.short_id_edit.text().strip(),
                    controller_name=self.name_edit.text().strip(),
                    controller_description=self.description_edit.toPlainText().strip(),
                    baseline=WORKING_BASELINE
                )
                # Note: hierarchical ID will be auto-generated in the repository
            else:
                controller = self.controller
                controller.short_text_identifier = self.short_id_edit.text().strip()
                controller.controller_name = self.name_edit.text().strip()
                controller.controller_description = self.description_edit.toPlainText().strip()
            
            self.controller_saved.emit(controller)
            
            logger.info(f"Controller {'created' if self.is_new else 'updated'}: {controller.controller_name}")
            self.accept()
            
        except Exception as e:
            logger.error(f"Failed to save controller: {str(e)}")
            QMessageBox.critical(self, "Save Failed", f"Failed to save controller:\n{str(e)}")
    
    def get_controller(self) -> Optional[Controller]:
        """Get the controller entity."""
        return self.controller