"""
Baseline management dialog classes for STPA Tool
Contains dialogs for baseline creation, loading, and management.
"""

import os
from datetime import datetime
from typing import Optional, List, Dict, Any

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QTableWidget, QTableWidgetItem, 
    QHeaderView, QMessageBox, QDialogButtonBox, QGroupBox,
    QGridLayout, QComboBox, QProgressDialog, QApplication,
    QSplitter, QWidget, QTabWidget
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont

from ..database.baseline_manager import BaselineManager
from ..database.connection import DatabaseConnection
from ..log_config.config import get_logger

logger = get_logger(__name__)


class BaselineCreationDialog(QDialog):
    """Dialog for creating new baselines."""
    
    def __init__(self, parent=None, baseline_manager: BaselineManager = None):
        super().__init__(parent)
        self.baseline_manager = baseline_manager
        
        self.setWindowTitle("Create Baseline")
        self.setModal(True)
        self.resize(500, 350)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout()
        
        # Baseline info group
        info_group = QGroupBox("Baseline Information")
        info_layout = QGridLayout()
        
        # Name field
        info_layout.addWidget(QLabel("Baseline Name:"), 0, 0)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Leave empty for auto-generated name")
        info_layout.addWidget(self.name_edit, 0, 1)
        
        # Description field
        info_layout.addWidget(QLabel("Description:"), 1, 0, Qt.AlignTop)
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(100)
        self.description_edit.setPlaceholderText("Optional description of this baseline...")
        info_layout.addWidget(self.description_edit, 1, 1)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Preview section
        preview_group = QGroupBox("Current Database Status")
        preview_layout = QVBoxLayout()
        
        self.status_label = QLabel("Loading database information...")
        preview_layout.addWidget(self.status_label)
        
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.button(QDialogButtonBox.Ok).setText("Create Baseline")
        button_box.accepted.connect(self._create_baseline)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
        
        # Load database status
        self._load_database_status()
    
    def _load_database_status(self):
        """Load and display current database status."""
        if not self.baseline_manager:
            self.status_label.setText("No baseline manager available")
            return
        
        try:
            # Get record counts from main tables
            cursor = self.baseline_manager.db_connection.get_cursor()
            
            status_lines = []
            main_tables = [
                ('systems', 'Systems'),
                ('functions', 'Functions'),
                ('requirements', 'Requirements'),
                ('interfaces', 'Interfaces'),
                ('assets', 'Assets'),
                ('hazards', 'Hazards')
            ]
            
            total_records = 0
            for table_name, display_name in main_tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE baseline = 'Working'")
                    count = cursor.fetchone()[0]
                    status_lines.append(f"• {display_name}: {count}")
                    total_records += count
                except:
                    status_lines.append(f"• {display_name}: 0")
            
            status_lines.insert(0, f"Total Working Records: {total_records}")
            status_lines.append("")
            status_lines.append(f"Baseline will be created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            self.status_label.setText("\n".join(status_lines))
            
        except Exception as e:
            logger.error(f"Error loading database status: {str(e)}")
            self.status_label.setText(f"Error loading database status: {str(e)}")
    
    def _create_baseline(self):
        """Create the baseline."""
        if not self.baseline_manager:
            QMessageBox.warning(self, "Error", "No baseline manager available")
            return
        
        baseline_name = self.name_edit.text().strip()
        description = self.description_edit.toPlainText().strip()
        
        try:
            # Show progress dialog
            progress = QProgressDialog("Creating baseline...", "Cancel", 0, 0, self)
            progress.setWindowModality(Qt.WindowModal)
            progress.show()
            QApplication.processEvents()
            
            # Create baseline
            success, result = self.baseline_manager.create_baseline(baseline_name, description)
            
            progress.hide()
            
            if success:
                QMessageBox.information(
                    self,
                    "Baseline Created",
                    f"Baseline '{result}' created successfully."
                )
                self.accept()
            else:
                QMessageBox.warning(
                    self,
                    "Baseline Creation Failed",
                    f"Failed to create baseline:\n\n{result}"
                )
        
        except Exception as e:
            if 'progress' in locals():
                progress.hide()
            logger.error(f"Error creating baseline: {str(e)}")
            QMessageBox.critical(
                self,
                "Error",
                f"An error occurred while creating the baseline:\n\n{str(e)}"
            )


class BaselineManagementDialog(QDialog):
    """Dialog for managing existing baselines."""
    
    def __init__(self, parent=None, baseline_manager: BaselineManager = None):
        super().__init__(parent)
        self.baseline_manager = baseline_manager
        
        self.setWindowTitle("Baseline Management")
        self.setModal(True)
        self.resize(800, 600)
        
        self._setup_ui()
        self._load_baselines()
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout()
        
        # Toolbar
        toolbar_layout = QHBoxLayout()
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self._load_baselines)
        toolbar_layout.addWidget(self.refresh_button)
        
        self.create_button = QPushButton("Create New Baseline")
        self.create_button.clicked.connect(self._create_baseline)
        toolbar_layout.addWidget(self.create_button)
        
        toolbar_layout.addStretch()
        
        self.load_button = QPushButton("Load Selected")
        self.load_button.clicked.connect(self._load_baseline)
        self.load_button.setEnabled(False)
        toolbar_layout.addWidget(self.load_button)
        
        self.delete_button = QPushButton("Delete Selected")
        self.delete_button.clicked.connect(self._delete_baseline)
        self.delete_button.setEnabled(False)
        toolbar_layout.addWidget(self.delete_button)
        
        layout.addLayout(toolbar_layout)
        
        # Main content with tabs
        self.tab_widget = QTabWidget()
        
        # Baselines tab
        baselines_tab = QWidget()
        baselines_layout = QVBoxLayout()
        
        # Baselines table
        self.baselines_table = QTableWidget()
        self.baselines_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.baselines_table.selectionModel().selectionChanged.connect(self._on_selection_changed)
        baselines_layout.addWidget(self.baselines_table)
        
        baselines_tab.setLayout(baselines_layout)
        self.tab_widget.addTab(baselines_tab, "Baselines")
        
        # Comparison tab
        comparison_tab = QWidget()
        comparison_layout = QVBoxLayout()
        
        # Comparison controls
        comp_controls_layout = QHBoxLayout()
        comp_controls_layout.addWidget(QLabel("Compare:"))
        
        self.baseline1_combo = QComboBox()
        comp_controls_layout.addWidget(self.baseline1_combo)
        
        comp_controls_layout.addWidget(QLabel("with:"))
        
        self.baseline2_combo = QComboBox()
        comp_controls_layout.addWidget(self.baseline2_combo)
        
        self.compare_button = QPushButton("Compare")
        self.compare_button.clicked.connect(self._compare_baselines)
        comp_controls_layout.addWidget(self.compare_button)
        
        comp_controls_layout.addStretch()
        comparison_layout.addLayout(comp_controls_layout)
        
        # Comparison results
        self.comparison_text = QTextEdit()
        self.comparison_text.setFont(QFont("Consolas", 9))
        self.comparison_text.setReadOnly(True)
        comparison_layout.addWidget(self.comparison_text)
        
        comparison_tab.setLayout(comparison_layout)
        self.tab_widget.addTab(comparison_tab, "Comparison")
        
        layout.addWidget(self.tab_widget)
        
        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def _load_baselines(self):
        """Load and display baselines."""
        if not self.baseline_manager:
            return
        
        try:
            baselines = self.baseline_manager.list_baselines()
            
            # Set up table
            self.baselines_table.setRowCount(len(baselines))
            self.baselines_table.setColumnCount(4)
            self.baselines_table.setHorizontalHeaderLabels([
                "Name", "Description", "Created", "Records"
            ])
            
            # Populate table
            for row, baseline in enumerate(baselines):
                self.baselines_table.setItem(row, 0, QTableWidgetItem(baseline['name']))
                self.baselines_table.setItem(row, 1, QTableWidgetItem(baseline['description']))
                self.baselines_table.setItem(row, 2, QTableWidgetItem(baseline['created_date']))
                self.baselines_table.setItem(row, 3, QTableWidgetItem(str(baseline['record_count'])))
            
            # Resize columns
            header = self.baselines_table.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(1, QHeaderView.Stretch)
            header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
            
            # Update comparison combos
            self.baseline1_combo.clear()
            self.baseline2_combo.clear()
            for baseline in baselines:
                self.baseline1_combo.addItem(baseline['name'])
                self.baseline2_combo.addItem(baseline['name'])
            
        except Exception as e:
            logger.error(f"Error loading baselines: {str(e)}")
            QMessageBox.warning(self, "Error", f"Failed to load baselines:\n\n{str(e)}")
    
    def _on_selection_changed(self):
        """Handle baseline selection change."""
        has_selection = len(self.baselines_table.selectionModel().selectedRows()) > 0
        self.load_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)
    
    def _create_baseline(self):
        """Create a new baseline."""
        dialog = BaselineCreationDialog(self, self.baseline_manager)
        if dialog.exec() == QDialog.Accepted:
            self._load_baselines()
    
    def _load_baseline(self):
        """Load the selected baseline."""
        selected_rows = self.baselines_table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        row = selected_rows[0].row()
        baseline_name = self.baselines_table.item(row, 0).text()
        
        reply = QMessageBox.question(
            self,
            "Load Baseline",
            f"Load baseline '{baseline_name}'?\n\n"
            "This will replace the current working data with the baseline data (read-only).\n"
            "Make sure to save any current work before proceeding.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                success, message = self.baseline_manager.load_baseline(baseline_name)
                
                if success:
                    QMessageBox.information(self, "Baseline Loaded", message)
                    self.accept()  # Close dialog
                else:
                    QMessageBox.warning(self, "Load Failed", message)
                    
            except Exception as e:
                logger.error(f"Error loading baseline: {str(e)}")
                QMessageBox.critical(self, "Error", f"Failed to load baseline:\n\n{str(e)}")
    
    def _delete_baseline(self):
        """Delete the selected baseline."""
        selected_rows = self.baselines_table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        row = selected_rows[0].row()
        baseline_name = self.baselines_table.item(row, 0).text()
        
        reply = QMessageBox.question(
            self,
            "Delete Baseline",
            f"Delete baseline '{baseline_name}'?\n\n"
            "This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                success, message = self.baseline_manager.delete_baseline(baseline_name)
                
                if success:
                    QMessageBox.information(self, "Baseline Deleted", message)
                    self._load_baselines()
                else:
                    QMessageBox.warning(self, "Delete Failed", message)
                    
            except Exception as e:
                logger.error(f"Error deleting baseline: {str(e)}")
                QMessageBox.critical(self, "Error", f"Failed to delete baseline:\n\n{str(e)}")
    
    def _compare_baselines(self):
        """Compare two selected baselines."""
        baseline1 = self.baseline1_combo.currentText()
        baseline2 = self.baseline2_combo.currentText()
        
        if not baseline1 or not baseline2:
            QMessageBox.warning(self, "Invalid Selection", "Please select two baselines to compare.")
            return
        
        if baseline1 == baseline2:
            QMessageBox.warning(self, "Invalid Selection", "Please select two different baselines.")
            return
        
        try:
            progress = QProgressDialog("Comparing baselines...", "Cancel", 0, 0, self)
            progress.setWindowModality(Qt.WindowModal)
            progress.show()
            QApplication.processEvents()
            
            comparison = self.baseline_manager.compare_baselines(baseline1, baseline2)
            
            progress.hide()
            
            if 'error' in comparison:
                QMessageBox.warning(self, "Comparison Failed", comparison['error'])
                return
            
            # Display comparison results
            self._display_comparison_results(comparison)
            
        except Exception as e:
            if 'progress' in locals():
                progress.hide()
            logger.error(f"Error comparing baselines: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to compare baselines:\n\n{str(e)}")
    
    def _display_comparison_results(self, comparison: Dict[str, Any]):
        """Display baseline comparison results."""
        lines = []
        
        lines.append(f"Comparison: {comparison['baseline1']} vs {comparison['baseline2']}")
        lines.append("=" * 60)
        lines.append("")
        
        summary = comparison['summary']
        lines.append("Summary:")
        lines.append(f"  Total Differences: {summary['total_differences']}")
        lines.append(f"  Added Records: {summary['added_records']}")
        lines.append(f"  Modified Records: {summary['modified_records']}")
        lines.append(f"  Deleted Records: {summary['deleted_records']}")
        lines.append("")
        
        lines.append("Details by Table:")
        lines.append("-" * 30)
        
        for table_name, table_diff in comparison['tables'].items():
            if table_diff['added'] + table_diff['modified'] + table_diff['deleted'] > 0:
                lines.append(f"\n{table_name}:")
                lines.append(f"  Added: {table_diff['added']}")
                lines.append(f"  Modified: {table_diff['modified']}")
                lines.append(f"  Deleted: {table_diff['deleted']}")
                lines.append(f"  Total in {comparison['baseline1']}: {table_diff['total_baseline1']}")
                lines.append(f"  Total in {comparison['baseline2']}: {table_diff['total_baseline2']}")
        
        self.comparison_text.setPlainText("\n".join(lines))