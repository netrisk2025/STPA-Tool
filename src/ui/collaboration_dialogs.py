"""
Collaboration dialog classes for STPA Tool
Contains dialogs for branch management and merging operations.
"""

import os
from typing import Optional, List, Dict, Any

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QTableWidget, QTableWidgetItem, 
    QHeaderView, QMessageBox, QDialogButtonBox, QGroupBox,
    QGridLayout, QComboBox, QProgressDialog, QApplication,
    QTreeWidget, QTreeWidgetItem, QSplitter, QWidget, QTabWidget,
    QCheckBox, QFileDialog
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont

from ..collaboration import BranchManager, MergeManager
from ..database.connection import DatabaseConnection
from ..database.entities import System, EntityRepository
from ..log_config.config import get_logger

logger = get_logger(__name__)


class BranchCreationDialog(QDialog):
    """Dialog for creating new project branches."""
    
    def __init__(self, parent=None, branch_manager: BranchManager = None, db_connection: DatabaseConnection = None):
        super().__init__(parent)
        self.branch_manager = branch_manager
        self.db_connection = db_connection
        
        self.setWindowTitle("Create Project Branch")
        self.setModal(True)
        self.resize(600, 500)
        
        self._setup_ui()
        self._load_systems()
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout()
        
        # Branch info group
        info_group = QGroupBox("Branch Information")
        info_layout = QGridLayout()
        
        # Name field
        info_layout.addWidget(QLabel("Branch Name:"), 0, 0)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter branch name (letters, numbers, _, -)")
        info_layout.addWidget(self.name_edit, 0, 1)
        
        # Description field
        info_layout.addWidget(QLabel("Description:"), 1, 0, Qt.AlignTop)
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        self.description_edit.setPlaceholderText("Describe the purpose of this branch...")
        info_layout.addWidget(self.description_edit, 1, 1)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # System selection group
        system_group = QGroupBox("Root System Selection")
        system_layout = QVBoxLayout()
        
        system_layout.addWidget(QLabel("Select the root system for this branch:"))
        
        self.systems_tree = QTreeWidget()
        self.systems_tree.setHeaderLabels(["System", "ID", "Description"])
        self.systems_tree.selectionModel().selectionChanged.connect(self._on_system_selection_changed)
        system_layout.addWidget(self.systems_tree)
        
        # Selection info
        self.selection_label = QLabel("No system selected")
        system_layout.addWidget(self.selection_label)
        
        system_group.setLayout(system_layout)
        layout.addWidget(system_group)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.button(QDialogButtonBox.Ok).setText("Create Branch")
        button_box.button(QDialogButtonBox.Ok).setEnabled(False)
        button_box.accepted.connect(self._create_branch)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.button_box = button_box
        self.setLayout(layout)
    
    def _load_systems(self):
        """Load and display systems in tree."""
        if not self.db_connection:
            return
        
        try:
            system_repo = EntityRepository(self.db_connection, System)
            cursor = self.db_connection.get_cursor()
            cursor.execute("SELECT * FROM systems WHERE baseline = 'Working' ORDER BY hierarchical_id")
            
            self.systems_tree.clear()
            system_items = {}
            
            for row in cursor.fetchall():
                system = System()
                columns = [desc[0] for desc in cursor.description]
                for i, column in enumerate(columns):
                    if hasattr(system, column):
                        setattr(system, column, row[i])
                
                item = QTreeWidgetItem([
                    system.system_name,
                    system.hierarchical_id,
                    system.system_description[:50] + "..." if len(system.system_description) > 50 else system.system_description
                ])
                item.setData(0, Qt.UserRole, system.id)
                
                # Build hierarchy
                if system.parent_system_id and system.parent_system_id in system_items:
                    system_items[system.parent_system_id].addChild(item)
                else:
                    self.systems_tree.addTopLevelItem(item)
                
                system_items[system.id] = item
            
            self.systems_tree.expandAll()
            
        except Exception as e:
            logger.error(f"Error loading systems: {str(e)}")
            QMessageBox.warning(self, "Error", f"Failed to load systems:\n\n{str(e)}")
    
    def _on_system_selection_changed(self):
        """Handle system selection change."""
        selected_items = self.systems_tree.selectedItems()
        
        if selected_items:
            item = selected_items[0]
            system_name = item.text(0)
            system_id = item.text(1)
            self.selection_label.setText(f"Selected: {system_name} ({system_id})")
            self.button_box.button(QDialogButtonBox.Ok).setEnabled(True)
        else:
            self.selection_label.setText("No system selected")
            self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)
    
    def _create_branch(self):
        """Create the branch."""
        if not self.branch_manager:
            QMessageBox.warning(self, "Error", "No branch manager available")
            return
        
        selected_items = self.systems_tree.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select a root system for the branch.")
            return
        
        branch_name = self.name_edit.text().strip()
        if not branch_name:
            QMessageBox.warning(self, "Invalid Name", "Please enter a branch name.")
            return
        
        description = self.description_edit.toPlainText().strip()
        system_id = selected_items[0].data(0, Qt.UserRole)
        
        try:
            progress = QProgressDialog("Creating branch...", "Cancel", 0, 0, self)
            progress.setWindowModality(Qt.WindowModal)
            progress.show()
            QApplication.processEvents()
            
            success, result = self.branch_manager.create_branch(system_id, branch_name, description)
            
            progress.hide()
            
            if success:
                QMessageBox.information(
                    self,
                    "Branch Created",
                    f"Branch created successfully at:\n{result}"
                )
                self.accept()
            else:
                QMessageBox.warning(
                    self,
                    "Branch Creation Failed",
                    f"Failed to create branch:\n\n{result}"
                )
        
        except Exception as e:
            if 'progress' in locals():
                progress.hide()
            logger.error(f"Error creating branch: {str(e)}")
            QMessageBox.critical(
                self,
                "Error",
                f"An error occurred while creating the branch:\n\n{str(e)}"
            )


class BranchManagementDialog(QDialog):
    """Dialog for managing project branches."""
    
    def __init__(self, parent=None, branch_manager: BranchManager = None, merge_manager: MergeManager = None):
        super().__init__(parent)
        self.branch_manager = branch_manager
        self.merge_manager = merge_manager
        
        self.setWindowTitle("Branch Management")
        self.setModal(True)
        self.resize(900, 700)
        
        self._setup_ui()
        self._load_branches()
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout()
        
        # Toolbar
        toolbar_layout = QHBoxLayout()
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self._load_branches)
        toolbar_layout.addWidget(self.refresh_button)
        
        self.create_button = QPushButton("Create New Branch")
        self.create_button.clicked.connect(self._create_branch)
        toolbar_layout.addWidget(self.create_button)
        
        toolbar_layout.addStretch()
        
        self.merge_button = QPushButton("Merge Selected")
        self.merge_button.clicked.connect(self._merge_branch)
        self.merge_button.setEnabled(False)
        toolbar_layout.addWidget(self.merge_button)
        
        self.delete_button = QPushButton("Delete Selected")
        self.delete_button.clicked.connect(self._delete_branch)
        self.delete_button.setEnabled(False)
        toolbar_layout.addWidget(self.delete_button)
        
        layout.addLayout(toolbar_layout)
        
        # Main content with tabs
        self.tab_widget = QTabWidget()
        
        # Branches tab
        branches_tab = QWidget()
        branches_layout = QVBoxLayout()
        
        # Branches table
        self.branches_table = QTableWidget()
        self.branches_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.branches_table.selectionModel().selectionChanged.connect(self._on_selection_changed)
        branches_layout.addWidget(self.branches_table)
        
        # Branch details
        details_group = QGroupBox("Branch Details")
        details_layout = QVBoxLayout()
        
        self.details_text = QTextEdit()
        self.details_text.setMaximumHeight(150)
        self.details_text.setReadOnly(True)
        details_layout.addWidget(self.details_text)
        
        details_group.setLayout(details_layout)
        branches_layout.addWidget(details_group)
        
        branches_tab.setLayout(branches_layout)
        self.tab_widget.addTab(branches_tab, "Branches")
        
        layout.addWidget(self.tab_widget)
        
        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def _load_branches(self):
        """Load and display branches."""
        if not self.branch_manager:
            return
        
        try:
            branches = self.branch_manager.list_branches()
            
            # Set up table
            self.branches_table.setRowCount(len(branches))
            self.branches_table.setColumnCount(5)
            self.branches_table.setHorizontalHeaderLabels([
                "Name", "Root System", "Description", "Created", "Status"
            ])
            
            # Populate table
            for row, branch in enumerate(branches):
                self.branches_table.setItem(row, 0, QTableWidgetItem(branch['branch_name']))
                self.branches_table.setItem(row, 1, QTableWidgetItem(f"{branch['root_system_name']} ({branch['root_system_hierarchy']})"))
                self.branches_table.setItem(row, 2, QTableWidgetItem(branch['description']))
                self.branches_table.setItem(row, 3, QTableWidgetItem(branch['created_date']))
                
                status = "Ready" if branch['database_exists'] else "Incomplete"
                self.branches_table.setItem(row, 4, QTableWidgetItem(status))
                
                # Store branch data
                self.branches_table.item(row, 0).setData(Qt.UserRole, branch)
            
            # Resize columns
            header = self.branches_table.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(2, QHeaderView.Stretch)
            header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
            
        except Exception as e:
            logger.error(f"Error loading branches: {str(e)}")
            QMessageBox.warning(self, "Error", f"Failed to load branches:\n\n{str(e)}")
    
    def _on_selection_changed(self):
        """Handle branch selection change."""
        selected_rows = self.branches_table.selectionModel().selectedRows()
        has_selection = len(selected_rows) > 0
        
        self.merge_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)
        
        if has_selection:
            row = selected_rows[0].row()
            branch_data = self.branches_table.item(row, 0).data(Qt.UserRole)
            self._display_branch_details(branch_data)
        else:
            self.details_text.clear()
    
    def _display_branch_details(self, branch_data: Dict[str, Any]):
        """Display detailed information about a branch."""
        lines = []
        
        lines.append(f"Branch: {branch_data['branch_name']}")
        lines.append(f"Description: {branch_data['description']}")
        lines.append(f"Root System: {branch_data['root_system_name']} (ID: {branch_data['root_system_id']})")
        lines.append(f"System Hierarchy: {branch_data['root_system_hierarchy']}")
        lines.append(f"Created: {branch_data['created_date']}")
        lines.append(f"Parent Project: {branch_data['parent_project']}")
        lines.append(f"Database Exists: {'Yes' if branch_data['database_exists'] else 'No'}")
        lines.append(f"Branch Path: {branch_data['branch_path']}")
        
        self.details_text.setPlainText("\n".join(lines))
    
    def _create_branch(self):
        """Create a new branch."""
        # We need database connection for this dialog
        if hasattr(self.parent(), 'database_initializer'):
            db_manager = self.parent().database_initializer.get_database_manager()
            db_connection = db_manager.get_connection()
            
            dialog = BranchCreationDialog(self, self.branch_manager, db_connection)
            if dialog.exec() == QDialog.Accepted:
                self._load_branches()
        else:
            QMessageBox.warning(self, "Error", "Cannot access database connection.")
    
    def _merge_branch(self):
        """Merge the selected branch."""
        selected_rows = self.branches_table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        row = selected_rows[0].row()
        branch_data = self.branches_table.item(row, 0).data(Qt.UserRole)
        branch_path = branch_data['branch_path']
        
        if not self.merge_manager:
            QMessageBox.warning(self, "Error", "No merge manager available")
            return
        
        try:
            # Analyze merge first
            progress = QProgressDialog("Analyzing merge...", "Cancel", 0, 0, self)
            progress.setWindowModality(Qt.WindowModal)
            progress.show()
            QApplication.processEvents()
            
            can_auto_merge, analysis = self.merge_manager.analyze_merge(branch_path)
            
            progress.hide()
            
            if 'error' in analysis:
                QMessageBox.warning(self, "Merge Analysis Failed", analysis['error'])
                return
            
            # Show merge analysis dialog
            dialog = MergeAnalysisDialog(self, analysis)
            if dialog.exec() == QDialog.Accepted:
                # Perform merge
                conflict_resolutions = dialog.get_conflict_resolutions()
                
                progress = QProgressDialog("Merging branch...", "Cancel", 0, 0, self)
                progress.setWindowModality(Qt.WindowModal)
                progress.show()
                QApplication.processEvents()
                
                success, message = self.merge_manager.merge_branch(branch_path, conflict_resolutions)
                
                progress.hide()
                
                if success:
                    QMessageBox.information(self, "Merge Successful", message)
                    self._load_branches()
                else:
                    QMessageBox.warning(self, "Merge Failed", message)
        
        except Exception as e:
            if 'progress' in locals():
                progress.hide()
            logger.error(f"Error merging branch: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to merge branch:\n\n{str(e)}")
    
    def _delete_branch(self):
        """Delete the selected branch."""
        selected_rows = self.branches_table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        row = selected_rows[0].row()
        branch_data = self.branches_table.item(row, 0).data(Qt.UserRole)
        branch_name = branch_data['branch_name']
        
        reply = QMessageBox.question(
            self,
            "Delete Branch",
            f"Delete branch '{branch_name}'?\n\n"
            "This will permanently delete the branch directory and all its files.\n"
            "This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                success, message = self.branch_manager.delete_branch(branch_name)
                
                if success:
                    QMessageBox.information(self, "Branch Deleted", message)
                    self._load_branches()
                else:
                    QMessageBox.warning(self, "Delete Failed", message)
                    
            except Exception as e:
                logger.error(f"Error deleting branch: {str(e)}")
                QMessageBox.critical(self, "Error", f"Failed to delete branch:\n\n{str(e)}")


class MergeAnalysisDialog(QDialog):
    """Dialog for displaying merge analysis and resolving conflicts."""
    
    def __init__(self, parent=None, analysis: Dict[str, Any] = None):
        super().__init__(parent)
        self.analysis = analysis
        self.conflict_resolutions = {}
        
        self.setWindowTitle("Merge Analysis")
        self.setModal(True)
        self.resize(800, 600)
        
        self._setup_ui()
        self._display_analysis()
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout()
        
        # Summary section
        summary_group = QGroupBox("Merge Summary")
        summary_layout = QVBoxLayout()
        
        self.summary_label = QLabel()
        summary_layout.addWidget(self.summary_label)
        
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)
        
        # Conflicts section (if any)
        self.conflicts_group = QGroupBox("Conflicts Requiring Resolution")
        conflicts_layout = QVBoxLayout()
        
        self.conflicts_tree = QTreeWidget()
        self.conflicts_tree.setHeaderLabels(["Type", "Entity", "Description", "Resolution"])
        conflicts_layout.addWidget(self.conflicts_tree)
        
        self.conflicts_group.setLayout(conflicts_layout)
        layout.addWidget(self.conflicts_group)
        
        # Changes section
        changes_group = QGroupBox("Changes to be Applied")
        changes_layout = QVBoxLayout()
        
        self.changes_text = QTextEdit()
        self.changes_text.setMaximumHeight(150)
        self.changes_text.setReadOnly(True)
        changes_layout.addWidget(self.changes_text)
        
        changes_group.setLayout(changes_layout)
        layout.addWidget(changes_group)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.button(QDialogButtonBox.Ok).setText("Proceed with Merge")
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.button_box = button_box
        self.setLayout(layout)
    
    def _display_analysis(self):
        """Display the merge analysis results."""
        if not self.analysis:
            return
        
        # Summary
        metadata = self.analysis['branch_metadata']
        summary_lines = [
            f"Branch: {metadata['branch_name']}",
            f"Root System: {metadata['root_system_name']}",
            f"Changes: {self.analysis['change_count']} records",
            f"Conflicts: {self.analysis['conflict_count']}"
        ]
        
        if self.analysis['can_auto_merge']:
            summary_lines.append("\n✅ Can merge automatically")
            self.button_box.button(QDialogButtonBox.Ok).setEnabled(True)
        else:
            summary_lines.append("\n⚠️ Conflicts must be resolved before merging")
            self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)
        
        self.summary_label.setText("\n".join(summary_lines))
        
        # Conflicts
        conflicts = self.analysis['conflicts']
        if conflicts:
            self.conflicts_group.setVisible(True)
            
            for i, conflict in enumerate(conflicts):
                item = QTreeWidgetItem([
                    conflict['conflict_type'],
                    f"{conflict['table_name']}#{conflict['entity_id']}",
                    conflict['description'],
                    "Keep Main"  # Default resolution
                ])
                
                # Add resolution combo
                resolution_combo = QComboBox()
                resolution_combo.addItems(["Keep Main", "Keep Branch", "Manual Review"])
                resolution_combo.currentTextChanged.connect(
                    lambda text, idx=i: self._on_resolution_changed(idx, text)
                )
                
                self.conflicts_tree.addTopLevelItem(item)
                self.conflicts_tree.setItemWidget(item, 3, resolution_combo)
                
                # Store default resolution
                self.conflict_resolutions[str(i)] = {
                    'action': 'keep_main',
                    'table_name': conflict['table_name'],
                    'entity_id': conflict['entity_id']
                }
        else:
            self.conflicts_group.setVisible(False)
        
        # Changes
        changes = self.analysis['changes']
        changes_lines = [
            f"Records to be added: {changes['added']}",
            f"Records to be modified: {changes['modified']}",
            f"Records to be deleted: {changes['deleted']}"
        ]
        self.changes_text.setPlainText("\n".join(changes_lines))
    
    def _on_resolution_changed(self, conflict_index: int, resolution_text: str):
        """Handle conflict resolution change."""
        resolution_map = {
            "Keep Main": "keep_main",
            "Keep Branch": "keep_branch",
            "Manual Review": "manual"
        }
        
        if str(conflict_index) in self.conflict_resolutions:
            self.conflict_resolutions[str(conflict_index)]['action'] = resolution_map[resolution_text]
        
        # Check if all conflicts are resolved
        all_resolved = all(
            res['action'] != 'manual' 
            for res in self.conflict_resolutions.values()
        )
        
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(
            all_resolved or self.analysis['can_auto_merge']
        )
    
    def get_conflict_resolutions(self) -> Dict[str, Any]:
        """Get the conflict resolutions."""
        return self.conflict_resolutions