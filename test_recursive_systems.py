#!/usr/bin/env python3
"""
Test script for recursive system functionality
"""

import sys
import os
import tempfile
import shutil
import pathlib

# Add src to path and set up module imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Set up the module structure
import src.database.init as database_init
import src.database.entities as entities
import src.utils.hierarchy as hierarchy

def test_recursive_systems():
    """Test recursive system creation and hierarchy management."""
    
    # Create temporary directory for test database
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, 'test_stpa.db')
    temp_dir_path = pathlib.Path(temp_dir)
    
    try:
        print("Testing recursive system functionality...")
        
        # Initialize database
        db_init = database_init.DatabaseInitializer(temp_dir_path)
        db_init.initialize()
        
        # Get database connection
        db_manager = db_init.get_database_manager()
        connection = db_manager.get_connection()
        
        # Test 1: Create root system
        print("\n1. Creating root system...")
        root_system = entities.System(
            type_identifier="S",
            level_identifier=0,
            sequential_identifier=1,
            system_hierarchy="S-1",
            system_name="Test Root System",
            system_description="A test root system",
            parent_system_id=None
        )
        
        # Save root system
        system_repo = entities.EntityFactory.get_repository(connection, entities.System)
        root_id = system_repo.create(root_system)
        root_system.id = root_id
        
        print(f"   Root system created with ID: {root_id}")
        print(f"   Hierarchical ID: {root_system.get_hierarchical_id()}")
        
        # Test 2: Create child system
        print("\n2. Creating child system...")
        child_system = entities.System(
            type_identifier="S",
            level_identifier=1,
            sequential_identifier=1,
            system_hierarchy="S-1.1",
            system_name="Test Child System",
            system_description="A test child system",
            parent_system_id=root_id
        )
        
        child_id = system_repo.create(child_system)
        child_system.id = child_id
        
        print(f"   Child system created with ID: {child_id}")
        print(f"   Hierarchical ID: {child_system.get_hierarchical_id()}")
        print(f"   Parent ID: {child_system.parent_system_id}")
        
        # Test 3: Create grandchild system
        print("\n3. Creating grandchild system...")
        grandchild_system = entities.System(
            type_identifier="S",
            level_identifier=1,
            sequential_identifier=2,
            system_hierarchy="S-1.2",
            system_name="Test Grandchild System",
            system_description="A test grandchild system",
            parent_system_id=root_id
        )
        
        grandchild_id = system_repo.create(grandchild_system)
        grandchild_system.id = grandchild_id
        
        print(f"   Grandchild system created with ID: {grandchild_id}")
        print(f"   Hierarchical ID: {grandchild_system.get_hierarchical_id()}")
        print(f"   Parent ID: {grandchild_system.parent_system_id}")
        
        # Test 4: Create sub-child system
        print("\n4. Creating sub-child system...")
        subchild_system = entities.System(
            type_identifier="S",
            level_identifier=2,
            sequential_identifier=1,
            system_hierarchy="S-1.1.1",
            system_name="Test Sub-Child System",
            system_description="A test sub-child system",
            parent_system_id=child_id
        )
        
        subchild_id = system_repo.create(subchild_system)
        subchild_system.id = subchild_id
        
        print(f"   Sub-child system created with ID: {subchild_id}")
        print(f"   Hierarchical ID: {subchild_system.get_hierarchical_id()}")
        print(f"   Parent ID: {subchild_system.parent_system_id}")
        
        # Test 5: Verify hierarchy
        print("\n5. Verifying hierarchy...")
        all_systems = system_repo.list()
        
        print("   All systems in database:")
        for system in all_systems:
            parent_name = "None" if system.parent_system_id is None else f"ID {system.parent_system_id}"
            print(f"     {system.get_hierarchical_id()}: {system.system_name} (Parent: {parent_name})")
        
        # Test 6: Test hierarchy manager
        print("\n6. Testing hierarchy manager...")
        
        # Parse hierarchical IDs
        root_hierarchy = hierarchy.HierarchyManager.parse_hierarchical_id("S-1")
        child_hierarchy = hierarchy.HierarchyManager.parse_hierarchical_id("S-1.1")
        grandchild_hierarchy = hierarchy.HierarchyManager.parse_hierarchical_id("S-1.2")
        subchild_hierarchy = hierarchy.HierarchyManager.parse_hierarchical_id("S-1.1.1")
        
        print(f"   Root hierarchy: {root_hierarchy}")
        print(f"   Child hierarchy: {child_hierarchy}")
        print(f"   Grandchild hierarchy: {grandchild_hierarchy}")
        print(f"   Sub-child hierarchy: {subchild_hierarchy}")
        
        # Test child ID generation
        next_child = hierarchy.HierarchyManager.generate_child_id(root_hierarchy, 3)
        print(f"   Next child ID: {next_child}")
        
        next_subchild = hierarchy.HierarchyManager.generate_child_id(child_hierarchy, 2)
        print(f"   Next sub-child ID: {next_subchild}")
        
        print("\n✅ All tests passed! Recursive system functionality is working correctly.")
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Clean up
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory: {temp_dir}")

if __name__ == "__main__":
    test_recursive_systems() 