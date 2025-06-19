"""
Main application class for STPA Tool
Handles application initialization, startup, and shutdown.
"""

import sys
import traceback
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import QApplication, QSplashScreen, QMessageBox
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QIcon

from .config.settings import ConfigManager
from .config.constants import APP_NAME, APP_VERSION, APP_AUTHOR
from .log_config.config import LoggingConfig, get_logger
from .ui.dialogs import DirectorySelectionDialog, ErrorDialog
from .ui.main_window import MainWindow
from .utils.directory import DirectoryManager
from .database.init import DatabaseInitializer

logger = get_logger(__name__)


class STPAApplication(QApplication):
    """
    Main application class for STPA Tool.
    """
    
    def __init__(self, argv):
        """
        Initialize the STPA application.
        
        Args:
            argv: Command line arguments
        """
        super().__init__(argv)
        
        # Application metadata
        self.setApplicationName(APP_NAME)
        self.setApplicationVersion(APP_VERSION)
        self.setOrganizationName(APP_AUTHOR)
        
        # Application state
        self.config_manager: Optional[ConfigManager] = None
        self.main_window: Optional[MainWindow] = None
        self.splash_screen: Optional[QSplashScreen] = None
        self.database_initializer: Optional[DatabaseInitializer] = None
        
        # Setup exception handling
        sys.excepthook = self._handle_exception
        
        logger.info(f"Starting {APP_NAME} v{APP_VERSION}")
    
    def initialize(self) -> bool:
        """
        Initialize the application.
        
        Returns:
            True if initialization was successful
        """
        try:
            # Show splash screen
            self._show_splash_screen()
            
            # Setup logging
            self._update_splash("Setting up logging...")
            self._setup_logging()
            
            # Select working directory
            self._update_splash("Selecting working directory...")
            working_directory = self._select_working_directory()
            if not working_directory:
                return False
            
            # Initialize configuration
            self._update_splash("Loading configuration...")
            self.config_manager = ConfigManager(working_directory)
            self.config_manager.load_config()
            
            # Initialize database
            self._update_splash("Initializing database...")
            self.database_initializer = DatabaseInitializer(working_directory)
            if not self.database_initializer.initialize():
                raise Exception("Failed to initialize database")
            
            # Create main window
            self._update_splash("Creating main window...")
            self.main_window = MainWindow(self.config_manager, self.database_initializer)
            
            # Hide splash screen and show main window
            self._hide_splash_screen()
            self.main_window.show()
            
            logger.info("Application initialization completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Application initialization failed: {str(e)}")
            self._hide_splash_screen()
            
            ErrorDialog.show_error(
                None,
                "Initialization Error",
                "Failed to initialize STPA Tool.",
                str(e)
            )
            return False
    
    def shutdown(self) -> bool:
        """
        Shutdown the application gracefully.
        
        Returns:
            True if shutdown was successful
        """
        try:
            logger.info("Shutting down application...")
            
            # Save configuration
            if self.config_manager:
                if self.main_window:
                    # Update UI state in configuration
                    self.main_window.save_ui_state()
                
                # Save configuration to file
                self.config_manager.save_config()
            
            # Close database
            if self.database_initializer:
                self.database_initializer.close()
            
            # Close main window
            if self.main_window:
                self.main_window.close()
            
            logger.info("Application shutdown completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error during application shutdown: {str(e)}")
            return False
    
    def _show_splash_screen(self):
        """Show splash screen during initialization."""
        try:
            # Create a simple splash screen (we'll add an image later)
            splash_pixmap = QPixmap(400, 300)
            splash_pixmap.fill(Qt.lightGray)
            
            self.splash_screen = QSplashScreen(splash_pixmap)
            self.splash_screen.setWindowFlags(
                Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint
            )
            
            # Add text to splash screen
            self.splash_screen.showMessage(
                f"{APP_NAME} v{APP_VERSION}\nLoading...",
                Qt.AlignBottom | Qt.AlignCenter,
                Qt.black
            )
            
            self.splash_screen.show()
            self.processEvents()
            
        except Exception as e:
            logger.warning(f"Could not show splash screen: {str(e)}")
    
    def _update_splash(self, message: str):
        """Update splash screen message."""
        if self.splash_screen:
            self.splash_screen.showMessage(
                f"{APP_NAME} v{APP_VERSION}\n{message}",
                Qt.AlignBottom | Qt.AlignCenter,
                Qt.black
            )
            self.processEvents()
    
    def _hide_splash_screen(self):
        """Hide splash screen."""
        if self.splash_screen:
            self.splash_screen.hide()
            self.splash_screen = None
    
    def _setup_logging(self):
        """Setup application logging."""
        # For now, use default logging setup
        # Later we can make this configurable
        LoggingConfig.setup_logging()
    
    def _select_working_directory(self) -> Optional[Path]:
        """
        Select working directory for the application.
        
        Returns:
            Selected working directory or None if cancelled
        """
        # Check if we have a working directory from previous session
        # (This would be stored in system settings in a real application)
        
        dialog = DirectorySelectionDialog()
        
        if dialog.exec() == DirectorySelectionDialog.Accepted:
            return dialog.get_selected_directory()
        
        return None
    
    def _handle_exception(self, exc_type, exc_value, exc_traceback):
        """
        Handle uncaught exceptions.
        
        Args:
            exc_type: Exception type
            exc_value: Exception value
            exc_traceback: Exception traceback
        """
        if issubclass(exc_type, KeyboardInterrupt):
            # Handle Ctrl+C gracefully
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        # Log the exception
        error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        logger.critical(f"Uncaught exception: {error_msg}")
        
        # Show error dialog
        ErrorDialog.show_error(
            self.main_window,
            "Unexpected Error",
            "An unexpected error occurred. Please check the log files for details.",
            str(exc_value)
        )


def main():
    """
    Main entry point for the STPA Tool application.
    """
    app = STPAApplication(sys.argv)
    
    if app.initialize():
        # Run the application
        exit_code = app.exec()
        
        # Shutdown gracefully
        app.shutdown()
        
        sys.exit(exit_code)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()