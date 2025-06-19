# STPA Tool

**Systems-Theoretic Process Analysis Tool**

A standalone desktop application for performing STPA (Systems-Theoretic Process Analysis) methodology for safety and security analysis.

## Overview

The STPA Tool provides a structured environment for users to:
- Define system hierarchies
- Identify system components and their interactions
- Analyze control structures
- Identify hazards and loss scenarios
- Derive safety and security requirements

## Development Status

**Current Phase:** 1 - Project Setup and Infrastructure ✅ **COMPLETED**

**Next Phase:** 2 - Database Design and Implementation

### Completed Features (Phase 1)

✅ **Development Environment**
- Python 3.12.7 with virtual environment
- PySide6 6.9.1 for modern Qt-based GUI
- Comprehensive project structure

✅ **Application Framework**
- Main application class with startup/shutdown handling
- Splash screen with loading progress
- Exception handling and error reporting
- Configuration management (JSON/YAML)

✅ **Working Directory Management**
- Directory selection and validation
- Automatic subdirectory creation
- File permissions checking

✅ **User Interface Foundation**
- Main window with splitter layout
- Hierarchy navigation tree (left pane)
- Tabbed content area (right pane)
- Menu system and status bar
- Dialog framework

✅ **Logging System**
- Centralized logging configuration
- File and console logging
- Log rotation support

## Quick Start

### Prerequisites

- Python 3.11+ (tested with 3.12.7)
- Linux/Unix environment

### Installation

1. Clone or download the project
2. Navigate to the project directory:
   ```bash
   cd "STPA Tool"
   ```

3. Activate the virtual environment:
   ```bash
   source stpa_tool_env/bin/activate
   ```

4. Run the application:
   ```bash
   python main.py
   ```

### Testing

To verify the installation, run the test suite:

```bash
python test_app.py
```

Expected output:
```
==================================================
STPA Tool - Application Test Suite
==================================================
...
Test Results: 5/5 tests passed
🎉 All tests passed! Application is ready for Phase 2.
```

## Project Structure

```
STPA Tool/
├── main.py                     # Main entry point
├── test_app.py                 # Test suite
├── requirements.txt            # Python dependencies
├── src/
│   ├── app.py                 # Main application class
│   ├── config/                # Configuration management
│   ├── database/              # Database operations (TBD)
│   ├── log_config/            # Logging configuration
│   ├── ui/                    # User interface components
│   └── utils/                 # Utility functions
├── tests/                     # Unit tests (TBD)
├── docs/                      # Documentation
├── resources/                 # UI resources (TBD)
├── scripts/                   # Build scripts (TBD)
└── stpa_tool_env/            # Virtual environment
```

## Dependencies

Core dependencies are managed in `requirements.txt`:

- **PySide6 6.9.1** - Qt 6 bindings for GUI
- **PyYAML 6.0.2** - YAML configuration support
- **pytest 8.4.1** - Testing framework
- **pytest-qt 4.4.0** - Qt testing support

## Development

### Current Status

The application foundation is complete and all core components are tested and functional. The next development phase will focus on:

1. **Database Design** - SQLite schema implementation
2. **Entity Management** - CRUD operations for STPA entities
3. **Data Visualization** - Mermaid.js integration for diagrams

### Architecture

- **Modular Design**: Clear separation between UI, business logic, and data layers
- **Configuration-Driven**: JSON/YAML configuration with validation
- **Extensible**: Plugin-ready architecture for future enhancements
- **Cross-Platform**: Built on Qt/PySide6 for platform independence

## Documentation

- **[Development Plan](Project Plan/STPA_Tool_Development_Plan.md)** - Complete development roadmap
- **[Requirements Specification](STPA Tool SRS.md)** - Detailed requirements
- **[Entity Relationship Diagram](STPA ER Diagram.md)** - Database design
- **[Development Documentation](Claude documentation.md)** - Progress tracking

## License

This project is developed by Nicholas Triska.

## Contact

For questions or contributions, please refer to the project documentation or development plan.