"""
Warnings tab widget for displaying validation issues.
Implements the warnings tab as specified in the SRS.
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                               QTableWidgetItem, QHeaderView, QPushButton, QLabel,
                               QComboBox, QProgressBar, QTextEdit, QSplitter,
                               QGroupBox, QGridLayout, QFrame)
from PySide6.QtCore import Qt, QTimer, Signal, QThread, pyqtSignal
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor
from typing import List, Optional, Dict, Any
import logging

from ..validation.engine import ValidationEngine, ValidationIssue, ValidationSeverity
from ..database.connection import DatabaseConnection


logger = logging.getLogger(__name__)


class ValidationWorker(QThread):
    """Worker thread for running validation in background."""
    
    validation_finished = pyqtSignal(list)  # List of ValidationIssue
    validation_progress = pyqtSignal(str)    # Progress message
    validation_error = pyqtSignal(str)       # Error message
    
    def __init__(self, connection: DatabaseConnection, system_id: Optional[int] = None):
        super().__init__()
        self.connection = connection
        self.system_id = system_id
        self.validation_engine = ValidationEngine(connection)
    
    def run(self):
        """Run validation in background thread."""
        try:
            self.validation_progress.emit("Starting validation...")
            
            if self.system_id:
                self.validation_progress.emit(f"Validating system ID {self.system_id}...")
                issues = self.validation_engine.validate_system(self.system_id)
            else:
                self.validation_progress.emit("Validating all systems...")
                issues = self.validation_engine.validate_all()
            
            self.validation_progress.emit(f"Validation complete: {len(issues)} issues found")
            self.validation_finished.emit(issues)
            
        except Exception as e:
            logger.error(f"Validation error: {e}")
            self.validation_error.emit(str(e))


class ValidationIssueTableWidget(QTableWidget):
    """Table widget for displaying validation issues."""
    
    issue_selected = Signal(ValidationIssue)
    
    def __init__(self):
        super().__init__()
        self.setup_table()
        self.issues = []
    
    def setup_table(self):
        """Set up the table columns and appearance."""
        columns = [
            ("Severity", 80),
            ("Entity Type", 100),
            ("Entity Name", 150),
            ("Issue Type", 120),
            ("Message", 300),
            ("Hierarchical ID", 120),
            ("Suggestion", 250)
        ]
        
        self.setColumnCount(len(columns))
        self.setHorizontalHeaderLabels([col[0] for col in columns])
        
        # Set column widths
        header = self.horizontalHeader()
        for i, (name, width) in enumerate(columns):
            header.resizeSection(i, width)
        
        header.setStretchLastSection(True)
        
        # Set table properties
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setSelectionMode(QTableWidget.SingleSelection)
        self.setSortingEnabled(True)
        
        # Connect signals
        self.cellDoubleClicked.connect(self._on_row_double_clicked)
    
    def populate_issues(self, issues: List[ValidationIssue]):
        """Populate the table with validation issues."""
        self.issues = issues
        self.setRowCount(len(issues))
        
        for row, issue in enumerate(issues):
            # Severity (with color coding)
            severity_item = QTableWidgetItem(issue.severity.value.title())
            severity_item.setData(Qt.UserRole, issue)
            
            # Color code by severity
            if issue.severity == ValidationSeverity.ERROR:
                severity_item.setBackground(QColor(255, 200, 200))  # Light red
            elif issue.severity == ValidationSeverity.WARNING:
                severity_item.setBackground(QColor(255, 255, 200))  # Light yellow
            else:
                severity_item.setBackground(QColor(200, 255, 200))  # Light green
            
            self.setItem(row, 0, severity_item)
            
            # Entity Type
            self.setItem(row, 1, QTableWidgetItem(issue.entity_type))
            
            # Entity Name
            self.setItem(row, 2, QTableWidgetItem(issue.entity_name))
            
            # Issue Type
            issue_type_item = QTableWidgetItem(issue.issue_type.replace('_', ' ').title())
            self.setItem(row, 3, issue_type_item)
            
            # Message
            self.setItem(row, 4, QTableWidgetItem(issue.message))
            
            # Hierarchical ID
            hierarchical_id = issue.hierarchical_id or ""
            self.setItem(row, 5, QTableWidgetItem(hierarchical_id))
            
            # Suggestion
            suggestion = issue.suggestion or ""
            self.setItem(row, 6, QTableWidgetItem(suggestion))
        
        # Sort by severity (errors first)
        self.sortByColumn(0, Qt.AscendingOrder)
    
    def _on_row_double_clicked(self, row: int, column: int):
        """Handle double-click on table row."""
        if 0 <= row < len(self.issues):
            issue = self.issues[row]
            self.issue_selected.emit(issue)
    
    def filter_by_severity(self, severity: Optional[ValidationSeverity]):
        """Filter issues by severity level."""
        for row in range(self.rowCount()):
            item = self.item(row, 0)
            if item and item.data(Qt.UserRole):
                issue = item.data(Qt.UserRole)
                if severity is None or issue.severity == severity:
                    self.showRow(row)
                else:
                    self.hideRow(row)
    
    def filter_by_entity_type(self, entity_type: Optional[str]):
        """Filter issues by entity type."""
        for row in range(self.rowCount()):
            entity_type_item = self.item(row, 1)
            if entity_type_item:
                if entity_type is None or entity_type_item.text() == entity_type:
                    self.showRow(row)
                else:
                    self.hideRow(row)
    
    def get_selected_issue(self) -> Optional[ValidationIssue]:
        """Get the currently selected validation issue."""
        current_row = self.currentRow()
        if 0 <= current_row < len(self.issues):
            return self.issues[current_row]
        return None


class ValidationSummaryWidget(QWidget):
    """Widget displaying validation summary statistics."""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the summary UI."""
        layout = QGridLayout(self)
        
        # Title
        title_label = QLabel("Validation Summary")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title_label, 0, 0, 1, 4)
        
        # Summary statistics labels
        self.total_label = QLabel("Total Issues: 0")
        self.errors_label = QLabel("Errors: 0")
        self.warnings_label = QLabel("Warnings: 0")
        self.info_label = QLabel("Info: 0")
        
        # Style labels with colors
        self.errors_label.setStyleSheet("color: #d32f2f; font-weight: bold;")
        self.warnings_label.setStyleSheet("color: #f57c00; font-weight: bold;")
        self.info_label.setStyleSheet("color: #388e3c; font-weight: bold;")
        
        layout.addWidget(self.total_label, 1, 0)
        layout.addWidget(self.errors_label, 1, 1)
        layout.addWidget(self.warnings_label, 1, 2)
        layout.addWidget(self.info_label, 1, 3)
        
        # Entity type breakdown
        self.entity_breakdown_label = QLabel("Most Issues: N/A")
        layout.addWidget(self.entity_breakdown_label, 2, 0, 1, 4)
    
    def update_summary(self, summary: Dict[str, Any]):
        """Update the summary display with new statistics."""
        total = summary.get('total_issues', 0)
        by_severity = summary.get('by_severity', {})
        by_entity_type = summary.get('by_entity_type', {})
        
        self.total_label.setText(f"Total Issues: {total}")
        self.errors_label.setText(f"Errors: {by_severity.get('error', 0)}")
        self.warnings_label.setText(f"Warnings: {by_severity.get('warning', 0)}")
        self.info_label.setText(f"Info: {by_severity.get('info', 0)}")
        
        # Find entity type with most issues
        if by_entity_type:
            max_entity = max(by_entity_type.items(), key=lambda x: x[1])
            self.entity_breakdown_label.setText(f"Most Issues: {max_entity[0]} ({max_entity[1]})")
        else:
            self.entity_breakdown_label.setText("Most Issues: N/A")


class ValidationDetailWidget(QWidget):
    """Widget showing details of selected validation issue."""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.current_issue = None
    
    def setup_ui(self):
        """Set up the detail UI."""
        layout = QVBoxLayout(self)
        
        # Group box for issue details
        details_group = QGroupBox("Issue Details")
        details_layout = QGridLayout(details_group)
        
        # Detail labels
        self.severity_label = QLabel("Severity: N/A")
        self.entity_label = QLabel("Entity: N/A")
        self.issue_type_label = QLabel("Issue Type: N/A")
        self.hierarchical_id_label = QLabel("Hierarchical ID: N/A")
        
        details_layout.addWidget(QLabel("Severity:"), 0, 0)
        details_layout.addWidget(self.severity_label, 0, 1)
        details_layout.addWidget(QLabel("Entity:"), 1, 0)
        details_layout.addWidget(self.entity_label, 1, 1)
        details_layout.addWidget(QLabel("Issue Type:"), 2, 0)
        details_layout.addWidget(self.issue_type_label, 2, 1)
        details_layout.addWidget(QLabel("Hierarchical ID:"), 3, 0)
        details_layout.addWidget(self.hierarchical_id_label, 3, 1)
        
        layout.addWidget(details_group)
        
        # Message text
        message_group = QGroupBox("Message")
        message_layout = QVBoxLayout(message_group)
        self.message_text = QTextEdit()
        self.message_text.setReadOnly(True)
        self.message_text.setMaximumHeight(80)
        message_layout.addWidget(self.message_text)
        layout.addWidget(message_group)
        
        # Suggestion text
        suggestion_group = QGroupBox("Suggestion")
        suggestion_layout = QVBoxLayout(suggestion_group)
        self.suggestion_text = QTextEdit()
        self.suggestion_text.setReadOnly(True)
        self.suggestion_text.setMaximumHeight(80)
        suggestion_layout.addWidget(self.suggestion_text)
        layout.addWidget(suggestion_group)
        
        # Navigation button
        self.navigate_button = QPushButton("Navigate to Entity")
        self.navigate_button.setEnabled(False)
        layout.addWidget(self.navigate_button)
    
    def show_issue(self, issue: ValidationIssue):
        """Display details of a validation issue."""
        self.current_issue = issue
        
        # Update labels
        self.severity_label.setText(issue.severity.value.title())
        self.entity_label.setText(f"{issue.entity_type}: {issue.entity_name}")
        self.issue_type_label.setText(issue.issue_type.replace('_', ' ').title())
        self.hierarchical_id_label.setText(issue.hierarchical_id or "N/A")
        
        # Color code severity
        if issue.severity == ValidationSeverity.ERROR:
            self.severity_label.setStyleSheet("color: #d32f2f; font-weight: bold;")
        elif issue.severity == ValidationSeverity.WARNING:
            self.severity_label.setStyleSheet("color: #f57c00; font-weight: bold;")
        else:
            self.severity_label.setStyleSheet("color: #388e3c; font-weight: bold;")
        
        # Update text areas
        self.message_text.setPlainText(issue.message)
        self.suggestion_text.setPlainText(issue.suggestion or "No suggestion available")
        
        # Enable navigation if entity ID is available
        self.navigate_button.setEnabled(issue.entity_id is not None)
    
    def clear_details(self):
        """Clear the detail display."""
        self.current_issue = None
        self.severity_label.setText("Severity: N/A")
        self.entity_label.setText("Entity: N/A")
        self.issue_type_label.setText("Issue Type: N/A")
        self.hierarchical_id_label.setText("Hierarchical ID: N/A")
        self.message_text.clear()
        self.suggestion_text.clear()
        self.navigate_button.setEnabled(False)


class WarningsTab(QWidget):
    """Main warnings tab widget implementing the SRS warnings tab functionality."""
    
    navigate_to_entity = Signal(str, int)  # entity_type, entity_id
    
    def __init__(self, connection: DatabaseConnection):
        super().__init__()
        self.connection = connection
        self.validation_engine = ValidationEngine(connection)
        self.current_system_id = None
        self.validation_worker = None
        
        self.setup_ui()
        self.connect_signals()
        
        logger.info("Warnings tab initialized")
    
    def setup_ui(self):
        """Set up the warnings tab UI."""
        layout = QVBoxLayout(self)
        
        # Controls section
        controls_frame = QFrame()
        controls_layout = QHBoxLayout(controls_frame)
        
        # Validation controls
        self.validate_button = QPushButton("Run Validation")
        self.validate_all_button = QPushButton("Validate All")
        self.refresh_button = QPushButton("Refresh")
        
        controls_layout.addWidget(self.validate_button)
        controls_layout.addWidget(self.validate_all_button)
        controls_layout.addWidget(self.refresh_button)
        controls_layout.addStretch()
        
        # Filter controls
        controls_layout.addWidget(QLabel("Filter by Severity:"))
        self.severity_filter = QComboBox()
        self.severity_filter.addItems(["All", "Error", "Warning", "Info"])
        controls_layout.addWidget(self.severity_filter)
        
        controls_layout.addWidget(QLabel("Filter by Entity:"))
        self.entity_filter = QComboBox()
        self.entity_filter.addItem("All")
        controls_layout.addWidget(self.entity_filter)
        
        layout.addWidget(controls_frame)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Ready to validate")
        layout.addWidget(self.status_label)
        
        # Main content splitter
        main_splitter = QSplitter(Qt.Horizontal)
        
        # Left side: Issues table and summary
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # Summary widget
        self.summary_widget = ValidationSummaryWidget()
        left_layout.addWidget(self.summary_widget)
        
        # Issues table
        self.issues_table = ValidationIssueTableWidget()
        left_layout.addWidget(self.issues_table)
        
        main_splitter.addWidget(left_widget)
        
        # Right side: Issue details
        self.detail_widget = ValidationDetailWidget()
        main_splitter.addWidget(self.detail_widget)
        
        # Set splitter proportions
        main_splitter.setSizes([600, 300])
        
        layout.addWidget(main_splitter)
    
    def connect_signals(self):
        """Connect widget signals."""
        self.validate_button.clicked.connect(self.run_validation)
        self.validate_all_button.clicked.connect(self.run_validation_all)
        self.refresh_button.clicked.connect(self.refresh_validation)
        
        self.severity_filter.currentTextChanged.connect(self.apply_severity_filter)
        self.entity_filter.currentTextChanged.connect(self.apply_entity_filter)
        
        self.issues_table.issue_selected.connect(self.detail_widget.show_issue)
        self.issues_table.issue_selected.connect(self._on_issue_selected)
        
        self.detail_widget.navigate_button.clicked.connect(self._navigate_to_current_entity)
    
    def set_current_system(self, system_id: Optional[int]):
        """Set the current system for validation."""
        self.current_system_id = system_id
        
        if system_id:
            self.validate_button.setText(f"Validate System {system_id}")
            self.validate_button.setEnabled(True)
        else:
            self.validate_button.setText("Validate System")
            self.validate_button.setEnabled(False)
    
    def run_validation(self):
        """Run validation for current system."""
        if not self.current_system_id:
            self.status_label.setText("No system selected for validation")
            return
        
        self._start_validation(self.current_system_id)
    
    def run_validation_all(self):
        """Run validation for all systems."""
        self._start_validation(None)
    
    def refresh_validation(self):
        """Refresh the current validation results."""
        if self.current_system_id:
            self.run_validation()
        else:
            self.run_validation_all()
    
    def _start_validation(self, system_id: Optional[int]):
        """Start validation in background thread."""
        if self.validation_worker and self.validation_worker.isRunning():
            return  # Already running
        
        self.validation_worker = ValidationWorker(self.connection, system_id)
        self.validation_worker.validation_finished.connect(self._on_validation_finished)
        self.validation_worker.validation_progress.connect(self._on_validation_progress)
        self.validation_worker.validation_error.connect(self._on_validation_error)
        
        # Update UI for validation start
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.validate_button.setEnabled(False)
        self.validate_all_button.setEnabled(False)
        self.refresh_button.setEnabled(False)
        
        self.validation_worker.start()
    
    def _on_validation_finished(self, issues: List[ValidationIssue]):
        """Handle validation completion."""
        logger.info(f"Validation completed with {len(issues)} issues")
        
        # Update UI
        self.progress_bar.setVisible(False)
        self.validate_button.setEnabled(True)
        self.validate_all_button.setEnabled(True)
        self.refresh_button.setEnabled(True)
        
        # Update issues table
        self.issues_table.populate_issues(issues)
        
        # Update summary
        summary = self.validation_engine.get_validation_summary(issues)
        self.summary_widget.update_summary(summary)
        
        # Update entity filter
        self._update_entity_filter(summary.get('by_entity_type', {}))
        
        # Update status
        if issues:
            error_count = summary['by_severity'].get('error', 0)
            warning_count = summary['by_severity'].get('warning', 0)
            self.status_label.setText(
                f"Validation complete: {len(issues)} issues found "
                f"({error_count} errors, {warning_count} warnings)"
            )
        else:
            self.status_label.setText("Validation complete: No issues found")
        
        # Clear detail view
        self.detail_widget.clear_details()
    
    def _on_validation_progress(self, message: str):
        """Handle validation progress updates."""
        self.status_label.setText(message)
    
    def _on_validation_error(self, error_message: str):
        """Handle validation errors."""
        logger.error(f"Validation error: {error_message}")
        
        # Update UI
        self.progress_bar.setVisible(False)
        self.validate_button.setEnabled(True)
        self.validate_all_button.setEnabled(True)
        self.refresh_button.setEnabled(True)
        
        self.status_label.setText(f"Validation error: {error_message}")
    
    def _update_entity_filter(self, entity_types: Dict[str, int]):
        """Update the entity filter combo box."""
        self.entity_filter.clear()
        self.entity_filter.addItem("All")
        
        for entity_type in sorted(entity_types.keys()):
            self.entity_filter.addItem(entity_type)
    
    def apply_severity_filter(self, severity_text: str):
        """Apply severity filter to issues table."""
        if severity_text == "All":
            self.issues_table.filter_by_severity(None)
        else:
            severity_map = {
                "Error": ValidationSeverity.ERROR,
                "Warning": ValidationSeverity.WARNING,
                "Info": ValidationSeverity.INFO
            }
            severity = severity_map.get(severity_text)
            self.issues_table.filter_by_severity(severity)
    
    def apply_entity_filter(self, entity_type: str):
        """Apply entity type filter to issues table."""
        if entity_type == "All":
            self.issues_table.filter_by_entity_type(None)
        else:
            self.issues_table.filter_by_entity_type(entity_type)
    
    def _on_issue_selected(self, issue: ValidationIssue):
        """Handle issue selection in table."""
        logger.debug(f"Issue selected: {issue.entity_type} - {issue.message}")
    
    def _navigate_to_current_entity(self):
        """Navigate to the currently selected entity."""
        issue = self.detail_widget.current_issue
        if issue and issue.entity_id:
            self.navigate_to_entity.emit(issue.entity_type, issue.entity_id)
            logger.info(f"Navigating to {issue.entity_type} with ID {issue.entity_id}")