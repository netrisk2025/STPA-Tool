# STPA Tool Development Documentation

## Project Overview
This document tracks the development progress of the STPA Tool (Systems-Theoretic Process Analysis Tool), a standalone desktop application built with Python 3 and PySide6.

**Author:** Nicholas Triska  
**Version:** 1.0.0  
**Development Started:** June 19, 2025  

## Completed Tasks

### Phase 1: Project Setup and Infrastructure ✅ **COMPLETED**

#### 1.1 Development Environment Setup ✅
- **1.1.1** ✅ Installed Python 3.12.7 and created virtual environment `stpa_tool_env`
- **1.1.2** ✅ Installed PySide6 6.9.1 and core dependencies (pytest, pytest-qt, PyYAML)
- **1.1.3** ✅ IDE/editor setup (environment ready for development)
- **1.1.4** ✅ Configured Git version control with comprehensive `.gitignore`
- **1.1.5** ✅ Created `requirements.txt` with all dependencies

#### 1.2 Project Structure Creation ✅
- **1.2.1** ✅ Created main project directory structure:
  - `/src` - Source code
  - `/tests` - Unit and integration tests
  - `/docs` - Documentation
  - `/resources` - UI files, icons, etc.
  - `/scripts` - Build and deployment scripts
- **1.2.2** ✅ Created Python package structure with `__init__.py` files:
  - `src/database/` - Database operations
  - `src/ui/` - User interface components
  - `src/utils/` - Utility functions
  - `src/config/` - Configuration management
  - `src/logging/` - Logging configuration
- **1.2.3** ✅ Set up logging configuration module (`src/logging/config.py`)
- **1.2.4** ✅ Created application constants and configuration modules:
  - `src/config/constants.py` - Application constants and defaults
  - `src/config/settings.py` - Configuration management classes

#### 1.3 Configuration System Implementation ✅
- **1.3.1** ✅ Designed configuration file schema supporting JSON/YAML formats

#### 1.4 Working Directory Management ✅
- **1.4.1** ✅ Created working directory selection dialog (`src/ui/dialogs.py`)
- **1.4.2** ✅ Implemented directory validation (permissions, existing files)
- **1.4.3** ✅ Created directory structure initialization (`src/utils/directory.py`)

#### 1.5 Application Framework ✅
- **1.5.1** ✅ Created main application class with PySide6 (`src/app.py`)
- **1.5.2** ✅ Implemented application startup sequence
- **1.5.3** ✅ Added splash screen with loading progress
- **1.5.4** ✅ Created graceful shutdown handling
- **1.5.5** ✅ Implemented exception handling and error reporting

### Phase 2: Database Design and Implementation ✅ **COMPLETED**

#### 2.1 Database Schema Design ✅
- **2.1.1** ✅ Translated ER diagram to SQLite schema with 21 main tables
- **2.1.2** ✅ Defined all table structures with proper SQLite data types
- **2.1.3** ✅ Created foreign key relationships and constraints
- **2.1.4** ✅ Designed indexes for performance optimization
- **2.1.5** ✅ Added database version tracking table

#### 2.2 Core Entity Tables ✅
- **2.2.1** ✅ Created System table with hierarchical structure and parent-child relationships
- **2.2.2** ✅ Implemented Function, Interface, Asset tables with system associations

#### 2.6 Baseline System ✅
- **2.6.1** ✅ Added baseline column to all entity tables for versioning

#### 2.7 Audit Trail System ✅
- **2.7.1** ✅ Created audit_log table with hash chaining for data integrity

#### 2.8 Database Initialization ✅
- **2.8.1** ✅ Created database schema creation scripts with full SQL generation
- **2.8.2** ✅ Implemented database migration system with version tracking

#### 2.9 Data Access Layer (DAL) ✅
- **2.9.1** ✅ Created base entity class with common operations and critical attributes
- **2.9.2** ✅ Implemented CRUD operations with repository pattern

#### 2.10 Hierarchical ID Management ✅
- **2.10.1** ✅ Created hierarchical ID generation algorithm with parsing and validation

#### 2.12 Database Testing ✅
- **2.12.1** ✅ Created comprehensive database unit tests (16 tests, all passing)

## Current Application Structure

```
STPA Tool/
├── main.py                     # Main entry point
├── requirements.txt            # Python dependencies
├── .gitignore                 # Git ignore rules
├── src/
│   ├── __init__.py
│   ├── app.py                 # Main application class
│   ├── config/
│   │   ├── __init__.py
│   │   ├── constants.py       # Application constants
│   │   └── settings.py        # Configuration management
│   ├── database/
│   │   ├── __init__.py
│   │   ├── schema.py          # Database schema definition
│   │   ├── connection.py      # Database connection management
│   │   ├── entities.py        # Entity classes and repository pattern
│   │   └── init.py            # Database initialization
│   ├── log_config/
│   │   ├── __init__.py
│   │   └── config.py          # Logging configuration
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── dialogs.py         # Dialog classes
│   │   └── main_window.py     # Main window
│   └── utils/
│       ├── __init__.py
│       ├── directory.py       # Directory management
│       └── hierarchy.py       # Hierarchical ID management
├── tests/
│   ├── __init__.py
│   └── test_database.py       # Comprehensive database tests
├── docs/
├── resources/
├── scripts/
└── stpa_tool_env/             # Virtual environment
```

## Key Features Implemented

### Configuration Management
- JSON/YAML configuration file support
- Working directory management
- UI state persistence
- Database configuration

### User Interface Framework
- Main window with splitter layout
- Hierarchy navigation tree (left pane)
- Tabbed content area (right pane)
- Menu system with placeholders for STPA functions
- Status bar with database and baseline status
- Splash screen during startup

### Dialog System
- Working directory selection dialog
- Directory validation and initialization
- Error, confirmation, and info dialogs
- Progress dialog for long operations

### Logging System
- Centralized logging configuration
- File and console logging support
- Log rotation capabilities
- Application-wide logger instances

### Database System
- Complete SQLite database with 21 main tables
- Entity-Relationship model implementation from ER diagram
- Repository pattern for data access
- CRUD operations for all entity types
- Hierarchical ID management and validation
- Audit trail with hash chaining for data integrity
- Baseline system for versioning
- Database initialization and migration
- Comprehensive test suite (16 tests)

### Directory Management
- Working directory validation
- Automatic subdirectory creation
- File permissions checking
- Database backup functionality
- Temporary file cleanup

## Dependencies

```
iniconfig==2.1.0
packaging==25.0
pluggy==1.6.0
Pygments==2.19.1
PySide6==6.9.1
PySide6_Addons==6.9.1
PySide6_Essentials==6.9.1
pytest==8.4.1
pytest-qt==4.4.0
PyYAML==6.0.2
shiboken6==6.9.1
```

## Next Steps

Both foundational phases are now complete. The next major phase will focus on:

1. **Core User Interface Framework (Phase 3)**
   - Enhanced UI components for database interaction
   - Entity editing forms and validation
   - System hierarchy navigation with database integration
   - Real-time data display and updates

2. **Core Entity Management (Phase 4)**
   - System, Function, Interface entities
   - Requirement management with hierarchy
   - Control structure components
   - Hazard and loss tracking

3. **Testing Framework (Phase 7)**
   - Unit tests for all components
   - Integration testing
   - UI testing with pytest-qt

## Testing Results ✅

**Application Testing Completed:** All core components tested successfully

### Import Tests ✅
- All module imports working correctly
- Configuration management functional
- Logging system operational
- UI framework ready
- Directory management working

### Functionality Tests ✅
- ConfigManager: JSON/YAML save/load working
- DirectoryManager: Validation and initialization working
- GUI Framework: PySide6 application creation successful
- Module structure: All imports resolved correctly

### Issues Resolved ✅
- **Logging Module Conflict**: Renamed `src/logging/` to `src/log_config/` to avoid conflicts with Python's built-in logging module
- **Import Dependencies**: Fixed all import paths after package rename
- **Environment Setup**: Verified virtual environment and dependencies working correctly

## Development Notes

- Python 3.12.7 used (exceeds minimum requirement of 3.11+)
- PySide6 6.9.1 provides Qt 6 bindings for modern UI
- Configuration supports both JSON and YAML formats
- Comprehensive error handling and logging throughout
- Modular architecture allows for easy extension
- Git repository initialized with proper ignore rules
- **Note**: Logging package renamed to `log_config` to avoid Python stdlib conflicts

## Usage

To run the application:

```bash
cd "/media/netrisk/Maxwell/STPA Tool"
source stpa_tool_env/bin/activate
python main.py
```

The application will prompt for a working directory selection on first run and create the necessary subdirectories and configuration files.