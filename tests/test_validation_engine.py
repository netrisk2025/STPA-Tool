"""
Unit tests for the validation engine.
Tests data validation rules and validation functionality.
"""

import pytest
import tempfile
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.validation.engine import (
    ValidationEngine, ValidationIssue, ValidationSeverity,
    CompletenessValidationRule, LogicalConsistencyValidationRule
)
from src.database.init import DatabaseInitializer
from src.database.entities import System, Function, Requirement, EntityFactory


@pytest.fixture
def validation_database():
    """Create database with test data for validation testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Initialize database
        db_init = DatabaseInitializer(temp_path)
        db_init.initialize()
        db_manager = db_init.get_database_manager()
        connection = db_manager.get_connection()
        
        # Add test data with validation issues
        system_repo = EntityFactory.get_repository(connection, System)
        function_repo = EntityFactory.get_repository(connection, Function)
        requirement_repo = EntityFactory.get_repository(connection, Requirement)
        
        # Create system with missing fields (validation issues)
        incomplete_system = System(
            type_identifier="S",
            level_identifier=0,
            sequential_identifier=200,
            system_hierarchy="S-200",
            system_name="",  # Missing name - should trigger validation issue
            system_description=""  # Missing description - should trigger validation issue
        )
        incomplete_system_id = system_repo.create(incomplete_system)
        
        # Create system with criticality but no security attributes
        critical_system = System(
            type_identifier="S",
            level_identifier=0,
            sequential_identifier=201,
            system_hierarchy="S-201",
            system_name="Critical System",
            system_description="System with criticality issues",
            criticality="Safety Critical",  # Set to critical but no security attributes
            confidentiality=False,  # All security attributes false
            integrity=False,
            availability=False,
            authenticity=False,
            non_repudiation=False,
            assurance=False,
            trustworthy=False,
            privacy=False
        )
        critical_system_id = system_repo.create(critical_system)
        
        # Create function with missing fields
        incomplete_function = Function(
            type_identifier="F",
            level_identifier=0,
            sequential_identifier=1,
            system_hierarchy="F-200.1",
            system_id=incomplete_system_id,
            function_name="",  # Missing name
            function_description=""  # Missing description
        )
        function_repo.create(incomplete_function)
        
        # Create requirement with missing text
        incomplete_requirement = Requirement(
            type_identifier="R",
            level_identifier=0,
            alphanumeric_identifier="REQ-200",
            system_hierarchy="R-200.1",
            system_id=incomplete_system_id,
            requirement_text=""  # Missing requirement text
        )
        requirement_repo.create(incomplete_requirement)
        
        # Create requirements with circular reference
        parent_req = Requirement(
            type_identifier="R",
            level_identifier=0,
            alphanumeric_identifier="REQ-300",
            system_hierarchy="R-300",
            system_id=critical_system_id,
            requirement_text="Parent requirement"
        )
        parent_req_id = requirement_repo.create(parent_req)
        
        child_req = Requirement(
            type_identifier="R",
            level_identifier=1,
            alphanumeric_identifier="REQ-301",
            system_hierarchy="R-301",
            system_id=critical_system_id,
            requirement_text="Child requirement",
            parent_requirement_id=parent_req_id
        )
        child_req_id = requirement_repo.create(child_req)
        
        # Create circular reference by making parent point to child
        parent_req.id = parent_req_id  # Set the ID for update
        parent_req.parent_requirement_id = child_req_id
        requirement_repo.update(parent_req)
        
        yield db_init, incomplete_system_id, critical_system_id
        
        db_init.close()


class TestValidationIssue:
    """Test ValidationIssue data class."""
    
    def test_validation_issue_creation(self):
        """Test creating validation issues."""
        issue = ValidationIssue(
            entity_type="System",
            entity_id=1,
            entity_name="Test System",
            issue_type="missing_name",
            severity=ValidationSeverity.ERROR,
            message="System name is required",
            hierarchical_id="S-1",
            suggestion="Provide a system name"
        )
        
        assert issue.entity_type == "System"
        assert issue.entity_id == 1
        assert issue.entity_name == "Test System"
        assert issue.issue_type == "missing_name"
        assert issue.severity == ValidationSeverity.ERROR
        assert issue.message == "System name is required"
        assert issue.hierarchical_id == "S-1"
        assert issue.suggestion == "Provide a system name"


class TestCompletenessValidationRule:
    """Test completeness validation rule."""
    
    def test_completeness_rule_creation(self):
        """Test creating completeness validation rule."""
        rule = CompletenessValidationRule()
        
        assert rule.name == "Completeness Check"
        assert rule.severity == ValidationSeverity.WARNING
        assert rule.description is not None
    
    def test_validate_incomplete_systems(self, validation_database):
        """Test validation of incomplete systems."""
        db_init, incomplete_system_id, critical_system_id = validation_database
        connection = db_init.get_database_manager().get_connection()
        
        rule = CompletenessValidationRule()
        issues = rule.validate(connection, incomplete_system_id)
        
        # Should find issues for missing name and description
        assert len(issues) >= 2
        
        # Check for missing name issue
        name_issues = [i for i in issues if i.issue_type == "missing_name" and i.entity_type == "System"]
        assert len(name_issues) == 1
        assert name_issues[0].severity == ValidationSeverity.ERROR
        
        # Check for missing description issue
        desc_issues = [i for i in issues if i.issue_type == "missing_description" and i.entity_type == "System"]
        assert len(desc_issues) == 1
        assert desc_issues[0].severity == ValidationSeverity.WARNING
    
    def test_validate_critical_system_without_attributes(self, validation_database):
        """Test validation of critical system without security attributes."""
        db_init, incomplete_system_id, critical_system_id = validation_database
        connection = db_init.get_database_manager().get_connection()
        
        rule = CompletenessValidationRule()
        issues = rule.validate(connection, critical_system_id)
        
        # Should find issue for incomplete criticality
        criticality_issues = [i for i in issues if i.issue_type == "incomplete_criticality"]
        assert len(criticality_issues) == 1
        assert criticality_issues[0].severity == ValidationSeverity.WARNING
        assert "Safety Critical" in criticality_issues[0].message
    
    def test_validate_incomplete_functions(self, validation_database):
        """Test validation of incomplete functions."""
        db_init, incomplete_system_id, critical_system_id = validation_database
        connection = db_init.get_database_manager().get_connection()
        
        rule = CompletenessValidationRule()
        issues = rule.validate(connection, incomplete_system_id)
        
        # Should find issues for function with missing name and description
        function_issues = [i for i in issues if i.entity_type == "Function"]
        assert len(function_issues) >= 2
        
        # Check for missing function name
        name_issues = [i for i in function_issues if i.issue_type == "missing_name"]
        assert len(name_issues) == 1
        assert name_issues[0].severity == ValidationSeverity.ERROR
    
    def test_validate_incomplete_requirements(self, validation_database):
        """Test validation of incomplete requirements."""
        db_init, incomplete_system_id, critical_system_id = validation_database
        connection = db_init.get_database_manager().get_connection()
        
        rule = CompletenessValidationRule()
        issues = rule.validate(connection, incomplete_system_id)
        
        # Should find issues for requirement with missing text
        requirement_issues = [i for i in issues if i.entity_type == "Requirement"]
        assert len(requirement_issues) >= 1
        
        # Check for missing requirement text
        text_issues = [i for i in requirement_issues if i.issue_type == "missing_text"]
        assert len(text_issues) == 1
        assert text_issues[0].severity == ValidationSeverity.ERROR


class TestLogicalConsistencyValidationRule:
    """Test logical consistency validation rule."""
    
    def test_consistency_rule_creation(self):
        """Test creating logical consistency validation rule."""
        rule = LogicalConsistencyValidationRule()
        
        assert rule.name == "Logical Consistency Check"
        assert rule.severity == ValidationSeverity.ERROR
        assert rule.description is not None
    
    def test_validate_circular_requirements(self, validation_database):
        """Test detection of circular requirement references."""
        db_init, incomplete_system_id, critical_system_id = validation_database
        connection = db_init.get_database_manager().get_connection()
        
        rule = LogicalConsistencyValidationRule()
        issues = rule.validate(connection, critical_system_id)
        
        # Should find circular reference issue
        circular_issues = [i for i in issues if i.issue_type == "circular_reference"]
        assert len(circular_issues) >= 1
        assert circular_issues[0].severity == ValidationSeverity.ERROR
        assert "circular reference" in circular_issues[0].message.lower()
    
    def test_validate_system_hierarchy(self, validation_database):
        """Test validation of system hierarchy consistency."""
        db_init, incomplete_system_id, critical_system_id = validation_database
        connection = db_init.get_database_manager().get_connection()
        
        # Create system with invalid hierarchical ID
        system_repo = EntityFactory.get_repository(connection, System)
        invalid_system = System(
            type_identifier="S",
            level_identifier=0,
            sequential_identifier=300,
            system_hierarchy="INVALID-ID",  # Invalid format
            system_name="Invalid Hierarchy System",
            system_description="System with invalid hierarchical ID"
        )
        invalid_system_id = system_repo.create(invalid_system)
        
        rule = LogicalConsistencyValidationRule()
        issues = rule.validate(connection, invalid_system_id)
        
        # Should find hierarchy issue
        hierarchy_issues = [i for i in issues if i.issue_type == "invalid_hierarchy"]
        assert len(hierarchy_issues) == 1
        assert hierarchy_issues[0].severity == ValidationSeverity.ERROR
        assert "Invalid hierarchical ID format" in hierarchy_issues[0].message


class TestValidationEngine:
    """Test main validation engine."""
    
    def test_validation_engine_creation(self, validation_database):
        """Test creating validation engine."""
        db_init, incomplete_system_id, critical_system_id = validation_database
        connection = db_init.get_database_manager().get_connection()
        
        engine = ValidationEngine(connection)
        
        assert engine is not None
        assert len(engine.rules) >= 2  # Should have completeness and consistency rules
        assert engine.connection == connection
    
    def test_validate_system(self, validation_database):
        """Test validating a specific system."""
        db_init, incomplete_system_id, critical_system_id = validation_database
        connection = db_init.get_database_manager().get_connection()
        
        engine = ValidationEngine(connection)
        issues = engine.validate_system(incomplete_system_id)
        
        # Should find multiple issues for incomplete system
        assert len(issues) >= 4  # System name, description, function name, requirement text
        
        # Check that issues are from different rules
        entity_types = set(issue.entity_type for issue in issues)
        assert "System" in entity_types
        assert "Function" in entity_types
        assert "Requirement" in entity_types
    
    def test_validate_all(self, validation_database):
        """Test validating all systems."""
        db_init, incomplete_system_id, critical_system_id = validation_database
        connection = db_init.get_database_manager().get_connection()
        
        engine = ValidationEngine(connection)
        issues = engine.validate_all()
        
        # Should find issues across all systems
        assert len(issues) >= 5  # Multiple systems with various issues
        
        # Should include issues from different systems
        system_ids = set(issue.entity_id for issue in issues if issue.entity_id)
        assert len(system_ids) >= 2
    
    def test_add_custom_rule(self, validation_database):
        """Test adding a custom validation rule."""
        db_init, incomplete_system_id, critical_system_id = validation_database
        connection = db_init.get_database_manager().get_connection()
        
        # Create custom rule
        class CustomRule(CompletenessValidationRule):
            def __init__(self):
                super().__init__()
                self.name = "Custom Test Rule"
            
            def validate(self, connection, system_id=None):
                return [ValidationIssue(
                    entity_type="Test",
                    entity_id=None,
                    entity_name="Custom",
                    issue_type="custom_issue",
                    severity=ValidationSeverity.INFO,
                    message="Custom rule executed"
                )]
        
        engine = ValidationEngine(connection)
        initial_count = len(engine.rules)
        
        engine.add_rule(CustomRule())
        
        assert len(engine.rules) == initial_count + 1
        
        # Validate and check for custom issue
        issues = engine.validate_system(incomplete_system_id)
        custom_issues = [i for i in issues if i.issue_type == "custom_issue"]
        assert len(custom_issues) == 1
    
    def test_get_validation_summary(self, validation_database):
        """Test generating validation summary."""
        db_init, incomplete_system_id, critical_system_id = validation_database
        connection = db_init.get_database_manager().get_connection()
        
        engine = ValidationEngine(connection)
        issues = engine.validate_system(incomplete_system_id)
        
        summary = engine.get_validation_summary(issues)
        
        assert 'total_issues' in summary
        assert 'by_severity' in summary
        assert 'by_entity_type' in summary
        assert 'by_issue_type' in summary
        assert 'critical_issues' in summary
        
        assert summary['total_issues'] == len(issues)
        assert summary['total_issues'] > 0
        
        # Check severity breakdown
        error_count = summary['by_severity'].get('error', 0)
        warning_count = summary['by_severity'].get('warning', 0)
        assert error_count > 0  # Should have errors for missing required fields
        assert warning_count >= 0  # May have warnings
        
        # Check entity type breakdown
        assert 'System' in summary['by_entity_type']
        assert summary['by_entity_type']['System'] > 0
        
        # Check critical issues
        critical_issues = summary['critical_issues']
        assert len(critical_issues) == error_count
        assert all(issue.severity == ValidationSeverity.ERROR for issue in critical_issues)


class TestValidationEngineErrorHandling:
    """Test validation engine error handling."""
    
    def test_validation_with_database_error(self, validation_database):
        """Test validation engine behavior with database errors."""
        from unittest.mock import Mock, patch
        
        db_init, incomplete_system_id, critical_system_id = validation_database
        connection = db_init.get_database_manager().get_connection()
        
        # Create a validation rule that will definitely throw an exception
        class FailingValidationRule(CompletenessValidationRule):
            def validate(self, connection, system_id=None):
                raise Exception("Database connection failed during validation")
        
        engine = ValidationEngine(connection)
        # Replace one of the rules with our failing rule
        engine.rules[0] = FailingValidationRule()
        
        # Should handle database errors gracefully
        issues = engine.validate_system(incomplete_system_id)
        
        # Should return at least one error issue about the validation failure
        error_issues = [i for i in issues if i.issue_type == "rule_error"]
        assert len(error_issues) >= 1
        
        # Verify the error message contains information about the database failure
        assert any("Database connection failed during validation" in issue.message for issue in error_issues)
    
    def test_validation_with_invalid_system_id(self, validation_database):
        """Test validation with non-existent system ID."""
        db_init, incomplete_system_id, critical_system_id = validation_database
        connection = db_init.get_database_manager().get_connection()
        
        engine = ValidationEngine(connection)
        
        # Validate non-existent system
        issues = engine.validate_system(999999)
        
        # Should return empty list or handle gracefully
        assert isinstance(issues, list)
        # May be empty or contain rule errors depending on implementation
    
    def test_empty_database_validation(self):
        """Test validation with empty database."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Initialize empty database
            db_init = DatabaseInitializer(temp_path)
            db_init.initialize()
            connection = db_init.get_database_manager().get_connection()
            
            # Clear all example data
            connection.execute("DELETE FROM systems")
            connection.execute("DELETE FROM functions")
            connection.execute("DELETE FROM requirements")
            
            try:
                engine = ValidationEngine(connection)
                issues = engine.validate_all()
                
                # Should handle empty database gracefully
                assert isinstance(issues, list)
                assert len(issues) == 0  # No data, no issues
                
            finally:
                db_init.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])