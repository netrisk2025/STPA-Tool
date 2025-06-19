STPA Tool - Software Requirements Specification (SRS) Version: 2.0 Date: June 14, 2025 Status: Approved for Development 

## Introduction 1.1
Purpose This Software Requirements Specification (SRS) defines the complete functional and non-functional requirements for the Systems-Theoretic Process Analysis (STPA) Tool. This document is intended to be the single source of truth for all project stakeholders, including developers, testers, and project managers. It describes the system's features, capabilities, operational environment, and constraints, ensuring a common understanding and guiding the design, implementation, and verification of the software. 

### 1.2 Scope 
The STPA Tool is a standalone desktop application designed to facilitate the STPA methodology for safety and security analysis. The tool will provide a structured environment for users to define a system hierarchy, identify system components and their interactions, analyze control structures, identify hazards and loss scenarios, and derive safety and security requirements. The scope of this document encompasses: The required functionality for a Minimum Viable Product (MVP). The underlying data model and storage mechanisms. The user interface (UI) and user experience (UX) paradigms.  Provisions for manual, multi-user collaboration through project splitting and merging. A clear delineation between in-scope MVP features and identified post-MVP enhancements.

### 1.3 Definitions
Acronyms, and Abbreviations Term Definition Air-Gapped A computer or network that is physically isolated from any other networks, particularly the Internet. Asset A tangible or intangible item of value to the system or its stakeholders that must be protected. Baseline A read-only, timestamped snapshot of the entire project database at a specific point in time. Control Action A command or signal issued by a controller to a controlled process. Control Structure An abstract model of the feedback control loops within a System of Interest. Controlled Process A component or function within the control structure that is managed by a controller. Controller A component within the control structure that makes decisions and issues Control Actions. Critical Attributes A standard set of safety, security, and privacy-related attributes applied to every entity in the data model. ERD Entity-Relationship Diagram. Feedback Information about the state of a controlled process that is sent back to the controller. Hazard A system state or condition that, together with a worst-case set of environmental conditions, will lead to a loss. Hierarchical ID The system-generated, unique identifier for an entity that encodes its position within the system hierarchy (e.g., S-1.2.1). Loss An unacceptable outcome, such as loss of life, mission failure, financial loss, or damage to reputation. MVP Minimum Viable Product. PySide A set of Python bindings for the Qt application framework. SoI System of Interest. The system, at any level of the hierarchy, that is currently the focus of the user's analysis. SQLite A C-language library that implements a small, fast, self-contained, high-reliability, full-featured, SQL database engine. SRS Software Requirements Specification. STPA Systems-Theoretic Process Analysis. UCA Unsafe/Unsecure Control Action. Working Directory The user-selected folder on the local file system where all project artifacts, including the database and diagrams, are stored and managed. WAL Write-Ahead Logging. A mode in SQLite that improves concurrency and performance. 

# 2.Overall Description
### 2.1 Product Perspective
The STPA Tool is a self-contained, standalone software application. It shall be delivered as a single executable file, bundling all necessary dependencies, including the Python runtime, UI framework (PySide 6), and the Mermaid.js command-line interface for diagram rendering. The tool operates entirely offline and is designed for use on air-gapped systems. Its primary function is to serve as a data capture, analysis, and visualization aid for STPA practitioners. 
### 2.2 Product Functions
The major functions of the STPA Tool are: Manage a  well structured relational database, present a compelling user interface for database management, the development of reports and graphics based on information in the database.

The SPTA Tool will consist of:
- Relational Database
- User Interface
- Reports pane
- Graphics pane


### 2.3 The Relational Database
The relational data base will be constructed to host a well structured schema.
The Relational Database shall be configured to be extendable to host from one to ~300,000 records.
The relational database shall be configured according to a defined database schema (developed from an Entity Relationship Diagram)
The Relational Database shall be recursive on systems and requirement records.


### 2.3 The User Interface
The User Interface must perform setup, user tasks and shut-down tasks.
#### 2.3.1 The User Interface Startup
On startup, the STPA Tool User Interface shall present the user with an input box for entry of the  User directory.
The STPA Tool User Interface shall navigate to the User provided directory (User Directory) and configure itself based on the most current STPA Tool Configuration File found there.  
The STPA Tool Configuration File may be JASON or YAML format.
The STPA Tool User Interface shall load the relational database found in the User  Directory identified in the STPA Tool Configuration File.
The STPA Tool User Interface shall report status of database loading in a status icon
The STPA Tool User Interface shall have three windows active at all times:  At top center the Status View, At left the Hierarchy Navigator, at right the Main Window.
The STPA Tool User Interface Status Window shall display the following information:
 - Database path
- Loading Status
- ID, Hierarchy and Name and description of the System of Interest.
- A selector for STPA Tool top-level functions
	- Shutdown
	- Set Baseline
	- Load baseline (read only)
	- Export SoI (no children) in JSON format
	- Export SoI (no Children) in Markdown format
- A selector for STPA Tool Report Functions
	- Output System Specification (for Selected SoI)
	- Output System Description (for Selected SoI)
	- Output Requirement Diagram (for selected SoI) using Mermaid
	- Display State Diagram (for selected SoI) using Mermaid
	- Display Control Structure Block Diagram (for SoI) using Mermaid
	-

The STPA Tool User Interface Hierarchy Navigator shall display the Hierarchy of systems in the loaded database in a slider window.
The STPA Tool User Interface Hierarchy Navigator shall allow the user to roll up and roll down elements in the hierarchy.
STPA Tool shall focus the main window on the System of Interest (SoI) identified in the STPA Tool User Interface Hierarchy Navigator window.
The STPA Tool User Interface Hierarchy Navigator Window shall default to highest level system in the hierarchy with the lowest ID number at startup when not identified by the STPA Tool Configuration File.


#### 2.3.1 The User Interface Run-Time
The STAP Tool User Interface Main window shall display selectors for each element of the SoI.
The STPA Tool User Interface Main Window element selector shall allow the user to select element instances to edit.  When selected the attributes of the element instance will be displayed in editable format in a pop-up window.  Each Pop-up window shall have buttons to Save (update the database), Delete the element instance (if pressed, a popup will be displayed allowing the user to confirm or cancel the delete function) and an "X" in the upper right corner to close the window without saving.
The STPA Tool User Interface Main Window Element selector shall allow the user to add a new element instance.  When selected the new element instance will be displayed in editable format with null values in each field. this pop-up will have the same function buttons to save, delete and close the window as described previously.

### 2.4 Functions
STPA Tool Functions are selected in the Status window at the top center.  All functions operate on the System of Interest (SoI) selected by the Hirarchy Navigator.

The STPA Tool  Shutdown Function shall update hte configuraion file in the User Directory and exit.  The configuration file shall be updated with the current  SoI focus.  All pop-ups active will be closed and the database updated and closed in the User Directory.  When complete, the STPA Tool shall exit.

The STPA Tool Set Baseline function shall clone the entire database and set all records baseline attributes from "working" to the current date.  The clone's file name will be appended with the date and the word "Baseline" and stored in a dated baseline sub-directory created by the STPA Tool in the User Directory.  If  a baseline of the same name exists the user will be asked to overwrite or cancel.  If overwrite is selected, the new clone will overwrite the old clone, if cancel is selected, the clone is deleted.

The STPA Load Baseline function will allow the user to select an existing baseline which will reload the STPA Tool.  All pop-ups will close and the selected baseline shall load into the STAP tool.  The STAP tool will operate the same excepting selected attributes will not be editable (all records are read only)

The STPA Tool Export JSON function will generate a pop-up with the SoI in JSON format  This JSON file will contain all elements and associated attribute values associated with the SoI to include each Child System but go no further than the child system record.  The Pop-Up window shall use the system's file manager to save the file in a directory of the users choosing with default being the User Directory.

The STPA Tool Export Markdown function will generate a pop-up with the SoI in Markdown format  This Markdown file will contain all elements and associated attribute values associated with the SoI to include each Child System but go no further than the child system record.  The Pop-Up window shall use the system's file manager to save the file in a directory of the users choosing with default being the User Directory.

The STPA Tool Output System Specification function creates a pop-up window with text in Markdown format.  The title is "SoI Name" Specification, followed by the SoI description followed by all associated SoI requirements.  Preceding each requirement will be that requirements Unique ID on the same line.  Each requirement will be succeeded by a new line.  The Pop-Up window shall use the system's file manager to save the file in a directory of the users choosing with default being the User Directory.

The STPA Tool Output System Description function will create a pop-up window with text in Markdown format to present the system description, system Function instances (name and description), System Interface instances (name and description) and child systems (name and description).  The Pop-Up window shall use the system's file manager to save the file in a directory of the users choosing with default being the User Directory.

The STPA Tool Output Requirement Diagram function shall allow the user to select any or all requirement instances associated with the SoI.  The function shall transform the selected requirements and all associated requirement children in the database into a mermaid script which will be displayed as a requirements diagram in a pop-up window.  This window will have buttons to close the window (x on window upper right), and Save (using system file manager) as a .png file.  The Window shall also have a button to display the Mermaid script generated in a pop-up which allows the window to close and to save as a .txt file.  

### 2.5 User Characteristics
The target users are systems engineers, safety engineers, and cybersecurity professionals trained in the STPA methodology. Users are expected to have technical expertise in systems analysis but may have varying levels of software proficiency. The UI shall be designed to be intuitive for this target audience. 
### 2.4 General Constraints
The tool shall not require an internet connection for any function. The tool shall be developed using Python 3 and the PySide 6 UI framework. The tool shall not have any inherent security features (e.g., encryption, user authentication, digital signatures) and relies entirely on the security of the host operating system and environment. All data persistence shall be handled via a single SQLite database file. 
### 2.5 Assumptions and Dependencies
The user's host machine will have a compatible operating system (initially Windows, with potential for future Mac/Linux support). The user has sufficient permissions to read and write to the chosen Working Directory. The Mermaid.js CLI, bundled with the application, is capable of rendering all required diagram types. 3. Specific Requirements 3.1 System Environment 
#### 3.1.1
The tool shall operate entirely offline on an air-gapped workstation.
3.1.2 All third-party libraries and dependencies, including the Python runtime and Node.js for Mermaid, shall be bundled within the single executable installer.
3.1.3 Upon launch, the tool shall prompt the user to select a Working Directory. The tool shall not operate without a valid Working Directory. 
3.1.4 Once a Working Directory is established, the tool shall create or modify files only within that directory's scope. Permitted artifacts are: - stpa.db: The SQLite project database. - config.json: The project configuration and UI state file. - diagrams/: A sub-folder for storing generated diagram source files and images. 

### 3.2 Data Storage and Integrity

### 3.2.1 Database Engine

3.2.1.1 The system shall use an SQLite 3 database as its data storage engine.
3.2.1.2 The database shall be configured to operate in Write-Ahead Logging (WAL) mode.
3.2.1.3 The database shall be stored as a single file named stpa.db in the root of the Working Directory.

### 3.2.2 Database Schema
3.2.2.1 The database schema shall implement the entities and relationships defined in the Entity-Relationship Diagram (see Appendix A).
3.2.2.2 Every table representing a user-editable entity shall include columns for: - A unique primary key. - A Baseline text field. - A set of Critical Attributes as defined in section 3.3. 3.2.2.3 The Requirement entity shall support a recursive, self-referencing many-to-many relationship to model parent-child requirement traceability. 
3.2.2.4 All text-based fields intended for short descriptions or names shall have a maximum storage size of 256 bytes and use UTF-8 encoding. Longer text fields, such as requirement text, shall support larger inputs. 
3.2.2.5 All text fields shall store plain text only for the MVP. 3.2.3 Baselining
3.2.3.1 The system shall provide a "Create Baseline" function accessible from the main menu. 3.2.3.2 When executed, the "Create Baseline" function shall perform a transaction that clones every record in every data table. 3.2.3.3 For each cloned record, the Baseline field shall be set to the ISO 8601 date of the operation (e.g., "2025-06-14"). 
3.2.3.4 For each cloned record, an editable flag shall be set to false. 
3.2.3.5 The user shall only be permitted to create or edit records where the Baseline field is equal to "Working". All other baseline records are strictly read-only. 
3.2.4 Audit Trail 
3.2.4.1 The database shall include an audit table to log all data manipulation events (INSERT, UPDATE, DELETE). 3.2.4.2 Database triggers shall be implemented to automatically populate the audit table upon any DML event on any data table. 
3.2.4.3 Each audit log entry shall contain: a unique ID, a timestamp, the operation type, the target table name, the target row ID, a SHA-256 hash of the new row data, and the SHA-256 hash of the previous audit log entry for that table (hash-chaining). 
3.2.4.4 The tool shall include a command-line interface (CLI) verification function (e.g., stpa_tool.exe --verify) that re-computes the entire audit hash chain and reports success or the location of the first integrity failure. 

### 3.3 Data Model Entities and Attributes
Every entity in the data model shall possess the following set of "Critical Attributes" in addition to its own specific attributes. 3.3.1 Common Critical Attributes Criticality: A multi-choice field from ("Non-Critical", "Mission Critical", "Safety Critical", "Flight Critical", "Security Critical", "Privacy Critical"). Default: "Non-Critical". Confidentiality: Boolean (checkbox). Confidentiality Rationale: Text (256 bytes). Integrity: Boolean (checkbox). Integrity Rationale: Text (256 bytes). Availability: Boolean (checkbox). Availability Rationale: Text (256 bytes). Authenticity: Boolean (checkbox). Authenticity Rationale: Text (256 bytes). Non-Repudiation: Boolean (checkbox). Non-Repudiation Rationale: Text (256 bytes). Assurance: Boolean (checkbox). Assurance Rationale: Text (256 bytes). Trustworthy: Boolean (checkbox). Trustworthy Rationale: Text (256 bytes). Private: Boolean (checkbox). Private Rationale: Text (256 bytes). 

### 3.4 User Interface (UI)
3.4.1 Main Window Layout 
3.4.1.1 The main application window shall be divided into a left pane and a right pane by a movable vertical splitter. 
3.4.1.2 The left pane shall contain a hierarchical tree view displaying all System and System Element entities. 
3.4.1.3 The right pane shall be a tabbed widget for displaying details of the selected SoI. 
3.4.1.4 A non-scrollable header area shall be anchored at the top of the right pane, permanently displaying a breadcrumb trail of the currently selected SoI (e.g.,   System A › Subsystem B). 3.4.1.5 A status bar shall be present at the bottom of the window, displaying the current baseline state ("Working" or date), the last save time, and the full path to the stpa.db file. 3.4.2 Navigation and Workflow 
3.4.2.1 Selecting a node in the left-hand hierarchy tree shall set the System of Interest (SoI) for the entire UI. 
3.4.2.2 Upon selecting an SoI, the right-hand tabbed pane shall populate with tabs relevant to that SoI, including "Overview", "Functions", "Interfaces", "States", "Warnings", and "Audit". 
3.4.2.3 Within a component tab (e.g., "Functions"), the UI shall display a table listing all components associated with the current SoI. 
3.4.2.4 Selecting a row in a component table shall open a detailed editor view for that specific component. 
3.4.2.5 To link entities (e.g., a Hazard to an Asset), the editor view shall provide a multi-select list box displaying all available linkable entities within the current SoI. 

### 3.4.3 Warnings Tab
3.4.3.1 The "Warnings" tab shall display a table of all data model validation violations for the current SoI. 
 3.4.3.2 Each row in the warnings table shall describe a single violation. 
3.4.3.3 Double-clicking a row in the warnings table shall navigate the UI to the editor view of the offending entity. 
3.4.3.4 The validation engine shall be extendable and, for the MVP, will check for the following rules: - Completeness -Default will be non-critical. Selection of any other criticality in addition to non-critical will result in a warning. - Completeness - Unmapped Control Structure: A warning shall be generated if a Control Structure is defined but its Controller or Controlled Process attributes have not been mapped to a Function or System Element. - Logic - Circular Requirement: A warning shall be generated if a Requirement is detected as its own ancestor in the parent-child hierarchy. - Logic - Invalid Requirement Parent: A warning shall be generated if a Requirement is parented by another Requirement at a lower level of abstraction (e.g., L4 requirement parented by an L5 requirement). 

### 3.4.4 Performance and Scalability
3.4.4.1 The UI shall remain responsive and usable with a total database record count of at least 100,000 entities. 
3.4.4.2 Thumbnail galleries shall use a lazy-loading strategy. If the number of diagrams for an entity is greater than 200, thumbnails shall only be rendered when they are scrolled into view. 3.5 Diagramming 3.5.1 The tool shall automatically generate diagrams for Control Structures, State Diagrams, and any other defined entity relationships. 

3.5.2 Diagram source code shall be generated in Mermaid.js syntax and stored as .mmd files in the diagrams/ sub-folder. 
3.5.3 The bundled, offline @mermaid-js/mermaid-cli shall be invoked out-of-process to render .mmd files into both .svg and .png formats. 
3.5.4 The UI shall display the rendered .svg file in a zoomable and pannable viewer widget (e.g., QSvgWidget). JavaScript execution within the viewer is forbidden. 
3.5.5 Upon baselining, the current .mmd source file for each diagram shall be cloned and frozen (e.g., renamed with a date stamp) to preserve the diagram's state at that baseline. 

## 3.6 Import / Export and Collaboration
3.6.1 Export 3.6.1.1 The system shall provide an "Export Working Directory..." function under the "File" menu. 
3.6.1.2 This function shall create a single ZIP archive containing the complete contents of the Working Directory, including the stpa.db database, config.json, and the diagrams/ folder. 
3.6.2 Branch and Merge Utility 3.6.2.1 The tool shall include a utility, accessible via the main menu, for managing project branches to facilitate manual collaboration. 
3.6.2.2 The "Split Branch" utility shall allow a user to select a System node in the hierarchy. It will then: a. Create a new Working Directory. b. Copy the main config.json file to the new directory. c. Create a new stpa.db file in the new directory containing only the selected system and all of its descendants and associated entities. 
3.6.2.3 The "Merge Branch" utility shall allow a user to select a ZIP export or Working Directory of a previously split branch. 
3.6.2.4 The merge utility shall analyze the branch data for conflicts with the main project. A conflict is defined as an entity in the branch having the same Hierarchical ID as an entity in the main project. 
3.6.2.5 If conflicts are detected, the utility shall display a modal dialog prompting the user to resolve the conflict by choosing to Overwrite the existing data in the main project, Reject the import of the conflicting branch data, or Cancel the entire merge operation. 
3.6.2.6 If no conflicts exist, or once all conflicts are resolved, the utility shall import the branch data into the main project's database. 

### 3.6.3 External Tool Integration
3.6.3.1 The system shall be capable of exporting its data in a standardized, machine-readable format (ReqIF or JSON) to facilitate integration with external tools like DOORS or Cameo. 
3.6.3.2 The development of specific import/export scripts for these external tools is out of scope for this project. 
## 3.7 Packaging and Deployment 
3.7.1 The tool shall be packaged as a single executable file (stpa_tool.exe) using PyInstaller. 
3.7.2 The "About" dialog box shall display the software's semantic version, the Git commit hash of the build, and the SHA-256 hash of the executable file itself. 
# 4. Post-MVP / Future Enhancements
The following items have been identified as valuable but are explicitly out of scope for the Minimum Viable Product. They may be considered for future releases. Enhanced UI: Global search functionality; column-based filtering and sorting in all tables. Advanced Baselining: UI for viewing past baselines; a "diff" tool to compare baselines; the ability to "fork" a new working copy from an old baseline. Advanced Diagramming: A drag-and-drop graphical editor for adjusting and saving node positions in diagrams. Multi-User Concurrency: A built-in sync server or support for a shared network database (e.g., PostgreSQL) to enable real-time, concurrent multi-user editing. User Roles and Permissions: An administrative layer for managing user roles (e.g., Analyst, Reviewer) and access permissions. Encryption at Rest: Full-disk or database-level encryption (e.g., SQLCipher) to protect project data. 

# Appendix A: Entity-Relationship Diagram
erDiagram System ||--o{ System : "has child (recursive)" System ||--o{ Function : has_function System ||--o{ Interface : has_interface System ||--o{ Asset : has_asset System ||--o{ Constraint : has_constraint System ||--o{ Requirement : has_requirement System ||--o{ StateDiagram : has System ||--o{ ControlStructure : has System ||--o{ Environment : has ControlledProcess ||--o{ System : is_controlled_by ControlStructure ||--o{ ControlAction : includes ControlStructure ||--o{ Feedback : includes ControlStructure ||--o| Controller : includes ControlStructure ||--o{ ControlledProcess : includes ControlStructure ||--o| ProcessModel : includes ControlStructure ||--o| ControlAlgorithm : includes Controller ||--|| Function : is_a ControlAlgorithm ||--|| Function : is_a ControlAlgorithm ||--|| Interface : is_a ControlAlgorithm ||--|{ ControlAction : generates ProcessModel ||--|| Function : is_a ProcessModel ||--|{ Feedback : processes StateDiagram ||--o{ State : has StateDiagram ||--o{ InTransition : has StateDiagram ||--o{ OutTransition : has State ||--o{ Hazard : may_be State ||--o{ InTransition : has State ||--o{ OutTransition : has Feedback ||--o| InTransition : causes Feedback ||--o| OutTransition: causes ControlAction ||--o| InTransition : causes ControlAction ||--o| OutTransition : causes Requirement ||--o{ SafetySecurityControl : satisfies Requirement ||--o{ Requirement : "has child (recursive)" Controller ||--o{ ControlAction : issues ControlledProcess ||--o{ Feedback : issues Asset ||--o{ Loss : has_loss Hazard ||--o{ SafetySecurityControl : mitigated_by Hazard ||--o{ Asset : impairs Loss ||--o{ SafetySecurityControl : mitigated_by Constraint ||--o{ Requirement : is_a