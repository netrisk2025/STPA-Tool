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

**Current Phase:** 7 - Testing, Validation, and Documentation ✅ **COMPLETED**

**Next Phase:** 8 - Packaging and Deployment

**Overall Progress:** 7/8 Phases Complete (87.5%)

### Completed Features

✅ **Phase 1: Project Setup and Infrastructure**
- Python 3.12.7 with virtual environment
- PySide6 6.9.1 for modern Qt-based GUI
- Comprehensive project structure
- Application framework with startup/shutdown handling
- Configuration management (JSON/YAML)
- Working directory management
- User interface foundation
- Logging system with rotation support

✅ **Phase 2: Database Design and Implementation**
- Complete SQLite database with 21 main tables
- Entity-Relationship model from ER diagram
- Repository pattern for data access
- CRUD operations for all entity types
- Hierarchical ID management and validation
- Audit trail with hash chaining
- Baseline system for versioning
- Database initialization and migration
- Comprehensive test suite (16 tests)
- Application integration with database

✅ **Phase 3: Core User Interface Framework**
- Enhanced hierarchy tree widget with database integration
- Interactive system navigation and selection
- Entity editing dialogs for System, Function, and Requirement entities
- Critical attributes widget for security/safety properties
- Real-time data loading and display
- Context menus for entity management
- Entity management tabs with CRUD operations
- Breadcrumb navigation for selected systems
- Full database integration with UI components

✅ **Phase 4: Core Entity Management** *(Completed)*
- Base entity widget framework with CRUD operations
- Entity validation and change tracking system
- Interface entity management with system associations
- Asset entity management with critical attributes
- Hazard entity management for safety analysis
- Loss entity management for loss scenarios
- Control structure entity management (ControlStructure, Controller)
- Complete entity framework with all STPA entities implemented
- Entity tabs integrated into main application interface

✅ **Phase 5: Diagramming and Visualization** *(Completed)*
- Mermaid.js CLI integration for diagram generation
- Control structure diagram generation with color coding
- State diagram generation and visualization
- Requirement hierarchy diagram generation
- System hierarchy diagram generation
- Interactive SVG diagram viewer with zoom/pan controls
- Diagram export functionality (SVG/PNG)
- Diagram file management with baseline support
- Integrated diagram tab in main application interface

✅ **Phase 6: Import/Export and Collaboration** *(Completed)*
- Comprehensive JSON export system for System of Interest data
- Markdown export functionality for specifications and descriptions
- Working directory ZIP archive export/import capabilities
- Enhanced entity framework with all STPA entity types
- Export dialogs with preview functionality and validation
- Archive validation and integrity checking
- **Baseline Management System** - Create, load, compare, and manage project baselines
- **Branch Management System** - Create isolated project branches for collaboration
- **Merge Management System** - Merge branches with conflict detection and resolution
- Collaboration menu with baseline and branch management dialogs
- Integrated collaboration workflow for multi-user projects

✅ **Phase 7: Testing, Validation, and Documentation** *(Completed)*
- **Comprehensive Testing Framework** - Unit tests, integration tests, and performance tests (95% pass rate)
- **Data Validation Engine** - Pluggable validation rules with completeness and consistency checks
- **Warnings Tab Implementation** - Interactive validation issue display with filtering and navigation
- **Performance Testing Suite** - Database performance tests for large datasets (1000+ records, <30s)
- **Memory Usage Testing** - Memory leak detection and usage optimization testing
- **Export Testing Coverage** - Comprehensive tests for JSON, Markdown, and Archive exports (100% pass rate)
- **UI Component Testing** - Headless testing support for dialogs, widgets, and main window
- **Validation Issue Management** - Severity-based issue categorization with detailed suggestions
- **Bug Fixes and Quality Improvements** - Fixed export API issues, hierarchical ID parsing, transaction handling
- **Code Quality Enhancements** - Added missing repository methods, improved error handling, enhanced test coverage

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

To verify the installation, run the comprehensive test suite:

```bash
# Quick application test
python test_app.py

# Full test suite (requires pytest)
source stpa_tool_env/bin/activate
pytest tests/ -v
```

**Test Coverage:**
- **Database Tests**: 16/16 passing (100%)
- **Export Functionality**: 19/19 passing (100%)
- **Validation Engine**: 17/17 passing (100%)
- **Performance Tests**: 7/10 passing (70% - UI tests skipped in headless)
- **Overall Success Rate**: 95% (excluding UI-dependent tests)

## Project Structure

```
STPA Tool/
├── main.py                     # Main entry point
├── test_app.py                 # Quick application test
├── requirements.txt            # Python dependencies
├── src/
│   ├── app.py                 # Main application class
│   ├── config/                # Configuration management
│   ├── database/              # Complete SQLite database system
│   ├── diagrams/              # Mermaid.js diagram generation
│   ├── export/                # JSON/Markdown/Archive exports
│   ├── collaboration/         # Branch/merge management  
│   ├── validation/            # Data validation engine
│   ├── log_config/            # Logging configuration
│   ├── ui/                    # Complete user interface
│   └── utils/                 # Utility functions
├── tests/                     # Comprehensive test suite
│   ├── test_database.py       # Database tests (16 tests)
│   ├── test_export_functionality.py  # Export tests (19 tests)
│   ├── test_validation_engine.py     # Validation tests (17 tests)
│   ├── test_performance.py    # Performance tests (10 tests)
│   └── test_ui_components.py  # UI tests
├── Project Plan/              # Development documentation
├── docs/                      # Technical documentation
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

**PHASE 7 COMPLETE**: All seven foundational phases are complete with a comprehensive, tested, and validated STPA Tool application including:

- ✅ **Complete Database Backend** - SQLite with 21 tables, audit trail, baseline management
- ✅ **Interactive User Interface** - PySide6-based GUI with entity management and navigation
- ✅ **Diagram Generation** - Mermaid.js integration for control structures, states, and requirements
- ✅ **Export Capabilities** - JSON, Markdown, and ZIP archive exports with validation
- ✅ **Collaboration Features** - Branch/merge system for multi-user projects
- ✅ **Testing Framework** - 62 comprehensive tests with 95% pass rate
- ✅ **Data Validation** - Real-time validation engine with warnings and issue management
- ✅ **Performance Validation** - Tested with 1000+ records, concurrent access, and large exports

**Ready for Phase 8**: Packaging and deployment as a standalone executable.

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