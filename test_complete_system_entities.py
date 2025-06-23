#!/usr/bin/env python3
"""
Comprehensive test for system-aware entity management
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

def test_complete_system_entities():
    """Test that all entity types work with system filtering and association."""
    
    # Create temporary directory for test database
    temp_dir = tempfile.mkdtemp()
    temp_dir_path = pathlib.Path(temp_dir)
    
    try:
        print("Testing complete system-aware entity management...")
        
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
        
        # Test 2: Test all entity types with system filtering
        print("\n2. Testing all entity types...")
        
        # First create some assets and environments for Hazards and Losses
        print("\n   Creating supporting entities...")
        
        # Create assets for the systems (and store for reuse)
        asset_repo = entities.EntityFactory.get_repository(connection, entities.Asset)
        assets_by_system = {}
        for sys_id, sys_label in [(root_id, "Root"), (child_id, "Child")]:
            asset = entities.Asset(
                type_identifier="A",
                level_identifier=0,
                sequential_identifier=1,
                system_hierarchy=f"S-{sys_id}.A-1",
                asset_name=f"{sys_label} Asset",
                asset_description=f"Asset for {sys_label.lower()} system",
                system_id=sys_id
            )
            asset_id = asset_repo.create(asset)
            assets_by_system[sys_id] = asset_id
        
        # Create environments for the systems (and store for reuse)
        environment_repo = entities.EntityFactory.get_repository(connection, entities.Environment)
        envs_by_system = {}
        for sys_id, sys_label in [(root_id, "Root"), (child_id, "Child")]:
            env = entities.Environment(
                type_identifier="E",
                level_identifier=0,
                sequential_identifier=1,
                system_hierarchy=f"S-{sys_id}.E-1",
                environment_name=f"{sys_label} Environment",
                environment_description=f"Environment for {sys_label.lower()} system",
                system_id=sys_id
            )
            env_id = environment_repo.create(env)
            envs_by_system[sys_id] = env_id
        
        print(f"     Created assets: Root={assets_by_system[root_id]}, Child={assets_by_system[child_id]}")
        print(f"     Created environments: Root={envs_by_system[root_id]}, Child={envs_by_system[child_id]}")
        
        entity_tests = [
            ("Interface", entities.Interface, "interface_name", "interface_description"),
            ("ControlStructure", entities.ControlStructure, "structure_name", "structure_description"),
            ("Controller", entities.Controller, "controller_name", "controller_description"),
        ]
        
        for entity_name, entity_class, name_field, desc_field in entity_tests:
            print(f"\n   Testing {entity_name}...")
            
            # Create repository
            entity_repo = entities.EntityFactory.get_repository(connection, entity_class)
            
            # Create entity for root system
            root_entity_data = {
                'type_identifier': entity_name[0],
                'level_identifier': 0,
                'sequential_identifier': 1,
                'system_hierarchy': f"S-1.{entity_name[0]}-1",
                'system_id': root_id,
                'baseline': 'Working'
            }
            
            # Add entity-specific fields
            if entity_name == "Interface":
                root_entity_data.update({
                    'interface_name': f"Root {entity_name}",
                    'interface_description': f"Root {entity_name} description"
                })
            elif entity_name == "ControlStructure":
                root_entity_data.update({
                    'structure_name': f"Root {entity_name}",
                    'structure_description': f"Root {entity_name} description"
                })
            elif entity_name == "Controller":
                root_entity_data.update({
                    'controller_name': f"Root {entity_name}",
                    'controller_description': f"Root {entity_name} description",
                    'short_text_identifier': f"R{entity_name[0]}"
                })
            
            root_entity = entity_class(**root_entity_data)
            root_entity_id = entity_repo.create(root_entity)
            
            # Create entity for child system
            child_entity_data = {
                'type_identifier': entity_name[0],
                'level_identifier': 0,
                'sequential_identifier': 1,
                'system_hierarchy': f"S-1.1.{entity_name[0]}-1",
                'system_id': child_id,
                'baseline': 'Working'
            }
            
            # Add entity-specific fields
            if entity_name == "Interface":
                child_entity_data.update({
                    'interface_name': f"Child {entity_name}",
                    'interface_description': f"Child {entity_name} description"
                })
            elif entity_name == "ControlStructure":
                child_entity_data.update({
                    'structure_name': f"Child {entity_name}",
                    'structure_description': f"Child {entity_name} description"
                })
            elif entity_name == "Controller":
                child_entity_data.update({
                    'controller_name': f"Child {entity_name}",
                    'controller_description': f"Child {entity_name} description",
                    'short_text_identifier': f"C{entity_name[0]}"
                })
            
            child_entity = entity_class(**child_entity_data)
            child_entity_id = entity_repo.create(child_entity)
            
            print(f"     Created root {entity_name} with ID: {root_entity_id}")
            print(f"     Created child {entity_name} with ID: {child_entity_id}")
            
            # Test system filtering
            root_entities = entity_repo.find_by_system_id(root_id)
            child_entities = entity_repo.find_by_system_id(child_id)
            all_entities = entity_repo.list()
            
            print(f"     Root system {entity_name}s: {len(root_entities)}")
            print(f"     Child system {entity_name}s: {len(child_entities)}")
            print(f"     All {entity_name}s: {len(all_entities)}")
            
            # Verify filtering works
            if len(root_entities) == 1 and len(child_entities) == 1 and len(all_entities) == 2:
                print(f"     ✅ {entity_name} filtering works correctly")
            else:
                print(f"     ❌ {entity_name} filtering failed")
                return False
        
        # Test Asset separately (already created above)
        print(f"\n   Testing Asset...")
        asset_repo = entities.EntityFactory.get_repository(connection, entities.Asset)
        root_assets = asset_repo.find_by_system_id(root_id)
        child_assets = asset_repo.find_by_system_id(child_id)
        all_assets = asset_repo.list()
        print(f"     Root system Assets: {len(root_assets)}")
        print(f"     Child system Assets: {len(child_assets)}")
        print(f"     All Assets: {len(all_assets)}")
        if len(root_assets) == 1 and len(child_assets) == 1 and len(all_assets) == 2:
            print(f"     ✅ Asset filtering works correctly")
        else:
            print(f"     ❌ Asset filtering failed")
            return False
        
        # Test Hazards (associated with environments)
        print(f"\n   Testing Hazard...")
        hazard_repo = entities.EntityFactory.get_repository(connection, entities.Hazard)
        
        root_hazard = entities.Hazard(
            type_identifier="H",
            level_identifier=0,
            sequential_identifier=1,
            system_hierarchy="S-1.H-1",
            h_name="Root Hazard",
            h_description="Hazard for root system",
            environment_id=envs_by_system[root_id]
        )
        root_hazard_id = hazard_repo.create(root_hazard)
        
        child_hazard = entities.Hazard(
            type_identifier="H",
            level_identifier=0,
            sequential_identifier=1,
            system_hierarchy="S-1.1.H-1",
            h_name="Child Hazard",
            h_description="Hazard for child system",
            environment_id=envs_by_system[child_id]
        )
        child_hazard_id = hazard_repo.create(child_hazard)
        
        print(f"     Created root Hazard with ID: {root_hazard_id}")
        print(f"     Created child Hazard with ID: {child_hazard_id}")
        
        # For hazards, we need to filter by environment's system_id
        root_hazards = [h for h in hazard_repo.list() if h.environment_id == envs_by_system[root_id]]
        child_hazards = [h for h in hazard_repo.list() if h.environment_id == envs_by_system[child_id]]
        all_hazards = hazard_repo.list()
        
        print(f"     Root system Hazards: {len(root_hazards)}")
        print(f"     Child system Hazards: {len(child_hazards)}")
        print(f"     All Hazards: {len(all_hazards)}")
        
        if len(root_hazards) == 1 and len(child_hazards) == 1 and len(all_hazards) == 2:
            print(f"     ✅ Hazard filtering works correctly")
        else:
            print(f"     ❌ Hazard filtering failed")
            return False
        
        # Test Losses (associated with assets)
        print(f"\n   Testing Loss...")
        loss_repo = entities.EntityFactory.get_repository(connection, entities.Loss)
        
        root_loss = entities.Loss(
            type_identifier="L",
            level_identifier=0,
            sequential_identifier=1,
            system_hierarchy="S-1.L-1",
            l_name="Root Loss",
            l_description="Loss for root system",
            loss_description="Loss description for root system",
            asset_id=assets_by_system[root_id]
        )
        root_loss_id = loss_repo.create(root_loss)
        
        child_loss = entities.Loss(
            type_identifier="L",
            level_identifier=0,
            sequential_identifier=1,
            system_hierarchy="S-1.1.L-1",
            l_name="Child Loss",
            l_description="Loss for child system",
            loss_description="Loss description for child system",
            asset_id=assets_by_system[child_id]
        )
        child_loss_id = loss_repo.create(child_loss)
        
        print(f"     Created root Loss with ID: {root_loss_id}")
        print(f"     Created child Loss with ID: {child_loss_id}")
        
        # For losses, we need to filter by asset's system_id
        root_losses = [l for l in loss_repo.list() if l.asset_id == assets_by_system[root_id]]
        child_losses = [l for l in loss_repo.list() if l.asset_id == assets_by_system[child_id]]
        all_losses = loss_repo.list()
        
        print(f"     Root system Losses: {len(root_losses)}")
        print(f"     Child system Losses: {len(child_losses)}")
        print(f"     All Losses: {len(all_losses)}")
        
        if len(root_losses) == 1 and len(child_losses) == 1 and len(all_losses) == 2:
            print(f"     ✅ Loss filtering works correctly")
        else:
            print(f"     ❌ Loss filtering failed")
            return False
        
        print("\n✅ All entity types work with system filtering!")
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
    success = test_complete_system_entities()
    if success:
        print("\n🎉 Complete system-aware entity management is working correctly!")
    else:
        print("\n💥 Complete system-aware entity management has issues!")
        sys.exit(1) 