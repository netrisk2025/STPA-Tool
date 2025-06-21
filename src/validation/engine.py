"""
Data validation engine for the STPA Tool.
Implements validation rules as specified in the SRS.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

from ..database.connection import DatabaseConnection
from ..database.entities import System, Requirement, ControlStructure, EntityFactory
from ..utils.hierarchy import HierarchyManager


logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """Severity levels for validation issues."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    """Represents a validation issue found in the data."""
    entity_type: str
    entity_id: Optional[int]
    entity_name: str
    issue_type: str
    severity: ValidationSeverity
    message: str
    hierarchical_id: Optional[str] = None
    suggestion: Optional[str] = None


class ValidationRule:
    """Base class for validation rules."""
    
    def __init__(self, name: str, description: str, severity: ValidationSeverity = ValidationSeverity.WARNING):
        self.name = name
        self.description = description
        self.severity = severity
    
    def validate(self, connection: DatabaseConnection, system_id: Optional[int] = None) -> List[ValidationIssue]:
        """
        Validate the rule and return any issues found.
        
        Args:
            connection: Database connection
            system_id: Optional system ID to limit validation scope
            
        Returns:
            List of validation issues
        """
        raise NotImplementedError("Subclasses must implement validate method")


class CompletenessValidationRule(ValidationRule):
    """Validates completeness of required fields and relationships."""
    
    def __init__(self):
        super().__init__(
            "Completeness Check",
            "Ensures all required fields are populated and relationships are complete",
            ValidationSeverity.WARNING
        )
    
    def validate(self, connection: DatabaseConnection, system_id: Optional[int] = None) -> List[ValidationIssue]:
        issues = []
        
        # Check systems for completeness
        issues.extend(self._validate_systems(connection, system_id))
        
        # Check functions for completeness
        issues.extend(self._validate_functions(connection, system_id))
        
        # Check requirements for completeness
        issues.extend(self._validate_requirements(connection, system_id))
        
        # Check control structures for completeness
        issues.extend(self._validate_control_structures(connection, system_id))
        
        return issues
    
    def _validate_systems(self, connection: DatabaseConnection, system_id: Optional[int] = None) -> List[ValidationIssue]:
        """Validate system completeness."""
        issues = []
        
        system_repo = EntityFactory.get_repository(connection, System)
        
        if system_id:
            systems = [system_repo.read(system_id)] if system_repo.read(system_id) else []
        else:
            # Get all systems using SQL query since there's no list() method
            from ..config.constants import WORKING_BASELINE
            sql = "SELECT * FROM systems WHERE baseline = ? ORDER BY id"
            rows = connection.fetchall(sql, (WORKING_BASELINE,))
            systems = [system_repo._row_to_entity(row) for row in rows]
        
        for system in systems:
            if not system:
                continue
                
            # Check for empty required fields
            if not system.system_name or system.system_name.strip() == "":
                issues.append(ValidationIssue(
                    entity_type="System",
                    entity_id=system.id,
                    entity_name=system.system_hierarchy or "Unknown",
                    issue_type="missing_name",
                    severity=ValidationSeverity.ERROR,
                    message="System name is required but not provided",
                    hierarchical_id=system.system_hierarchy,
                    suggestion="Provide a descriptive name for this system"
                ))
            
            if not system.system_description or system.system_description.strip() == "":
                issues.append(ValidationIssue(
                    entity_type="System",
                    entity_id=system.id,
                    entity_name=system.system_name or "Unknown",
                    issue_type="missing_description",
                    severity=ValidationSeverity.WARNING,
                    message="System description is recommended but not provided",
                    hierarchical_id=system.system_hierarchy,
                    suggestion="Provide a clear description of this system's purpose and functionality"
                ))
            
            # Check criticality settings
            if (system.criticality and system.criticality != "Non-Critical" and 
                not any([system.confidentiality, system.integrity, system.availability,
                        system.authenticity, system.non_repudiation, system.assurance,
                        system.trustworthy, system.privacy])):
                issues.append(ValidationIssue(
                    entity_type="System",
                    entity_id=system.id,
                    entity_name=system.system_name or "Unknown",
                    issue_type="incomplete_criticality",
                    severity=ValidationSeverity.WARNING,
                    message=f"System marked as {system.criticality} but no security attributes are selected",
                    hierarchical_id=system.system_hierarchy,
                    suggestion="Select appropriate security attributes or change criticality level"
                ))
        
        return issues
    
    def _validate_functions(self, connection: DatabaseConnection, system_id: Optional[int] = None) -> List[ValidationIssue]:
        """Validate function completeness."""
        issues = []
        
        from ..database.entities import Function
        function_repo = EntityFactory.get_repository(connection, Function)
        
        if system_id:
            functions = function_repo.list_by_system(system_id)
        else:
            # Get all functions using SQL query
            from ..config.constants import WORKING_BASELINE
            sql = "SELECT * FROM functions WHERE baseline = ? ORDER BY id"
            rows = connection.fetchall(sql, (WORKING_BASELINE,))
            functions = [function_repo._row_to_entity(row) for row in rows]
        
        for function in functions:
            if not function.function_name or function.function_name.strip() == "":
                issues.append(ValidationIssue(
                    entity_type="Function",
                    entity_id=function.id,
                    entity_name=function.system_hierarchy or "Unknown",
                    issue_type="missing_name",
                    severity=ValidationSeverity.ERROR,
                    message="Function name is required but not provided",
                    hierarchical_id=function.system_hierarchy,
                    suggestion="Provide a descriptive name for this function"
                ))
            
            if not function.function_description or function.function_description.strip() == "":
                issues.append(ValidationIssue(
                    entity_type="Function",
                    entity_id=function.id,
                    entity_name=function.function_name or "Unknown",
                    issue_type="missing_description",
                    severity=ValidationSeverity.WARNING,
                    message="Function description is recommended but not provided",
                    hierarchical_id=function.system_hierarchy,
                    suggestion="Provide a clear description of what this function does"
                ))
        
        return issues
    
    def _validate_requirements(self, connection: DatabaseConnection, system_id: Optional[int] = None) -> List[ValidationIssue]:
        """Validate requirement completeness."""
        issues = []
        
        requirement_repo = EntityFactory.get_repository(connection, Requirement)
        
        if system_id:
            requirements = requirement_repo.list_by_system(system_id)
        else:
            # Get all requirements using SQL query
            from ..config.constants import WORKING_BASELINE
            sql = "SELECT * FROM requirements WHERE baseline = ? ORDER BY id"
            rows = connection.fetchall(sql, (WORKING_BASELINE,))
            requirements = [requirement_repo._row_to_entity(row) for row in rows]
        
        for requirement in requirements:
            if not requirement.requirement_text or requirement.requirement_text.strip() == "":
                issues.append(ValidationIssue(
                    entity_type="Requirement",
                    entity_id=requirement.id,
                    entity_name=requirement.alphanumeric_identifier or "Unknown",
                    issue_type="missing_text",
                    severity=ValidationSeverity.ERROR,
                    message="Requirement text is required but not provided",
                    hierarchical_id=requirement.system_hierarchy,
                    suggestion="Provide the requirement text describing what must be implemented"
                ))
            
            if not requirement.verification_method:
                issues.append(ValidationIssue(
                    entity_type="Requirement",
                    entity_id=requirement.id,
                    entity_name=requirement.alphanumeric_identifier or "Unknown",
                    issue_type="missing_verification",
                    severity=ValidationSeverity.WARNING,
                    message="Verification method is recommended but not specified",
                    hierarchical_id=requirement.system_hierarchy,
                    suggestion="Specify how this requirement will be verified (Test, Analysis, Inspection, Demonstration)"
                ))
        
        return issues
    
    def _validate_control_structures(self, connection: DatabaseConnection, system_id: Optional[int] = None) -> List[ValidationIssue]:
        """Validate control structure completeness."""
        issues = []
        
        try:
            control_structure_repo = EntityFactory.get_repository(connection, ControlStructure)
            
            if system_id:
                control_structures = control_structure_repo.list_by_system(system_id)
            else:
                # Get all control structures using SQL query
                from ..config.constants import WORKING_BASELINE
                sql = "SELECT * FROM control_structures WHERE baseline = ? ORDER BY id"
                rows = connection.fetchall(sql, (WORKING_BASELINE,))
                control_structures = [control_structure_repo._row_to_entity(row) for row in rows]
            
            for cs in control_structures:
                if not cs.structure_name or cs.structure_name.strip() == "":
                    issues.append(ValidationIssue(
                        entity_type="ControlStructure",
                        entity_id=cs.id,
                        entity_name=cs.system_hierarchy or "Unknown",
                        issue_type="missing_name",
                        severity=ValidationSeverity.ERROR,
                        message="Control structure name is required but not provided",
                        hierarchical_id=cs.system_hierarchy,
                        suggestion="Provide a descriptive name for this control structure"
                    ))
                
                # Check for unmapped components (placeholder - would need more complex queries)
                if not cs.structure_description or cs.structure_description.strip() == "":
                    issues.append(ValidationIssue(
                        entity_type="ControlStructure",
                        entity_id=cs.id,
                        entity_name=cs.structure_name or "Unknown",
                        issue_type="missing_description",
                        severity=ValidationSeverity.WARNING,
                        message="Control structure description is recommended but not provided",
                        hierarchical_id=cs.system_hierarchy,
                        suggestion="Provide a description of this control structure's purpose and components"
                    ))
        
        except Exception as e:
            logger.warning(f"Could not validate control structures: {e}")
        
        return issues


class LogicalConsistencyValidationRule(ValidationRule):
    """Validates logical consistency of data relationships."""
    
    def __init__(self):
        super().__init__(
            "Logical Consistency Check",
            "Validates logical consistency and prevents circular references",
            ValidationSeverity.ERROR
        )
    
    def validate(self, connection: DatabaseConnection, system_id: Optional[int] = None) -> List[ValidationIssue]:
        issues = []
        
        # Check for circular requirement references
        issues.extend(self._validate_requirement_hierarchy(connection, system_id))
        
        # Check for invalid requirement parent relationships
        issues.extend(self._validate_requirement_levels(connection, system_id))
        
        # Check system hierarchy consistency
        issues.extend(self._validate_system_hierarchy(connection, system_id))
        
        return issues
    
    def _validate_requirement_hierarchy(self, connection: DatabaseConnection, system_id: Optional[int] = None) -> List[ValidationIssue]:
        """Check for circular references in requirement hierarchy."""
        issues = []
        
        requirement_repo = EntityFactory.get_repository(connection, Requirement)
        
        if system_id:
            requirements = requirement_repo.list_by_system(system_id)
        else:
            # Get all requirements using SQL query
            from ..config.constants import WORKING_BASELINE
            sql = "SELECT * FROM requirements WHERE baseline = ? ORDER BY id"
            rows = connection.fetchall(sql, (WORKING_BASELINE,))
            requirements = [requirement_repo._row_to_entity(row) for row in rows]
        
        # Build requirement hierarchy map
        requirement_map = {req.id: req for req in requirements if req.id}
        
        for requirement in requirements:
            if not requirement.id:
                continue
                
            visited = set()
            current_id = requirement.parent_requirement_id
            
            while current_id:
                if current_id in visited:
                    # Circular reference detected
                    issues.append(ValidationIssue(
                        entity_type="Requirement",
                        entity_id=requirement.id,
                        entity_name=requirement.alphanumeric_identifier or "Unknown",
                        issue_type="circular_reference",
                        severity=ValidationSeverity.ERROR,
                        message="Circular reference detected in requirement hierarchy",
                        hierarchical_id=requirement.system_hierarchy,
                        suggestion="Remove the circular reference by changing the parent requirement"
                    ))
                    break
                
                visited.add(current_id)
                
                if current_id in requirement_map:
                    current_id = requirement_map[current_id].parent_requirement_id
                else:
                    # Parent requirement doesn't exist
                    issues.append(ValidationIssue(
                        entity_type="Requirement",
                        entity_id=requirement.id,
                        entity_name=requirement.alphanumeric_identifier or "Unknown",
                        issue_type="invalid_parent",
                        severity=ValidationSeverity.ERROR,
                        message="Parent requirement does not exist",
                        hierarchical_id=requirement.system_hierarchy,
                        suggestion="Select a valid parent requirement or remove the parent reference"
                    ))
                    break
        
        return issues
    
    def _validate_requirement_levels(self, connection: DatabaseConnection, system_id: Optional[int] = None) -> List[ValidationIssue]:
        """Check for invalid requirement level relationships."""
        issues = []
        
        requirement_repo = EntityFactory.get_repository(connection, Requirement)
        
        if system_id:
            requirements = requirement_repo.list_by_system(system_id)
        else:
            # Get all requirements using SQL query
            from ..config.constants import WORKING_BASELINE
            sql = "SELECT * FROM requirements WHERE baseline = ? ORDER BY id"
            rows = connection.fetchall(sql, (WORKING_BASELINE,))
            requirements = [requirement_repo._row_to_entity(row) for row in rows]
        
        requirement_map = {req.id: req for req in requirements if req.id}
        
        for requirement in requirements:
            if not requirement.id or not requirement.parent_requirement_id:
                continue
            
            parent = requirement_map.get(requirement.parent_requirement_id)
            if not parent:
                continue
            
            # Check that child requirement is at a higher level than parent
            if requirement.level_identifier <= parent.level_identifier:
                issues.append(ValidationIssue(
                    entity_type="Requirement",
                    entity_id=requirement.id,
                    entity_name=requirement.alphanumeric_identifier or "Unknown",
                    issue_type="invalid_level",
                    severity=ValidationSeverity.WARNING,
                    message=f"Requirement level ({requirement.level_identifier}) should be greater than parent level ({parent.level_identifier})",
                    hierarchical_id=requirement.system_hierarchy,
                    suggestion="Adjust the requirement level to be more specific than its parent"
                ))
        
        return issues
    
    def _validate_system_hierarchy(self, connection: DatabaseConnection, system_id: Optional[int] = None) -> List[ValidationIssue]:
        """Check system hierarchy consistency."""
        issues = []
        
        system_repo = EntityFactory.get_repository(connection, System)
        
        if system_id:
            systems = [system_repo.read(system_id)] if system_repo.read(system_id) else []
        else:
            # Get all systems using SQL query
            from ..config.constants import WORKING_BASELINE
            sql = "SELECT * FROM systems WHERE baseline = ? ORDER BY id"
            rows = connection.fetchall(sql, (WORKING_BASELINE,))
            systems = [system_repo._row_to_entity(row) for row in rows]
        
        for system in systems:
            if not system or not system.system_hierarchy:
                continue
            
            # Validate hierarchical ID format
            parsed_id = HierarchyManager.parse_hierarchical_id(system.system_hierarchy)
            if not parsed_id:
                issues.append(ValidationIssue(
                    entity_type="System",
                    entity_id=system.id,
                    entity_name=system.system_name or "Unknown",
                    issue_type="invalid_hierarchy",
                    severity=ValidationSeverity.ERROR,
                    message=f"Invalid hierarchical ID format: {system.system_hierarchy}",
                    hierarchical_id=system.system_hierarchy,
                    suggestion="Use valid hierarchical ID format (e.g., S-1, S-1.1, S-1.1.1)"
                ))
                continue
            
            # Validate hierarchy consistency with level and sequential identifiers
            expected_level = len(system.system_hierarchy.split('.')) - 1
            if system.level_identifier != expected_level:
                issues.append(ValidationIssue(
                    entity_type="System",
                    entity_id=system.id,
                    entity_name=system.system_name or "Unknown",
                    issue_type="inconsistent_level",
                    severity=ValidationSeverity.WARNING,
                    message=f"Level identifier ({system.level_identifier}) doesn't match hierarchy depth ({expected_level})",
                    hierarchical_id=system.system_hierarchy,
                    suggestion="Update level identifier to match the hierarchy depth"
                ))
        
        return issues


class ValidationEngine:
    """Main validation engine that runs all validation rules."""
    
    def __init__(self, connection: DatabaseConnection):
        self.connection = connection
        self.rules = [
            CompletenessValidationRule(),
            LogicalConsistencyValidationRule(),
        ]
        logger.info(f"Initialized validation engine with {len(self.rules)} rules")
    
    def add_rule(self, rule: ValidationRule):
        """Add a custom validation rule."""
        self.rules.append(rule)
        logger.info(f"Added validation rule: {rule.name}")
    
    def validate_system(self, system_id: int) -> List[ValidationIssue]:
        """
        Validate a specific system and its components.
        
        Args:
            system_id: System ID to validate
            
        Returns:
            List of validation issues found
        """
        logger.info(f"Starting validation for system ID: {system_id}")
        all_issues = []
        
        for rule in self.rules:
            try:
                issues = rule.validate(self.connection, system_id)
                all_issues.extend(issues)
                logger.debug(f"Rule '{rule.name}' found {len(issues)} issues for system {system_id}")
            except Exception as e:
                logger.error(f"Error running validation rule '{rule.name}': {e}")
                all_issues.append(ValidationIssue(
                    entity_type="ValidationEngine",
                    entity_id=None,
                    entity_name="Validation Error",
                    issue_type="rule_error",
                    severity=ValidationSeverity.ERROR,
                    message=f"Error running validation rule '{rule.name}': {str(e)}",
                    suggestion="Check system logs for more details"
                ))
        
        logger.info(f"Validation completed for system {system_id}: {len(all_issues)} issues found")
        return all_issues
    
    def validate_all(self) -> List[ValidationIssue]:
        """
        Validate all data in the database.
        
        Returns:
            List of all validation issues found
        """
        logger.info("Starting full database validation")
        all_issues = []
        
        for rule in self.rules:
            try:
                issues = rule.validate(self.connection)
                all_issues.extend(issues)
                logger.debug(f"Rule '{rule.name}' found {len(issues)} issues globally")
            except Exception as e:
                logger.error(f"Error running validation rule '{rule.name}': {e}")
                all_issues.append(ValidationIssue(
                    entity_type="ValidationEngine",
                    entity_id=None,
                    entity_name="Validation Error",
                    issue_type="rule_error",
                    severity=ValidationSeverity.ERROR,
                    message=f"Error running validation rule '{rule.name}': {str(e)}",
                    suggestion="Check system logs for more details"
                ))
        
        logger.info(f"Full validation completed: {len(all_issues)} issues found")
        return all_issues
    
    def get_validation_summary(self, issues: List[ValidationIssue]) -> Dict[str, Any]:
        """
        Generate a summary of validation results.
        
        Args:
            issues: List of validation issues
            
        Returns:
            Dictionary with validation summary statistics
        """
        summary = {
            'total_issues': len(issues),
            'by_severity': {severity.value: 0 for severity in ValidationSeverity},
            'by_entity_type': {},
            'by_issue_type': {},
            'critical_issues': []
        }
        
        for issue in issues:
            # Count by severity
            summary['by_severity'][issue.severity.value] += 1
            
            # Count by entity type
            if issue.entity_type not in summary['by_entity_type']:
                summary['by_entity_type'][issue.entity_type] = 0
            summary['by_entity_type'][issue.entity_type] += 1
            
            # Count by issue type
            if issue.issue_type not in summary['by_issue_type']:
                summary['by_issue_type'][issue.issue_type] = 0
            summary['by_issue_type'][issue.issue_type] += 1
            
            # Collect critical issues
            if issue.severity == ValidationSeverity.ERROR:
                summary['critical_issues'].append(issue)
        
        return summary