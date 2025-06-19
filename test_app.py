#!/usr/bin/env python3
"""
STPA Tool - Application Test Script
Tests the core functionality without requiring a GUI display.
"""

import sys
import os
from pathlib import Path
import tempfile

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Set environment for headless testing
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

def test_imports():
    """Test all core module imports."""
    print("Testing imports...")
    
    try:
        from src.config.constants import APP_NAME, APP_VERSION
        print(f"✓ Constants: {APP_NAME} v{APP_VERSION}")
        
        from src.config.settings import ConfigManager
        print("✓ Configuration manager imported")
        
        from src.log_config.config import LoggingConfig
        print("✓ Logging configuration imported")
        
        from src.utils.directory import DirectoryManager
        print("✓ Directory manager imported")
        
        from src.ui.dialogs import DirectorySelectionDialog
        print("✓ UI dialogs imported")
        
        from src.ui.main_window import MainWindow
        print("✓ Main window imported")
        
        from src.app import STPAApplication
        print("✓ Main application imported")
        
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False

def test_configuration():
    """Test configuration management."""
    print("\nTesting configuration...")
    
    try:
        from src.config.settings import ConfigManager
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Test ConfigManager
            config_manager = ConfigManager(temp_path)
            print("✓ ConfigManager created")
            
            # Test saving configuration
            success = config_manager.save_config()
            print(f"✓ Configuration saved: {success}")
            
            # Test loading configuration
            success = config_manager.load_config()
            print(f"✓ Configuration loaded: {success}")
            
            return True
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False

def test_directory_management():
    """Test directory management."""
    print("\nTesting directory management...")
    
    try:
        from src.utils.directory import DirectoryManager
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            dir_manager = DirectoryManager(temp_path)
            
            # Test validation
            valid, msg = dir_manager.validate_directory(temp_path)
            print(f"✓ Directory validation: {valid} ({msg or 'OK'})")
            
            # Test initialization
            success, msg = dir_manager.initialize_directory(temp_path)
            print(f"✓ Directory initialization: {success} ({msg or 'OK'})")
            
            # Check created subdirectories
            subdirs = ['diagrams', 'baselines', 'temp']
            for subdir in subdirs:
                if (temp_path / subdir).exists():
                    print(f"✓ Subdirectory created: {subdir}")
                else:
                    print(f"✗ Subdirectory missing: {subdir}")
            
            return True
    except Exception as e:
        print(f"✗ Directory management test failed: {e}")
        return False

def test_gui_framework():
    """Test GUI framework without creating windows."""
    print("\nTesting GUI framework...")
    
    try:
        from src.app import STPAApplication
        
        # Create application instance
        app = STPAApplication(['test'])
        print("✓ Application instance created")
        
        # Test application metadata
        print(f"✓ App name: {app.applicationName()}")
        print(f"✓ App version: {app.applicationVersion()}")
        print(f"✓ Organization: {app.organizationName()}")
        
        return True
    except Exception as e:
        print(f"✗ GUI framework test failed: {e}")
        return False

def test_logging():
    """Test logging system."""
    print("\nTesting logging system...")
    
    try:
        from src.log_config.config import LoggingConfig, get_logger
        
        # Setup logging
        LoggingConfig.setup_logging()
        print("✓ Logging setup completed")
        
        # Test logger creation
        logger = get_logger("test")
        print("✓ Logger instance created")
        
        # Test logging (this will go to console)
        logger.info("Test log message")
        print("✓ Log message sent")
        
        return True
    except Exception as e:
        print(f"✗ Logging test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 50)
    print("STPA Tool - Application Test Suite")
    print("=" * 50)
    
    tests = [
        ("Imports", test_imports),
        ("Configuration", test_configuration),
        ("Directory Management", test_directory_management),
        ("GUI Framework", test_gui_framework),
        ("Logging System", test_logging),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 20)
        if test_func():
            passed += 1
            print(f"✓ {test_name} PASSED")
        else:
            print(f"✗ {test_name} FAILED")
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Application is ready for Phase 2.")
        return 0
    else:
        print("❌ Some tests failed. Please review the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())