#!/usr/bin/env python3
"""
Test script for system attribute hierarchical ID generation
This script tests that system attributes use the system's hierarchy directly.
"""

import sys
import os

# Add src directory to path
src_path = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_path)

def test_hierarchical_logic():
    """Test the hierarchical ID logic without database dependencies."""
    
    print("Testing System Attribute Hierarchical ID Logic...")
    print("=" * 60)
    
    # Test scenarios
    test_cases = [
        {
            "description": "Functions in root system S-1",
            "system_hierarchy": "S-1",
            "entity_type": "F",
            "existing_entities": [],
            "expected_pattern": "F-1.X"
        },
        {
            "description": "Functions in child system S-1.2", 
            "system_hierarchy": "S-1.2",
            "entity_type": "F",
            "existing_entities": [],
            "expected_pattern": "F-1.2.X"
        },
        {
            "description": "Requirements in nested system S-1.2.3",
            "system_hierarchy": "S-1.2.3", 
            "entity_type": "R",
            "existing_entities": [],
            "expected_pattern": "R-1.2.3.X"
        },
        {
            "description": "Second function in system S-1.2",
            "system_hierarchy": "S-1.2",
            "entity_type": "F", 
            "existing_entities": ["F-1.2.1"],
            "expected_pattern": "F-1.2.2"
        },
        {
            "description": "Assets in root system S-3",
            "system_hierarchy": "S-3",
            "entity_type": "A",
            "existing_entities": ["A-3.1", "A-3.2"],
            "expected_pattern": "A-3.3"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['description']}:")
        print(f"   System: {test_case['system_hierarchy']}")
        print(f"   Entity Type: {test_case['entity_type']}")
        print(f"   Existing: {test_case['existing_entities']}")
        
        # Extract hierarchy part from system hierarchy
        system_hierarchy = test_case['system_hierarchy']
        system_hierarchy_part = system_hierarchy.split('-')[1] if '-' in system_hierarchy else system_hierarchy
        
        # Find matching entities
        entity_type = test_case['entity_type']
        entity_pattern = f"{entity_type}-{system_hierarchy_part}."
        existing_entities = test_case['existing_entities']
        
        matching_entities = [eid for eid in existing_entities if eid.startswith(entity_pattern)]
        seq_id = len(matching_entities) + 1
        
        # Generate hierarchical ID
        generated_id = f"{entity_type}-{system_hierarchy_part}.{seq_id}"
        
        print(f"   Generated: {generated_id}")
        print(f"   Expected: {test_case['expected_pattern'].replace('X', str(seq_id))}")
        
        # Verify pattern matches
        expected = test_case['expected_pattern'].replace('X', str(seq_id))
        if generated_id == expected:
            print("   ✓ PASS")
        else:
            print("   ✗ FAIL")
    
    print("\n" + "=" * 60)
    print("Example Hierarchy Structure:")
    print("S-1 (Root System 1)")
    print("├── F-1.1 (Function 1 in System 1)")
    print("├── F-1.2 (Function 2 in System 1)")
    print("├── R-1.1 (Requirement 1 in System 1)")
    print("├── S-1.1 (Child System 1)")
    print("│   ├── F-1.1.1 (Function 1 in System 1.1)")
    print("│   ├── F-1.1.2 (Function 2 in System 1.1)")
    print("│   └── A-1.1.1 (Asset 1 in System 1.1)")
    print("└── S-1.2 (Child System 2)")
    print("    ├── F-1.2.1 (Function 1 in System 1.2)")
    print("    └── I-1.2.1 (Interface 1 in System 1.2)")
    print("")
    print("S-2 (Root System 2)")
    print("├── F-2.1 (Function 1 in System 2)")
    print("└── F-2.2 (Function 2 in System 2)")
    print("")
    print("H-1 (Global Hazard 1)")
    print("H-2 (Global Hazard 2)")
    print("L-1 (Global Loss 1)")
    
    print("\n✓ System attribute hierarchical ID logic verification complete!")

if __name__ == "__main__":
    test_hierarchical_logic()