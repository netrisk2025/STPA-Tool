#!/usr/bin/env python3
"""
Test script for system filtering functionality
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

def test_system_filtering():
    """Test that entity widgets properly filter by system."""
    
    # Create temporary directory for test database
    temp_dir = tempfile.mkdtemp()
    temp_dir_path = pathlib.Path(temp_dir)
    
    try:
        print("Testing system filtering functionality...")
        
        # Initialize database
        db_init = database_init.DatabaseInitializer(temp_dir_path)
        db_init.initialize()
        
        # Get database connection
        db_manager = db_init.get_database_manager()
        connection = db_manager.get_connection()
        
        # Create test systems
        print("\n1. Creating test systems...")
        system_repo = entities.EntityFactory.get_repository(connection, entities.System)
        
        # Create root system
        root_system = entities.System(
            type_identifier="S",
            level_identifier=0,
            sequential_identifier=1,
            system_hierarchy="S-1",
            system_name="Test Root System",
            system_description="A test root system",
            parent_system_id=None
        )
        root_id = system_repo.create(root_system)
        root_system.id = root_id
        
        # Create child system
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
        
        print(f"   Root system created with ID: {root_id}")
        print(f"   Child system created with ID: {child_id}")
        
        # Test 2: Create entities for different systems
        print("\n2. Creating test entities...")
        
        # Create interface for root system
        interface_repo = entities.EntityFactory.get_repository(connection, entities.Interface)
        root_interface = entities.Interface(
            type_identifier="I",
            level_identifier=0,
            sequential_identifier=1,
            system_hierarchy="S-1.I-1",
            interface_name="Root Interface",
            interface_description="Interface for root system",
            system_id=root_id
        )
        root_interface_id = interface_repo.create(root_interface)
        
        # Create interface for child system
        child_interface = entities.Interface(
            type_identifier="I",
            level_identifier=0,
            sequential_identifier=1,
            system_hierarchy="S-1.1.I-1",
            interface_name="Child Interface",
            interface_description="Interface for child system",
            system_id=child_id
        )
        child_interface_id = interface_repo.create(child_interface)
        
        print(f"   Root interface created with ID: {root_interface_id}")
        print(f"   Child interface created with ID: {child_interface_id}")
        
        # Test 3: Test system filtering
        print("\n3. Testing system filtering...")
        
        # Test filtering by root system
        root_interfaces = interface_repo.find_by_system_id(root_id)
        print(f"   Interfaces for root system ({root_id}): {len(root_interfaces)}")
        for interface in root_interfaces:
            print(f"     - {interface.interface_name} (ID: {interface.id})")
        
        # Test filtering by child system
        child_interfaces = interface_repo.find_by_system_id(child_id)
        print(f"   Interfaces for child system ({child_id}): {len(child_interfaces)}")
        for interface in child_interfaces:
            print(f"     - {interface.interface_name} (ID: {interface.id})")
        
        # Test 4: Verify filtering works correctly
        print("\n4. Verifying filtering results...")
        
        if len(root_interfaces) == 1 and root_interfaces[0].interface_name == "Root Interface":
            print("   ✅ Root system filtering works correctly")
        else:
            print("   ❌ Root system filtering failed")
            return False
        
        if len(child_interfaces) == 1 and child_interfaces[0].interface_name == "Child Interface":
            print("   ✅ Child system filtering works correctly")
        else:
            print("   ❌ Child system filtering failed")
            return False
        
        # Test 5: Test with no system filter (should show all)
        print("\n5. Testing no system filter...")
        all_interfaces = interface_repo.list()
        print(f"   All interfaces: {len(all_interfaces)}")
        for interface in all_interfaces:
            print(f"     - {interface.interface_name} (System: {interface.system_id})")
        
        if len(all_interfaces) == 2:
            print("   ✅ No filter shows all interfaces")
        else:
            print("   ❌ No filter failed")
            return False
        
        print("\n✅ All system filtering tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Clean up
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory: {temp_dir}")

if __name__ == "__main__":
    success = test_system_filtering()
    if success:
        print("\n🎉 System filtering functionality is working correctly!")
    else:
        print("\n💥 System filtering functionality has issues!")
        sys.exit(1) 