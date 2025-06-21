"""
Main window for STPA Tool
Contains the primary user interface layout and components.
"""

import os
from PySide6.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QSplitter,
    QMenuBar, QStatusBar, QToolBar, QLabel, QTreeWidget, QTabWidget,
    QTableWidget, QTableWidgetItem, QPushButton, QHeaderView, QMessageBox,
    QComboBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QIcon

from ..config.settings import ConfigManager
from ..config.constants import (
    APP_NAME, WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT, SPLITTER_DEFAULT_SIZES
)
from ..log_config.config import get_logger
from .hierarchy_tree import HierarchyTreeWidget
from .entity_dialogs import SystemEditDialog, FunctionEditDialog, RequirementEditDialog
from .entity_widgets import (
    InterfaceWidget, AssetWidget, HazardWidget, LossWidget,
    ControlStructureWidget, ControllerWidget
)
from .export_dialogs import JsonExportDialog, MarkdownExportDialog, ArchiveExportDialog
from .baseline_dialogs import BaselineCreationDialog, BaselineManagementDialog
from .collaboration_dialogs import BranchCreationDialog, BranchManagementDialog
from ..database.entities import (
    System, Function, Requirement, Interface, Asset, Hazard, Loss, 
    ControlStructure, Controller, EntityFactory
)
from ..diagrams import DiagramGenerator, DiagramRenderer, DiagramViewer
from ..database.baseline_manager import BaselineManager
from ..collaboration import BranchManager, MergeManager
from ..diagrams.types import DiagramType

logger = get_logger(__name__)


class MainWindow(QMainWindow):
    """
    Main application window for STPA Tool.
    """
    
    def __init__(self, config_manager: ConfigManager, database_initializer=None):
        """
        Initialize the main window.
        
        Args:
            config_manager: Configuration manager instance
            database_initializer: Database initializer instance (optional)
        """
        super().__init__()
        
        self.config_manager = config_manager
        self.database_initializer = database_initializer
        
        # Window setup
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        
        # UI components
        self.hierarchy_tree = None
        self.content_tabs = None
        self.status_bar = None
        self.splitter = None
        self.current_system_id = None
        
        # Diagram components
        self.diagram_generator = None
        self.diagram_renderer = None
        self.diagram_viewer = None
        
        # Collaboration components
        self.baseline_manager = None
        self.branch_manager = None
        self.merge_manager = None
        
        # Initialize components if database is available
        if self.database_initializer:
            self._setup_diagram_components()
            self._setup_collaboration_components()
        
        # Setup UI
        self._setup_ui()
        self._setup_menus()
        self._setup_toolbar()
        self._setup_status_bar()
        
        # Restore window state
        self._restore_window_state()
        
        # Load hierarchy tree from database if available
        if self.database_initializer:
            QTimer.singleShot(100, self._load_initial_data)
        
        logger.info("Main window initialized")
    
    def _load_initial_data(self):
        """Load initial data from database."""
        try:
            self.hierarchy_tree.refresh_from_database()
        except Exception as e:
            logger.error(f"Failed to load initial data: {str(e)}")
    
    def _setup_ui(self):
        """Setup the main user interface layout."""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Splitter for left and right panes
        self.splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(self.splitter)
        
        # Left pane - Hierarchy Navigator
        self._setup_hierarchy_pane()
        
        # Right pane - Content Area
        self._setup_content_pane()
        
        # Set initial splitter sizes
        self.splitter.setSizes(SPLITTER_DEFAULT_SIZES)
        self.splitter.setCollapsible(0, False)  # Don't allow left pane to collapse
        self.splitter.setCollapsible(1, False)  # Don't allow right pane to collapse
    
    def _setup_hierarchy_pane(self):
        """Setup the left hierarchy navigation pane."""
        # Create enhanced hierarchy tree widget
        self.hierarchy_tree = HierarchyTreeWidget(self.database_initializer)
        self.hierarchy_tree.setMinimumWidth(250)
        
        # Connect signals
        self.hierarchy_tree.system_selected.connect(self._on_system_selected)
        self.hierarchy_tree.system_changed.connect(self._on_system_changed)
        
        # Add to splitter
        self.splitter.addWidget(self.hierarchy_tree)
    
    def _setup_content_pane(self):
        """Setup the right content area pane."""
        # Create content widget
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        
        # Breadcrumb area (header)
        self.breadcrumb_label = QLabel("No system selected")
        self.breadcrumb_label.setStyleSheet("""
            QLabel {
                background-color: #f0f0f0;
                padding: 8px;
                border-bottom: 1px solid #ccc;
                font-weight: bold;
            }
        """)
        content_layout.addWidget(self.breadcrumb_label)
        
        # Tabbed content area
        self.content_tabs = QTabWidget()
        self.content_tabs.setTabPosition(QTabWidget.North)
        
        # Add placeholder tabs
        self._setup_placeholder_tabs()
        
        content_layout.addWidget(self.content_tabs)
        
        # Add to splitter
        self.splitter.addWidget(content_widget)
    
    def _setup_placeholder_tabs(self):
        """Setup tabs for entity management."""
        # Overview tab
        self._setup_overview_tab()
        
        # Functions tab
        self._setup_functions_tab()
        
        # Requirements tab
        self._setup_requirements_tab()
        
        # Interfaces tab
        self._setup_interfaces_tab()
        
        # Assets tab
        self._setup_assets_tab()
        
        # Hazards tab
        self._setup_hazards_tab()
        
        # Losses tab
        self._setup_losses_tab()
        
        # Control Structure tab
        self._setup_control_structures_tab()
        
        # Controllers tab
        self._setup_controllers_tab()
        
        # Diagrams tab
        self._setup_diagrams_tab()
        
        # Warnings tab
        warnings_widget = QWidget()
        warnings_layout = QVBoxLayout(warnings_widget)
        warnings_layout.addWidget(QLabel("Warnings - Coming Soon"))
        self.content_tabs.addTab(warnings_widget, "Warnings")
        
        # Audit tab
        audit_widget = QWidget()
        audit_layout = QVBoxLayout(audit_widget)
        audit_layout.addWidget(QLabel("Audit - Coming Soon"))
        self.content_tabs.addTab(audit_widget, "Audit")
    
    def _setup_overview_tab(self):
        """Setup system overview tab."""
        overview_widget = QWidget()
        overview_layout = QVBoxLayout(overview_widget)
        
        self.system_info_label = QLabel("Select a system to view details")
        self.system_info_label.setWordWrap(True)
        overview_layout.addWidget(self.system_info_label)
        
        # Edit system button
        self.edit_system_btn = QPushButton("Edit System")
        self.edit_system_btn.setEnabled(False)
        self.edit_system_btn.clicked.connect(self._edit_current_system)
        overview_layout.addWidget(self.edit_system_btn)
        
        overview_layout.addStretch()
        self.content_tabs.addTab(overview_widget, "Overview")
    
    def _setup_functions_tab(self):
        """Setup functions management tab."""
        functions_widget = QWidget()
        functions_layout = QVBoxLayout(functions_widget)
        
        # Toolbar
        functions_toolbar = QHBoxLayout()
        
        add_function_btn = QPushButton("Add Function")
        add_function_btn.clicked.connect(self._add_function)
        functions_toolbar.addWidget(add_function_btn)
        
        functions_toolbar.addStretch()
        functions_layout.addLayout(functions_toolbar)
        
        # Functions table
        self.functions_table = QTableWidget()
        self.functions_table.setColumnCount(4)
        self.functions_table.setHorizontalHeaderLabels(["ID", "Name", "Description", "Criticality"])
        
        header = self.functions_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        
        self.functions_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.functions_table.doubleClicked.connect(self._edit_function)
        
        functions_layout.addWidget(self.functions_table)
        
        self.content_tabs.addTab(functions_widget, "Functions")
    
    def _setup_interfaces_tab(self):
        """Setup interfaces tab (placeholder)."""
        interfaces_widget = QWidget()
        interfaces_layout = QVBoxLayout(interfaces_widget)
        interfaces_layout.addWidget(QLabel("Interfaces - Coming Soon"))
        self.content_tabs.addTab(interfaces_widget, "Interfaces")
    
    def _setup_requirements_tab(self):
        """Setup requirements management tab."""
        requirements_widget = QWidget()
        requirements_layout = QVBoxLayout(requirements_widget)
        
        # Toolbar
        requirements_toolbar = QHBoxLayout()
        
        add_requirement_btn = QPushButton("Add Requirement")
        add_requirement_btn.clicked.connect(self._add_requirement)
        requirements_toolbar.addWidget(add_requirement_btn)
        
        requirements_toolbar.addStretch()
        requirements_layout.addLayout(requirements_toolbar)
        
        # Requirements table
        self.requirements_table = QTableWidget()
        self.requirements_table.setColumnCount(5)
        self.requirements_table.setHorizontalHeaderLabels(["ID", "Alphanumeric ID", "Text", "Verification", "Criticality"])
        
        header = self.requirements_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        
        self.requirements_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.requirements_table.doubleClicked.connect(self._edit_requirement)
        
        requirements_layout.addWidget(self.requirements_table)
        
        self.content_tabs.addTab(requirements_widget, "Requirements")
    
    def _on_system_selected(self, system_id: int):
        """Handle system selection from hierarchy tree."""
        try:
            self.current_system_id = system_id
            
            # Get system from database
            db_manager = self.database_initializer.get_database_manager()
            connection = db_manager.get_connection()
            
            system_data = connection.fetchone(
                "SELECT * FROM systems WHERE id = ?",
                (system_id,)
            )
            
            if system_data:
                system_dict = dict(system_data)
                system = System(**system_dict)
                
                # Update breadcrumb
                self.breadcrumb_label.setText(f"{system.get_hierarchical_id()} - {system.system_name}")
                
                # Update overview tab
                self.system_info_label.setText(f"""
                <h3>{system.system_name}</h3>
                <p><strong>ID:</strong> {system.get_hierarchical_id()}</p>
                <p><strong>Description:</strong> {system.system_description or 'No description'}</p>
                <p><strong>Baseline:</strong> {system.baseline}</p>
                <p><strong>Created:</strong> {system.created_date}</p>
                """)
                
                # Enable edit button
                self.edit_system_btn.setEnabled(True)
                
                # Load related entities
                self._load_functions_for_system(system_id)
                self._load_requirements_for_system(system_id)
                
                logger.info(f"System selected: {system.system_name}")
            
        except Exception as e:
            logger.error(f"Failed to load system details: {str(e)}")
            self.breadcrumb_label.setText("Error loading system")
    
    def _on_system_changed(self, system_id: int):
        """Handle system changes from hierarchy tree."""
        if system_id == self.current_system_id:
            # Refresh current system view
            self._on_system_selected(system_id)
    
    def _load_functions_for_system(self, system_id: int):
        """Load functions for the selected system."""
        try:
            db_manager = self.database_initializer.get_database_manager()
            connection = db_manager.get_connection()
            
            functions = connection.fetchall(
                "SELECT * FROM functions WHERE system_id = ? AND baseline = ? ORDER BY system_hierarchy",
                (system_id, "Working")
            )
            
            # Clear and populate functions table
            self.functions_table.setRowCount(len(functions))
            
            for row, func_data in enumerate(functions):
                func_dict = dict(func_data)
                function = Function(**func_dict)
                
                self.functions_table.setItem(row, 0, QTableWidgetItem(function.get_hierarchical_id()))
                self.functions_table.setItem(row, 1, QTableWidgetItem(function.function_name))
                self.functions_table.setItem(row, 2, QTableWidgetItem(function.function_description or ""))
                self.functions_table.setItem(row, 3, QTableWidgetItem(function.criticality or "Medium"))
                
                # Store function ID for editing
                self.functions_table.item(row, 0).setData(Qt.UserRole, function.id)
            
        except Exception as e:
            logger.error(f"Failed to load functions: {str(e)}")
    
    def _load_requirements_for_system(self, system_id: int):
        """Load requirements for the selected system."""
        try:
            db_manager = self.database_initializer.get_database_manager()
            connection = db_manager.get_connection()
            
            requirements = connection.fetchall(
                "SELECT * FROM requirements WHERE system_id = ? AND baseline = ? ORDER BY system_hierarchy",
                (system_id, "Working")
            )
            
            # Clear and populate requirements table
            self.requirements_table.setRowCount(len(requirements))
            
            for row, req_data in enumerate(requirements):
                req_dict = dict(req_data)
                requirement = Requirement(**req_dict)
                
                self.requirements_table.setItem(row, 0, QTableWidgetItem(requirement.get_hierarchical_id()))
                self.requirements_table.setItem(row, 1, QTableWidgetItem(requirement.alphanumeric_identifier or ""))
                self.requirements_table.setItem(row, 2, QTableWidgetItem(requirement.requirement_text[:100] + "..." if len(requirement.requirement_text) > 100 else requirement.requirement_text))
                self.requirements_table.setItem(row, 3, QTableWidgetItem(requirement.verification_method or ""))
                self.requirements_table.setItem(row, 4, QTableWidgetItem(requirement.criticality or "Medium"))
                
                # Store requirement ID for editing
                self.requirements_table.item(row, 0).setData(Qt.UserRole, requirement.id)
            
        except Exception as e:
            logger.error(f"Failed to load requirements: {str(e)}")
    
    def _edit_current_system(self):
        """Edit the currently selected system."""
        if not self.current_system_id:
            return
        
        try:
            # Get system from database
            db_manager = self.database_initializer.get_database_manager()
            connection = db_manager.get_connection()
            
            system_data = connection.fetchone(
                "SELECT * FROM systems WHERE id = ?",
                (self.current_system_id,)
            )
            
            if system_data:
                system_dict = dict(system_data)
                system = System(**system_dict)
                
                # Open edit dialog
                dialog = SystemEditDialog(system, parent=self)
                dialog.system_saved.connect(self._on_system_saved)
                dialog.exec()
        
        except Exception as e:
            logger.error(f"Failed to edit system: {str(e)}")
    
    def _add_function(self):
        """Add a new function to the current system."""
        if not self.current_system_id:
            QMessageBox.warning(self, "No System Selected", "Please select a system first.")
            return
        
        dialog = FunctionEditDialog(system_id=self.current_system_id, parent=self)
        dialog.function_saved.connect(self._on_function_saved)
        dialog.exec()
    
    def _edit_function(self):
        """Edit selected function."""
        current_row = self.functions_table.currentRow()
        if current_row < 0:
            return
        
        function_id = self.functions_table.item(current_row, 0).data(Qt.UserRole)
        if not function_id:
            return
        
        try:
            # Get function from database
            db_manager = self.database_initializer.get_database_manager()
            connection = db_manager.get_connection()
            
            function_data = connection.fetchone(
                "SELECT * FROM functions WHERE id = ?",
                (function_id,)
            )
            
            if function_data:
                func_dict = dict(function_data)
                function = Function(**func_dict)
                
                dialog = FunctionEditDialog(function, parent=self)
                dialog.function_saved.connect(self._on_function_saved)
                dialog.exec()
        
        except Exception as e:
            logger.error(f"Failed to edit function: {str(e)}")
    
    def _add_requirement(self):
        """Add a new requirement to the current system."""
        if not self.current_system_id:
            QMessageBox.warning(self, "No System Selected", "Please select a system first.")
            return
        
        dialog = RequirementEditDialog(system_id=self.current_system_id, parent=self)
        dialog.requirement_saved.connect(self._on_requirement_saved)
        dialog.exec()
    
    def _edit_requirement(self):
        """Edit selected requirement."""
        current_row = self.requirements_table.currentRow()
        if current_row < 0:
            return
        
        requirement_id = self.requirements_table.item(current_row, 0).data(Qt.UserRole)
        if not requirement_id:
            return
        
        try:
            # Get requirement from database
            db_manager = self.database_initializer.get_database_manager()
            connection = db_manager.get_connection()
            
            requirement_data = connection.fetchone(
                "SELECT * FROM requirements WHERE id = ?",
                (requirement_id,)
            )
            
            if requirement_data:
                req_dict = dict(requirement_data)
                requirement = Requirement(**req_dict)
                
                dialog = RequirementEditDialog(requirement, parent=self)
                dialog.requirement_saved.connect(self._on_requirement_saved)
                dialog.exec()
        
        except Exception as e:
            logger.error(f"Failed to edit requirement: {str(e)}")
    
    def _on_system_saved(self, system: System):
        """Handle system save event."""
        try:
            db_manager = self.database_initializer.get_database_manager()
            connection = db_manager.get_connection()
            system_repo = EntityFactory.get_repository(connection, System)
            
            if system.id is None:
                # New system
                saved_system = system_repo.create(system)
                if saved_system:
                    self.hierarchy_tree.add_system(saved_system)
                    self.hierarchy_tree.select_system(saved_system.id)
                    logger.info(f"Created new system: {saved_system.system_name}")
            else:
                # Update existing system
                if system_repo.update(system):
                    self.hierarchy_tree.update_system(system)
                    if system.id == self.current_system_id:
                        self._on_system_selected(system.id)
                    logger.info(f"Updated system: {system.system_name}")
        
        except Exception as e:
            logger.error(f"Failed to save system: {str(e)}")
            QMessageBox.critical(self, "Save Failed", f"Failed to save system: {str(e)}")
    
    def _on_function_saved(self, function: Function):
        """Handle function save event."""
        try:
            db_manager = self.database_initializer.get_database_manager()
            connection = db_manager.get_connection()
            function_repo = EntityFactory.get_repository(connection, Function)
            
            if function.id is None:
                # New function
                saved_function = function_repo.create(function)
                if saved_function:
                    self._load_functions_for_system(self.current_system_id)
                    logger.info(f"Created new function: {saved_function.function_name}")
            else:
                # Update existing function
                if function_repo.update(function):
                    self._load_functions_for_system(self.current_system_id)
                    logger.info(f"Updated function: {function.function_name}")
        
        except Exception as e:
            logger.error(f"Failed to save function: {str(e)}")
            QMessageBox.critical(self, "Save Failed", f"Failed to save function: {str(e)}")
    
    def _on_requirement_saved(self, requirement: Requirement):
        """Handle requirement save event."""
        try:
            db_manager = self.database_initializer.get_database_manager()
            connection = db_manager.get_connection()
            requirement_repo = EntityFactory.get_repository(connection, Requirement)
            
            if requirement.id is None:
                # New requirement
                saved_requirement = requirement_repo.create(requirement)
                if saved_requirement:
                    self._load_requirements_for_system(self.current_system_id)
                    logger.info(f"Created new requirement: {saved_requirement.alphanumeric_identifier}")
            else:
                # Update existing requirement
                if requirement_repo.update(requirement):
                    self._load_requirements_for_system(self.current_system_id)
                    logger.info(f"Updated requirement: {requirement.alphanumeric_identifier}")
        
        except Exception as e:
            logger.error(f"Failed to save requirement: {str(e)}")
            QMessageBox.critical(self, "Save Failed", f"Failed to save requirement: {str(e)}")
    
    def _setup_menus(self):
        """Setup the application menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        # New action
        new_action = QAction("&New Project", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self._new_project)
        file_menu.addAction(new_action)
        
        # Open action
        open_action = QAction("&Open Project", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._open_project)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        # Export actions
        export_menu = file_menu.addMenu("&Export")
        
        json_export_action = QAction("Export as &JSON", self)
        json_export_action.triggered.connect(self._export_json)
        export_menu.addAction(json_export_action)
        
        md_export_action = QAction("Export as &Markdown", self)
        md_export_action.triggered.connect(self._export_markdown)
        export_menu.addAction(md_export_action)
        
        export_menu.addSeparator()
        
        archive_export_action = QAction("Export &Working Directory", self)
        archive_export_action.triggered.connect(self._export_working_directory)
        export_menu.addAction(archive_export_action)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        
        # Baseline actions
        baseline_menu = edit_menu.addMenu("&Baseline")
        
        create_baseline_action = QAction("&Create Baseline", self)
        create_baseline_action.triggered.connect(self._create_baseline)
        baseline_menu.addAction(create_baseline_action)
        
        manage_baselines_action = QAction("&Manage Baselines", self)
        manage_baselines_action.triggered.connect(self._manage_baselines)
        baseline_menu.addAction(manage_baselines_action)
        
        baseline_menu.addSeparator()
        
        load_baseline_action = QAction("&Load Baseline", self)
        load_baseline_action.triggered.connect(self._load_baseline)
        baseline_menu.addAction(load_baseline_action)
        
        # Collaboration menu
        collaboration_menu = menubar.addMenu("&Collaboration")
        
        # Branch actions
        branch_menu = collaboration_menu.addMenu("&Branches")
        
        create_branch_action = QAction("&Create Branch", self)
        create_branch_action.triggered.connect(self._create_branch)
        branch_menu.addAction(create_branch_action)
        
        manage_branches_action = QAction("&Manage Branches", self)
        manage_branches_action.triggered.connect(self._manage_branches)
        branch_menu.addAction(manage_branches_action)
        
        collaboration_menu.addSeparator()
        
        merge_branch_action = QAction("&Merge Branch", self)
        merge_branch_action.triggered.connect(self._merge_branch)
        collaboration_menu.addAction(merge_branch_action)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _setup_toolbar(self):
        """Setup the application toolbar."""
        toolbar = self.addToolBar("Main")
        
        # Add common actions to toolbar
        # TODO: Add actual toolbar actions
        pass
    
    def _setup_status_bar(self):
        """Setup the status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Database status
        if self.database_initializer:
            db_manager = self.database_initializer.get_database_manager()
            if db_manager.is_healthy():
                db_status = "Database: Connected"
                db_info = self.database_initializer.get_database_info()
                if 'tables' in db_info and 'systems' in db_info['tables']:
                    systems_count = db_info['tables']['systems']
                    db_status += f" ({systems_count} systems)"
            else:
                db_status = "Database: Error"
        else:
            db_status = "Database: Not initialized"
            
        self.db_label = QLabel(db_status)
        self.status_bar.addPermanentWidget(self.db_label)
        
        # Baseline status
        self.baseline_label = QLabel("Baseline: Working")
        self.status_bar.addPermanentWidget(self.baseline_label)
        
        # Default status message
        self.status_bar.showMessage("Ready")
    
    def _restore_window_state(self):
        """Restore window state from configuration."""
        if not self.config_manager:
            return
        
        ui_config = self.config_manager.config.ui
        
        # Restore window size
        self.resize(ui_config.window_width, ui_config.window_height)
        
        # Restore maximized state
        if ui_config.window_maximized:
            self.showMaximized()
        
        # Restore splitter sizes
        if ui_config.splitter_sizes and self.splitter:
            self.splitter.setSizes(ui_config.splitter_sizes)
    
    def save_ui_state(self):
        """Save current UI state to configuration."""
        if not self.config_manager:
            return
        
        # Save window size and state
        self.config_manager.update_ui_state(
            window_width=self.width(),
            window_height=self.height(),
            window_maximized=self.isMaximized(),
            splitter_sizes=self.splitter.sizes() if self.splitter else None
        )
    
    def closeEvent(self, event):
        """Handle window close event."""
        self.save_ui_state()
        event.accept()
    
    # Menu action handlers (placeholders for now)
    def _new_project(self):
        """Handle new project action."""
        logger.info("New project action triggered")
        # TODO: Implement new project functionality
    
    def _open_project(self):
        """Handle open project action."""
        logger.info("Open project action triggered")
        # TODO: Implement open project functionality
    
    def _export_json(self):
        """Handle JSON export action."""
        logger.info("JSON export action triggered")
        
        # Check if we have a selected system
        if not self.current_system_id:
            QMessageBox.warning(
                self, 
                "No System Selected", 
                "Please select a system in the hierarchy tree before exporting."
            )
            return
        
        # Check database connection
        if not self.database_initializer:
            QMessageBox.warning(self, "No Database", "No database connection available.")
            return
        
        try:
            db_manager = self.database_initializer.get_database_manager()
            db_connection = db_manager.get_connection()
            
            dialog = JsonExportDialog(self, db_connection, self.current_system_id)
            dialog.exec()
            
        except Exception as e:
            logger.error(f"Error opening JSON export dialog: {str(e)}")
            QMessageBox.critical(
                self,
                "Export Error",
                f"Failed to open JSON export dialog:\n\n{str(e)}"
            )
    
    def _export_markdown(self):
        """Handle Markdown export action."""
        logger.info("Markdown export action triggered")
        
        # Check if we have a selected system
        if not self.current_system_id:
            QMessageBox.warning(
                self, 
                "No System Selected", 
                "Please select a system in the hierarchy tree before exporting."
            )
            return
        
        # Check database connection
        if not self.database_initializer:
            QMessageBox.warning(self, "No Database", "No database connection available.")
            return
        
        try:
            db_manager = self.database_initializer.get_database_manager()
            db_connection = db_manager.get_connection()
            
            dialog = MarkdownExportDialog(self, db_connection, self.current_system_id)
            dialog.exec()
            
        except Exception as e:
            logger.error(f"Error opening Markdown export dialog: {str(e)}")
            QMessageBox.critical(
                self,
                "Export Error",
                f"Failed to open Markdown export dialog:\n\n{str(e)}"
            )
    
    def _export_working_directory(self):
        """Handle working directory export action."""
        logger.info("Working directory export action triggered")
        
        # Get the working directory from config
        if not self.config_manager:
            QMessageBox.warning(self, "No Configuration", "No configuration manager available.")
            return
        
        try:
            config = self.config_manager.get_config()
            working_dir = config.get('working_directory')
            
            if not working_dir or not os.path.exists(working_dir):
                QMessageBox.warning(
                    self,
                    "No Working Directory",
                    "No valid working directory configured."
                )
                return
            
            dialog = ArchiveExportDialog(self, working_dir)
            dialog.exec()
            
        except Exception as e:
            logger.error(f"Error opening working directory export dialog: {str(e)}")
            QMessageBox.critical(
                self,
                "Export Error",
                f"Failed to open working directory export dialog:\n\n{str(e)}"
            )
    
    def _create_baseline(self):
        """Handle create baseline action."""
        logger.info("Create baseline action triggered")
        
        if not self.baseline_manager:
            QMessageBox.warning(self, "No Baseline Manager", "Baseline management is not available.")
            return
        
        try:
            dialog = BaselineCreationDialog(self, self.baseline_manager)
            dialog.exec()
            
        except Exception as e:
            logger.error(f"Error opening baseline creation dialog: {str(e)}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to open baseline creation dialog:\n\n{str(e)}"
            )
    
    def _manage_baselines(self):
        """Handle manage baselines action."""
        logger.info("Manage baselines action triggered")
        
        if not self.baseline_manager:
            QMessageBox.warning(self, "No Baseline Manager", "Baseline management is not available.")
            return
        
        try:
            dialog = BaselineManagementDialog(self, self.baseline_manager)
            dialog.exec()
            
        except Exception as e:
            logger.error(f"Error opening baseline management dialog: {str(e)}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to open baseline management dialog:\n\n{str(e)}"
            )
    
    def _load_baseline(self):
        """Handle load baseline action."""
        logger.info("Load baseline action triggered")
        
        if not self.baseline_manager:
            QMessageBox.warning(self, "No Baseline Manager", "Baseline management is not available.")
            return
        
        # Open baseline management dialog in load mode
        self._manage_baselines()
    
    def _create_branch(self):
        """Handle create branch action."""
        logger.info("Create branch action triggered")
        
        if not self.branch_manager:
            QMessageBox.warning(self, "No Branch Manager", "Branch management is not available.")
            return
        
        if not self.database_initializer:
            QMessageBox.warning(self, "No Database", "No database connection available.")
            return
        
        try:
            db_manager = self.database_initializer.get_database_manager()
            db_connection = db_manager.get_connection()
            
            dialog = BranchCreationDialog(self, self.branch_manager, db_connection)
            dialog.exec()
            
        except Exception as e:
            logger.error(f"Error opening branch creation dialog: {str(e)}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to open branch creation dialog:\n\n{str(e)}"
            )
    
    def _manage_branches(self):
        """Handle manage branches action."""
        logger.info("Manage branches action triggered")
        
        if not self.branch_manager or not self.merge_manager:
            QMessageBox.warning(self, "No Branch Manager", "Branch management is not available.")
            return
        
        try:
            dialog = BranchManagementDialog(self, self.branch_manager, self.merge_manager)
            dialog.exec()
            
        except Exception as e:
            logger.error(f"Error opening branch management dialog: {str(e)}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to open branch management dialog:\n\n{str(e)}"
            )
    
    def _merge_branch(self):
        """Handle merge branch action."""
        logger.info("Merge branch action triggered")
        
        if not self.merge_manager:
            QMessageBox.warning(self, "No Merge Manager", "Merge functionality is not available.")
            return
        
        # Open branch management dialog which includes merge functionality
        self._manage_branches()
    
    def _show_about(self):
        """Show about dialog."""
        from PySide6.QtWidgets import QMessageBox
        from ..config.constants import APP_VERSION, APP_AUTHOR
        
        QMessageBox.about(
            self,
            f"About {APP_NAME}",
            f"""
            <h3>{APP_NAME}</h3>
            <p>Version: {APP_VERSION}</p>
            <p>Author: {APP_AUTHOR}</p>
            <p>A Systems-Theoretic Process Analysis Tool</p>
            """
        )
    
    def _setup_interfaces_tab(self):
        """Setup interfaces management tab."""
        try:
            self.interfaces_widget = InterfaceWidget(self.database_initializer)
            self.content_tabs.addTab(self.interfaces_widget, "Interfaces")
        except Exception as e:
            logger.error(f"Failed to setup interfaces tab: {str(e)}")
            # Add fallback placeholder
            interfaces_widget = QWidget()
            interfaces_layout = QVBoxLayout(interfaces_widget)
            interfaces_layout.addWidget(QLabel("Interfaces - Setup Error"))
            self.content_tabs.addTab(interfaces_widget, "Interfaces")
    
    def _setup_assets_tab(self):
        """Setup assets management tab."""
        try:
            self.assets_widget = AssetWidget(self.database_initializer)
            self.content_tabs.addTab(self.assets_widget, "Assets")
        except Exception as e:
            logger.error(f"Failed to setup assets tab: {str(e)}")
            # Add fallback placeholder
            assets_widget = QWidget()
            assets_layout = QVBoxLayout(assets_widget)
            assets_layout.addWidget(QLabel("Assets - Setup Error"))
            self.content_tabs.addTab(assets_widget, "Assets")
    
    def _setup_hazards_tab(self):
        """Setup hazards management tab."""
        try:
            self.hazards_widget = HazardWidget(self.database_initializer)
            self.content_tabs.addTab(self.hazards_widget, "Hazards")
        except Exception as e:
            logger.error(f"Failed to setup hazards tab: {str(e)}")
            # Add fallback placeholder
            hazards_widget = QWidget()
            hazards_layout = QVBoxLayout(hazards_widget)
            hazards_layout.addWidget(QLabel("Hazards - Setup Error"))
            self.content_tabs.addTab(hazards_widget, "Hazards")
    
    def _setup_losses_tab(self):
        """Setup losses management tab."""
        try:
            self.losses_widget = LossWidget(self.database_initializer)
            self.content_tabs.addTab(self.losses_widget, "Losses")
        except Exception as e:
            logger.error(f"Failed to setup losses tab: {str(e)}")
            # Add fallback placeholder
            losses_widget = QWidget()
            losses_layout = QVBoxLayout(losses_widget)
            losses_layout.addWidget(QLabel("Losses - Setup Error"))
            self.content_tabs.addTab(losses_widget, "Losses")
    
    def _setup_control_structures_tab(self):
        """Setup control structures management tab."""
        try:
            self.control_structures_widget = ControlStructureWidget(self.database_initializer)
            self.content_tabs.addTab(self.control_structures_widget, "Control Structures")
        except Exception as e:
            logger.error(f"Failed to setup control structures tab: {str(e)}")
            # Add fallback placeholder
            control_structures_widget = QWidget()
            control_structures_layout = QVBoxLayout(control_structures_widget)
            control_structures_layout.addWidget(QLabel("Control Structures - Setup Error"))
            self.content_tabs.addTab(control_structures_widget, "Control Structures")
    
    def _setup_controllers_tab(self):
        """Setup controllers management tab."""
        try:
            self.controllers_widget = ControllerWidget(self.database_initializer)
            self.content_tabs.addTab(self.controllers_widget, "Controllers")
        except Exception as e:
            logger.error(f"Failed to setup controllers tab: {str(e)}")
            # Add fallback placeholder
            controllers_widget = QWidget()
            controllers_layout = QVBoxLayout(controllers_widget)
            controllers_layout.addWidget(QLabel("Controllers - Setup Error"))
            self.content_tabs.addTab(controllers_widget, "Controllers")
    
    def _setup_diagram_components(self):
        """Initialize diagram generation and rendering components."""
        try:
            working_directory = self.config_manager.working_directory
            
            # Initialize diagram renderer
            self.diagram_renderer = DiagramRenderer()
            
            # Initialize diagram generator with output directory
            diagram_output_dir = working_directory / 'diagrams'
            self.diagram_generator = DiagramGenerator(diagram_output_dir)
            
            logger.info("Diagram components initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize diagram components: {str(e)}")
    
    def _setup_collaboration_components(self):
        """Setup baseline and collaboration managers."""
        try:
            if not self.database_initializer or not self.config_manager:
                return
            
            # Get database connection and working directory
            db_manager = self.database_initializer.get_database_manager()
            db_connection = db_manager.get_connection()
            
            config = self.config_manager.get_config()
            working_directory = config.get('working_directory', '')
            
            if not working_directory:
                logger.warning("No working directory configured for collaboration components")
                return
            
            # Initialize managers
            self.baseline_manager = BaselineManager(db_connection, working_directory)
            self.branch_manager = BranchManager(db_connection, working_directory)
            self.merge_manager = MergeManager(db_connection, working_directory)
            
            # Ensure baseline metadata table exists
            self.baseline_manager.ensure_baseline_metadata_table()
            
            logger.info("Collaboration components initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to setup collaboration components: {str(e)}")
    
    def _setup_diagrams_tab(self):
        """Setup diagrams management tab."""
        try:
            # Create diagram tab widget
            diagrams_widget = QWidget()
            diagrams_layout = QVBoxLayout(diagrams_widget)
            
            # Create diagram controls
            controls_layout = QHBoxLayout()
            
            # Diagram type selector
            self.diagram_type_combo = QComboBox()
            self.diagram_type_combo.addItem("Control Structure", DiagramType.CONTROL_STRUCTURE)
            self.diagram_type_combo.addItem("State Diagram", DiagramType.STATE_DIAGRAM)
            self.diagram_type_combo.addItem("Requirement Hierarchy", DiagramType.REQUIREMENT_HIERARCHY)
            self.diagram_type_combo.addItem("System Hierarchy", DiagramType.SYSTEM_HIERARCHY)
            
            # Generate button
            generate_btn = QPushButton("Generate Diagram")
            generate_btn.clicked.connect(self._generate_diagram)
            
            # Refresh button
            refresh_btn = QPushButton("Refresh")
            refresh_btn.clicked.connect(self._refresh_diagrams)
            
            controls_layout.addWidget(QLabel("Type:"))
            controls_layout.addWidget(self.diagram_type_combo)
            controls_layout.addWidget(generate_btn)
            controls_layout.addWidget(refresh_btn)
            controls_layout.addStretch()
            
            diagrams_layout.addLayout(controls_layout)
            
            # Create diagram viewer
            self.diagram_viewer = DiagramViewer()
            diagrams_layout.addWidget(self.diagram_viewer)
            
            self.content_tabs.addTab(diagrams_widget, "Diagrams")
            
        except Exception as e:
            logger.error(f"Failed to setup diagrams tab: {str(e)}")
            # Add fallback placeholder
            diagrams_widget = QWidget()
            diagrams_layout = QVBoxLayout(diagrams_widget)
            diagrams_layout.addWidget(QLabel("Diagrams - Setup Error"))
            self.content_tabs.addTab(diagrams_widget, "Diagrams")
    
    def _generate_diagram(self):
        """Generate diagram for current system."""
        if not self.current_system_id:
            QMessageBox.warning(self, "No System Selected", "Please select a system to generate a diagram.")
            return
        
        if not self.diagram_generator or not self.diagram_renderer:
            QMessageBox.critical(self, "Diagram Error", "Diagram components not properly initialized.")
            return
        
        try:
            # Get selected diagram type
            diagram_type = self.diagram_type_combo.currentData()
            
            # Generate diagram based on type
            mermaid_source = ""
            diagram_name = f"system_{self.current_system_id}_{diagram_type.value}"
            
            if diagram_type == DiagramType.CONTROL_STRUCTURE:
                mermaid_source = self.diagram_generator.generate_control_structure_diagram(
                    self.current_system_id
                )
            elif diagram_type == DiagramType.STATE_DIAGRAM:
                mermaid_source = self.diagram_generator.generate_state_diagram(
                    self.current_system_id
                )
            elif diagram_type == DiagramType.REQUIREMENT_HIERARCHY:
                mermaid_source = self.diagram_generator.generate_requirement_hierarchy_diagram(
                    self.current_system_id
                )
            elif diagram_type == DiagramType.SYSTEM_HIERARCHY:
                mermaid_source = self.diagram_generator.generate_system_hierarchy_diagram(
                    self.current_system_id
                )
            
            if not mermaid_source:
                QMessageBox.warning(self, "Generation Error", "Failed to generate diagram source.")
                return
            
            # Render diagram
            output_files = self.diagram_renderer.render_diagram(
                mermaid_source,
                diagram_name,
                diagram_type,
                output_formats=['svg', 'png']
            )
            
            # Load SVG in viewer
            if 'svg' in output_files:
                self.diagram_viewer.load_diagram(output_files['svg'])
                QMessageBox.information(
                    self, 
                    "Diagram Generated", 
                    f"Diagram generated successfully!\nSVG: {output_files['svg']}"
                )
            else:
                QMessageBox.warning(self, "Render Error", "Failed to render diagram to SVG.")
                
        except Exception as e:
            logger.error(f"Error generating diagram: {str(e)}")
            QMessageBox.critical(
                self, 
                "Diagram Generation Error", 
                f"Failed to generate diagram:\n{str(e)}"
            )
    
    def _refresh_diagrams(self):
        """Refresh diagram display."""
        if self.diagram_viewer:
            # Could implement gallery refresh here
            logger.info("Diagram refresh requested")