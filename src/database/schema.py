"""
Database schema definition for STPA Tool
Defines all table structures, relationships, and constraints.
"""

from typing import List, Dict, Any

# Database schema version
SCHEMA_VERSION = "1.0.0"

# Common field definitions
COMMON_FIELDS = {
    'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
    'type_identifier': 'TEXT NOT NULL',
    'level_identifier': 'INTEGER NOT NULL',
    'sequential_identifier': 'INTEGER NOT NULL',
    'system_hierarchy': 'TEXT NOT NULL',
    'baseline': 'TEXT NOT NULL DEFAULT "Working"',
    'created_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
    'updated_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
}

# Critical attributes fields (applied to applicable entities)
CRITICAL_ATTRIBUTES = {
    'criticality': 'TEXT NOT NULL DEFAULT "Non-Critical" CHECK (criticality IN ("Non-Critical", "Mission Critical", "Safety Critical", "Flight Critical", "Security Critical", "Privacy Critical"))',
    'confidentiality': 'BOOLEAN NOT NULL DEFAULT 0',
    'confidentiality_description': 'TEXT',
    'integrity': 'BOOLEAN NOT NULL DEFAULT 0', 
    'integrity_description': 'TEXT',
    'availability': 'BOOLEAN NOT NULL DEFAULT 0',
    'availability_description': 'TEXT',
    'authenticity': 'BOOLEAN NOT NULL DEFAULT 0',
    'authenticity_description': 'TEXT',
    'non_repudiation': 'BOOLEAN NOT NULL DEFAULT 0',
    'non_repudiation_description': 'TEXT',
    'assurance': 'BOOLEAN NOT NULL DEFAULT 0',
    'assurance_description': 'TEXT',
    'trustworthy': 'BOOLEAN NOT NULL DEFAULT 0',
    'trustworthy_description': 'TEXT',
    'privacy': 'BOOLEAN NOT NULL DEFAULT 0',
    'privacy_description': 'TEXT'
}

# Table definitions
TABLES = {
    # Database metadata
    'db_version': {
        'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
        'version': 'TEXT NOT NULL',
        'applied_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
        'description': 'TEXT'
    },
    
    # Core entities
    'systems': {
        **COMMON_FIELDS,
        'system_name': 'TEXT NOT NULL',
        'system_description': 'TEXT',
        'parent_system_id': 'INTEGER REFERENCES systems(id)',
        **CRITICAL_ATTRIBUTES
    },
    
    'functions': {
        **COMMON_FIELDS,
        'system_id': 'INTEGER NOT NULL REFERENCES systems(id)',
        'short_text_identifier': 'TEXT',
        'function_name': 'TEXT NOT NULL',
        'function_description': 'TEXT',
        **CRITICAL_ATTRIBUTES
    },
    
    'interfaces': {
        **COMMON_FIELDS,
        'system_id': 'INTEGER NOT NULL REFERENCES systems(id)',
        'interface_name': 'TEXT NOT NULL',
        'interface_description': 'TEXT',
        **CRITICAL_ATTRIBUTES
    },
    
    'assets': {
        **COMMON_FIELDS,
        'system_id': 'INTEGER NOT NULL REFERENCES systems(id)',
        'asset_name': 'TEXT NOT NULL',
        'asset_description': 'TEXT',
        **CRITICAL_ATTRIBUTES
    },
    
    'constraints': {
        **COMMON_FIELDS,
        'system_id': 'INTEGER NOT NULL REFERENCES systems(id)',
        'constraint_name': 'TEXT NOT NULL',
        'constraint_description': 'TEXT'
    },
    
    'requirements': {
        **COMMON_FIELDS,
        'system_id': 'INTEGER NOT NULL REFERENCES systems(id)',
        'parent_requirement_id': 'INTEGER REFERENCES requirements(id)',
        'alphanumeric_identifier': 'TEXT',
        'short_text_identifier': 'TEXT',
        'requirement_text': 'TEXT NOT NULL',
        'verification_method': 'TEXT CHECK (verification_method IN ("Inspection", "Analysis", "Demonstration", "Test"))',
        'verification_statement': 'TEXT',
        'imperative': 'TEXT CHECK (imperative IN ("Shall", "Should", "May", "Will"))',
        'actor': 'TEXT',
        'action': 'TEXT',
        **CRITICAL_ATTRIBUTES
    },
    
    'environments': {
        **COMMON_FIELDS,
        'system_id': 'INTEGER NOT NULL REFERENCES systems(id)',
        'environment_name': 'TEXT NOT NULL',
        'environment_description': 'TEXT',
        'operational_context': 'TEXT',
        'environmental_conditions': 'TEXT'
    },
    
    'hazards': {
        **COMMON_FIELDS,
        'environment_id': 'INTEGER REFERENCES environments(id)',
        'h_name': 'TEXT NOT NULL',
        'h_description': 'TEXT',
        **CRITICAL_ATTRIBUTES
    },
    
    'losses': {
        **COMMON_FIELDS,
        'asset_id': 'INTEGER NOT NULL REFERENCES assets(id)',
        'l_name': 'TEXT NOT NULL',
        'l_description': 'TEXT',
        'loss_description': 'TEXT'
    },
    
    # Control structure entities
    'control_structures': {
        **COMMON_FIELDS,
        'system_id': 'INTEGER NOT NULL REFERENCES systems(id)',
        'structure_name': 'TEXT NOT NULL',
        'structure_description': 'TEXT',
        'diagram_url': 'TEXT',
        **CRITICAL_ATTRIBUTES
    },
    
    'controllers': {
        **COMMON_FIELDS,
        'system_id': 'INTEGER NOT NULL REFERENCES systems(id)',
        'short_text_identifier': 'TEXT',
        'controller_name': 'TEXT NOT NULL',
        'controller_description': 'TEXT'
    },
    
    'control_algorithms': {
        **COMMON_FIELDS,
        'function_id': 'INTEGER REFERENCES functions(id)',
        'interface_id': 'INTEGER REFERENCES interfaces(id)',
        'short_text_identifier': 'TEXT',
        'control_algo_name': 'TEXT NOT NULL',
        'control_algo_description': 'TEXT'
    },
    
    'process_models': {
        **COMMON_FIELDS,
        'function_id': 'INTEGER NOT NULL REFERENCES functions(id)',
        'short_text_identifier': 'TEXT',
        'pm_name': 'TEXT NOT NULL',
        'pm_description': 'TEXT'
    },
    
    'controlled_processes': {
        **COMMON_FIELDS,
        'system_id': 'INTEGER REFERENCES systems(id)',
        'function_id': 'INTEGER REFERENCES functions(id)',
        'short_text_identifier': 'TEXT',
        'cp_name': 'TEXT NOT NULL',
        'cp_description': 'TEXT'
    },
    
    'control_actions': {
        **COMMON_FIELDS,
        'control_algorithm_id': 'INTEGER REFERENCES control_algorithms(id)',
        'ca_name': 'TEXT NOT NULL',
        'ca_description': 'TEXT',
        'unsafe': 'BOOLEAN NOT NULL DEFAULT 0',
        'unsecure': 'BOOLEAN NOT NULL DEFAULT 0',
        **CRITICAL_ATTRIBUTES
    },
    
    'feedback': {
        **COMMON_FIELDS,
        'controlled_process_id': 'INTEGER REFERENCES controlled_processes(id)',
        'process_model_id': 'INTEGER REFERENCES process_models(id)',
        'fb_name': 'TEXT NOT NULL',
        'fb_description': 'TEXT',
        'description': 'TEXT',
        **CRITICAL_ATTRIBUTES
    },
    
    # State management
    'state_diagrams': {
        **COMMON_FIELDS,
        'system_id': 'INTEGER NOT NULL REFERENCES systems(id)',
        'sd_name': 'TEXT NOT NULL',
        'sd_description': 'TEXT',
        'diagram_url': 'TEXT'
    },
    
    'states': {
        **COMMON_FIELDS,
        'state_diagram_id': 'INTEGER NOT NULL REFERENCES state_diagrams(id)',
        'short_text_identifier': 'TEXT',
        'state_description': 'TEXT',
        **CRITICAL_ATTRIBUTES
    },
    
    'in_transitions': {
        **COMMON_FIELDS,
        'state_id': 'INTEGER NOT NULL REFERENCES states(id)',
        'control_action_id': 'INTEGER REFERENCES control_actions(id)',
        'feedback_id': 'INTEGER REFERENCES feedback(id)',
        'in_transition_name': 'TEXT NOT NULL',
        'in_transition_description': 'TEXT',
        'in_transition_description_detail': 'TEXT'
    },
    
    'out_transitions': {
        **COMMON_FIELDS,
        'state_id': 'INTEGER NOT NULL REFERENCES states(id)',
        'control_action_id': 'INTEGER REFERENCES control_actions(id)',
        'feedback_id': 'INTEGER REFERENCES feedback(id)',
        'out_transition_name': 'TEXT NOT NULL',
        'out_transition_description': 'TEXT',
        'out_transition_description_detail': 'TEXT'
    },
    
    # Safety and security controls
    'safety_security_controls': {
        **COMMON_FIELDS,
        'sc_name': 'TEXT NOT NULL',
        'sc_description': 'TEXT',
        'description': 'TEXT',
        **CRITICAL_ATTRIBUTES
    },
    
    # Audit trail
    'audit_log': {
        'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
        'timestamp': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
        'operation': 'TEXT NOT NULL CHECK (operation IN ("INSERT", "UPDATE", "DELETE"))',
        'table_name': 'TEXT NOT NULL',
        'row_id': 'INTEGER NOT NULL',
        'row_data_hash': 'TEXT NOT NULL',
        'previous_hash': 'TEXT',
        'user_context': 'TEXT'
    }
}

# Relationship tables for many-to-many relationships
RELATIONSHIP_TABLES = {
    # Control structure relationships
    'control_structure_control_actions': {
        'control_structure_id': 'INTEGER NOT NULL REFERENCES control_structures(id)',
        'control_action_id': 'INTEGER NOT NULL REFERENCES control_actions(id)',
        'PRIMARY KEY': '(control_structure_id, control_action_id)'
    },
    
    'control_structure_feedback': {
        'control_structure_id': 'INTEGER NOT NULL REFERENCES control_structures(id)',
        'feedback_id': 'INTEGER NOT NULL REFERENCES feedback(id)',
        'PRIMARY KEY': '(control_structure_id, feedback_id)'
    },
    
    'control_structure_controllers': {
        'control_structure_id': 'INTEGER NOT NULL REFERENCES control_structures(id)',
        'controller_id': 'INTEGER NOT NULL REFERENCES controllers(id)',
        'PRIMARY KEY': '(control_structure_id, controller_id)'
    },
    
    'control_structure_controlled_processes': {
        'control_structure_id': 'INTEGER NOT NULL REFERENCES control_structures(id)',
        'controlled_process_id': 'INTEGER NOT NULL REFERENCES controlled_processes(id)',
        'PRIMARY KEY': '(control_structure_id, controlled_process_id)'
    },
    
    'control_structure_process_models': {
        'control_structure_id': 'INTEGER NOT NULL REFERENCES control_structures(id)',
        'process_model_id': 'INTEGER NOT NULL REFERENCES process_models(id)',
        'PRIMARY KEY': '(control_structure_id, process_model_id)'
    },
    
    'control_structure_control_algorithms': {
        'control_structure_id': 'INTEGER NOT NULL REFERENCES control_structures(id)',
        'control_algorithm_id': 'INTEGER NOT NULL REFERENCES control_algorithms(id)',
        'PRIMARY KEY': '(control_structure_id, control_algorithm_id)'
    },
    
    # Safety and security control relationships
    'requirement_safety_controls': {
        'requirement_id': 'INTEGER NOT NULL REFERENCES requirements(id)',
        'safety_security_control_id': 'INTEGER NOT NULL REFERENCES safety_security_controls(id)',
        'PRIMARY KEY': '(requirement_id, safety_security_control_id)'
    },
    
    'hazard_safety_controls': {
        'hazard_id': 'INTEGER NOT NULL REFERENCES hazards(id)',
        'safety_security_control_id': 'INTEGER NOT NULL REFERENCES safety_security_controls(id)',
        'PRIMARY KEY': '(hazard_id, safety_security_control_id)'
    },
    
    'loss_safety_controls': {
        'loss_id': 'INTEGER NOT NULL REFERENCES losses(id)',
        'safety_security_control_id': 'INTEGER NOT NULL REFERENCES safety_security_controls(id)',
        'PRIMARY KEY': '(loss_id, safety_security_control_id)'
    },
    
    # Hazard relationships
    'hazard_assets': {
        'hazard_id': 'INTEGER NOT NULL REFERENCES hazards(id)',
        'asset_id': 'INTEGER NOT NULL REFERENCES assets(id)',
        'PRIMARY KEY': '(hazard_id, asset_id)'
    },
    
    'state_hazards': {
        'state_id': 'INTEGER NOT NULL REFERENCES states(id)',
        'hazard_id': 'INTEGER NOT NULL REFERENCES hazards(id)',
        'PRIMARY KEY': '(state_id, hazard_id)'
    },
    
    # Environment interface access
    'environment_interfaces': {
        'environment_id': 'INTEGER NOT NULL REFERENCES environments(id)',
        'interface_id': 'INTEGER NOT NULL REFERENCES interfaces(id)',
        'PRIMARY KEY': '(environment_id, interface_id)'
    }
}

# Indexes for performance optimization
INDEXES = {
    # Hierarchical queries
    'idx_systems_parent': 'CREATE INDEX idx_systems_parent ON systems(parent_system_id)',
    'idx_systems_hierarchy': 'CREATE INDEX idx_systems_hierarchy ON systems(system_hierarchy)',
    'idx_requirements_parent': 'CREATE INDEX idx_requirements_parent ON requirements(parent_requirement_id)',
    
    # Foreign key indexes
    'idx_functions_system': 'CREATE INDEX idx_functions_system ON functions(system_id)',
    'idx_interfaces_system': 'CREATE INDEX idx_interfaces_system ON interfaces(system_id)',
    'idx_assets_system': 'CREATE INDEX idx_assets_system ON assets(system_id)',
    'idx_requirements_system': 'CREATE INDEX idx_requirements_system ON requirements(system_id)',
    
    # Baseline queries
    'idx_systems_baseline': 'CREATE INDEX idx_systems_baseline ON systems(baseline)',
    'idx_functions_baseline': 'CREATE INDEX idx_functions_baseline ON functions(baseline)',
    'idx_requirements_baseline': 'CREATE INDEX idx_requirements_baseline ON requirements(baseline)',
    
    # Audit log
    'idx_audit_table_row': 'CREATE INDEX idx_audit_table_row ON audit_log(table_name, row_id)',
    'idx_audit_timestamp': 'CREATE INDEX idx_audit_timestamp ON audit_log(timestamp)',
    
    # Identifiers
    'idx_systems_identifiers': 'CREATE INDEX idx_systems_identifiers ON systems(type_identifier, level_identifier, sequential_identifier)',
    'idx_functions_identifiers': 'CREATE INDEX idx_functions_identifiers ON functions(type_identifier, level_identifier, sequential_identifier)'
}

# Database constraints
CONSTRAINTS = {
    # Ensure hierarchical IDs are unique within baseline
    'unique_system_hierarchy': 'CREATE UNIQUE INDEX unique_system_hierarchy ON systems(system_hierarchy, baseline)',
    'unique_function_hierarchy': 'CREATE UNIQUE INDEX unique_function_hierarchy ON functions(system_hierarchy, baseline)',
    'unique_requirement_hierarchy': 'CREATE UNIQUE INDEX unique_requirement_hierarchy ON requirements(system_hierarchy, baseline)',
    
    # Prevent circular requirements
    'check_requirement_not_self_parent': 'CHECK (id != parent_requirement_id)',
}

def get_create_table_sql(table_name: str, fields: Dict[str, str]) -> str:
    """
    Generate CREATE TABLE SQL statement.
    
    Args:
        table_name: Name of the table
        fields: Dictionary of field definitions
        
    Returns:
        SQL CREATE TABLE statement
    """
    field_definitions = []
    constraints = []
    
    for field_name, field_def in fields.items():
        if field_name == 'PRIMARY KEY':
            constraints.append(f"PRIMARY KEY {field_def}")
        else:
            field_definitions.append(f"{field_name} {field_def}")
    
    all_definitions = field_definitions + constraints
    
    return f"""
CREATE TABLE {table_name} (
    {',\n    '.join(all_definitions)}
);
"""

def get_full_schema_sql() -> str:
    """
    Generate complete database schema SQL.
    
    Returns:
        Complete SQL for creating the database schema
    """
    sql_parts = [
        "-- STPA Tool Database Schema",
        f"-- Version: {SCHEMA_VERSION}",
        f"-- Generated: CURRENT_TIMESTAMP",
        "",
        "PRAGMA foreign_keys = ON;",
        "PRAGMA journal_mode = WAL;",
        ""
    ]
    
    # Create main tables
    sql_parts.append("-- Main Tables")
    for table_name, fields in TABLES.items():
        sql_parts.append(get_create_table_sql(table_name, fields))
    
    # Create relationship tables
    sql_parts.append("-- Relationship Tables")
    for table_name, fields in RELATIONSHIP_TABLES.items():
        sql_parts.append(get_create_table_sql(table_name, fields))
    
    # Create indexes
    sql_parts.append("-- Indexes")
    for index_name, index_sql in INDEXES.items():
        sql_parts.append(f"{index_sql};")
        sql_parts.append("")
    
    # Insert initial version record
    sql_parts.append("-- Initial Data")
    sql_parts.append(f"""
INSERT INTO db_version (version, description) 
VALUES ('{SCHEMA_VERSION}', 'Initial database schema');
""")
    
    return "\n".join(sql_parts)