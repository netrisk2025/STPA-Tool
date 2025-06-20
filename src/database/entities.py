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
    system_id: Optional[int] = None
    environment_id: Optional[int] = None
    asset_id: Optional[int] = None
    h_name: str = ""
    h_description: str = ""
    
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
    system_id: int = 0
    asset_id: int = 0
    l_name: str = ""
    l_description: str = ""
    loss_description: str = ""
    
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
                
                logger.debug(f"Created {self.entity_class.__name__} with ID {entity_id}")
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