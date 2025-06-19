"""
Dialog classes for STPA Tool
Contains common dialog implementations including directory selection.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QMessageBox, QDialogButtonBox, QTextEdit,
    QProgressDialog, QApplication
)
from PySide6.QtCore import Qt, QThread, Signal
from pathlib import Path
from typing import Optional, Callable

from ..utils.directory import DirectoryManager
from ..log_config.config import get_logger

logger = get_logger(__name__)


class DirectorySelectionDialog(QDialog):
    """
    Dialog for selecting and validating working directory.
    """
    
    def __init__(self, parent=None, current_directory: Optional[Path] = None):
        """
        Initialize directory selection dialog.
        
        Args:
            parent: Parent widget
            current_directory: Currently selected directory
        """
        super().__init__(parent)
        self.selected_directory = current_directory
        self.directory_manager = DirectoryManager()
        
        self.setWindowTitle("Select Working Directory")
        self.setModal(True)
        self.resize(500, 200)
        
        self._setup_ui()
        
        if current_directory:
            self.directory_label.setText(str(current_directory))
    
    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Instructions
        instructions = QLabel(
            "Select a directory where STPA Tool will store its files.\n"
            "This directory will contain the database, configuration, and diagram files."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Directory selection
        dir_layout = QHBoxLayout()
        
        self.directory_label = QLabel("No directory selected")
        self.directory_label.setStyleSheet("QLabel { border: 1px solid gray; padding: 5px; }")
        dir_layout.addWidget(self.directory_label)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_directory)
        dir_layout.addWidget(browse_btn)
        
        layout.addLayout(dir_layout)
        
        # Validation status
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self._accept_dialog)
        button_box.rejected.connect(self.reject)
        
        self.ok_button = button_box.button(QDialogButtonBox.Ok)
        self.ok_button.setEnabled(False)
        
        layout.addWidget(button_box)
        
        layout.addStretch()
    
    def _browse_directory(self):
        """Open directory browser dialog."""
        start_dir = str(self.selected_directory) if self.selected_directory else ""
        
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Working Directory",
            start_dir
        )
        
        if directory:
            self.selected_directory = Path(directory)
            self.directory_label.setText(directory)
            self._validate_directory()
    
    def _validate_directory(self):
        """Validate the selected directory."""
        if not self.selected_directory:
            self.status_label.setText("")
            self.ok_button.setEnabled(False)
            return
        
        is_valid, error_msg = self.directory_manager.validate_directory(
            self.selected_directory
        )
        
        if is_valid:
            # Check for existing files
            existing_files = self.directory_manager.list_existing_files()
            if existing_files:
                status_text = f"✓ Valid directory (contains existing STPA files: {', '.join(existing_files)})"
                self.status_label.setStyleSheet("color: orange;")
            else:
                status_text = "✓ Valid directory (will be initialized for STPA Tool)"
                self.status_label.setStyleSheet("color: green;")
            
            self.status_label.setText(status_text)
            self.ok_button.setEnabled(True)
        else:
            self.status_label.setText(f"✗ {error_msg}")
            self.status_label.setStyleSheet("color: red;")
            self.ok_button.setEnabled(False)
    
    def _accept_dialog(self):
        """Accept dialog and initialize directory if needed."""
        if not self.selected_directory:
            return
        
        # Initialize directory
        success, error_msg = self.directory_manager.initialize_directory(
            self.selected_directory
        )
        
        if success:
            self.accept()
        else:
            QMessageBox.critical(
                self,
                "Directory Initialization Failed",
                f"Failed to initialize directory:\n{error_msg}"
            )
    
    def get_selected_directory(self) -> Optional[Path]:
        """
        Get the selected directory.
        
        Returns:
            Selected directory path or None
        """
        return self.selected_directory


class ProgressDialog(QProgressDialog):
    """
    Custom progress dialog for long-running operations.
    """
    
    def __init__(self, title: str, parent=None):
        """
        Initialize progress dialog.
        
        Args:
            title: Dialog title
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setAutoClose(False)
        self.setAutoReset(False)
        self.setCancelButton(None)  # No cancel button by default
        
        self.setMinimumWidth(400)
    
    def update_progress(self, value: int, text: str = ""):
        """
        Update progress value and text.
        
        Args:
            value: Progress value (0-100)
            text: Progress text
        """
        self.setValue(value)
        if text:
            self.setLabelText(text)
        
        QApplication.processEvents()


class ConfirmationDialog(QMessageBox):
    """
    Custom confirmation dialog.
    """
    
    @staticmethod
    def confirm(
        parent,
        title: str,
        message: str,
        details: str = ""
    ) -> bool:
        """
        Show confirmation dialog.
        
        Args:
            parent: Parent widget
            title: Dialog title
            message: Main message
            details: Detailed message (optional)
            
        Returns:
            True if user confirmed
        """
        dialog = QMessageBox(parent)
        dialog.setWindowTitle(title)
        dialog.setText(message)
        
        if details:
            dialog.setDetailedText(details)
        
        dialog.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dialog.setDefaultButton(QMessageBox.No)
        dialog.setIcon(QMessageBox.Question)
        
        return dialog.exec() == QMessageBox.Yes


class ErrorDialog(QMessageBox):
    """
    Custom error dialog.
    """
    
    @staticmethod
    def show_error(
        parent,
        title: str,
        message: str,
        details: str = ""
    ):
        """
        Show error dialog.
        
        Args:
            parent: Parent widget
            title: Dialog title
            message: Main error message
            details: Detailed error message (optional)
        """
        dialog = QMessageBox(parent)
        dialog.setWindowTitle(title)
        dialog.setText(message)
        
        if details:
            dialog.setDetailedText(details)
        
        dialog.setStandardButtons(QMessageBox.Ok)
        dialog.setIcon(QMessageBox.Critical)
        
        dialog.exec()


class InfoDialog(QMessageBox):
    """
    Custom information dialog.
    """
    
    @staticmethod
    def show_info(
        parent,
        title: str,
        message: str,
        details: str = ""
    ):
        """
        Show information dialog.
        
        Args:
            parent: Parent widget
            title: Dialog title
            message: Main message
            details: Detailed message (optional)
        """
        dialog = QMessageBox(parent)
        dialog.setWindowTitle(title)
        dialog.setText(message)
        
        if details:
            dialog.setDetailedText(details)
        
        dialog.setStandardButtons(QMessageBox.Ok)
        dialog.setIcon(QMessageBox.Information)
        
        dialog.exec()