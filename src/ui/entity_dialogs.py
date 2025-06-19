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

from ..database.entities import System, Function, Requirement, BaseEntity
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
    
    def __init__(self, system: Optional[System] = None, parent_system: Optional[System] = None, parent=None):
        """
        Initialize system edit dialog.
        
        Args:
            system: System to edit (None for new system)
            parent_system: Parent system for new child systems
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.system = system
        self.parent_system = parent_system
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
        
        # Hierarchical ID (read-only for existing systems)
        self.hierarchy_edit = QLineEdit()
        if not self.is_new:
            self.hierarchy_edit.setReadOnly(True)
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
                # TODO: Generate child ID based on parent
                self.hierarchy_edit.setText("S-?.?")
            else:
                # TODO: Generate root ID
                self.hierarchy_edit.setText("S-?")
    
    def _validate_form(self):
        """Validate form and enable/disable save button."""
        is_valid = True
        
        # Check required fields
        if not self.name_edit.text().strip():
            is_valid = False
        
        if self.is_new and not self.hierarchy_edit.text().strip():
            is_valid = False
        
        # Validate hierarchical ID format
        if self.hierarchy_edit.text().strip():
            parsed_id = HierarchyManager.parse_hierarchical_id(self.hierarchy_edit.text())
            if not parsed_id:
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
            # Validate hierarchical ID
            hierarchy_text = self.hierarchy_edit.text().strip()
            parsed_id = HierarchyManager.parse_hierarchical_id(hierarchy_text)
            
            if not parsed_id:
                QMessageBox.warning(self, "Invalid ID", "Please enter a valid hierarchical ID (e.g., S-1 or S-1.2)")
                return
            
            # Create or update system
            if self.is_new:
                system = System(
                    type_identifier=parsed_id.type_identifier,
                    level_identifier=parsed_id.level_identifier,
                    sequential_identifier=parsed_id.sequential_identifier,
                    system_hierarchy=hierarchy_text,
                    system_name=self.name_edit.text().strip(),
                    system_description=self.description_edit.toPlainText().strip(),
                    parent_system_id=self.parent_system.id if self.parent_system else None,
                    baseline=WORKING_BASELINE
                )
            else:
                system = self.system
                system.system_name = self.name_edit.text().strip()
                system.system_description = self.description_edit.toPlainText().strip()
            
            # Apply critical attributes
            critical_values = self.critical_attrs.get_values()
            for key, value in critical_values.items():
                setattr(system, key, value)
            
            # Emit signal
            self.system_saved.emit(system)
            
            logger.info(f"System {'created' if self.is_new else 'updated'}: {system.system_name}")
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
        if not self.is_new:
            self.hierarchy_edit.setReadOnly(True)
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
            # Generate placeholder ID
            self.hierarchy_edit.setText("F-?")
    
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
            hierarchy_text = self.hierarchy_edit.text().strip()
            parsed_id = HierarchyManager.parse_hierarchical_id(hierarchy_text)
            
            if not parsed_id:
                QMessageBox.warning(self, "Invalid ID", "Please enter a valid hierarchical ID")
                return
            
            if self.is_new:
                function = Function(
                    type_identifier=parsed_id.type_identifier,
                    level_identifier=parsed_id.level_identifier,
                    sequential_identifier=parsed_id.sequential_identifier,
                    system_hierarchy=hierarchy_text,
                    system_id=self.system_id,
                    short_text_identifier=self.short_id_edit.text().strip(),
                    function_name=self.name_edit.text().strip(),
                    function_description=self.description_edit.toPlainText().strip(),
                    baseline=WORKING_BASELINE
                )
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
        self.resize(600, 800)
        
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
        if not self.is_new:
            self.hierarchy_edit.setReadOnly(True)
        basic_layout.addRow("Hierarchical ID:", self.hierarchy_edit)
        
        self.alphanumeric_edit = QLineEdit()
        self.alphanumeric_edit.setPlaceholderText("e.g., REQ-001")
        basic_layout.addRow("Alphanumeric ID:", self.alphanumeric_edit)
        
        self.short_id_edit = QLineEdit()
        self.short_id_edit.setPlaceholderText("Short text identifier...")
        basic_layout.addRow("Short ID:", self.short_id_edit)
        
        self.requirement_text = QTextEdit()
        self.requirement_text.setPlaceholderText("Enter requirement text...")
        self.requirement_text.setMinimumHeight(100)
        basic_layout.addRow("Requirement Text*:", self.requirement_text)
        
        scroll_layout.addWidget(basic_group)
        
        # Verification Information
        verification_group = QGroupBox("Verification Information")
        verification_layout = QFormLayout(verification_group)
        
        self.verification_method_combo = QComboBox()
        self.verification_method_combo.addItems(VERIFICATION_METHODS)
        verification_layout.addRow("Verification Method:", self.verification_method_combo)
        
        self.verification_statement = QTextEdit()
        self.verification_statement.setPlaceholderText("Enter verification statement...")
        self.verification_statement.setMaximumHeight(80)
        verification_layout.addRow("Verification Statement:", self.verification_statement)
        
        self.imperative_combo = QComboBox()
        self.imperative_combo.addItems(IMPERATIVES)
        verification_layout.addRow("Imperative:", self.imperative_combo)
        
        self.actor_edit = QLineEdit()
        self.actor_edit.setPlaceholderText("Actor/Subject...")
        verification_layout.addRow("Actor:", self.actor_edit)
        
        self.action_edit = QLineEdit()
        self.action_edit.setPlaceholderText("Action/Verb...")
        verification_layout.addRow("Action:", self.action_edit)
        
        scroll_layout.addWidget(verification_group)
        
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
        self.requirement_text.textChanged.connect(self._validate_form)
        self._validate_form()
    
    def _load_data(self):
        """Load data from requirement entity."""
        if self.requirement:
            self.hierarchy_edit.setText(self.requirement.get_hierarchical_id())
            self.alphanumeric_edit.setText(self.requirement.alphanumeric_identifier or "")
            self.short_id_edit.setText(self.requirement.short_text_identifier or "")
            self.requirement_text.setPlainText(self.requirement.requirement_text)
            
            # Set verification method
            method_index = self.verification_method_combo.findText(self.requirement.verification_method)
            if method_index >= 0:
                self.verification_method_combo.setCurrentIndex(method_index)
            
            self.verification_statement.setPlainText(self.requirement.verification_statement or "")
            
            # Set imperative
            imperative_index = self.imperative_combo.findText(self.requirement.imperative)
            if imperative_index >= 0:
                self.imperative_combo.setCurrentIndex(imperative_index)
            
            self.actor_edit.setText(self.requirement.actor or "")
            self.action_edit.setText(self.requirement.action or "")
            
            self.critical_attrs.set_values(self.requirement)
        else:
            # Generate placeholder ID
            self.hierarchy_edit.setText("R-?")
    
    def _validate_form(self):
        """Validate form."""
        is_valid = bool(self.requirement_text.toPlainText().strip())
        
        button_box = self.findChild(QDialogButtonBox)
        if button_box:
            save_button = button_box.button(QDialogButtonBox.Save)
            if save_button:
                save_button.setEnabled(is_valid)
    
    def _save_requirement(self):
        """Save the requirement."""
        try:
            hierarchy_text = self.hierarchy_edit.text().strip()
            parsed_id = HierarchyManager.parse_hierarchical_id(hierarchy_text)
            
            if not parsed_id:
                QMessageBox.warning(self, "Invalid ID", "Please enter a valid hierarchical ID")
                return
            
            if self.is_new:
                requirement = Requirement(
                    type_identifier=parsed_id.type_identifier,
                    level_identifier=parsed_id.level_identifier,
                    sequential_identifier=parsed_id.sequential_identifier,
                    system_hierarchy=hierarchy_text,
                    system_id=self.system_id,
                    alphanumeric_identifier=self.alphanumeric_edit.text().strip(),
                    short_text_identifier=self.short_id_edit.text().strip(),
                    requirement_text=self.requirement_text.toPlainText().strip(),
                    verification_method=self.verification_method_combo.currentText(),
                    verification_statement=self.verification_statement.toPlainText().strip(),
                    imperative=self.imperative_combo.currentText(),
                    actor=self.actor_edit.text().strip(),
                    action=self.action_edit.text().strip(),
                    baseline=WORKING_BASELINE
                )
            else:
                requirement = self.requirement
                requirement.alphanumeric_identifier = self.alphanumeric_edit.text().strip()
                requirement.short_text_identifier = self.short_id_edit.text().strip()
                requirement.requirement_text = self.requirement_text.toPlainText().strip()
                requirement.verification_method = self.verification_method_combo.currentText()
                requirement.verification_statement = self.verification_statement.toPlainText().strip()
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