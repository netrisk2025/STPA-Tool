"""
Hierarchical ID management utilities for STPA Tool
Handles generation, validation, and parsing of hierarchical identifiers.
"""

import re
from typing import Tuple, Optional, List, Dict
from dataclasses import dataclass

from ..config.constants import (
    SYSTEM_TYPE, FUNCTION_TYPE, INTERFACE_TYPE, ASSET_TYPE,
    CONSTRAINT_TYPE, REQUIREMENT_TYPE, ENVIRONMENT_TYPE, HAZARD_TYPE,
    LOSS_TYPE, CONTROL_STRUCTURE_TYPE, CONTROLLER_TYPE,
    CONTROLLED_PROCESS_TYPE, CONTROL_ACTION_TYPE, FEEDBACK_TYPE,
    CONTROL_ALGORITHM_TYPE, PROCESS_MODEL_TYPE, STATE_DIAGRAM_TYPE,
    STATE_TYPE, IN_TRANSITION_TYPE, OUT_TRANSITION_TYPE,
    SAFETY_SECURITY_CONTROL_TYPE
)
from ..log_config.config import get_logger

logger = get_logger(__name__)


@dataclass
class HierarchicalID:
    """
    Represents a hierarchical identifier.
    """
    type_identifier: str
    level_identifier: int
    sequential_identifier: int
    
    def __str__(self) -> str:
        """Return formatted hierarchical ID string."""
        if self.level_identifier == 0:
            return f"{self.type_identifier}-{self.sequential_identifier}"
        else:
            return f"{self.type_identifier}-{self.level_identifier}.{self.sequential_identifier}"
    
    def to_hierarchy_string(self) -> str:
        """Return hierarchy string for database storage."""
        return str(self)


class HierarchyManager:
    """
    Manages hierarchical ID generation and validation.
    """
    
    # Valid type identifiers
    VALID_TYPES = {
        SYSTEM_TYPE, FUNCTION_TYPE, INTERFACE_TYPE, ASSET_TYPE,
        CONSTRAINT_TYPE, REQUIREMENT_TYPE, ENVIRONMENT_TYPE, HAZARD_TYPE,
        LOSS_TYPE, CONTROL_STRUCTURE_TYPE, CONTROLLER_TYPE,
        CONTROLLED_PROCESS_TYPE, CONTROL_ACTION_TYPE, FEEDBACK_TYPE,
        CONTROL_ALGORITHM_TYPE, PROCESS_MODEL_TYPE, STATE_DIAGRAM_TYPE,
        STATE_TYPE, IN_TRANSITION_TYPE, OUT_TRANSITION_TYPE,
        SAFETY_SECURITY_CONTROL_TYPE
    }
    
    # Hierarchical type patterns
    HIERARCHICAL_TYPES = {
        SYSTEM_TYPE: {
            'max_levels': 10,  # Support deep system hierarchies
            'requires_parent': False
        },
        REQUIREMENT_TYPE: {
            'max_levels': 5,   # L1, L2, L3, L4, L5 requirements
            'requires_parent': False
        },
        FUNCTION_TYPE: {
            'max_levels': 3,   # Function hierarchies
            'requires_parent': True  # Must belong to a system
        }
    }
    
    # Regex pattern for parsing hierarchical IDs  
    ID_PATTERN = re.compile(r'^([A-Z]+)-(\d+(?:\.\d+)*)$')
    
    @classmethod
    def parse_hierarchical_id(cls, id_string: str) -> Optional[HierarchicalID]:
        """
        Parse hierarchical ID string into components.
        
        Args:
            id_string: Hierarchical ID string (e.g., "S-1.2.1")
            
        Returns:
            HierarchicalID object or None if invalid
        """
        try:
            match = cls.ID_PATTERN.match(id_string.strip())
            if not match:
                return None
            
            type_id = match.group(1)
            numbers_part = match.group(2)
            
            # Split by dots to get all levels
            number_parts = numbers_part.split('.')
            
            if len(number_parts) == 1:
                # Simple notation like "S-1"
                level_id = 0
                seq_id = int(number_parts[0])
            else:
                # Complex notation like "S-1.2" or "S-1.2.3"
                # Use the first number as level, last number as sequential
                level_id = int(number_parts[0])
                seq_id = int(number_parts[-1])
            
            # Validate type identifier
            if type_id not in cls.VALID_TYPES:
                logger.warning(f"Invalid type identifier: {type_id}")
                return None
            
            return HierarchicalID(
                type_identifier=type_id,
                level_identifier=level_id,
                sequential_identifier=seq_id
            )
            
        except Exception as e:
            logger.error(f"Failed to parse hierarchical ID '{id_string}': {str(e)}")
            return None
    
    @classmethod
    def validate_hierarchical_id(cls, hierarchical_id: HierarchicalID) -> Tuple[bool, Optional[str]]:
        """
        Validate hierarchical ID structure and rules.
        
        Args:
            hierarchical_id: Hierarchical ID to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check type identifier
            if hierarchical_id.type_identifier not in cls.VALID_TYPES:
                return False, f"Invalid type identifier: {hierarchical_id.type_identifier}"
            
            # Check level limits
            type_config = cls.HIERARCHICAL_TYPES.get(hierarchical_id.type_identifier)
            if type_config:
                max_levels = type_config['max_levels']
                if hierarchical_id.level_identifier > max_levels:
                    return False, f"Level {hierarchical_id.level_identifier} exceeds maximum {max_levels} for type {hierarchical_id.type_identifier}"
            
            # Check sequential identifier
            if hierarchical_id.sequential_identifier < 0:
                return False, "Sequential identifier cannot be negative"
            
            # Level 0 should not have sequential identifier
            if hierarchical_id.level_identifier == 0 and hierarchical_id.sequential_identifier == 0:
                return False, "Root level must have sequential identifier > 0"
            
            return True, None
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    @classmethod
    def generate_child_id(cls, parent_id: HierarchicalID, child_sequence: int) -> Optional[HierarchicalID]:
        """
        Generate child hierarchical ID from parent.
        
        Args:
            parent_id: Parent hierarchical ID
            child_sequence: Sequential number for child
            
        Returns:
            Child hierarchical ID or None if invalid
        """
        try:
            # For systems, we extend the hierarchy path
            if parent_id.type_identifier == SYSTEM_TYPE:
                # If parent is root level (S-1), child becomes S-1.1, S-1.2, etc.
                if parent_id.level_identifier == 0:
                    child_level = parent_id.sequential_identifier
                    child_seq = child_sequence
                else:
                    # For nested levels, extend the hierarchy
                    # Parent S-1.2 becomes child S-1.2.1, S-1.2.2, etc.
                    child_level = parent_id.level_identifier
                    child_seq = child_sequence
            else:
                # For other entity types, use simpler logic
                if parent_id.level_identifier == 0:
                    child_level = parent_id.sequential_identifier
                    child_seq = child_sequence
                else:
                    child_level = parent_id.level_identifier
                    child_seq = child_sequence
            
            child_id = HierarchicalID(
                type_identifier=parent_id.type_identifier,
                level_identifier=child_level,
                sequential_identifier=child_seq
            )
            
            # Validate the generated ID
            is_valid, error = cls.validate_hierarchical_id(child_id)
            if not is_valid:
                logger.error(f"Generated invalid child ID: {error}")
                return None
            
            return child_id
            
        except Exception as e:
            logger.error(f"Failed to generate child ID: {str(e)}")
            return None
    
    @classmethod
    def get_parent_hierarchy(cls, hierarchical_id: HierarchicalID) -> Optional[str]:
        """
        Get parent hierarchy string from hierarchical ID.
        
        Args:
            hierarchical_id: Child hierarchical ID
            
        Returns:
            Parent hierarchy string or None if root level
        """
        try:
            if hierarchical_id.level_identifier == 0:
                return None  # Root level has no parent
            
            # For systems like S-1.2.3, parent would be S-1.2
            # This needs more sophisticated logic based on the hierarchy depth
            # For now, simple implementation
            
            if hierarchical_id.sequential_identifier > 0:
                # Parent is at the same level but without the sequential part
                parent_id = HierarchicalID(
                    type_identifier=hierarchical_id.type_identifier,
                    level_identifier=0,
                    sequential_identifier=hierarchical_id.level_identifier
                )
                return str(parent_id)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get parent hierarchy: {str(e)}")
            return None
    
    @classmethod
    def sort_hierarchical_ids(cls, id_strings: List[str]) -> List[str]:
        """
        Sort hierarchical ID strings in hierarchical order.
        
        Args:
            id_strings: List of hierarchical ID strings
            
        Returns:
            Sorted list of hierarchical ID strings
        """
        try:
            # Parse all IDs
            parsed_ids = []
            for id_str in id_strings:
                parsed_id = cls.parse_hierarchical_id(id_str)
                if parsed_id:
                    parsed_ids.append((id_str, parsed_id))
                else:
                    logger.warning(f"Could not parse ID for sorting: {id_str}")
            
            # Sort by type, then level, then sequential
            def sort_key(item):
                _, parsed_id = item
                return (
                    parsed_id.type_identifier,
                    parsed_id.level_identifier,
                    parsed_id.sequential_identifier
                )
            
            sorted_ids = sorted(parsed_ids, key=sort_key)
            
            return [id_str for id_str, _ in sorted_ids]
            
        except Exception as e:
            logger.error(f"Failed to sort hierarchical IDs: {str(e)}")
            return id_strings  # Return original list if sorting fails
    
    @classmethod
    def find_next_sequential_id(cls, existing_ids: List[str], type_identifier: str, level_identifier: int) -> int:
        """
        Find the next available sequential identifier.
        
        Args:
            existing_ids: List of existing hierarchical ID strings
            type_identifier: Type identifier for new ID
            level_identifier: Level identifier for new ID
            
        Returns:
            Next available sequential identifier
        """
        try:
            max_seq = 0
            
            for id_str in existing_ids:
                parsed_id = cls.parse_hierarchical_id(id_str)
                if parsed_id and parsed_id.type_identifier == type_identifier:
                    # For level 0 (root), check sequential_identifier directly  
                    if level_identifier == 0 and parsed_id.level_identifier == 0:
                        max_seq = max(max_seq, parsed_id.sequential_identifier)
                    # For root items stored as single number (like S-1, S-2)
                    elif level_identifier == 0 and parsed_id.sequential_identifier == 0:
                        max_seq = max(max_seq, parsed_id.level_identifier)
                    # For nested levels
                    elif (parsed_id.level_identifier == level_identifier and 
                          parsed_id.sequential_identifier > 0):
                        max_seq = max(max_seq, parsed_id.sequential_identifier)
            
            return max_seq + 1
            
        except Exception as e:
            logger.error(f"Failed to find next sequential ID: {str(e)}")
            return 1  # Default to 1 if error occurs
    
    @classmethod
    def get_hierarchy_depth(cls, hierarchical_id: HierarchicalID) -> int:
        """
        Get the depth of a hierarchical ID.
        
        Args:
            hierarchical_id: Hierarchical ID
            
        Returns:
            Hierarchy depth (0 for root, 1 for first level, etc.)
        """
        if hierarchical_id.level_identifier == 0:
            return 0  # Root level
        elif hierarchical_id.sequential_identifier == 0:
            return 1  # First sub-level
        else:
            return 2  # Second sub-level or deeper
    
    @classmethod
    def is_ancestor(cls, potential_ancestor: str, potential_descendant: str) -> bool:
        """
        Check if one hierarchical ID is an ancestor of another.
        
        Args:
            potential_ancestor: Potential ancestor ID string
            potential_descendant: Potential descendant ID string
            
        Returns:
            True if ancestor relationship exists
        """
        try:
            ancestor_id = cls.parse_hierarchical_id(potential_ancestor)
            descendant_id = cls.parse_hierarchical_id(potential_descendant)
            
            if not ancestor_id or not descendant_id:
                return False
            
            # Must be same type
            if ancestor_id.type_identifier != descendant_id.type_identifier:
                return False
            
            # Ancestor must be at a higher level (lower depth)
            ancestor_depth = cls.get_hierarchy_depth(ancestor_id)
            descendant_depth = cls.get_hierarchy_depth(descendant_id)
            
            if ancestor_depth >= descendant_depth:
                return False
            
            # Check if descendant starts with ancestor pattern
            ancestor_str = str(ancestor_id)
            descendant_str = str(descendant_id)
            
            return descendant_str.startswith(ancestor_str + ".")
            
        except Exception as e:
            logger.error(f"Failed to check ancestor relationship: {str(e)}")
            return False
    
    @classmethod
    def get_type_description(cls, type_identifier: str) -> str:
        """
        Get human-readable description for type identifier.
        
        Args:
            type_identifier: Type identifier
            
        Returns:
            Human-readable description
        """
        descriptions = {
            SYSTEM_TYPE: "System",
            FUNCTION_TYPE: "Function", 
            INTERFACE_TYPE: "Interface",
            ASSET_TYPE: "Asset",
            CONSTRAINT_TYPE: "Constraint",
            REQUIREMENT_TYPE: "Requirement",
            ENVIRONMENT_TYPE: "Environment",
            HAZARD_TYPE: "Hazard",
            LOSS_TYPE: "Loss",
            CONTROL_STRUCTURE_TYPE: "Control Structure",
            CONTROLLER_TYPE: "Controller",
            CONTROLLED_PROCESS_TYPE: "Controlled Process",
            CONTROL_ACTION_TYPE: "Control Action",
            FEEDBACK_TYPE: "Feedback",
            CONTROL_ALGORITHM_TYPE: "Control Algorithm",
            PROCESS_MODEL_TYPE: "Process Model",
            STATE_DIAGRAM_TYPE: "State Diagram",
            STATE_TYPE: "State",
            IN_TRANSITION_TYPE: "In Transition",
            OUT_TRANSITION_TYPE: "Out Transition",
            SAFETY_SECURITY_CONTROL_TYPE: "Safety/Security Control"
        }
        
        return descriptions.get(type_identifier, f"Unknown ({type_identifier})")