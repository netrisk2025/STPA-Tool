"""
Main window for STPA Tool
Contains the primary user interface layout and components.
"""

import os
from PySide6.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QSplitter,
    QMenuBar, QStatusBar, QToolBar, QLabel, QTreeWidget, QTabWidget,
    QTableWidget, QTableWidgetItem, QPushButton, QHeaderView, QMessageBox,
    QComboBox, QDialog, QGroupBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QIcon

from ..config.settings import ConfigManager
from ..config.constants import (
    APP_NAME, WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT, SPLITTER_DEFAULT_SIZES
)
from ..log_config.config import get_logger
from .hierarchy_tree import HierarchyTreeWidget
from .entity_dialogs import (
    SystemEditDialog, FunctionEditDialog, RequirementEditDialog,
    InterfaceEditDialog, AssetEditDialog, HazardEditDialog,
    LossEditDialog, ControlStructureEditDialog, ControllerEditDialog
)
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
from ..diagrams.generator import DiagramGenerator
from ..diagrams.renderer import DiagramRenderer
from ..diagrams.viewer import DiagramViewer
from ..database.baseline_manager import BaselineManager
from ..collaboration import BranchManager, MergeManager

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
    
    def _setup_diagram_components(self):
        """Setup diagram generation and viewing components."""
        try:
            # Get working directory from config manager
            working_dir = self.config_manager.working_directory
            if not working_dir:
                logger.warning("Working directory not set. Diagrams will not be saved.")
                return

            # Get diagrams output directory from config
            diagrams_output_dir_name = self.config_manager.config.diagrams.output_dir
            diagrams_path = working_dir / diagrams_output_dir_name

            # Create components
            self.diagram_generator = DiagramGenerator(output_dir=diagrams_path)
            self.diagram_renderer = DiagramRenderer()
            self.diagram_viewer = DiagramViewer(parent=self)
            
            logger.info("Diagram components initialized.")

        except Exception as e:
            logger.error(f"Failed to initialize diagram components: {e}")
            QMessageBox.critical(self, "Diagram Initialization Error",
                                 f"Could not initialize diagram components: {e}")
    
    def _setup_collaboration_components(self):
        """Setup collaboration and baseline management components."""
        try:
            # Initialize baseline manager
            if self.database_initializer:
                db_manager = self.database_initializer.get_database_manager()
                self.baseline_manager = BaselineManager(db_manager)
                
                # Initialize branch and merge managers
                self.branch_manager = BranchManager(db_manager)
                self.merge_manager = MergeManager(db_manager)
                
                logger.info("Collaboration components initialized.")
            else:
                logger.warning("Database initializer not available. Collaboration features disabled.")
                
        except Exception as e:
            logger.error(f"Failed to initialize collaboration components: {e}")
            # Don't show error dialog here as it might be called during initialization
            # Just log the error and continue
    
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
        
        # System Information Section
        info_group = QGroupBox("System Information")
        info_layout = QVBoxLayout(info_group)
        
        self.system_info_label = QLabel("Select a system to view details")
        self.system_info_label.setWordWrap(True)
        info_layout.addWidget(self.system_info_label)
        
        overview_layout.addWidget(info_group)
        
        # System Management Section
        management_group = QGroupBox("System Management")
        management_layout = QVBoxLayout(management_group)
        
        # Edit system button
        self.edit_system_btn = QPushButton("Edit System")
        self.edit_system_btn.setEnabled(False)
        self.edit_system_btn.clicked.connect(self._edit_current_system)
        management_layout.addWidget(self.edit_system_btn)
        
        # Add child system button
        self.add_child_system_btn = QPushButton("Add Child System")
        self.add_child_system_btn.setEnabled(False)
        self.add_child_system_btn.clicked.connect(self._add_child_system)
        management_layout.addWidget(self.add_child_system_btn)
        
        overview_layout.addWidget(management_group)
        
        overview_layout.addStretch()
        self.content_tabs.addTab(overview_widget, "Overview")
    
    def _setup_functions_tab(self):
        """Setup functions management tab."""
        functions_widget = QWidget()
        functions_layout = QVBoxLayout(functions_widget)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        self.add_function_btn = QPushButton("Add Function")
        self.add_function_btn.clicked.connect(self._add_function)
        toolbar.addWidget(self.add_function_btn)
        
        self.edit_function_btn = QPushButton("Edit Function")
        self.edit_function_btn.clicked.connect(self._edit_function)
        self.edit_function_btn.setEnabled(False)
        toolbar.addWidget(self.edit_function_btn)

        self.delete_function_btn = QPushButton("Delete Function")
        self.delete_function_btn.clicked.connect(self._delete_function)
        self.delete_function_btn.setEnabled(False)
        toolbar.addWidget(self.delete_function_btn)
        
        toolbar.addStretch()
        functions_layout.addLayout(toolbar)
        
        # Functions table
        self.functions_table = QTableWidget()
        self.functions_table.setColumnCount(4)
        self.functions_table.setHorizontalHeaderLabels(["ID", "Name", "Description", "Criticality"])
        
        header = self.functions_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        
        self.functions_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.functions_table.itemSelectionChanged.connect(self._update_function_buttons_state)
        self.functions_table.doubleClicked.connect(self._edit_function)
        
        functions_layout.addWidget(self.functions_table)
        
        self.content_tabs.addTab(functions_widget, "Functions")
    
    def _update_function_buttons_state(self):
        """Enable/disable function buttons based on selection."""
        has_selection = bool(self.functions_table.selectedItems())
        self.edit_function_btn.setEnabled(has_selection)
        self.delete_function_btn.setEnabled(has_selection)
        
    def _delete_function(self):
        """Delete the selected function."""
        selected_items = self.functions_table.selectedItems()
        if not selected_items:
            return
            
        function_id = selected_items[0].data(Qt.UserRole)
        function_name = selected_items[1].text()
        
        reply = QMessageBox.question(
            self,
            "Delete Function",
            f"Are you sure you want to delete function '{function_name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                db_manager = self.database_initializer.get_database_manager()
                connection = db_manager.get_connection()
                repo = EntityFactory.get_repository(connection, Function)
                if repo.delete(function_id):
                    logger.info(f"Deleted function: {function_name} (ID: {function_id})")
                    if self.current_system_id:
                        self._load_functions_for_system(self.current_system_id)
                else:
                    self._show_error("Delete Failed", "Failed to delete function from database.")
            except Exception as e:
                logger.error(f"Failed to delete function: {str(e)}")
                self._show_error("Delete Failed", str(e))
    
    def _setup_requirements_tab(self):
        """Setup requirements management tab."""
        requirements_widget = QWidget()
        requirements_layout = QVBoxLayout(requirements_widget)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        self.add_requirement_btn = QPushButton("Add Requirement")
        self.add_requirement_btn.clicked.connect(self._add_requirement)
        toolbar.addWidget(self.add_requirement_btn)
        
        self.edit_requirement_btn = QPushButton("Edit Requirement")
        self.edit_requirement_btn.clicked.connect(self._edit_requirement)
        self.edit_requirement_btn.setEnabled(False)
        toolbar.addWidget(self.edit_requirement_btn)

        self.delete_requirement_btn = QPushButton("Delete Requirement")
        self.delete_requirement_btn.clicked.connect(self._delete_requirement)
        self.delete_requirement_btn.setEnabled(False)
        toolbar.addWidget(self.delete_requirement_btn)

        toolbar.addStretch()
        requirements_layout.addLayout(toolbar)
        
        # Requirements table
        self.requirements_table = QTableWidget()
        self.requirements_table.setColumnCount(5)
        self.requirements_table.setHorizontalHeaderLabels(["ID", "Alphanumeric ID", "Requirement Text", "Verification Method", "Criticality"])
        
        header = self.requirements_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        
        self.requirements_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.requirements_table.itemSelectionChanged.connect(self._update_requirement_buttons_state)
        self.requirements_table.doubleClicked.connect(self._edit_requirement)
        
        requirements_layout.addWidget(self.requirements_table)
        
        self.content_tabs.addTab(requirements_widget, "Requirements")

    def _update_requirement_buttons_state(self):
        """Enable/disable requirement buttons based on selection."""
        has_selection = bool(self.requirements_table.selectedItems())
        self.edit_requirement_btn.setEnabled(has_selection)
        self.delete_requirement_btn.setEnabled(has_selection)

    def _delete_requirement(self):
        """Delete the selected requirement."""
        selected_items = self.requirements_table.selectedItems()
        if not selected_items:
            return
            
        requirement_id = selected_items[0].data(Qt.UserRole)
        requirement_name = selected_items[1].text()
        
        reply = QMessageBox.question(
            self,
            "Delete Requirement",
            f"Are you sure you want to delete requirement '{requirement_name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                db_manager = self.database_initializer.get_database_manager()
                connection = db_manager.get_connection()
                repo = EntityFactory.get_repository(connection, Requirement)
                if repo.delete(requirement_id):
                    logger.info(f"Deleted requirement: {requirement_name} (ID: {requirement_id})")
                    if self.current_system_id:
                        self._load_requirements_for_system(self.current_system_id)
                else:
                    self._show_error("Delete Failed", "Failed to delete requirement from database.")
            except Exception as e:
                logger.error(f"Failed to delete requirement: {str(e)}")
                self._show_error("Delete Failed", str(e))

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

                items = [
                    QTableWidgetItem(requirement.get_hierarchical_id()),
                    QTableWidgetItem(requirement.alphanumeric_identifier or ""),
                    QTableWidgetItem(requirement.requirement_text[:100] + "..." if len(requirement.requirement_text) > 100 else requirement.requirement_text),
                    QTableWidgetItem(requirement.verification_method or ""),
                    QTableWidgetItem(requirement.criticality or "Medium")
                ]

                for item in items:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)

                for col, item in enumerate(items):
                    self.requirements_table.setItem(row, col, item)
                
                # Store requirement ID for editing
                self.requirements_table.item(row, 0).setData(Qt.UserRole, requirement.id)
            
        except Exception as e:
            logger.error(f"Failed to load requirements: {str(e)}")
    
    def _setup_interfaces_tab(self):
        """Setup interfaces management tab."""
        interfaces_widget = QWidget()
        interfaces_layout = QVBoxLayout(interfaces_widget)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        self.add_interface_btn = QPushButton("Add Interface")
        self.add_interface_btn.clicked.connect(self._add_interface)
        toolbar.addWidget(self.add_interface_btn)
        
        self.edit_interface_btn = QPushButton("Edit Interface")
        self.edit_interface_btn.clicked.connect(self._edit_interface)
        self.edit_interface_btn.setEnabled(False)
        toolbar.addWidget(self.edit_interface_btn)

        self.delete_interface_btn = QPushButton("Delete Interface")
        self.delete_interface_btn.clicked.connect(self._delete_interface)
        self.delete_interface_btn.setEnabled(False)
        toolbar.addWidget(self.delete_interface_btn)
        
        toolbar.addStretch()
        interfaces_layout.addLayout(toolbar)
        
        # Interfaces table
        self.interfaces_table = QTableWidget()
        self.interfaces_table.setColumnCount(4)
        self.interfaces_table.setHorizontalHeaderLabels(["ID", "Name", "System", "Description"])
        
        header = self.interfaces_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        
        self.interfaces_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.interfaces_table.itemSelectionChanged.connect(self._update_interface_buttons_state)
        self.interfaces_table.doubleClicked.connect(self._edit_interface)
        
        interfaces_layout.addWidget(self.interfaces_table)
        
        self.content_tabs.addTab(interfaces_widget, "Interfaces")

    def _update_interface_buttons_state(self):
        """Enable/disable interface buttons based on selection."""
        has_selection = bool(self.interfaces_table.selectedItems())
        self.edit_interface_btn.setEnabled(has_selection)
        self.delete_interface_btn.setEnabled(has_selection)
        
    def _delete_interface(self):
        """Delete the selected interface."""
        selected_items = self.interfaces_table.selectedItems()
        if not selected_items:
            return
            
        interface_id = selected_items[0].data(Qt.UserRole)
        interface_name = selected_items[1].text()
        
        reply = QMessageBox.question(
            self,
            "Delete Interface",
            f"Are you sure you want to delete interface '{interface_name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                db_manager = self.database_initializer.get_database_manager()
                connection = db_manager.get_connection()
                repo = EntityFactory.get_repository(connection, Interface)
                if repo.delete(interface_id):
                    logger.info(f"Deleted interface: {interface_name} (ID: {interface_id})")
                    if self.current_system_id:
                        self._load_interfaces_for_system(self.current_system_id)
                else:
                    self._show_error("Delete Failed", "Failed to delete interface from database.")
            except Exception as e:
                logger.error(f"Failed to delete interface: {str(e)}")
                self._show_error("Delete Failed", str(e))

    def _setup_assets_tab(self):
        """Setup assets management tab."""
        assets_widget = QWidget()
        assets_layout = QVBoxLayout(assets_widget)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        self.add_asset_btn = QPushButton("Add Asset")
        self.add_asset_btn.clicked.connect(self._add_asset)
        toolbar.addWidget(self.add_asset_btn)
        
        self.edit_asset_btn = QPushButton("Edit Asset")
        self.edit_asset_btn.clicked.connect(self._edit_asset)
        self.edit_asset_btn.setEnabled(False)
        toolbar.addWidget(self.edit_asset_btn)

        self.delete_asset_btn = QPushButton("Delete Asset")
        self.delete_asset_btn.clicked.connect(self._delete_asset)
        self.delete_asset_btn.setEnabled(False)
        toolbar.addWidget(self.delete_asset_btn)
        
        toolbar.addStretch()
        assets_layout.addLayout(toolbar)
        
        # Assets table
        self.assets_table = QTableWidget()
        self.assets_table.setColumnCount(4)
        self.assets_table.setHorizontalHeaderLabels(["ID", "Name", "System", "Description"])
        
        header = self.assets_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        
        self.assets_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.assets_table.itemSelectionChanged.connect(self._update_asset_buttons_state)
        self.assets_table.doubleClicked.connect(self._edit_asset)
        
        assets_layout.addWidget(self.assets_table)
        
        self.content_tabs.addTab(assets_widget, "Assets")

    def _update_asset_buttons_state(self):
        """Enable/disable asset buttons based on selection."""
        has_selection = bool(self.assets_table.selectedItems())
        self.edit_asset_btn.setEnabled(has_selection)
        self.delete_asset_btn.setEnabled(has_selection)
        
    def _delete_asset(self):
        """Delete the selected asset."""
        selected_items = self.assets_table.selectedItems()
        if not selected_items:
            return
            
        asset_id = selected_items[0].data(Qt.UserRole)
        asset_name = selected_items[1].text()
        
        reply = QMessageBox.question(
            self,
            "Delete Asset",
            f"Are you sure you want to delete asset '{asset_name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                db_manager = self.database_initializer.get_database_manager()
                connection = db_manager.get_connection()
                repo = EntityFactory.get_repository(connection, Asset)
                if repo.delete(asset_id):
                    logger.info(f"Deleted asset: {asset_name} (ID: {asset_id})")
                    if self.current_system_id:
                        self._load_assets_for_system(self.current_system_id)
                else:
                    self._show_error("Delete Failed", "Failed to delete asset from database.")
            except Exception as e:
                logger.error(f"Failed to delete asset: {str(e)}")
                self._show_error("Delete Failed", str(e))

    def _setup_hazards_tab(self):
        """Setup hazards management tab."""
        hazards_widget = QWidget()
        hazards_layout = QVBoxLayout(hazards_widget)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        self.add_hazard_btn = QPushButton("Add Hazard")
        self.add_hazard_btn.clicked.connect(self._add_hazard)
        toolbar.addWidget(self.add_hazard_btn)
        
        self.edit_hazard_btn = QPushButton("Edit Hazard")
        self.edit_hazard_btn.clicked.connect(self._edit_hazard)
        self.edit_hazard_btn.setEnabled(False)
        toolbar.addWidget(self.edit_hazard_btn)

        self.delete_hazard_btn = QPushButton("Delete Hazard")
        self.delete_hazard_btn.clicked.connect(self._delete_hazard)
        self.delete_hazard_btn.setEnabled(False)
        toolbar.addWidget(self.delete_hazard_btn)
        
        toolbar.addStretch()
        hazards_layout.addLayout(toolbar)
        
        # Hazards table
        self.hazards_table = QTableWidget()
        self.hazards_table.setColumnCount(4)
        self.hazards_table.setHorizontalHeaderLabels(["ID", "Name", "System", "Description"])
        
        header = self.hazards_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        
        self.hazards_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.hazards_table.itemSelectionChanged.connect(self._update_hazard_buttons_state)
        self.hazards_table.doubleClicked.connect(self._edit_hazard)
        
        hazards_layout.addWidget(self.hazards_table)
        
        self.content_tabs.addTab(hazards_widget, "Hazards")

    def _update_hazard_buttons_state(self):
        """Enable/disable hazard buttons based on selection."""
        has_selection = bool(self.hazards_table.selectedItems())
        self.edit_hazard_btn.setEnabled(has_selection)
        self.delete_hazard_btn.setEnabled(has_selection)
        
    def _delete_hazard(self):
        """Delete the selected hazard."""
        selected_items = self.hazards_table.selectedItems()
        if not selected_items:
            return
            
        hazard_id = selected_items[0].data(Qt.UserRole)
        hazard_name = selected_items[1].text()
        
        reply = QMessageBox.question(
            self,
            "Delete Hazard",
            f"Are you sure you want to delete hazard '{hazard_name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                db_manager = self.database_initializer.get_database_manager()
                connection = db_manager.get_connection()
                repo = EntityFactory.get_repository(connection, Hazard)
                if repo.delete(hazard_id):
                    logger.info(f"Deleted hazard: {hazard_name} (ID: {hazard_id})")
                    self._load_hazards_for_system(self.current_system_id if self.current_system_id else 0)
                else:
                    self._show_error("Delete Failed", "Failed to delete hazard from database.")
            except Exception as e:
                logger.error(f"Failed to delete hazard: {str(e)}")
                self._show_error("Delete Failed", str(e))

    def _setup_losses_tab(self):
        """Setup losses management tab."""
        losses_widget = QWidget()
        losses_layout = QVBoxLayout(losses_widget)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        self.add_loss_btn = QPushButton("Add Loss")
        self.add_loss_btn.clicked.connect(self._add_loss)
        toolbar.addWidget(self.add_loss_btn)
        
        self.edit_loss_btn = QPushButton("Edit Loss")
        self.edit_loss_btn.clicked.connect(self._edit_loss)
        self.edit_loss_btn.setEnabled(False)
        toolbar.addWidget(self.edit_loss_btn)

        self.delete_loss_btn = QPushButton("Delete Loss")
        self.delete_loss_btn.clicked.connect(self._delete_loss)
        self.delete_loss_btn.setEnabled(False)
        toolbar.addWidget(self.delete_loss_btn)
        
        toolbar.addStretch()
        losses_layout.addLayout(toolbar)
        
        # Losses table
        self.losses_table = QTableWidget()
        self.losses_table.setColumnCount(4)
        self.losses_table.setHorizontalHeaderLabels(["ID", "Name", "System", "Description"])
        
        header = self.losses_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        
        self.losses_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.losses_table.itemSelectionChanged.connect(self._update_loss_buttons_state)
        self.losses_table.doubleClicked.connect(self._edit_loss)
        
        losses_layout.addWidget(self.losses_table)
        
        self.content_tabs.addTab(losses_widget, "Losses")

    def _update_loss_buttons_state(self):
        """Enable/disable loss buttons based on selection."""
        has_selection = bool(self.losses_table.selectedItems())
        self.edit_loss_btn.setEnabled(has_selection)
        self.delete_loss_btn.setEnabled(has_selection)
        
    def _delete_loss(self):
        """Delete the selected loss."""
        selected_items = self.losses_table.selectedItems()
        if not selected_items:
            return
            
        loss_id = selected_items[0].data(Qt.UserRole)
        loss_name = selected_items[1].text()
        
        reply = QMessageBox.question(
            self,
            "Delete Loss",
            f"Are you sure you want to delete loss '{loss_name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                db_manager = self.database_initializer.get_database_manager()
                connection = db_manager.get_connection()
                repo = EntityFactory.get_repository(connection, Loss)
                if repo.delete(loss_id):
                    logger.info(f"Deleted loss: {loss_name} (ID: {loss_id})")
                    self._load_losses_for_system(self.current_system_id if self.current_system_id else 0)
                else:
                    self._show_error("Delete Failed", "Failed to delete loss from database.")
            except Exception as e:
                logger.error(f"Failed to delete loss: {str(e)}")
                self._show_error("Delete Failed", str(e))

    def _setup_control_structures_tab(self):
        """Setup control structures management tab."""
        control_structures_widget = QWidget()
        control_structures_layout = QVBoxLayout(control_structures_widget)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        self.add_control_structure_btn = QPushButton("Add Control Structure")
        self.add_control_structure_btn.clicked.connect(self._add_control_structure)
        toolbar.addWidget(self.add_control_structure_btn)
        
        self.edit_control_structure_btn = QPushButton("Edit Control Structure")
        self.edit_control_structure_btn.clicked.connect(self._edit_control_structure)
        self.edit_control_structure_btn.setEnabled(False)
        toolbar.addWidget(self.edit_control_structure_btn)

        self.delete_control_structure_btn = QPushButton("Delete Control Structure")
        self.delete_control_structure_btn.clicked.connect(self._delete_control_structure)
        self.delete_control_structure_btn.setEnabled(False)
        toolbar.addWidget(self.delete_control_structure_btn)
        
        toolbar.addStretch()
        control_structures_layout.addLayout(toolbar)
        
        # Control structures table
        self.control_structures_table = QTableWidget()
        self.control_structures_table.setColumnCount(4)
        self.control_structures_table.setHorizontalHeaderLabels(["ID", "Name", "System", "Description"])
        
        header = self.control_structures_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        
        self.control_structures_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.control_structures_table.itemSelectionChanged.connect(self._update_control_structure_buttons_state)
        self.control_structures_table.doubleClicked.connect(self._edit_control_structure)
        
        control_structures_layout.addWidget(self.control_structures_table)
        
        self.content_tabs.addTab(control_structures_widget, "Control Structures")

    def _update_control_structure_buttons_state(self):
        """Enable/disable control structure buttons based on selection."""
        has_selection = bool(self.control_structures_table.selectedItems())
        self.edit_control_structure_btn.setEnabled(has_selection)
        self.delete_control_structure_btn.setEnabled(has_selection)
        
    def _delete_control_structure(self):
        """Delete the selected control structure."""
        selected_items = self.control_structures_table.selectedItems()
        if not selected_items:
            return
            
        control_structure_id = selected_items[0].data(Qt.UserRole)
        control_structure_name = selected_items[1].text()
        
        reply = QMessageBox.question(
            self,
            "Delete Control Structure",
            f"Are you sure you want to delete control structure '{control_structure_name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                db_manager = self.database_initializer.get_database_manager()
                connection = db_manager.get_connection()
                repo = EntityFactory.get_repository(connection, ControlStructure)
                if repo.delete(control_structure_id):
                    logger.info(f"Deleted control structure: {control_structure_name} (ID: {control_structure_id})")
                    if self.current_system_id:
                        self._load_control_structures_for_system(self.current_system_id)
                else:
                    self._show_error("Delete Failed", "Failed to delete control structure from database.")
            except Exception as e:
                logger.error(f"Failed to delete control structure: {str(e)}")
                self._show_error("Delete Failed", str(e))

    def _setup_controllers_tab(self):
        """Setup controllers management tab."""
        controllers_widget = QWidget()
        controllers_layout = QVBoxLayout(controllers_widget)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        self.add_controller_btn = QPushButton("Add Controller")
        self.add_controller_btn.clicked.connect(self._add_controller)
        toolbar.addWidget(self.add_controller_btn)
        
        self.edit_controller_btn = QPushButton("Edit Controller")
        self.edit_controller_btn.clicked.connect(self._edit_controller)
        self.edit_controller_btn.setEnabled(False)
        toolbar.addWidget(self.edit_controller_btn)

        self.delete_controller_btn = QPushButton("Delete Controller")
        self.delete_controller_btn.clicked.connect(self._delete_controller)
        self.delete_controller_btn.setEnabled(False)
        toolbar.addWidget(self.delete_controller_btn)
        
        toolbar.addStretch()
        controllers_layout.addLayout(toolbar)
        
        # Controllers table
        self.controllers_table = QTableWidget()
        self.controllers_table.setColumnCount(4)
        self.controllers_table.setHorizontalHeaderLabels(["ID", "Name", "System", "Description"])
        
        header = self.controllers_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        
        self.controllers_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.controllers_table.itemSelectionChanged.connect(self._update_controller_buttons_state)
        self.controllers_table.doubleClicked.connect(self._edit_controller)
        
        controllers_layout.addWidget(self.controllers_table)
        
        self.content_tabs.addTab(controllers_widget, "Controllers")

    def _update_controller_buttons_state(self):
        """Enable/disable controller buttons based on selection."""
        has_selection = bool(self.controllers_table.selectedItems())
        self.edit_controller_btn.setEnabled(has_selection)
        self.delete_controller_btn.setEnabled(has_selection)
        
    def _delete_controller(self):
        """Delete the selected controller."""
        selected_items = self.controllers_table.selectedItems()
        if not selected_items:
            return
            
        controller_id = selected_items[0].data(Qt.UserRole)
        controller_name = selected_items[1].text()
        
        reply = QMessageBox.question(
            self,
            "Delete Controller",
            f"Are you sure you want to delete controller '{controller_name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                db_manager = self.database_initializer.get_database_manager()
                connection = db_manager.get_connection()
                repo = EntityFactory.get_repository(connection, Controller)
                if repo.delete(controller_id):
                    logger.info(f"Deleted controller: {controller_name} (ID: {controller_id})")
                    if self.current_system_id:
                        self._load_controllers_for_system(self.current_system_id)
                else:
                    self._show_error("Delete Failed", "Failed to delete controller from database.")
            except Exception as e:
                logger.error(f"Failed to delete controller: {str(e)}")
                self._show_error("Delete Failed", str(e))

    def _setup_diagrams_tab(self):
        """Setup diagrams management tab."""
        diagrams_widget = QWidget()
        diagrams_layout = QVBoxLayout(diagrams_widget)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        self.generate_diagram_btn = QPushButton("Generate Diagram")
        self.generate_diagram_btn.clicked.connect(self._generate_diagram)
        toolbar.addWidget(self.generate_diagram_btn)
        
        self.view_diagram_btn = QPushButton("View Diagram")
        self.view_diagram_btn.clicked.connect(self._view_diagram)
        self.view_diagram_btn.setEnabled(False)
        toolbar.addWidget(self.view_diagram_btn)
        
        toolbar.addStretch()
        diagrams_layout.addLayout(toolbar)
        
        # Diagrams list
        self.diagrams_list = QTableWidget()
        self.diagrams_list.setColumnCount(3)
        self.diagrams_list.setHorizontalHeaderLabels(["Name", "Type", "Last Generated"])
        
        header = self.diagrams_list.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        
        self.diagrams_list.setSelectionBehavior(QTableWidget.SelectRows)
        self.diagrams_list.itemSelectionChanged.connect(self._update_diagram_buttons_state)
        self.diagrams_list.doubleClicked.connect(self._view_diagram)
        
        diagrams_layout.addWidget(self.diagrams_list)
        
        self.content_tabs.addTab(diagrams_widget, "Diagrams")

    def _update_diagram_buttons_state(self):
        """Enable/disable diagram buttons based on selection."""
        has_selection = bool(self.diagrams_list.selectedItems())
        self.view_diagram_btn.setEnabled(has_selection)
    
    def _generate_diagram(self):
        """Generate a system diagram."""
        if not self.current_system_id:
            QMessageBox.warning(self, "No System Selected", "Please select a system first.")
            return
        
        if not self.diagram_generator:
            QMessageBox.warning(self, "Diagram Generator Not Available", "Diagram generation is not available.")
            return
        
        # TODO: Implement diagram generation
        QMessageBox.information(self, "Diagram Generation", "Diagram generation feature coming soon.")
    
    def _view_diagram(self):
        """View the selected diagram."""
        if not self.diagram_viewer:
            QMessageBox.warning(self, "Diagram Viewer Not Available", "Diagram viewing is not available.")
            return
        
        # TODO: Implement diagram viewing
        QMessageBox.information(self, "Diagram Viewing", "Diagram viewing feature coming soon.")
    
    def _edit_current_system(self):
        """Edit the currently selected system."""
        if not self.current_system_id:
            QMessageBox.information(self, "No Selection", "Please select a system to edit.")
            return
        
        try:
            # Get system from database
            db_manager = self.database_initializer.get_database_manager()
            connection = db_manager.get_connection()
            system_repo = EntityFactory.get_repository(connection, System)
            system = system_repo.get_by_id(self.current_system_id)
            
            if not system:
                QMessageBox.warning(self, "System Not Found", "Selected system not found in database.")
                return
            
            # Open edit dialog
            dialog = SystemEditDialog(system=system, parent=self)
            if dialog.exec() == QDialog.Accepted:
                updated_system = dialog.get_system()
                if updated_system and system_repo.update(updated_system):
                    # Refresh hierarchy tree
                    self.hierarchy_tree.refresh_from_database()
                    # Update breadcrumb
                    self._update_breadcrumb(updated_system)
                    logger.info(f"Updated system: {updated_system.system_name}")
                else:
                    QMessageBox.warning(self, "Update Failed", "Failed to update system.")
                    
        except Exception as e:
            logger.error(f"Failed to edit system: {str(e)}")
            QMessageBox.critical(self, "Edit Failed", f"Failed to edit system:\n{str(e)}")
    
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
    
    def _on_function_saved(self, function: Function):
        """Handle function saved event."""
        try:
            db_manager = self.database_initializer.get_database_manager()
            connection = db_manager.get_connection()
            function_repo = EntityFactory.get_repository(connection, Function)
            
            if function.id is None:
                # New function
                new_id = function_repo.create(function)
                if new_id:
                    function.id = new_id
                    logger.info(f"Created function: {function.function_name}")
                else:
                    QMessageBox.critical(self, "Save Failed", "Failed to create function in database")
                    return
            else:
                # Update existing function
                if not function_repo.update(function):
                    QMessageBox.critical(self, "Save Failed", "Failed to update function in database")
                    return
                logger.info(f"Updated function: {function.function_name}")
            
            # Refresh the functions table
            if self.current_system_id:
                self._load_functions_for_system(self.current_system_id)
            
        except Exception as e:
            logger.error(f"Failed to save function: {str(e)}")
            QMessageBox.critical(self, "Save Failed", f"Failed to save function:\n{str(e)}")
    
    def _add_interface(self):
        """Add a new interface to the current system."""
        if not self.current_system_id:
            QMessageBox.warning(self, "No System Selected", "Please select a system first.")
            return
        
        dialog = InterfaceEditDialog(system_id=self.current_system_id, parent=self)
        dialog.interface_saved.connect(self._on_interface_saved)
        dialog.exec()
    
    def _edit_interface(self):
        """Edit selected interface."""
        current_row = self.interfaces_table.currentRow()
        if current_row < 0:
            return
        
        interface_id = self.interfaces_table.item(current_row, 0).data(Qt.UserRole)
        if not interface_id:
            return
        
        try:
            # Get interface from database
            db_manager = self.database_initializer.get_database_manager()
            connection = db_manager.get_connection()
            
            interface_data = connection.fetchone(
                "SELECT * FROM interfaces WHERE id = ?",
                (interface_id,)
            )
            
            if interface_data:
                int_dict = dict(interface_data)
                interface = Interface(**int_dict)
                
                dialog = InterfaceEditDialog(interface, parent=self)
                dialog.interface_saved.connect(self._on_interface_saved)
                dialog.exec()
        
        except Exception as e:
            logger.error(f"Failed to edit interface: {str(e)}")
    
    def _on_interface_saved(self, interface: Interface):
        """Handle interface saved event."""
        try:
            # Save to database
            db_manager = self.database_initializer.get_database_manager()
            connection = db_manager.get_connection()
            interface_repo = EntityFactory.get_repository(connection, Interface)
            
            if interface.id is None:
                # New interface
                new_id = interface_repo.create(interface)
                if new_id:
                    interface.id = new_id
                    logger.info(f"Created interface: {interface.interface_name}")
                else:
                    QMessageBox.critical(self, "Save Failed", "Failed to create interface in database")
                    return
            else:
                # Update existing interface
                if not interface_repo.update(interface):
                    QMessageBox.critical(self, "Save Failed", "Failed to update interface in database")
                    return
                logger.info(f"Updated interface: {interface.interface_name}")
            
            # Refresh the interfaces table
            if self.current_system_id:
                self._load_interfaces_for_system(self.current_system_id)
            
        except Exception as e:
            logger.error(f"Failed to save interface: {str(e)}")
            QMessageBox.critical(self, "Save Failed", f"Failed to save interface:\n{str(e)}")
    
    def _add_asset(self):
        """Add a new asset to the current system."""
        if not self.current_system_id:
            QMessageBox.warning(self, "No System Selected", "Please select a system first.")
            return
        
        dialog = AssetEditDialog(system_id=self.current_system_id, parent=self)
        dialog.asset_saved.connect(self._on_asset_saved)
        dialog.exec()
    
    def _edit_asset(self):
        """Edit selected asset."""
        current_row = self.assets_table.currentRow()
        if current_row < 0:
            return
        
        asset_id = self.assets_table.item(current_row, 0).data(Qt.UserRole)
        if not asset_id:
            return
        
        try:
            # Get asset from database
            db_manager = self.database_initializer.get_database_manager()
            connection = db_manager.get_connection()
            
            asset_data = connection.fetchone(
                "SELECT * FROM assets WHERE id = ?",
                (asset_id,)
            )
            
            if asset_data:
                asset_dict = dict(asset_data)
                asset = Asset(**asset_dict)
                
                dialog = AssetEditDialog(asset, parent=self)
                dialog.asset_saved.connect(self._on_asset_saved)
                dialog.exec()
        
        except Exception as e:
            logger.error(f"Failed to edit asset: {str(e)}")
    
    def _on_asset_saved(self, asset: Asset):
        """Handle asset saved event."""
        try:
            # Save to database
            db_manager = self.database_initializer.get_database_manager()
            connection = db_manager.get_connection()
            asset_repo = EntityFactory.get_repository(connection, Asset)
            
            if asset.id is None:
                # New asset
                new_id = asset_repo.create(asset)
                if new_id:
                    asset.id = new_id
                    logger.info(f"Created asset: {asset.asset_name}")
                else:
                    QMessageBox.critical(self, "Save Failed", "Failed to create asset in database")
                    return
            else:
                # Update existing asset
                if not asset_repo.update(asset):
                    QMessageBox.critical(self, "Save Failed", "Failed to update asset in database")
                    return
                logger.info(f"Updated asset: {asset.asset_name}")
            
            # Refresh the assets table
            if self.current_system_id:
                self._load_assets_for_system(self.current_system_id)
            
        except Exception as e:
            logger.error(f"Failed to save asset: {str(e)}")
            QMessageBox.critical(self, "Save Failed", f"Failed to save asset:\n{str(e)}")
    
    def _add_hazard(self):
        """Add a new hazard."""
        dialog = HazardEditDialog(parent=self)
        dialog.hazard_saved.connect(self._on_hazard_saved)
        dialog.exec()
    
    def _edit_hazard(self):
        """Edit selected hazard."""
        current_row = self.hazards_table.currentRow()
        if current_row < 0:
            return
        
        hazard_id = self.hazards_table.item(current_row, 0).data(Qt.UserRole)
        if not hazard_id:
            return
        
        try:
            # Get hazard from database
            db_manager = self.database_initializer.get_database_manager()
            connection = db_manager.get_connection()
            
            hazard_data = connection.fetchone(
                "SELECT * FROM hazards WHERE id = ?",
                (hazard_id,)
            )
            
            if hazard_data:
                hazard_dict = dict(hazard_data)
                hazard = Hazard(**hazard_dict)
                
                dialog = HazardEditDialog(hazard, parent=self)
                dialog.hazard_saved.connect(self._on_hazard_saved)
                dialog.exec()
        
        except Exception as e:
            logger.error(f"Failed to edit hazard: {str(e)}")
    
    def _on_hazard_saved(self, hazard: Hazard):
        """Handle hazard saved event."""
        try:
            # Save to database
            db_manager = self.database_initializer.get_database_manager()
            connection = db_manager.get_connection()
            hazard_repo = EntityFactory.get_repository(connection, Hazard)
            
            if hazard.id is None:
                # New hazard
                new_id = hazard_repo.create(hazard)
                if new_id:
                    hazard.id = new_id
                    logger.info(f"Created hazard: {hazard.hazard_name}")
                else:
                    QMessageBox.critical(self, "Save Failed", "Failed to create hazard in database")
                    return
            else:
                # Update existing hazard
                if not hazard_repo.update(hazard):
                    QMessageBox.critical(self, "Save Failed", "Failed to update hazard in database")
                    return
                logger.info(f"Updated hazard: {hazard.hazard_name}")
            
            # Refresh the hazards table
            self._load_hazards_for_system(self.current_system_id if self.current_system_id else 0)
            
        except Exception as e:
            logger.error(f"Failed to save hazard: {str(e)}")
            QMessageBox.critical(self, "Save Failed", f"Failed to save hazard:\n{str(e)}")
    
    def _add_loss(self):
        """Add a new loss."""
        dialog = LossEditDialog(parent=self)
        dialog.loss_saved.connect(self._on_loss_saved)
        dialog.exec()
    
    def _edit_loss(self):
        """Edit selected loss."""
        current_row = self.losses_table.currentRow()
        if current_row < 0:
            return
        
        loss_id = self.losses_table.item(current_row, 0).data(Qt.UserRole)
        if not loss_id:
            return
        
        try:
            # Get loss from database
            db_manager = self.database_initializer.get_database_manager()
            connection = db_manager.get_connection()
            
            loss_data = connection.fetchone(
                "SELECT * FROM losses WHERE id = ?",
                (loss_id,)
            )
            
            if loss_data:
                loss_dict = dict(loss_data)
                loss = Loss(**loss_dict)
                
                dialog = LossEditDialog(loss, parent=self)
                dialog.loss_saved.connect(self._on_loss_saved)
                dialog.exec()
        
        except Exception as e:
            logger.error(f"Failed to edit loss: {str(e)}")
    
    def _on_loss_saved(self, loss: Loss):
        """Handle loss saved event."""
        try:
            # Save to database
            db_manager = self.database_initializer.get_database_manager()
            connection = db_manager.get_connection()
            loss_repo = EntityFactory.get_repository(connection, Loss)
            
            if loss.id is None:
                # New loss
                new_id = loss_repo.create(loss)
                if new_id:
                    loss.id = new_id
                    logger.info(f"Created loss: {loss.loss_name}")
                else:
                    QMessageBox.critical(self, "Save Failed", "Failed to create loss in database")
                    return
            else:
                # Update existing loss
                if not loss_repo.update(loss):
                    QMessageBox.critical(self, "Save Failed", "Failed to update loss in database")
                    return
                logger.info(f"Updated loss: {loss.loss_name}")
            
            # Refresh the losses table
            self._load_losses_for_system(self.current_system_id if self.current_system_id else 0)
            
        except Exception as e:
            logger.error(f"Failed to save loss: {str(e)}")
            QMessageBox.critical(self, "Save Failed", f"Failed to save loss:\n{str(e)}")
    
    def _add_control_structure(self):
        """Add a new control structure to the current system."""
        if not self.current_system_id:
            QMessageBox.warning(self, "No System Selected", "Please select a system first.")
            return
        
        dialog = ControlStructureEditDialog(system_id=self.current_system_id, parent=self)
        dialog.control_structure_saved.connect(self._on_control_structure_saved)
        dialog.exec()
    
    def _edit_control_structure(self):
        """Edit selected control structure."""
        current_row = self.control_structures_table.currentRow()
        if current_row < 0:
            return
        
        control_structure_id = self.control_structures_table.item(current_row, 0).data(Qt.UserRole)
        if not control_structure_id:
            return
        
        try:
            # Get control structure from database
            db_manager = self.database_initializer.get_database_manager()
            connection = db_manager.get_connection()
            
            control_structure_data = connection.fetchone(
                "SELECT * FROM control_structures WHERE id = ?",
                (control_structure_id,)
            )
            
            if control_structure_data:
                cs_dict = dict(control_structure_data)
                control_structure = ControlStructure(**cs_dict)
                
                dialog = ControlStructureEditDialog(control_structure, parent=self)
                dialog.control_structure_saved.connect(self._on_control_structure_saved)
                dialog.exec()
        
        except Exception as e:
            logger.error(f"Failed to edit control structure: {str(e)}")
    
    def _on_control_structure_saved(self, control_structure: ControlStructure):
        """Handle control structure saved event."""
        try:
            # Save to database
            db_manager = self.database_initializer.get_database_manager()
            connection = db_manager.get_connection()
            control_structure_repo = EntityFactory.get_repository(connection, ControlStructure)
            
            if control_structure.id is None:
                # New control structure
                new_id = control_structure_repo.create(control_structure)
                if new_id:
                    control_structure.id = new_id
                    logger.info(f"Created control structure: {control_structure.structure_name}")
                else:
                    QMessageBox.critical(self, "Save Failed", "Failed to create control structure in database")
                    return
            else:
                # Update existing control structure
                if not control_structure_repo.update(control_structure):
                    QMessageBox.critical(self, "Save Failed", "Failed to update control structure in database")
                    return
                logger.info(f"Updated control structure: {control_structure.structure_name}")
            
            # Refresh the control structures table
            if self.current_system_id:
                self._load_control_structures_for_system(self.current_system_id)
            
        except Exception as e:
            logger.error(f"Failed to save control structure: {str(e)}")
            QMessageBox.critical(self, "Save Failed", f"Failed to save control structure:\n{str(e)}")
    
    def _add_controller(self):
        """Add a new controller to the current system."""
        if not self.current_system_id:
            QMessageBox.warning(self, "No System Selected", "Please select a system first.")
            return
        
        dialog = ControllerEditDialog(system_id=self.current_system_id, parent=self)
        dialog.controller_saved.connect(self._on_controller_saved)
        dialog.exec()
    
    def _edit_controller(self):
        """Edit selected controller."""
        current_row = self.controllers_table.currentRow()
        if current_row < 0:
            return
        
        controller_id = self.controllers_table.item(current_row, 0).data(Qt.UserRole)
        if not controller_id:
            return
        
        try:
            # Get controller from database
            db_manager = self.database_initializer.get_database_manager()
            connection = db_manager.get_connection()
            
            controller_data = connection.fetchone(
                "SELECT * FROM controllers WHERE id = ?",
                (controller_id,)
            )
            
            if controller_data:
                controller_dict = dict(controller_data)
                controller = Controller(**controller_dict)
                
                dialog = ControllerEditDialog(controller, parent=self)
                dialog.controller_saved.connect(self._on_controller_saved)
                dialog.exec()
        
        except Exception as e:
            logger.error(f"Failed to edit controller: {str(e)}")
    
    def _on_controller_saved(self, controller: Controller):
        """Handle controller saved event."""
        try:
            # Save to database
            db_manager = self.database_initializer.get_database_manager()
            connection = db_manager.get_connection()
            controller_repo = EntityFactory.get_repository(connection, Controller)
            
            if controller.id is None:
                # New controller
                new_id = controller_repo.create(controller)
                if new_id:
                    controller.id = new_id
                    logger.info(f"Created controller: {controller.controller_name}")
                else:
                    QMessageBox.critical(self, "Save Failed", "Failed to create controller in database")
                    return
            else:
                # Update existing controller
                if not controller_repo.update(controller):
                    QMessageBox.critical(self, "Save Failed", "Failed to update controller in database")
                    return
                logger.info(f"Updated controller: {controller.controller_name}")
            
            # Refresh the controllers table
            if self.current_system_id:
                self._load_controllers_for_system(self.current_system_id)
            
        except Exception as e:
            logger.error(f"Failed to save controller: {str(e)}")
            QMessageBox.critical(self, "Save Failed", f"Failed to save controller:\n{str(e)}")
    
    def _load_interfaces_for_system(self, system_id: int):
        """Load interfaces for the selected system."""
        try:
            db_manager = self.database_initializer.get_database_manager()
            connection = db_manager.get_connection()
            
            interfaces = connection.fetchall(
                "SELECT * FROM interfaces WHERE system_id = ? AND baseline = ? ORDER BY system_hierarchy",
                (system_id, "Working")
            )
            
            # Clear and populate interfaces table
            self.interfaces_table.setRowCount(len(interfaces))
            
            for row, int_data in enumerate(interfaces):
                int_dict = dict(int_data)
                interface = Interface(**int_dict)
                
                items = [
                    QTableWidgetItem(interface.get_hierarchical_id()),
                    QTableWidgetItem(interface.interface_name),
                    QTableWidgetItem(self._get_system_name(interface.system_id)),
                    QTableWidgetItem(interface.interface_description[:100] + "..." if len(interface.interface_description or "") > 100 else interface.interface_description or "")
                ]

                for item in items:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)

                for col, item in enumerate(items):
                    self.interfaces_table.setItem(row, col, item)
                
                # Store interface ID for editing
                self.interfaces_table.item(row, 0).setData(Qt.UserRole, interface.id)
            
        except Exception as e:
            logger.error(f"Failed to load interfaces: {str(e)}")
    
    def _load_assets_for_system(self, system_id: int):
        """Load assets for the selected system."""
        try:
            db_manager = self.database_initializer.get_database_manager()
            connection = db_manager.get_connection()
            
            assets = connection.fetchall(
                "SELECT * FROM assets WHERE system_id = ? AND baseline = ? ORDER BY system_hierarchy",
                (system_id, "Working")
            )
            
            # Clear and populate assets table
            self.assets_table.setRowCount(len(assets))
            
            for row, asset_data in enumerate(assets):
                asset_dict = dict(asset_data)
                asset = Asset(**asset_dict)
                
                items = [
                    QTableWidgetItem(asset.get_hierarchical_id()),
                    QTableWidgetItem(asset.asset_name),
                    QTableWidgetItem(self._get_system_name(asset.system_id)),
                    QTableWidgetItem(asset.asset_description[:100] + "..." if len(asset.asset_description or "") > 100 else asset.asset_description or "")
                ]

                for item in items:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)

                for col, item in enumerate(items):
                    self.assets_table.setItem(row, col, item)

                # Store asset ID for editing
                self.assets_table.item(row, 0).setData(Qt.UserRole, asset.id)
            
        except Exception as e:
            logger.error(f"Failed to load assets: {str(e)}")
    
    def _load_hazards_for_system(self, system_id: int):
        """Load hazards for the selected system."""
        try:
            db_manager = self.database_initializer.get_database_manager()
            connection = db_manager.get_connection()
            
            hazards = connection.fetchall(
                "SELECT * FROM hazards WHERE baseline = ? ORDER BY system_hierarchy",
                ("Working",)
            )
            
            # Clear and populate hazards table
            self.hazards_table.setRowCount(len(hazards))
            
            for row, hazard_data in enumerate(hazards):
                hazard_dict = dict(hazard_data)
                hazard = Hazard(**hazard_dict)
                
                items = [
                    QTableWidgetItem(hazard.get_hierarchical_id()),
                    QTableWidgetItem(hazard.hazard_name),
                    QTableWidgetItem("All Systems"),  # Hazards are system-wide
                    QTableWidgetItem(hazard.hazard_description[:100] + "..." if len(hazard.hazard_description or "") > 100 else hazard.hazard_description or "")
                ]

                for item in items:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)

                for col, item in enumerate(items):
                    self.hazards_table.setItem(row, col, item)
                
                # Store hazard ID for editing
                self.hazards_table.item(row, 0).setData(Qt.UserRole, hazard.id)
            
        except Exception as e:
            logger.error(f"Failed to load hazards: {str(e)}")
    
    def _load_losses_for_system(self, system_id: int):
        """Load losses for the selected system."""
        try:
            db_manager = self.database_initializer.get_database_manager()
            connection = db_manager.get_connection()
            
            losses = connection.fetchall(
                "SELECT * FROM losses WHERE baseline = ? ORDER BY system_hierarchy",
                ("Working",)
            )
            
            # Clear and populate losses table
            self.losses_table.setRowCount(len(losses))
            
            for row, loss_data in enumerate(losses):
                loss_dict = dict(loss_data)
                loss = Loss(**loss_dict)
                
                items = [
                    QTableWidgetItem(loss.get_hierarchical_id()),
                    QTableWidgetItem(loss.loss_name),
                    QTableWidgetItem("All Systems"),  # Losses are system-wide
                    QTableWidgetItem(loss.loss_description[:100] + "..." if len(loss.loss_description or "") > 100 else loss.loss_description or "")
                ]

                for item in items:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)

                for col, item in enumerate(items):
                    self.losses_table.setItem(row, col, item)
                
                # Store loss ID for editing
                self.losses_table.item(row, 0).setData(Qt.UserRole, loss.id)
            
        except Exception as e:
            logger.error(f"Failed to load losses: {str(e)}")
    
    def _load_control_structures_for_system(self, system_id: int):
        """Load control structures for the selected system."""
        try:
            db_manager = self.database_initializer.get_database_manager()
            connection = db_manager.get_connection()
            
            control_structures = connection.fetchall(
                "SELECT * FROM control_structures WHERE system_id = ? AND baseline = ? ORDER BY system_hierarchy",
                (system_id, "Working")
            )
            
            # Clear and populate control structures table
            self.control_structures_table.setRowCount(len(control_structures))
            
            for row, cs_data in enumerate(control_structures):
                cs_dict = dict(cs_data)
                control_structure = ControlStructure(**cs_dict)
                
                items = [
                    QTableWidgetItem(control_structure.get_hierarchical_id()),
                    QTableWidgetItem(control_structure.structure_name),
                    QTableWidgetItem(self._get_system_name(control_structure.system_id)),
                    QTableWidgetItem(control_structure.structure_description[:100] + "..." if len(control_structure.structure_description or "") > 100 else control_structure.structure_description or "")
                ]

                for item in items:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)

                for col, item in enumerate(items):
                    self.control_structures_table.setItem(row, col, item)
                
                # Store control structure ID for editing
                self.control_structures_table.item(row, 0).setData(Qt.UserRole, control_structure.id)
            
        except Exception as e:
            logger.error(f"Failed to load control structures: {str(e)}")
    
    def _load_controllers_for_system(self, system_id: int):
        """Load controllers for the selected system."""
        try:
            db_manager = self.database_initializer.get_database_manager()
            connection = db_manager.get_connection()
            
            controllers = connection.fetchall(
                "SELECT * FROM controllers WHERE system_id = ? AND baseline = ? ORDER BY system_hierarchy",
                (system_id, "Working")
            )
            
            # Clear and populate controllers table
            self.controllers_table.setRowCount(len(controllers))
            
            for row, controller_data in enumerate(controllers):
                controller_dict = dict(controller_data)
                controller = Controller(**controller_dict)
                
                items = [
                    QTableWidgetItem(controller.get_hierarchical_id()),
                    QTableWidgetItem(controller.controller_name),
                    QTableWidgetItem(self._get_system_name(controller.system_id)),
                    QTableWidgetItem(controller.controller_description[:100] + "..." if len(controller.controller_description or "") > 100 else controller.controller_description or "")
                ]

                for item in items:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)

                for col, item in enumerate(items):
                    self.controllers_table.setItem(row, col, item)
                
                # Store controller ID for editing
                self.controllers_table.item(row, 0).setData(Qt.UserRole, controller.id)
            
        except Exception as e:
            logger.error(f"Failed to load controllers: {str(e)}")
    
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
    
    def _on_requirement_saved(self, requirement: Requirement):
        """Handle requirement saved event."""
        try:
            # Save to database
            db_manager = self.database_initializer.get_database_manager()
            connection = db_manager.get_connection()
            requirement_repo = EntityFactory.get_repository(connection, Requirement)
            
            if requirement.id is None:
                # New requirement
                new_id = requirement_repo.create(requirement)
                if new_id:
                    requirement.id = new_id
                    logger.info(f"Created requirement: {requirement.alphanumeric_identifier}")
                else:
                    QMessageBox.critical(self, "Save Failed", "Failed to create requirement in database")
                    return
            else:
                # Update existing requirement
                if not requirement_repo.update(requirement):
                    QMessageBox.critical(self, "Save Failed", "Failed to update requirement in database")
                    return
                logger.info(f"Updated requirement: {requirement.alphanumeric_identifier}")
            
            # Refresh the requirements table
            if self.current_system_id:
                self._load_requirements_for_system(self.current_system_id)
            
        except Exception as e:
            logger.error(f"Failed to save requirement: {str(e)}")
            QMessageBox.critical(self, "Save Failed", f"Failed to save requirement:\n{str(e)}")
    
    def _setup_menus(self):
        """Setup the application menus."""
        # Create menu bar
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        # Export submenu
        export_menu = file_menu.addMenu("Export")
        
        export_json_action = QAction("Export JSON", self)
        export_json_action.triggered.connect(self._export_json)
        export_menu.addAction(export_json_action)
        
        export_markdown_action = QAction("Export Markdown", self)
        export_markdown_action.triggered.connect(self._export_markdown)
        export_menu.addAction(export_markdown_action)
        
        export_archive_action = QAction("Export Archive", self)
        export_archive_action.triggered.connect(self._export_archive)
        export_menu.addAction(export_archive_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Baseline menu
        baseline_menu = menubar.addMenu("Baseline")
        
        create_baseline_action = QAction("Create Baseline", self)
        create_baseline_action.triggered.connect(self._create_baseline)
        baseline_menu.addAction(create_baseline_action)
        
        manage_baselines_action = QAction("Manage Baselines", self)
        manage_baselines_action.triggered.connect(self._manage_baselines)
        baseline_menu.addAction(manage_baselines_action)
        
        # Collaboration menu
        collaboration_menu = menubar.addMenu("Collaboration")
        
        create_branch_action = QAction("Create Branch", self)
        create_branch_action.triggered.connect(self._create_branch)
        collaboration_menu.addAction(create_branch_action)
        
        manage_branches_action = QAction("Manage Branches", self)
        manage_branches_action.triggered.connect(self._manage_branches)
        collaboration_menu.addAction(manage_branches_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _setup_toolbar(self):
        """Setup the application toolbar."""
        # Create toolbar
        toolbar = self.addToolBar("Main Toolbar")
        toolbar.setMovable(False)
        
        # Add system button
        add_system_action = QAction("Add System", self)
        add_system_action.triggered.connect(self._add_root_system)
        toolbar.addAction(add_system_action)
        
        toolbar.addSeparator()
        
        # Refresh button
        refresh_action = QAction("Refresh", self)
        refresh_action.triggered.connect(self._refresh_all)
        toolbar.addAction(refresh_action)
    
    def _setup_status_bar(self):
        """Setup the application status bar."""
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")
    
    def _restore_window_state(self):
        """Restore window state from configuration."""
        try:
            # Restore window geometry
            geometry = self.config_manager.get("window_geometry")
            if geometry:
                self.restoreGeometry(geometry)
            
            # Restore window state
            state = self.config_manager.get("window_state")
            if state:
                self.restoreState(state)
            
            # Restore splitter sizes
            splitter_sizes = self.config_manager.get("splitter_sizes")
            if splitter_sizes and self.splitter:
                self.splitter.setSizes(splitter_sizes)
                
        except Exception as e:
            logger.warning(f"Failed to restore window state: {str(e)}")
    
    def _export_json(self):
        """Export system data as JSON."""
        if not self.current_system_id:
            QMessageBox.warning(self, "No System Selected", "Please select a system first.")
            return
        
        dialog = JsonExportDialog(self.current_system_id, parent=self)
        dialog.exec()
    
    def _export_markdown(self):
        """Export system data as Markdown."""
        if not self.current_system_id:
            QMessageBox.warning(self, "No System Selected", "Please select a system first.")
            return
        
        dialog = MarkdownExportDialog(self.current_system_id, parent=self)
        dialog.exec()
    
    def _export_archive(self):
        """Export system data as archive."""
        if not self.current_system_id:
            QMessageBox.warning(self, "No System Selected", "Please select a system first.")
            return
        
        dialog = ArchiveExportDialog(self.current_system_id, parent=self)
        dialog.exec()
    
    def _create_baseline(self):
        """Create a new baseline."""
        if not self.baseline_manager:
            QMessageBox.warning(self, "Baseline Manager Not Available", "Baseline management is not available.")
            return
        
        dialog = BaselineCreationDialog(self.baseline_manager, parent=self)
        dialog.exec()
    
    def _manage_baselines(self):
        """Manage existing baselines."""
        if not self.baseline_manager:
            QMessageBox.warning(self, "Baseline Manager Not Available", "Baseline management is not available.")
            return
        
        dialog = BaselineManagementDialog(self.baseline_manager, parent=self)
        dialog.exec()
    
    def _create_branch(self):
        """Create a new branch."""
        if not self.branch_manager:
            QMessageBox.warning(self, "Branch Manager Not Available", "Branch management is not available.")
            return
        
        dialog = BranchCreationDialog(self.branch_manager, parent=self)
        dialog.exec()
    
    def _manage_branches(self):
        """Manage existing branches."""
        if not self.branch_manager:
            QMessageBox.warning(self, "Branch Manager Not Available", "Branch management is not available.")
            return
        
        dialog = BranchManagementDialog(self.branch_manager, parent=self)
        dialog.exec()
    
    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(self, "About STPA Tool", 
                         f"{APP_NAME}\n\n"
                         "A comprehensive tool for System-Theoretic Process Analysis (STPA).\n\n"
                         "Version: 1.0.0\n"
                         "Built with Python and PySide6")
    
    def _add_root_system(self):
        """Add a new root system."""
        dialog = SystemEditDialog(parent=self)
        dialog.system_saved.connect(self._on_system_saved)
        dialog.exec()
    
    def _on_system_saved(self, system: System):
        """Handle system saved event."""
        try:
            # Save to database
            db_manager = self.database_initializer.get_database_manager()
            connection = db_manager.get_connection()
            system_repo = EntityFactory.get_repository(connection, System)
            
            if system.id is None:
                # New system
                new_id = system_repo.create(system)
                if new_id:
                    system.id = new_id
                    logger.info(f"Created system: {system.system_name}")
                else:
                    QMessageBox.critical(self, "Save Failed", "Failed to create system in database")
                    return
            else:
                # Update existing system
                if not system_repo.update(system):
                    QMessageBox.critical(self, "Save Failed", "Failed to update system in database")
                    return
                logger.info(f"Updated system: {system.system_name}")
            
            # Refresh the hierarchy tree
            if self.hierarchy_tree:
                self.hierarchy_tree.refresh_from_database()
            
        except Exception as e:
            logger.error(f"Failed to save system: {str(e)}")
            QMessageBox.critical(self, "Save Failed", f"Failed to save system:\n{str(e)}")
    
    def _refresh_all(self):
        """Refresh all data."""
        try:
            # Refresh hierarchy tree
            if self.hierarchy_tree:
                self.hierarchy_tree.refresh_from_database()
            
            # Refresh current system data if selected
            if self.current_system_id:
                self._on_system_selected(self.current_system_id)
            
            self.status_bar.showMessage("Data refreshed", 3000)
            
        except Exception as e:
            logger.error(f"Failed to refresh data: {str(e)}")
            self.status_bar.showMessage("Failed to refresh data", 3000)
    
    def _show_error(self, title: str, message: str):
        """Show error message dialog."""
        QMessageBox.critical(self, title, message)
    
    def _get_system_name(self, system_id: int) -> str:
        """Get system name by ID."""
        try:
            if not self.database_initializer:
                return "Unknown"
            
            db_manager = self.database_initializer.get_database_manager()
            connection = db_manager.get_connection()
            
            system_data = connection.fetchone(
                "SELECT system_name FROM systems WHERE id = ?",
                (system_id,)
            )
            
            if system_data:
                return system_data['system_name']
            else:
                return "Unknown"
                
        except Exception as e:
            logger.error(f"Failed to get system name: {str(e)}")
            return "Unknown"
    
    def _on_system_selected(self, system_id: int):
        """Handle system selection from hierarchy tree."""
        try:
            self.current_system_id = system_id
            
            # Update breadcrumb
            if self.database_initializer:
                db_manager = self.database_initializer.get_database_manager()
                connection = db_manager.get_connection()
                system_repo = EntityFactory.get_repository(connection, System)
                system = system_repo.get_by_id(system_id)
                
                if system:
                    self._update_breadcrumb(system)
                    self._enable_system_buttons()
                    
                    # Load data for all tabs
                    self._load_functions_for_system(system_id)
                    self._load_requirements_for_system(system_id)
                    self._load_interfaces_for_system(system_id)
                    self._load_assets_for_system(system_id)
                    self._load_hazards_for_system(system_id)
                    self._load_losses_for_system(system_id)
                    self._load_control_structures_for_system(system_id)
                    self._load_controllers_for_system(system_id)
                    
        except Exception as e:
            logger.error(f"Failed to handle system selection: {str(e)}")
    
    def _on_system_changed(self):
        """Handle system change notification."""
        if self.hierarchy_tree:
            self.hierarchy_tree.refresh_from_database()
    
    def _update_breadcrumb(self, system: System):
        """Update the breadcrumb with system information."""
        if system:
            breadcrumb_text = f"System: {system.system_name}"
            if system.system_description:
                breadcrumb_text += f" - {system.system_description[:50]}..."
            self.breadcrumb_label.setText(breadcrumb_text)
        else:
            self.breadcrumb_label.setText("No system selected")
    
    def _enable_system_buttons(self):
        """Enable system-related buttons when a system is selected."""
        self.edit_system_btn.setEnabled(True)
        self.add_child_system_btn.setEnabled(True)
        
        # Enable add buttons for all entity types
        self.add_function_btn.setEnabled(True)
        self.add_requirement_btn.setEnabled(True)
        self.add_interface_btn.setEnabled(True)
        self.add_asset_btn.setEnabled(True)
        self.add_control_structure_btn.setEnabled(True)
        self.add_controller_btn.setEnabled(True)
    
    def _add_child_system(self):
        """Add a child system to the currently selected system."""
        if not self.current_system_id:
            QMessageBox.warning(self, "No System Selected", "Please select a parent system first.")
            return
        
        dialog = SystemEditDialog(parent_id=self.current_system_id, parent=self)
        dialog.system_saved.connect(self._on_system_saved)
        dialog.exec()
    
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
                
                items = [
                    QTableWidgetItem(function.get_hierarchical_id()),
                    QTableWidgetItem(function.function_name),
                    QTableWidgetItem(function.function_description[:100] + "..." if len(function.function_description or "") > 100 else function.function_description or ""),
                    QTableWidgetItem(function.criticality or "Medium")
                ]

                for item in items:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)

                for col, item in enumerate(items):
                    self.functions_table.setItem(row, col, item)
                
                # Store function ID for editing
                self.functions_table.item(row, 0).setData(Qt.UserRole, function.id)
            
        except Exception as e:
            logger.error(f"Failed to load functions: {str(e)}")
    
    def closeEvent(self, event):
        """Handle window close event."""
        try:
            # Save window state
            self.config_manager.set("window_geometry", self.saveGeometry())
            self.config_manager.set("window_state", self.saveState())
            
            if self.splitter:
                self.config_manager.set("splitter_sizes", self.splitter.sizes())
            
            # Save configuration
            self.config_manager.save()
            
            event.accept()
            
        except Exception as e:
            logger.error(f"Failed to save window state: {str(e)}")
            event.accept()