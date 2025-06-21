"""
JSON export functionality for STPA Tool
Exports System of Interest data and associated entities to JSON format.
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..database.entities import (
    System, Function, Interface, Asset, Constraint, Requirement,
    Environment, Hazard, Loss, ControlStructure, Controller, 
    ControlledProcess, ControlAction, Feedback, StateDiagram,
    State, SafetySecurityControl, EntityRepository
)
from ..database.connection import DatabaseConnection
from ..log_config.config import get_logger

logger = get_logger(__name__)


class JsonExporter:
    """Handles JSON export of STPA Tool data."""
    
    def __init__(self, db_connection: DatabaseConnection):
        self.db_connection = db_connection
        # Create repositories for all entity types
        self.repositories = {
            'System': EntityRepository(db_connection, System),
            'Function': EntityRepository(db_connection, Function),
            'Interface': EntityRepository(db_connection, Interface),
            'Asset': EntityRepository(db_connection, Asset),
            'Constraint': EntityRepository(db_connection, Constraint),
            'Requirement': EntityRepository(db_connection, Requirement),
            'Environment': EntityRepository(db_connection, Environment),
            'Hazard': EntityRepository(db_connection, Hazard),
            'Loss': EntityRepository(db_connection, Loss),
            'ControlStructure': EntityRepository(db_connection, ControlStructure),
            'Controller': EntityRepository(db_connection, Controller),
            'ControlledProcess': EntityRepository(db_connection, ControlledProcess),
            'ControlAction': EntityRepository(db_connection, ControlAction),
            'Feedback': EntityRepository(db_connection, Feedback),
            'StateDiagram': EntityRepository(db_connection, StateDiagram),
            'State': EntityRepository(db_connection, State),
            'SafetySecurityControl': EntityRepository(db_connection, SafetySecurityControl)
        }
    
    def export_system_of_interest(self, system_id: int, include_children: bool = True) -> Optional[Dict[str, Any]]:
        """
        Export a System of Interest and all associated entities to JSON format.
        
        Args:
            system_id: The ID of the system to export
            include_children: Whether to include child systems (but not their descendants)
        
        Returns:
            Dictionary containing the exported data
        """
        logger.info(f"Starting JSON export for system ID {system_id}")
        
        try:
            # Get the main system
            system = self.repositories['System'].get_by_id(system_id)
            if not system:
                logger.warning(f"System with ID {system_id} not found")
                return None
            
            export_data = {
                "export_metadata": {
                    "export_timestamp": datetime.now().isoformat(),
                    "export_type": "System of Interest",
                    "stpa_tool_version": "1.0.0",
                    "system_id": system_id,
                    "system_name": system.system_name,
                    "include_children": include_children
                },
                "system": system.to_dict(),
                "functions": [],
                "interfaces": [],
                "assets": [],
                "constraints": [],
                "requirements": [],
                "environments": [],
                "hazards": [],
                "losses": [],
                "control_structures": [],
                "controllers": [],
                "controlled_processes": [],
                "control_actions": [],
                "feedback": [],
                "state_diagrams": [],
                "states": [],
                "safety_security_controls": []
            }
            
            # Export associated entities
            self._export_associated_entities(system, export_data)
            
            # Export child systems if requested
            if include_children:
                child_systems = self._get_child_systems(system_id)
                export_data["child_systems"] = [child.to_dict() for child in child_systems]
                
                # Export entities for each child system
                for child_system in child_systems:
                    self._export_associated_entities(child_system, export_data)
            
            logger.info(f"JSON export completed successfully for system ID {system_id}")
            return export_data
            
        except Exception as e:
            logger.error(f"Error during JSON export: {str(e)}")
            raise
    
    def _export_associated_entities(self, system: System, export_data: Dict[str, Any]):
        """Export all entities associated with a given system."""
        system_id = system.id
        
        # Functions
        functions = self.repositories['Function'].find_by_system_id(system_id)
        export_data["functions"].extend([func.to_dict() for func in functions])
        
        # Interfaces
        interfaces = self.repositories['Interface'].find_by_system_id(system_id)
        export_data["interfaces"].extend([intf.to_dict() for intf in interfaces])
        
        # Assets
        assets = self.repositories['Asset'].find_by_system_id(system_id)
        export_data["assets"].extend([asset.to_dict() for asset in assets])
        
        # Constraints
        constraints = self.repositories['Constraint'].find_by_system_id(system_id)
        export_data["constraints"].extend([const.to_dict() for const in constraints])
        
        # Requirements
        requirements = self.repositories['Requirement'].find_by_system_id(system_id)
        export_data["requirements"].extend([req.to_dict() for req in requirements])
        
        # Environments
        environments = self.repositories['Environment'].find_by_system_id(system_id)
        export_data["environments"].extend([env.to_dict() for env in environments])
        
        # Hazards (linked through environment)
        hazards = self.repositories['Hazard'].find_by_system_hierarchy(system.system_hierarchy)
        export_data["hazards"].extend([hazard.to_dict() for hazard in hazards])
        
        # Losses (linked through assets)
        losses = self.repositories['Loss'].find_by_system_hierarchy(system.system_hierarchy)
        export_data["losses"].extend([loss.to_dict() for loss in losses])
        
        # Control Structures
        control_structures = self.repositories['ControlStructure'].find_by_system_id(system_id)
        export_data["control_structures"].extend([cs.to_dict() for cs in control_structures])
        
        # Controllers
        controllers = self.repositories['Controller'].find_by_system_id(system_id)
        export_data["controllers"].extend([ctrl.to_dict() for ctrl in controllers])
        
        # Controlled Processes
        controlled_processes = self.repositories['ControlledProcess'].find_by_system_id(system_id)
        export_data["controlled_processes"].extend([cp.to_dict() for cp in controlled_processes])
        
        # Control Actions (linked through control structure)
        control_actions = self.repositories['ControlAction'].find_by_system_hierarchy(system.system_hierarchy)
        export_data["control_actions"].extend([ca.to_dict() for ca in control_actions])
        
        # Feedback (linked through control structure)
        feedback = self.repositories['Feedback'].find_by_system_hierarchy(system.system_hierarchy)
        export_data["feedback"].extend([fb.to_dict() for fb in feedback])
        
        # State Diagrams
        state_diagrams = self.repositories['StateDiagram'].find_by_system_id(system_id)
        export_data["state_diagrams"].extend([sd.to_dict() for sd in state_diagrams])
        
        # States (linked through state diagrams)
        states = self.repositories['State'].find_by_system_hierarchy(system.system_hierarchy)
        export_data["states"].extend([state.to_dict() for state in states])
        
        # Safety Security Controls (linked through requirements/hazards)
        safety_controls = self.repositories['SafetySecurityControl'].find_by_system_hierarchy(system.system_hierarchy)
        export_data["safety_security_controls"].extend([sc.to_dict() for sc in safety_controls])
    
    def _get_child_systems(self, parent_system_id: int) -> List[System]:
        """Get immediate child systems of a parent system."""
        try:
            # Use direct SQL query since we need to filter by parent_system_id
            # which is not covered by the existing repository methods
            with self.db_connection.get_cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM systems WHERE parent_system_id = ? AND baseline = 'Working'",
                    (parent_system_id,)
                )
                
                child_systems = []
                for row in cursor.fetchall():
                    system = System()
                    # Populate system from database row using repository pattern
                    columns = [desc[0] for desc in cursor.description]
                    for i, column in enumerate(columns):
                        if hasattr(system, column):
                            setattr(system, column, row[i])
                    child_systems.append(system)
                
                return child_systems
        except Exception as e:
            logger.error(f"Error getting child systems for parent {parent_system_id}: {str(e)}")
            return []
    
    def export_to_file(self, system_id: int, file_path: str, include_children: bool = True, indent: int = 2) -> bool:
        """
        Export system data to JSON file.
        
        Args:
            system_id: The ID of the system to export
            file_path: Path where to save the JSON file
            include_children: Whether to include child systems
            indent: JSON indentation level
        
        Returns:
            True if export successful, False otherwise
        """
        try:
            export_data = self.export_system_of_interest(system_id, include_children)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=indent, ensure_ascii=False, default=str)
            
            logger.info(f"JSON export saved to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export to file {file_path}: {str(e)}")
            return False
    
    def validate_export_data(self, export_data: Dict[str, Any]) -> List[str]:
        """
        Validate the exported JSON data for completeness and consistency.
        
        Args:
            export_data: The exported data dictionary
        
        Returns:
            List of validation warnings/errors
        """
        warnings = []
        
        # Check required metadata
        if "export_metadata" not in export_data:
            warnings.append("Missing export metadata")
        
        # Check main system
        if "system" not in export_data or not export_data["system"]:
            warnings.append("Missing main system data")
        
        # Check for empty categories that might indicate issues
        entity_counts = {
            "functions": len(export_data.get("functions", [])),
            "interfaces": len(export_data.get("interfaces", [])),
            "assets": len(export_data.get("assets", [])),
            "requirements": len(export_data.get("requirements", []))
        }
        
        total_entities = sum(entity_counts.values())
        if total_entities == 0:
            warnings.append("No associated entities found - system may be empty")
        
        # Log entity counts
        logger.info(f"Export validation - Entity counts: {entity_counts}")
        
        return warnings