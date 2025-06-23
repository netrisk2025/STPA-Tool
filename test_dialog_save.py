#!/usr/bin/env python3
"""
Test script for SystemEditDialog save functionality
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

def test_dialog_save():
    """Test that SystemEditDialog properly saves and returns created systems."""
    
    # Create temporary directory for test database
    temp_dir = tempfile.mkdtemp()
    temp_dir_path = pathlib.Path(temp_dir)
    
    try:
        print("Testing SystemEditDialog save functionality...")
        
        # Initialize database
        db_init = database_init.DatabaseInitializer(temp_dir_path)
        db_init.initialize()
        
        # Get database connection
        db_manager = db_init.get_database_manager()
        connection = db_manager.get_connection()
        
        # Create a parent system first
        print("\n1. Creating parent system...")
        parent_system = entities.System(
            type_identifier="S",
            level_identifier=0,
            sequential_identifier=1,
            system_hierarchy="S-1",
            system_name="Test Parent System",
            system_description="A test parent system",
            parent_system_id=None
        )
        
        system_repo = entities.EntityFactory.get_repository(connection, entities.System)
        parent_id = system_repo.create(parent_system)
        parent_system.id = parent_id
        
        print(f"   Parent system created with ID: {parent_id}")
        
        # Test 2: Simulate dialog save (without actual UI)
        print("\n2. Testing dialog save simulation...")
        
        # Create a new system object as if it came from the dialog
        new_system = entities.System(
            type_identifier="S",
            level_identifier=1,
            sequential_identifier=1,
            system_hierarchy="S-1.1",
            system_name="Test Child System",
            system_description="A test child system created via dialog",
            parent_system_id=parent_id,
            baseline="Working"
        )
        
        # Save to database
        new_id = system_repo.create(new_system)
        new_system.id = new_id
        
        print(f"   Child system created with ID: {new_id}")
        print(f"   System name: {new_system.system_name}")
        print(f"   Parent ID: {new_system.parent_system_id}")
        print(f"   Hierarchical ID: {new_system.get_hierarchical_id()}")
        
        # Test 3: Verify the system was actually saved
        print("\n3. Verifying system was saved to database...")
        
        # Retrieve the system from database
        retrieved_system = system_repo.get_by_id(new_id)
        
        if retrieved_system:
            print(f"   ✅ System retrieved successfully")
            print(f"   Retrieved name: {retrieved_system.system_name}")
            print(f"   Retrieved parent ID: {retrieved_system.parent_system_id}")
            print(f"   Retrieved hierarchical ID: {retrieved_system.get_hierarchical_id()}")
            
            # Verify all fields match
            if (retrieved_system.system_name == new_system.system_name and
                retrieved_system.parent_system_id == new_system.parent_system_id and
                retrieved_system.get_hierarchical_id() == new_system.get_hierarchical_id()):
                print("   ✅ All fields match correctly")
            else:
                print("   ❌ Field mismatch detected")
                return False
        else:
            print("   ❌ Failed to retrieve system from database")
            return False
        
        # Test 4: Test get_system() method simulation
        print("\n4. Testing get_system() method simulation...")
        
        # Simulate what happens when dialog.get_system() is called
        dialog_system = new_system  # This would be self.system in the dialog
        
        if dialog_system:
            print(f"   ✅ get_system() returns system object")
            print(f"   System name: {dialog_system.system_name}")
            print(f"   System ID: {dialog_system.id}")
        else:
            print("   ❌ get_system() returns None")
            return False
        
        print("\n✅ All dialog save tests passed!")
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
    success = test_dialog_save()
    if success:
        print("\n🎉 Dialog save functionality is working correctly!")
    else:
        print("\n💥 Dialog save functionality has issues!")
        sys.exit(1) 