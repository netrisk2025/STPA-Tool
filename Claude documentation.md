# STPA Tool Development Documentation

## Project Overview
This document tracks the development progress of the STPA Tool (Systems-Theoretic Process Analysis Tool), a standalone desktop application built with Python 3 and PySide6.

**Author:** Nicholas Triska  
**Version:** 1.0.0  
**Development Started:** June 19, 2025  

## Completed Tasks

### Phase 1: Project Setup and Infrastructure

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
│   │   └── __init__.py
│   ├── logging/
│   │   ├── __init__.py
│   │   └── config.py          # Logging configuration
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── dialogs.py         # Dialog classes
│   │   └── main_window.py     # Main window
│   └── utils/
│       ├── __init__.py
│       └── directory.py       # Directory management
├── tests/
│   └── __init__.py
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

The foundation has been established for the STPA Tool. The next major phase will focus on:

1. **Database Design and Implementation (Phase 2)**
   - SQLite database schema creation
   - Entity-Relationship model implementation
   - Data Access Layer (DAL) development
   - Baseline and audit trail systems

2. **Core Entity Management (Phase 4)**
   - System, Function, Interface entities
   - Requirement management with hierarchy
   - Control structure components
   - Hazard and loss tracking

3. **Testing Framework (Phase 7)**
   - Unit tests for all components
   - Integration testing
   - UI testing with pytest-qt

## Development Notes

- Python 3.12.7 used (exceeds minimum requirement of 3.11+)
- PySide6 6.9.1 provides Qt 6 bindings for modern UI
- Configuration supports both JSON and YAML formats
- Comprehensive error handling and logging throughout
- Modular architecture allows for easy extension
- Git repository initialized with proper ignore rules

## Usage

To run the application:

```bash
cd "/media/netrisk/Maxwell/STPA Tool"
source stpa_tool_env/bin/activate
python main.py
```

The application will prompt for a working directory selection on first run and create the necessary subdirectories and configuration files.