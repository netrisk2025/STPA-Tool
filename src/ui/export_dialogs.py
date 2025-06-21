"""
Export dialog classes for STPA Tool
Contains dialogs for various export operations including JSON, Markdown, and ZIP exports.
"""

import os
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QMessageBox, QDialogButtonBox, QTextEdit,
    QProgressDialog, QApplication, QCheckBox, QComboBox,
    QGroupBox, QGridLayout, QSpinBox, QTabWidget, QWidget,
    QPlainTextEdit
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont

from ..export import JsonExporter, MarkdownExporter, ArchiveExporter
from ..database.connection import DatabaseConnection
from ..database.entities import System, EntityRepository
from ..log_config.config import get_logger

logger = get_logger(__name__)


class JsonExportDialog(QDialog):
    """Dialog for JSON export configuration and execution."""
    
    def __init__(self, parent=None, db_connection: DatabaseConnection = None, system_id: int = None):
        super().__init__(parent)
        self.db_connection = db_connection
        self.system_id = system_id
        self.json_exporter = JsonExporter(db_connection) if db_connection else None
        
        self.setWindowTitle("Export to JSON")
        self.setModal(True)
        self.resize(500, 400)
        
        self._setup_ui()
        self._load_system_info()
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout()
        
        # System info group
        system_group = QGroupBox("System Information")
        system_layout = QGridLayout()
        
        self.system_label = QLabel("Loading...")
        system_layout.addWidget(QLabel("System:"), 0, 0)
        system_layout.addWidget(self.system_label, 0, 1)
        
        system_group.setLayout(system_layout)
        layout.addWidget(system_group)
        
        # Export options group
        options_group = QGroupBox("Export Options")
        options_layout = QVBoxLayout()
        
        self.include_children_cb = QCheckBox("Include child systems")
        self.include_children_cb.setChecked(True)
        self.include_children_cb.setToolTip("Include immediate child systems (but not their descendants)")
        options_layout.addWidget(self.include_children_cb)
        
        # JSON formatting
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("JSON Indentation:"))
        self.indent_spinbox = QSpinBox()
        self.indent_spinbox.setRange(0, 8)
        self.indent_spinbox.setValue(2)
        format_layout.addWidget(self.indent_spinbox)
        format_layout.addStretch()
        options_layout.addLayout(format_layout)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # Preview section
        preview_group = QGroupBox("Export Preview")
        preview_layout = QVBoxLayout()
        
        self.preview_button = QPushButton("Generate Preview")
        self.preview_button.clicked.connect(self._generate_preview)
        preview_layout.addWidget(self.preview_button)
        
        self.preview_text = QPlainTextEdit()
        self.preview_text.setMaximumHeight(150)
        self.preview_text.setFont(QFont("Consolas", 9))
        preview_layout.addWidget(self.preview_text)
        
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.button(QDialogButtonBox.Ok).setText("Export...")
        button_box.accepted.connect(self._export_json)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def _load_system_info(self):
        """Load and display system information."""
        if not self.json_exporter or not self.system_id:
            self.system_label.setText("No system selected")
            return
        
        try:
            system_repo = EntityRepository(self.db_connection, System)
            system = system_repo.get_by_id(self.system_id)
            
            if system:
                self.system_label.setText(f"{system.hierarchical_id} - {system.system_name}")
            else:
                self.system_label.setText("System not found")
                
        except Exception as e:
            logger.error(f"Error loading system info: {str(e)}")
            self.system_label.setText("Error loading system")
    
    def _generate_preview(self):
        """Generate a preview of the export data."""
        if not self.json_exporter:
            return
        
        try:
            self.preview_button.setEnabled(False)
            self.preview_button.setText("Generating...")
            
            # Generate export data
            export_data = self.json_exporter.export_system_of_interest(
                self.system_id, 
                self.include_children_cb.isChecked()
            )
            
            # Create preview text
            preview_lines = [
                "Export Data Summary:",
                "=" * 50,
                f"System: {export_data['export_metadata']['system_name']}",
                f"Export Time: {export_data['export_metadata']['export_timestamp']}",
                f"Include Children: {export_data['export_metadata']['include_children']}",
                "",
                "Entity Counts:",
                f"  Functions: {len(export_data.get('functions', []))}",
                f"  Interfaces: {len(export_data.get('interfaces', []))}",
                f"  Assets: {len(export_data.get('assets', []))}",
                f"  Requirements: {len(export_data.get('requirements', []))}",
                f"  Hazards: {len(export_data.get('hazards', []))}",
                f"  Control Structures: {len(export_data.get('control_structures', []))}",
                f"  Child Systems: {len(export_data.get('child_systems', []))}"
            ]
            
            # Validation warnings
            warnings = self.json_exporter.validate_export_data(export_data)
            if warnings:
                preview_lines.extend(["", "Warnings:"] + [f"  • {w}" for w in warnings])
            
            self.preview_text.setPlainText("\n".join(preview_lines))
            
        except Exception as e:
            logger.error(f"Error generating preview: {str(e)}")
            self.preview_text.setPlainText(f"Error generating preview: {str(e)}")
        
        finally:
            self.preview_button.setEnabled(True)
            self.preview_button.setText("Generate Preview")
    
    def _export_json(self):
        """Execute the JSON export."""
        if not self.json_exporter:
            QMessageBox.warning(self, "Export Error", "No export system available")
            return
        
        # Get export file path
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export JSON File",
            f"system_{self.system_id}_export.json",
            "JSON Files (*.json);;All Files (*.*)"
        )
        
        if not file_path:
            return
        
        try:
            # Perform export
            success = self.json_exporter.export_to_file(
                self.system_id,
                file_path,
                self.include_children_cb.isChecked(),
                self.indent_spinbox.value()
            )
            
            if success:
                QMessageBox.information(
                    self, 
                    "Export Successful", 
                    f"JSON export completed successfully.\n\nFile saved to:\n{file_path}"
                )
                self.accept()
            else:
                QMessageBox.warning(
                    self,
                    "Export Failed",
                    "JSON export failed. Check the log for details."
                )
        
        except Exception as e:
            logger.error(f"Error during JSON export: {str(e)}")
            QMessageBox.critical(
                self,
                "Export Error",
                f"An error occurred during export:\n\n{str(e)}"
            )


class MarkdownExportDialog(QDialog):
    """Dialog for Markdown export configuration and execution."""
    
    def __init__(self, parent=None, db_connection: DatabaseConnection = None, system_id: int = None):
        super().__init__(parent)
        self.db_connection = db_connection
        self.system_id = system_id
        self.markdown_exporter = MarkdownExporter(db_connection) if db_connection else None
        
        self.setWindowTitle("Export to Markdown")
        self.setModal(True)
        self.resize(600, 500)
        
        self._setup_ui()
        self._load_system_info()
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout()
        
        # System info group
        system_group = QGroupBox("System Information")
        system_layout = QGridLayout()
        
        self.system_label = QLabel("Loading...")
        system_layout.addWidget(QLabel("System:"), 0, 0)
        system_layout.addWidget(self.system_label, 0, 1)
        
        system_group.setLayout(system_layout)
        layout.addWidget(system_group)
        
        # Export type selection
        type_group = QGroupBox("Export Type")
        type_layout = QVBoxLayout()
        
        self.export_type_combo = QComboBox()
        self.export_type_combo.addItems([
            "System Specification",
            "System Description"
        ])
        self.export_type_combo.currentTextChanged.connect(self._on_export_type_changed)
        type_layout.addWidget(self.export_type_combo)
        
        # Description of export types
        self.type_description = QLabel()
        self._update_type_description()
        type_layout.addWidget(self.type_description)
        
        type_group.setLayout(type_layout)
        layout.addWidget(type_group)
        
        # Preview section
        preview_group = QGroupBox("Document Preview")
        preview_layout = QVBoxLayout()
        
        self.preview_button = QPushButton("Generate Preview")
        self.preview_button.clicked.connect(self._generate_preview)
        preview_layout.addWidget(self.preview_button)
        
        self.preview_text = QPlainTextEdit()
        self.preview_text.setMaximumHeight(200)
        preview_layout.addWidget(self.preview_text)
        
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.button(QDialogButtonBox.Ok).setText("Export...")
        button_box.accepted.connect(self._export_markdown)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def _load_system_info(self):
        """Load and display system information."""
        if not self.markdown_exporter or not self.system_id:
            self.system_label.setText("No system selected")
            return
        
        try:
            system_repo = EntityRepository(self.db_connection, System)
            system = system_repo.get_by_id(self.system_id)
            
            if system:
                self.system_label.setText(f"{system.hierarchical_id} - {system.system_name}")
            else:
                self.system_label.setText("System not found")
                
        except Exception as e:
            logger.error(f"Error loading system info: {str(e)}")
            self.system_label.setText("Error loading system")
    
    def _on_export_type_changed(self):
        """Handle export type change."""
        self._update_type_description()
        self.preview_text.clear()
    
    def _update_type_description(self):
        """Update the description based on selected export type."""
        export_type = self.export_type_combo.currentText()
        
        if export_type == "System Specification":
            desc = "Generates a formal specification document with system requirements"
        else:  # System Description
            desc = "Generates a comprehensive description including functions, interfaces, and child systems"
        
        self.type_description.setText(desc)
    
    def _generate_preview(self):
        """Generate a preview of the markdown document."""
        if not self.markdown_exporter:
            return
        
        try:
            self.preview_button.setEnabled(False)
            self.preview_button.setText("Generating...")
            
            export_type = self.export_type_combo.currentText()
            
            if export_type == "System Specification":
                content = self.markdown_exporter.export_system_specification(self.system_id)
            else:  # System Description
                content = self.markdown_exporter.export_system_description(self.system_id)
            
            # Show first 2000 characters as preview
            preview_content = content[:2000]
            if len(content) > 2000:
                preview_content += "\n\n... (preview truncated) ..."
            
            self.preview_text.setPlainText(preview_content)
            
        except Exception as e:
            logger.error(f"Error generating preview: {str(e)}")
            self.preview_text.setPlainText(f"Error generating preview: {str(e)}")
        
        finally:
            self.preview_button.setEnabled(True)
            self.preview_button.setText("Generate Preview")
    
    def _export_markdown(self):
        """Execute the Markdown export."""
        if not self.markdown_exporter:
            QMessageBox.warning(self, "Export Error", "No export system available")
            return
        
        export_type = self.export_type_combo.currentText()
        file_suffix = "specification" if export_type == "System Specification" else "description"
        
        # Get export file path
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Markdown File",
            f"system_{self.system_id}_{file_suffix}.md",
            "Markdown Files (*.md);;All Files (*.*)"
        )
        
        if not file_path:
            return
        
        try:
            # Determine export type parameter
            export_param = "specification" if export_type == "System Specification" else "description"
            
            # Perform export
            success = self.markdown_exporter.export_to_file(
                self.system_id,
                file_path,
                export_param
            )
            
            if success:
                QMessageBox.information(
                    self, 
                    "Export Successful", 
                    f"Markdown export completed successfully.\n\nFile saved to:\n{file_path}"
                )
                self.accept()
            else:
                QMessageBox.warning(
                    self,
                    "Export Failed",
                    "Markdown export failed. Check the log for details."
                )
        
        except Exception as e:
            logger.error(f"Error during Markdown export: {str(e)}")
            QMessageBox.critical(
                self,
                "Export Error",
                f"An error occurred during export:\n\n{str(e)}"
            )


class ArchiveExportDialog(QDialog):
    """Dialog for working directory archive export."""
    
    def __init__(self, parent=None, working_directory: str = None):
        super().__init__(parent)
        self.working_directory = working_directory
        self.archive_exporter = ArchiveExporter()
        
        self.setWindowTitle("Export Working Directory")
        self.setModal(True)
        self.resize(500, 400)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout()
        
        # Directory info
        if self.working_directory:
            info_label = QLabel(f"Working Directory: {self.working_directory}")
            layout.addWidget(info_label)
        
        # Export options group
        options_group = QGroupBox("Export Options")
        options_layout = QVBoxLayout()
        
        # File exclusions
        exclusions_label = QLabel("Files to exclude (one pattern per line):")
        options_layout.addWidget(exclusions_label)
        
        self.exclusions_text = QPlainTextEdit()
        self.exclusions_text.setMaximumHeight(100)
        self.exclusions_text.setPlainText("*.tmp\n*.log\n*~\n.DS_Store\nThumbs.db\n*.bak")
        options_layout.addWidget(self.exclusions_text)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # Progress section (initially hidden)
        self.progress_dialog = None
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.export_button = QPushButton("Export...")
        self.export_button.clicked.connect(self._export_archive)
        button_layout.addWidget(self.export_button)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def _export_archive(self):
        """Execute the archive export."""
        if not self.working_directory or not os.path.exists(self.working_directory):
            QMessageBox.warning(self, "Export Error", "Working directory is not valid")
            return
        
        # Get export file path
        default_name = f"stpa_export_{os.path.basename(self.working_directory)}.zip"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Archive",
            default_name,
            "ZIP Archives (*.zip);;All Files (*.*)"
        )
        
        if not file_path:
            return
        
        try:
            # Get exclusion patterns
            exclusion_text = self.exclusions_text.toPlainText().strip()
            exclusions = [line.strip() for line in exclusion_text.split('\n') if line.strip()]
            
            # Create progress dialog
            self.progress_dialog = QProgressDialog("Preparing export...", "Cancel", 0, 100, self)
            self.progress_dialog.setWindowModality(Qt.WindowModal)
            self.progress_dialog.show()
            
            def progress_callback(current, message):
                if self.progress_dialog.wasCanceled():
                    return
                self.progress_dialog.setLabelText(message)
                # We don't know total files beforehand, so just pulse
                self.progress_dialog.setValue((current % 100))
                QApplication.processEvents()
            
            # Perform export
            success = self.archive_exporter.export_working_directory(
                self.working_directory,
                file_path,
                exclusions,
                progress_callback
            )
            
            self.progress_dialog.hide()
            
            if success:
                QMessageBox.information(
                    self, 
                    "Export Successful", 
                    f"Working directory exported successfully.\n\nArchive saved to:\n{file_path}"
                )
                self.accept()
            else:
                QMessageBox.warning(
                    self,
                    "Export Failed",
                    "Archive export failed. Check the log for details."
                )
        
        except Exception as e:
            if self.progress_dialog:
                self.progress_dialog.hide()
            
            logger.error(f"Error during archive export: {str(e)}")
            QMessageBox.critical(
                self,
                "Export Error",
                f"An error occurred during export:\n\n{str(e)}"
            )