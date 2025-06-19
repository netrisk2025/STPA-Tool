"""
Main window for STPA Tool
Contains the primary user interface layout and components.
"""

from PySide6.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QSplitter,
    QMenuBar, QStatusBar, QToolBar, QLabel, QTreeWidget, QTabWidget
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QIcon

from ..config.settings import ConfigManager
from ..config.constants import (
    APP_NAME, WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT, SPLITTER_DEFAULT_SIZES
)
from ..log_config.config import get_logger

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
        
        # Setup UI
        self._setup_ui()
        self._setup_menus()
        self._setup_toolbar()
        self._setup_status_bar()
        
        # Restore window state
        self._restore_window_state()
        
        logger.info("Main window initialized")
    
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
        # Create hierarchy tree widget
        self.hierarchy_tree = QTreeWidget()
        self.hierarchy_tree.setHeaderLabel("System Hierarchy")
        self.hierarchy_tree.setMinimumWidth(200)
        
        # TODO: Connect to database and populate tree
        # For now, add placeholder items
        self._populate_hierarchy_placeholder()
        
        # Add to splitter
        self.splitter.addWidget(self.hierarchy_tree)
    
    def _setup_content_pane(self):
        """Setup the right content area pane."""
        # Create content widget
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        
        # Breadcrumb area (header)
        breadcrumb_label = QLabel("System A › Subsystem B")
        breadcrumb_label.setStyleSheet("""
            QLabel {
                background-color: #f0f0f0;
                padding: 8px;
                border-bottom: 1px solid #ccc;
                font-weight: bold;
            }
        """)
        content_layout.addWidget(breadcrumb_label)
        
        # Tabbed content area
        self.content_tabs = QTabWidget()
        self.content_tabs.setTabPosition(QTabWidget.North)
        
        # Add placeholder tabs
        self._setup_placeholder_tabs()
        
        content_layout.addWidget(self.content_tabs)
        
        # Add to splitter
        self.splitter.addWidget(content_widget)
    
    def _setup_placeholder_tabs(self):
        """Setup placeholder tabs for development."""
        # Overview tab
        overview_widget = QWidget()
        overview_layout = QVBoxLayout(overview_widget)
        overview_layout.addWidget(QLabel("System Overview - Coming Soon"))
        self.content_tabs.addTab(overview_widget, "Overview")
        
        # Functions tab
        functions_widget = QWidget()
        functions_layout = QVBoxLayout(functions_widget)
        functions_layout.addWidget(QLabel("Functions - Coming Soon"))
        self.content_tabs.addTab(functions_widget, "Functions")
        
        # Interfaces tab
        interfaces_widget = QWidget()
        interfaces_layout = QVBoxLayout(interfaces_widget)
        interfaces_layout.addWidget(QLabel("Interfaces - Coming Soon"))
        self.content_tabs.addTab(interfaces_widget, "Interfaces")
        
        # States tab
        states_widget = QWidget()
        states_layout = QVBoxLayout(states_widget)
        states_layout.addWidget(QLabel("States - Coming Soon"))
        self.content_tabs.addTab(states_widget, "States")
        
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
    
    def _populate_hierarchy_placeholder(self):
        """Add placeholder items to hierarchy tree."""
        # TODO: Replace with actual database data
        from PySide6.QtWidgets import QTreeWidgetItem
        
        # Root system
        root_item = QTreeWidgetItem(self.hierarchy_tree)
        root_item.setText(0, "S-1 Root System")
        
        # Subsystem 1
        subsystem1 = QTreeWidgetItem(root_item)
        subsystem1.setText(0, "S-1.1 Subsystem A")
        
        # Subsystem 2
        subsystem2 = QTreeWidgetItem(root_item)
        subsystem2.setText(0, "S-1.2 Subsystem B")
        
        # Sub-subsystem
        subsubsystem = QTreeWidgetItem(subsystem2)
        subsubsystem.setText(0, "S-1.2.1 Component X")
        
        # Expand all items
        self.hierarchy_tree.expandAll()
    
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
        
        load_baseline_action = QAction("&Load Baseline", self)
        load_baseline_action.triggered.connect(self._load_baseline)
        baseline_menu.addAction(load_baseline_action)
        
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
        # TODO: Implement JSON export functionality
    
    def _export_markdown(self):
        """Handle Markdown export action."""
        logger.info("Markdown export action triggered")
        # TODO: Implement Markdown export functionality
    
    def _create_baseline(self):
        """Handle create baseline action."""
        logger.info("Create baseline action triggered")
        # TODO: Implement create baseline functionality
    
    def _load_baseline(self):
        """Handle load baseline action."""
        logger.info("Load baseline action triggered")
        # TODO: Implement load baseline functionality
    
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