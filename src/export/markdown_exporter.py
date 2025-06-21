"""
Markdown export functionality for STPA Tool
Exports System of Interest data as formatted Markdown documents.
"""

from typing import List, Optional
from datetime import datetime

from ..database.entities import (
    System, Function, Interface, Asset, Requirement,
    EntityRepository
)
from ..database.connection import DatabaseConnection
from ..log_config.config import get_logger

logger = get_logger(__name__)


class MarkdownExporter:
    """Handles Markdown export of STPA Tool data."""
    
    def __init__(self, db_connection: DatabaseConnection):
        self.db_connection = db_connection
        # Create repositories for needed entity types
        self.repositories = {
            'System': EntityRepository(db_connection, System),
            'Function': EntityRepository(db_connection, Function),
            'Interface': EntityRepository(db_connection, Interface),
            'Asset': EntityRepository(db_connection, Asset),
            'Requirement': EntityRepository(db_connection, Requirement)
        }
    
    def export_system_specification(self, system_id: int) -> Optional[str]:
        """
        Export system specification as Markdown.
        
        Args:
            system_id: The ID of the system to export
        
        Returns:
            Markdown formatted system specification
        """
        logger.info(f"Generating system specification for system ID {system_id}")
        
        try:
            # Get the main system
            system = self.repositories['System'].get_by_id(system_id)
            if not system:
                logger.warning(f"System with ID {system_id} not found")
                return None
            
            # Build the specification document
            lines = []
            
            # Title
            lines.append(f"# {system.system_name} Specification")
            lines.append("")
            
            # Metadata
            lines.append("## Document Information")
            lines.append("")
            lines.append(f"- **System ID:** {system.get_hierarchical_id()}")
            lines.append(f"- **System Name:** {system.system_name}")
            lines.append(f"- **Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append(f"- **Baseline:** {system.baseline}")
            lines.append("")
            
            # System Description
            if system.system_description:
                lines.append("## System Description")
                lines.append("")
                lines.append(system.system_description)
                lines.append("")
            
            # System Requirements
            requirements = self.repositories['Requirement'].find_by_system_id(system.id)
            if requirements:
                lines.append("## Requirements")
                lines.append("")
                
                # Sort requirements by hierarchical ID
                requirements.sort(key=lambda r: r.get_hierarchical_id())
                
                for req in requirements:
                    lines.append(f"### {req.get_hierarchical_id()}")
                    lines.append("")
                    lines.append(req.requirement_text)
                    lines.append("")
                    
                    # Add verification information if available
                    if req.verification_method and req.verification_method != "Not Specified":
                        lines.append(f"**Verification Method:** {req.verification_method}")
                        lines.append("")
                    
                    if req.verification_statement:
                        lines.append(f"**Verification Statement:** {req.verification_statement}")
                        lines.append("")
            
            # Critical Attributes Summary
            if self._has_critical_attributes(system):
                lines.append("## Critical Attributes")
                lines.append("")
                lines.append(f"- **Criticality:** {system.criticality}")
                
                critical_attrs = []
                if getattr(system, 'confidentiality', False):
                    critical_attrs.append("Confidentiality")
                if getattr(system, 'integrity', False):
                    critical_attrs.append("Integrity")
                if getattr(system, 'availability', False):
                    critical_attrs.append("Availability")
                if getattr(system, 'authenticity', False):
                    critical_attrs.append("Authenticity")
                if getattr(system, 'non_repudiation', False):
                    critical_attrs.append("Non-Repudiation")
                if getattr(system, 'assurance', False):
                    critical_attrs.append("Assurance")
                if getattr(system, 'trustworthy', False):
                    critical_attrs.append("Trustworthy")
                if getattr(system, 'privacy', False):
                    critical_attrs.append("Privacy")
                
                if critical_attrs:
                    lines.append(f"- **Security/Safety Attributes:** {', '.join(critical_attrs)}")
                
                lines.append("")
            
            result = "\n".join(lines)
            logger.info(f"System specification generated successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error generating system specification: {str(e)}")
            raise
    
    def export_system_description(self, system_id: int) -> Optional[str]:
        """
        Export comprehensive system description as Markdown.
        
        Args:
            system_id: The ID of the system to export
        
        Returns:
            Markdown formatted system description
        """
        logger.info(f"Generating system description for system ID {system_id}")
        
        try:
            # Get the main system
            system = self.repositories['System'].get_by_id(system_id)
            if not system:
                logger.warning(f"System with ID {system_id} not found")
                return None
            
            lines = []
            
            # Title
            lines.append(f"# {system.system_name} Description")
            lines.append("")
            
            # System Overview
            lines.append("## System Overview")
            lines.append("")
            if system.system_description:
                lines.append(system.system_description)
            else:
                lines.append("*No description provided*")
            lines.append("")
            
            # System Functions
            functions = self.repositories['Function'].find_by_system_id(system.id)
            if functions:
                lines.append("## System Functions")
                lines.append("")
                
                functions.sort(key=lambda f: f.get_hierarchical_id())
                
                for func in functions:
                    lines.append(f"### {func.get_hierarchical_id()} - {func.function_name}")
                    lines.append("")
                    if func.function_description:
                        lines.append(func.function_description)
                    else:
                        lines.append("*No description provided*")
                    lines.append("")
            
            # System Interfaces
            interfaces = self.repositories['Interface'].find_by_system_id(system.id)
            if interfaces:
                lines.append("## System Interfaces")
                lines.append("")
                
                interfaces.sort(key=lambda i: i.get_hierarchical_id())
                
                for intf in interfaces:
                    lines.append(f"### {intf.get_hierarchical_id()} - {intf.interface_name}")
                    lines.append("")
                    if intf.interface_description:
                        lines.append(intf.interface_description)
                    else:
                        lines.append("*No description provided*")
                    lines.append("")
            
            # Child Systems
            child_systems = self._get_child_systems(system_id)
            if child_systems:
                lines.append("## Child Systems")
                lines.append("")
                
                child_systems.sort(key=lambda s: s.hierarchical_id)
                
                for child in child_systems:
                    lines.append(f"### {child.hierarchical_id} - {child.system_name}")
                    lines.append("")
                    if child.system_description:
                        lines.append(child.system_description)
                    else:
                        lines.append("*No description provided*")
                    lines.append("")
            
            # Assets
            assets = self.repositories['Asset'].find_by_system_id(system.id)
            if assets:
                lines.append("## System Assets")
                lines.append("")
                
                assets.sort(key=lambda a: a.get_hierarchical_id())
                
                for asset in assets:
                    lines.append(f"### {asset.get_hierarchical_id()} - {asset.asset_name}")
                    lines.append("")
                    if asset.asset_description:
                        lines.append(asset.asset_description)
                    else:
                        lines.append("*No description provided*")
                    lines.append("")
            
            result = "\n".join(lines)
            logger.info(f"System description generated successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error generating system description: {str(e)}")
            raise
    
    def _get_child_systems(self, parent_system_id: int) -> List[System]:
        """Get immediate child systems of a parent system."""
        with self.db_connection.get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM systems WHERE parent_system_id = ? AND baseline = 'Working'",
                (parent_system_id,)
            )
            
            child_systems = []
            for row in cursor.fetchall():
                system = System()
                # Populate system from database row
                columns = [desc[0] for desc in cursor.description]
                for i, column in enumerate(columns):
                    if hasattr(system, column):
                        setattr(system, column, row[i])
                child_systems.append(system)
            
            return child_systems
    
    def _has_critical_attributes(self, system: System) -> bool:
        """Check if system has any critical attributes set."""
        critical_attrs = [
            'confidentiality', 'integrity', 'availability', 'authenticity',
            'non_repudiation', 'assurance', 'trustworthy', 'privacy'
        ]
        
        for attr in critical_attrs:
            if getattr(system, attr, False):
                return True
        
        return system.criticality != "Non-Critical"
    
    def export_to_file(self, system_id: int, file_path: str, export_type: str = "specification") -> bool:
        """
        Export system data to Markdown file.
        
        Args:
            system_id: The ID of the system to export
            file_path: Path where to save the Markdown file
            export_type: Type of export ("specification" or "description")
        
        Returns:
            True if export successful, False otherwise
        """
        try:
            if export_type == "specification":
                content = self.export_system_specification(system_id)
            elif export_type == "description":
                content = self.export_system_description(system_id)
            else:
                raise ValueError(f"Unknown export type: {export_type}")
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"Markdown export saved to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export to file {file_path}: {str(e)}")
            return False
    
    def export_specification_to_file(self, system_id: int, file_path: str) -> bool:
        """
        Export system specification to Markdown file.
        
        Args:
            system_id: The ID of the system to export
            file_path: Path where to save the Markdown file
        
        Returns:
            True if export successful, False otherwise
        """
        return self.export_to_file(system_id, file_path, "specification")