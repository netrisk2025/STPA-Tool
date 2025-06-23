"""
Entity classes for STPA Tool database
Provides base classes and CRUD operations for database entities.
"""

import hashlib
from datetime import datetime
from typing import Dict, Any, Optional, List, Type, Union
from dataclasses import dataclass, field, fields
from abc import ABC, abstractmethod

from ..config.constants import (
    WORKING_BASELINE, CRITICALITY_NON_CRITICAL, 
    VERIFICATION_INSPECTION, IMPERATIVE_SHALL
)
from ..log_config.config import get_logger
from .connection import DatabaseConnection

logger = get_logger(__name__)


@dataclass
class BaseEntity(ABC):
    """
    Base class for all database entities.
    """
    id: Optional[int] = None
    type_identifier: str = ""
    level_identifier: int = 0
    sequential_identifier: int = 0
    system_hierarchy: str = ""
    baseline: str = WORKING_BASELINE
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @classmethod
    @abstractmethod
    def get_table_name(cls) -> str:
        """Get the database table name for this entity."""
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entity to dictionary."""
        result = {}
        for field_info in fields(self):
            value = getattr(self, field_info.name)
            if isinstance(value, datetime):
                result[field_info.name] = value.isoformat()
            else:
                result[field_info.name] = value
        return result
    
    def get_hierarchical_id(self) -> str:
        """
        Generate hierarchical ID string.
        
        Returns:
            Formatted hierarchical ID (e.g., "S-1.2.1")
        """
        # Use the auto-generated system_hierarchy if available
        if self.system_hierarchy:
            return self.system_hierarchy
        
        # Fallback to the old method if system_hierarchy is not set
        if self.level_identifier == 0:
            return f"{self.type_identifier}-{self.sequential_identifier}"
        else:
            return f"{self.type_identifier}-{self.level_identifier}.{self.sequential_identifier}"


@dataclass 
class CriticalAttributes:
    """Critical attributes mixin for entities that support them."""
    criticality: str = CRITICALITY_NON_CRITICAL
    confidentiality: bool = False
    confidentiality_description: str = ""
    integrity: bool = False
    integrity_description: str = ""
    availability: bool = False
    availability_description: str = ""
    authenticity: bool = False
    authenticity_description: str = ""
    non_repudiation: bool = False
    non_repudiation_description: str = ""
    assurance: bool = False
    assurance_description: str = ""
    trustworthy: bool = False
    trustworthy_description: str = ""
    privacy: bool = False
    privacy_description: str = ""


@dataclass
class System(BaseEntity):
    """System entity representing a system in the hierarchy."""
    system_name: str = ""
    system_description: str = ""
    parent_system_id: Optional[int] = None
    type_identifier: str = "S"
    
    # Critical attributes
    criticality: str = CRITICALITY_NON_CRITICAL
    confidentiality: bool = False
    confidentiality_description: str = ""
    integrity: bool = False
    integrity_description: str = ""
    availability: bool = False
    availability_description: str = ""
    authenticity: bool = False
    authenticity_description: str = ""
    non_repudiation: bool = False
    non_repudiation_description: str = ""
    assurance: bool = False
    assurance_description: str = ""
    trustworthy: bool = False
    trustworthy_description: str = ""
    privacy: bool = False
    privacy_description: str = ""
    
    @classmethod
    def get_table_name(cls) -> str:
        return "systems"


@dataclass
class Function(BaseEntity):
    """Function entity representing a system function."""
    system_id: int = 0
    short_text_identifier: str = ""
    function_name: str = ""
    function_description: str = ""
    type_identifier: str = "F"
    
    # Critical attributes  
    criticality: str = CRITICALITY_NON_CRITICAL
    confidentiality: bool = False
    confidentiality_description: str = ""
    integrity: bool = False
    integrity_description: str = ""
    availability: bool = False
    availability_description: str = ""
    authenticity: bool = False
    authenticity_description: str = ""
    non_repudiation: bool = False
    non_repudiation_description: str = ""
    assurance: bool = False
    assurance_description: str = ""
    trustworthy: bool = False
    trustworthy_description: str = ""
    privacy: bool = False
    privacy_description: str = ""
    
    @classmethod
    def get_table_name(cls) -> str:
        return "functions"


@dataclass
class Interface(BaseEntity):
    """Interface entity representing a system interface."""
    system_id: int = 0
    interface_name: str = ""
    interface_description: str = ""
    type_identifier: str = "I"
    
    # Critical attributes
    criticality: str = CRITICALITY_NON_CRITICAL
    confidentiality: bool = False
    confidentiality_description: str = ""
    integrity: bool = False
    integrity_description: str = ""
    availability: bool = False
    availability_description: str = ""
    authenticity: bool = False
    authenticity_description: str = ""
    non_repudiation: bool = False
    non_repudiation_description: str = ""
    assurance: bool = False
    assurance_description: str = ""
    trustworthy: bool = False
    trustworthy_description: str = ""
    privacy: bool = False
    privacy_description: str = ""
    
    @classmethod
    def get_table_name(cls) -> str:
        return "interfaces"


@dataclass
class Asset(BaseEntity):
    """Asset entity representing a system asset."""
    system_id: int = 0
    asset_name: str = ""
    asset_description: str = ""
    type_identifier: str = "A"
    
    # Critical attributes
    criticality: str = CRITICALITY_NON_CRITICAL
    confidentiality: bool = False
    confidentiality_description: str = ""
    integrity: bool = False
    integrity_description: str = ""
    availability: bool = False
    availability_description: str = ""
    authenticity: bool = False
    authenticity_description: str = ""
    non_repudiation: bool = False
    non_repudiation_description: str = ""
    assurance: bool = False
    assurance_description: str = ""
    trustworthy: bool = False
    trustworthy_description: str = ""
    privacy: bool = False
    privacy_description: str = ""
    
    @classmethod
    def get_table_name(cls) -> str:
        return "assets"


@dataclass
class Requirement(BaseEntity):
    """Requirement entity representing a system requirement."""
    system_id: int = 0
    parent_requirement_id: Optional[int] = None
    alphanumeric_identifier: str = ""
    short_text_identifier: str = ""
    requirement_text: str = ""
    verification_method: str = VERIFICATION_INSPECTION
    verification_statement: str = ""
    imperative: str = IMPERATIVE_SHALL
    actor: str = ""
    action: str = ""
    type_identifier: str = "R"
    
    # Critical attributes
    criticality: str = CRITICALITY_NON_CRITICAL
    confidentiality: bool = False
    confidentiality_description: str = ""
    integrity: bool = False
    integrity_description: str = ""
    availability: bool = False
    availability_description: str = ""
    authenticity: bool = False
    authenticity_description: str = ""
    non_repudiation: bool = False
    non_repudiation_description: str = ""
    assurance: bool = False
    assurance_description: str = ""
    trustworthy: bool = False
    trustworthy_description: str = ""
    privacy: bool = False
    privacy_description: str = ""
    
    @classmethod
    def get_table_name(cls) -> str:
        return "requirements"


@dataclass
class Hazard(BaseEntity):
    """Hazard entity representing a system hazard."""
    environment_id: Optional[int] = None
    h_name: str = ""
    h_description: str = ""
    type_identifier: str = "H"
    
    # Critical attributes
    criticality: str = CRITICALITY_NON_CRITICAL
    confidentiality: bool = False
    confidentiality_description: str = ""
    integrity: bool = False
    integrity_description: str = ""
    availability: bool = False
    availability_description: str = ""
    authenticity: bool = False
    authenticity_description: str = ""
    non_repudiation: bool = False
    non_repudiation_description: str = ""
    assurance: bool = False
    assurance_description: str = ""
    trustworthy: bool = False
    trustworthy_description: str = ""
    privacy: bool = False
    privacy_description: str = ""
    
    @classmethod
    def get_table_name(cls) -> str:
        return "hazards"
    
    @property
    def hazard_name(self) -> str:
        """Get hazard name (alias for h_name)."""
        return self.h_name
    
    @hazard_name.setter
    def hazard_name(self, value: str):
        """Set hazard name (alias for h_name)."""
        self.h_name = value
        
    @property
    def hazard_description(self) -> str:
        """Get hazard description (alias for h_description)."""
        return self.h_description
    
    @hazard_description.setter
    def hazard_description(self, value: str):
        """Set hazard description (alias for h_description)."""
        self.h_description = value


@dataclass
class Loss(BaseEntity):
    """Loss entity representing a system loss."""
    asset_id: int = 0
    l_name: str = ""
    l_description: str = ""
    loss_description: str = ""
    type_identifier: str = "L"
    
    @classmethod
    def get_table_name(cls) -> str:
        return "losses"
    
    @property
    def loss_name(self) -> str:
        """Get loss name (alias for l_name)."""
        return self.l_name
    
    @loss_name.setter
    def loss_name(self, value: str):
        """Set loss name (alias for l_name)."""
        self.l_name = value


@dataclass
class ControlStructure(BaseEntity):
    """Control Structure entity representing a control system structure."""
    system_id: int = 0
    structure_name: str = ""
    structure_description: str = ""
    diagram_url: str = ""
    type_identifier: str = "CS"
    
    # Critical attributes
    criticality: str = CRITICALITY_NON_CRITICAL
    confidentiality: bool = False
    confidentiality_description: str = ""
    integrity: bool = False
    integrity_description: str = ""
    availability: bool = False
    availability_description: str = ""
    authenticity: bool = False
    authenticity_description: str = ""
    non_repudiation: bool = False
    non_repudiation_description: str = ""
    assurance: bool = False
    assurance_description: str = ""
    trustworthy: bool = False
    trustworthy_description: str = ""
    privacy: bool = False
    privacy_description: str = ""
    
    @classmethod
    def get_table_name(cls) -> str:
        return "control_structures"


@dataclass
class Controller(BaseEntity):
    """Controller entity representing a control system controller."""
    system_id: int = 0
    short_text_identifier: str = ""
    controller_name: str = ""
    controller_description: str = ""
    type_identifier: str = "CT"
    
    @classmethod
    def get_table_name(cls) -> str:
        return "controllers"


@dataclass
class ControlledProcess(BaseEntity):
    """Controlled Process entity representing a controlled process."""
    system_id: Optional[int] = None
    function_id: Optional[int] = None
    short_text_identifier: str = ""
    cp_name: str = ""
    cp_description: str = ""
    type_identifier: str = "CP"
    
    @classmethod
    def get_table_name(cls) -> str:
        return "controlled_processes"


@dataclass
class ControlAction(BaseEntity):
    """Control Action entity representing a control action."""
    control_algorithm_id: Optional[int] = None
    ca_name: str = ""
    ca_description: str = ""
    unsafe: bool = False
    unsecure: bool = False
    type_identifier: str = "CA"
    
    # Critical attributes
    criticality: str = CRITICALITY_NON_CRITICAL
    confidentiality: bool = False
    confidentiality_description: str = ""
    integrity: bool = False
    integrity_description: str = ""
    availability: bool = False
    availability_description: str = ""
    authenticity: bool = False
    authenticity_description: str = ""
    non_repudiation: bool = False
    non_repudiation_description: str = ""
    assurance: bool = False
    assurance_description: str = ""
    trustworthy: bool = False
    trustworthy_description: str = ""
    privacy: bool = False
    privacy_description: str = ""
    
    @classmethod
    def get_table_name(cls) -> str:
        return "control_actions"


@dataclass
class Feedback(BaseEntity):
    """Feedback entity representing a feedback signal."""
    controlled_process_id: Optional[int] = None
    process_model_id: Optional[int] = None
    fb_name: str = ""
    fb_description: str = ""
    description: str = ""
    type_identifier: str = "FB"
    
    # Critical attributes
    criticality: str = CRITICALITY_NON_CRITICAL
    confidentiality: bool = False
    confidentiality_description: str = ""
    integrity: bool = False
    integrity_description: str = ""
    availability: bool = False
    availability_description: str = ""
    authenticity: bool = False
    authenticity_description: str = ""
    non_repudiation: bool = False
    non_repudiation_description: str = ""
    assurance: bool = False
    assurance_description: str = ""
    trustworthy: bool = False
    trustworthy_description: str = ""
    privacy: bool = False
    privacy_description: str = ""
    
    @classmethod
    def get_table_name(cls) -> str:
        return "feedback"


@dataclass
class Constraint(BaseEntity):
    """Database entity for constraints."""
    constraint_name: str = ""
    type_identifier: str = "C"
    constraint_description: str = ""
    
    @classmethod
    def get_table_name(cls) -> str:
        return "constraints"


@dataclass
class Environment(BaseEntity):
    """Database entity for environments, associated with a system."""
    system_id: int = 0
    environment_name: str = ""
    environment_description: str = ""
    operational_context: str = ""
    environmental_conditions: str = ""
    type_identifier: str = "E"
    
    @classmethod
    def get_table_name(cls) -> str:
        return "environments"


@dataclass  
class StateDiagram(BaseEntity):
    """Database entity for state diagrams."""
    sd_name: str = ""
    sd_description: str = ""
    diagram_url: str = ""
    type_identifier: str = "SD"
    
    @classmethod
    def get_table_name(cls) -> str:
        return "state_diagrams"


@dataclass
class State(BaseEntity):
    """Database entity for states."""
    short_text_identifier: str = ""
    state_description: str = ""
    criticality: str = CRITICALITY_NON_CRITICAL
    confidentiality: bool = False
    integrity: bool = False
    availability: bool = False
    authenticity: bool = False
    type_identifier: str = "ST"
    non_repudiation: bool = False
    assurance: bool = False
    trustworthy: bool = False
    privacy: bool = False
    confidentiality_description: str = ""
    integrity_description: str = ""
    availability_description: str = ""
    authenticity_description: str = ""
    non_repudiation_description: str = ""
    assurance_description: str = ""
    trustworthy_description: str = ""
    privacy_description: str = ""
    
    @classmethod
    def get_table_name(cls) -> str:
        return "states"


@dataclass
class SafetySecurityControl(BaseEntity):
    """Database entity for safety and security controls."""
    sc_name: str = ""
    sc_description: str = ""
    description: str = ""
    criticality: str = CRITICALITY_NON_CRITICAL
    confidentiality: bool = False
    integrity: bool = False
    availability: bool = False
    authenticity: bool = False
    type_identifier: str = "SC"
    non_repudiation: bool = False
    assurance: bool = False
    trustworthy: bool = False
    privacy: bool = False
    confidentiality_description: str = ""
    integrity_description: str = ""
    availability_description: str = ""
    authenticity_description: str = ""
    non_repudiation_description: str = ""
    assurance_description: str = ""
    trustworthy_description: str = ""
    privacy_description: str = ""
    
    @classmethod
    def get_table_name(cls) -> str:
        return "safety_security_controls"


class EntityRepository:
    """
    Repository pattern implementation for database entities.
    Provides CRUD operations and query methods.
    """
    
    def __init__(self, connection: DatabaseConnection, entity_class: Type[BaseEntity]):
        """
        Initialize repository.
        
        Args:
            connection: Database connection
            entity_class: Entity class this repository manages
        """
        self.connection = connection
        self.entity_class = entity_class
        self.table_name = entity_class.get_table_name()
    
    def create(self, entity: BaseEntity) -> Optional[int]:
        """
        Create a new entity in the database.
        
        Args:
            entity: Entity to create
            
        Returns:
            ID of created entity or None if failed
        """
        try:
            # Auto-generate hierarchical ID if not already set
            if not entity.system_hierarchy:
                self._generate_hierarchical_id(entity)
            
            # Prepare field data
            entity_dict = entity.to_dict()
            
            # Remove id and timestamp fields for insert
            entity_dict.pop('id', None)
            entity_dict.pop('created_at', None) 
            entity_dict.pop('updated_at', None)
            
            # Generate SQL
            fields_str = ', '.join(entity_dict.keys())
            placeholders = ', '.join(['?' for _ in entity_dict])
            values = list(entity_dict.values())
            
            sql = f"""
            INSERT INTO {self.table_name} ({fields_str})
            VALUES ({placeholders})
            """
            
            # Execute insert
            with self.connection.transaction():
                cursor = self.connection.execute(sql, values)
                entity_id = cursor.lastrowid
                
                # Log audit trail
                self._log_audit('INSERT', entity_id, entity_dict)
                
                logger.debug(f"Created {self.entity_class.__name__} with ID {entity_id} and hierarchical ID {entity.system_hierarchy}")
                return entity_id
                
        except Exception as e:
            logger.error(f"Failed to create {self.entity_class.__name__}: {str(e)}")
            return None
    
    def read(self, entity_id: int, baseline: str = WORKING_BASELINE) -> Optional[BaseEntity]:
        """
        Read entity by ID.
        
        Args:
            entity_id: Entity ID
            baseline: Baseline to read from
            
        Returns:
            Entity instance or None if not found
        """
        try:
            sql = f"SELECT * FROM {self.table_name} WHERE id = ? AND baseline = ?"
            row = self.connection.fetchone(sql, (entity_id, baseline))
            
            if row:
                return self._row_to_entity(row)
            return None
            
        except Exception as e:
            logger.error(f"Failed to read {self.entity_class.__name__} {entity_id}: {str(e)}")
            return None
    
    def update(self, entity: BaseEntity) -> bool:
        """
        Update existing entity.
        
        Args:
            entity: Entity to update
            
        Returns:
            True if update was successful
        """
        if not entity.id:
            logger.error("Cannot update entity without ID")
            return False
        
        try:
            # Prepare field data
            entity_dict = entity.to_dict()
            entity_dict.pop('id')
            entity_dict.pop('created_at', None)
            entity_dict['updated_at'] = datetime.now().isoformat()
            
            # Generate SQL
            set_clause = ', '.join([f"{k} = ?" for k in entity_dict.keys()])
            values = list(entity_dict.values()) + [entity.id]
            
            sql = f"UPDATE {self.table_name} SET {set_clause} WHERE id = ?"
            
            # Execute update
            with self.connection.transaction():
                cursor = self.connection.execute(sql, values)
                
                if cursor.rowcount > 0:
                    # Log audit trail
                    self._log_audit('UPDATE', entity.id, entity_dict)
                    logger.debug(f"Updated {self.entity_class.__name__} {entity.id}")
                    return True
                else:
                    logger.warning(f"No rows updated for {self.entity_class.__name__} {entity.id}")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to update {self.entity_class.__name__} {entity.id}: {str(e)}")
            return False
    
    def delete(self, entity_id: int) -> bool:
        """
        Delete entity by ID.
        
        Args:
            entity_id: Entity ID to delete
            
        Returns:
            True if deletion was successful
        """
        try:
            sql = f"DELETE FROM {self.table_name} WHERE id = ?"
            
            with self.connection.transaction():
                cursor = self.connection.execute(sql, (entity_id,))
                
                if cursor.rowcount > 0:
                    # Log audit trail
                    self._log_audit('DELETE', entity_id, {})
                    logger.debug(f"Deleted {self.entity_class.__name__} {entity_id}")
                    return True
                else:
                    logger.warning(f"No rows deleted for {self.entity_class.__name__} {entity_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to delete {self.entity_class.__name__} {entity_id}: {str(e)}")
            return False
    
    def list_by_system(self, system_id: int, baseline: str = WORKING_BASELINE) -> List[BaseEntity]:
        """
        List entities by system ID.
        
        Args:
            system_id: System ID
            baseline: Baseline to read from
            
        Returns:
            List of entities
        """
        try:
            sql = f"SELECT * FROM {self.table_name} WHERE system_id = ? AND baseline = ? ORDER BY id"
            rows = self.connection.fetchall(sql, (system_id, baseline))
            
            return [self._row_to_entity(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to list {self.entity_class.__name__} by system {system_id}: {str(e)}")
            return []
    
    def find_by_system_hierarchy(self, system_hierarchy: str, baseline: str = WORKING_BASELINE) -> List[BaseEntity]:
        """
        Find all entities with a specific system hierarchy.
        
        Args:
            system_hierarchy: The system hierarchy to filter by
            baseline: The baseline to filter by
        
        Returns:
            List of entities matching the system hierarchy
        """
        try:
            sql = f"SELECT * FROM {self.table_name} WHERE system_hierarchy = ? AND baseline = ? ORDER BY id"
            rows = self.connection.fetchall(sql, (system_hierarchy, baseline))
            
            return [self._row_to_entity(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to find {self.entity_class.__name__} by system hierarchy {system_hierarchy}: {str(e)}")
            return []
    
    def find_by_system_id(self, system_id: int, baseline: str = WORKING_BASELINE) -> List[BaseEntity]:
        """
        Find all entities associated with a specific system ID.
        
        Args:
            system_id: The system ID to filter by
            baseline: The baseline to filter by
        
        Returns:
            List of entities associated with the system
        """
        try:
            # Check if this entity type has a system_id field
            sql = f"PRAGMA table_info({self.table_name})"
            columns = [row[1] for row in self.connection.fetchall(sql)]
            
            if 'system_id' not in columns:
                logger.warning(f"Entity {self.entity_class.__name__} does not have system_id field")
                return []
            
            sql = f"SELECT * FROM {self.table_name} WHERE system_id = ? AND baseline = ? ORDER BY id"
            rows = self.connection.fetchall(sql, (system_id, baseline))
            
            return [self._row_to_entity(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to find {self.entity_class.__name__} by system ID {system_id}: {str(e)}")
            return []
    
    def get_by_id(self, entity_id: int, baseline: str = WORKING_BASELINE) -> Optional[BaseEntity]:
        """
        Get entity by ID (alias for read method for consistency).
        
        Args:
            entity_id: The entity ID
            baseline: The baseline to filter by
        
        Returns:
            Entity instance or None if not found
        """
        return self.read(entity_id, baseline)
    
    def list(self, baseline: str = WORKING_BASELINE) -> List[BaseEntity]:
        """
        List all entities of this type.
        
        Args:
            baseline: Baseline to read from
            
        Returns:
            List of all entities
        """
        try:
            sql = f"SELECT * FROM {self.table_name} WHERE baseline = ? ORDER BY id"
            rows = self.connection.fetchall(sql, (baseline,))
            
            return [self._row_to_entity(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to list all {self.entity_class.__name__}: {str(e)}")
            return []
    
    def _row_to_entity(self, row) -> BaseEntity:
        """
        Convert database row to entity instance.
        
        Args:
            row: Database row
            
        Returns:
            Entity instance
        """
        # Convert row to dictionary
        row_dict = dict(row)
        
        # Convert datetime strings back to datetime objects if needed
        for key, value in row_dict.items():
            if key in ['created_at', 'updated_at'] and isinstance(value, str):
                try:
                    row_dict[key] = datetime.fromisoformat(value)
                except ValueError:
                    row_dict[key] = None
        
        # Create entity instance
        return self.entity_class(**row_dict)
    
    def _generate_hierarchical_id(self, entity: BaseEntity):
        """
        Generate hierarchical ID for entity.
        
        Args:
            entity: Entity to generate hierarchical ID for
        """
        try:
            from ..utils.hierarchy import HierarchyManager
            
            # Get existing hierarchical IDs for this entity type and baseline
            existing_ids_sql = f"""
            SELECT system_hierarchy FROM {self.table_name} 
            WHERE baseline = ? AND system_hierarchy != ''
            """
            rows = self.connection.fetchall(existing_ids_sql, (entity.baseline,))
            existing_ids = [row['system_hierarchy'] for row in rows if row['system_hierarchy']]
            
            # For systems, handle parent-child hierarchy
            if isinstance(entity, System):
                if entity.parent_system_id:
                    # Get parent system hierarchy
                    parent_sql = "SELECT system_hierarchy FROM systems WHERE id = ? AND baseline = ?"
                    parent_row = self.connection.fetchone(parent_sql, (entity.parent_system_id, entity.baseline))
                    
                    if parent_row and parent_row['system_hierarchy']:
                        parent_hierarchy = parent_row['system_hierarchy']
                        parent_id = HierarchyManager.parse_hierarchical_id(parent_hierarchy)
                        
                        if parent_id:
                            # Find next sequential number for children of this parent
                            child_seq = 1
                            while True:
                                if parent_id.level_identifier == 0:
                                    # Parent is root (S-1), child becomes S-1.1, S-1.2, etc.
                                    child_hierarchy = f"{entity.type_identifier}-{parent_id.sequential_identifier}.{child_seq}"
                                else:
                                    # Parent is nested (S-1.2), child becomes S-1.2.1, S-1.2.2, etc.
                                    child_hierarchy = f"{entity.type_identifier}-{parent_id.level_identifier}.{parent_id.sequential_identifier}.{child_seq}"
                                
                                if child_hierarchy not in existing_ids:
                                    break
                                child_seq += 1
                            
                            entity.system_hierarchy = child_hierarchy
                            # For systems, set the hierarchical components
                            if child_hierarchy.count('.') == 1:
                                # Format: S-1.2
                                parts = child_hierarchy.split('-')[1].split('.')
                                entity.level_identifier = int(parts[0])
                                entity.sequential_identifier = int(parts[1])
                            else:
                                # Format: S-1.2.3 (deeper nesting)
                                parts = child_hierarchy.split('-')[1].split('.')
                                entity.level_identifier = int(parts[0])
                                entity.sequential_identifier = int(parts[-1])  # Use last part
                            return
                
                # Root system - find next sequential number
                seq_id = HierarchyManager.find_next_sequential_id(existing_ids, entity.type_identifier, 0)
                entity.system_hierarchy = f"{entity.type_identifier}-{seq_id}"
                entity.level_identifier = 0
                entity.sequential_identifier = seq_id
            
            else:
                # For non-system entities, use the system hierarchy they belong to
                if hasattr(entity, 'system_id') and entity.system_id is not None and entity.system_id > 0:
                    # Get system hierarchy
                    system_sql = "SELECT system_hierarchy FROM systems WHERE id = ? AND baseline = ?"
                    system_row = self.connection.fetchone(system_sql, (entity.system_id, entity.baseline))
                    
                    if system_row and system_row['system_hierarchy']:
                        system_hierarchy = system_row['system_hierarchy']
                        # Extract the hierarchy part after the type identifier (e.g., "1.2" from "S-1.2")
                        system_hierarchy_part = system_hierarchy.split('-')[1] if '-' in system_hierarchy else system_hierarchy
                        
                        # Find next sequential number for this entity type within this system
                        # Look for existing entities with the same system hierarchy pattern
                        entity_pattern = f"{entity.type_identifier}-{system_hierarchy_part}."
                        
                        # Count existing entities with this pattern
                        matching_entities = [eid for eid in existing_ids if eid.startswith(entity_pattern)]
                        seq_id = len(matching_entities) + 1
                        
                        # Create hierarchical ID: Type-SystemHierarchy.SequentialNumber
                        # Example: F-1.2.1 (Function 1 in System S-1.2)
                        entity.system_hierarchy = f"{entity.type_identifier}-{system_hierarchy_part}.{seq_id}"
                        
                        # Set hierarchical components
                        hierarchy_parts = system_hierarchy_part.split('.')
                        if len(hierarchy_parts) == 1:
                            # Simple system hierarchy like "1"
                            entity.level_identifier = int(hierarchy_parts[0])
                            entity.sequential_identifier = seq_id
                        else:
                            # Complex system hierarchy like "1.2"
                            entity.level_identifier = int(hierarchy_parts[0])
                            entity.sequential_identifier = seq_id
                    else:
                        # System not found or no hierarchy, create simple sequential ID
                        seq_id = HierarchyManager.find_next_sequential_id(existing_ids, entity.type_identifier, 0)
                        entity.system_hierarchy = f"{entity.type_identifier}-{seq_id}"
                        entity.level_identifier = 0
                        entity.sequential_identifier = seq_id
                else:
                    # Entity not associated with system (like hazards, losses)
                    seq_id = HierarchyManager.find_next_sequential_id(existing_ids, entity.type_identifier, 0)
                    entity.system_hierarchy = f"{entity.type_identifier}-{seq_id}"
                    entity.level_identifier = 0
                    entity.sequential_identifier = seq_id
                    
        except Exception as e:
            logger.error(f"Failed to generate hierarchical ID: {str(e)}")
            # Fallback to simple sequential ID
            seq_id = 1
            entity.system_hierarchy = f"{entity.type_identifier}-{seq_id}"
            entity.level_identifier = 0
            entity.sequential_identifier = seq_id
    
    def _log_audit(self, operation: str, entity_id: int, data: Dict[str, Any]) -> None:
        """
        Log operation to audit trail.
        
        Args:
            operation: Operation type (INSERT, UPDATE, DELETE)
            entity_id: Entity ID
            data: Entity data
        """
        try:
            # Create data hash
            data_str = str(sorted(data.items()))
            data_hash = hashlib.sha256(data_str.encode()).hexdigest()
            
            # Get previous hash for chaining
            prev_hash_row = self.connection.fetchone(
                "SELECT row_data_hash FROM audit_log WHERE table_name = ? ORDER BY timestamp DESC LIMIT 1",
                (self.table_name,)
            )
            prev_hash = prev_hash_row['row_data_hash'] if prev_hash_row else ''
            
            # Insert audit record
            audit_sql = """
            INSERT INTO audit_log (operation, table_name, row_id, row_data_hash, previous_hash)
            VALUES (?, ?, ?, ?, ?)
            """
            
            self.connection.execute(audit_sql, (operation, self.table_name, entity_id, data_hash, prev_hash))
            
        except Exception as e:
            logger.error(f"Failed to log audit trail: {str(e)}")


class EntityFactory:
    """
    Factory for creating entity repositories.
    """
    
    _repositories = {}
    
    @classmethod
    def get_repository(cls, connection: DatabaseConnection, entity_class: Type[BaseEntity]) -> EntityRepository:
        """
        Get or create repository for entity class.
        
        Args:
            connection: Database connection
            entity_class: Entity class
            
        Returns:
            Repository instance
        """
        key = (id(connection), entity_class.__name__)
        
        if key not in cls._repositories:
            cls._repositories[key] = EntityRepository(connection, entity_class)
        
        return cls._repositories[key]