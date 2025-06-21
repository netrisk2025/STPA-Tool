"""
Performance tests for the STPA Tool.
Tests application performance with large datasets and stress conditions.
"""

import pytest
import tempfile
import time
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import sys
import gc
import os
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.database.init import DatabaseInitializer
from src.database.entities import System, Function, Requirement, EntityFactory
from src.export.json_exporter import JsonExporter
from src.utils.hierarchy import HierarchyManager


@pytest.fixture
def performance_database():
    """Create database for performance testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        db_init = DatabaseInitializer(temp_path)
        db_init.initialize()
        
        yield db_init
        
        db_init.close()


class TestDatabasePerformance:
    """Test database performance with large datasets."""
    
    def test_large_system_creation(self, performance_database):
        """Test creating large number of systems."""
        db_init = performance_database
        connection = db_init.get_database_manager().get_connection()
        system_repo = EntityFactory.get_repository(connection, System)
        
        # Number of systems to create
        num_systems = 1000
        
        start_time = time.time()
        
        # Create systems in batch (without explicit transaction to avoid nesting)
        for i in range(num_systems):
            system = System(
                type_identifier="S",
                level_identifier=0,
                sequential_identifier=i + 1000,
                system_hierarchy=f"S-{i + 1000}",
                system_name=f"Performance Test System {i + 1000}",
                system_description=f"System {i + 1000} created for performance testing"
            )
            system_repo.create(system)
        
        end_time = time.time()
        creation_time = end_time - start_time
        
        print(f"Created {num_systems} systems in {creation_time:.2f} seconds")
        print(f"Average: {creation_time / num_systems * 1000:.2f} ms per system")
        
        # Performance assertion - should create 1000 systems in under 30 seconds
        assert creation_time < 30.0, f"System creation took too long: {creation_time:.2f}s"
        
        # Verify systems were created
        all_systems = system_repo.list()
        assert len(all_systems) >= num_systems
    
    def test_large_query_performance(self, performance_database):
        """Test query performance with large dataset."""
        db_init = performance_database
        connection = db_init.get_database_manager().get_connection()
        system_repo = EntityFactory.get_repository(connection, System)
        
        # Create test data (without explicit transaction to avoid nesting)
        num_systems = 500
        for i in range(num_systems):
            system = System(
                type_identifier="S",
                level_identifier=0,
                sequential_identifier=i + 2000,
                system_hierarchy=f"S-{i + 2000}",
                system_name=f"Query Test System {i + 2000}",
                system_description=f"System for query performance testing"
            )
            system_repo.create(system)
        
        # Test query performance
        start_time = time.time()
        
        # Perform multiple queries
        for _ in range(100):
            systems = system_repo.list()
            assert len(systems) >= num_systems
        
        end_time = time.time()
        query_time = end_time - start_time
        
        print(f"Performed 100 list queries in {query_time:.2f} seconds")
        print(f"Average: {query_time / 100 * 1000:.2f} ms per query")
        
        # Performance assertion - 100 queries should complete in under 10 seconds
        assert query_time < 10.0, f"Query performance too slow: {query_time:.2f}s"
    
    def test_hierarchical_id_performance(self, performance_database):
        """Test hierarchical ID operations performance."""
        # Generate large list of hierarchical IDs
        num_ids = 10000
        hierarchical_ids = []
        
        for i in range(num_ids):
            level = i % 5  # 0-4 levels deep
            if level == 0:
                hierarchical_ids.append(f"S-{i}")
            elif level == 1:
                hierarchical_ids.append(f"S-{i // 5}.{i % 5 + 1}")
            elif level == 2:
                hierarchical_ids.append(f"S-{i // 25}.{(i // 5) % 5 + 1}.{i % 5 + 1}")
            else:
                hierarchical_ids.append(f"S-{i // 125}.{(i // 25) % 5 + 1}.{(i // 5) % 5 + 1}.{i % 5 + 1}")
        
        # Test sorting performance
        start_time = time.time()
        sorted_ids = HierarchyManager.sort_hierarchical_ids(hierarchical_ids)
        end_time = time.time()
        
        sort_time = end_time - start_time
        print(f"Sorted {num_ids} hierarchical IDs in {sort_time:.2f} seconds")
        
        # Performance assertion - sorting should complete in under 5 seconds
        assert sort_time < 5.0, f"ID sorting too slow: {sort_time:.2f}s"
        assert len(sorted_ids) == num_ids
        
        # Test parsing performance
        start_time = time.time()
        
        for hid in hierarchical_ids[:1000]:  # Test subset for parsing
            parsed = HierarchyManager.parse_hierarchical_id(hid)
            assert parsed is not None
        
        end_time = time.time()
        parse_time = end_time - start_time
        
        print(f"Parsed 1000 hierarchical IDs in {parse_time:.2f} seconds")
        
        # Performance assertion - parsing should complete in under 2 seconds
        assert parse_time < 2.0, f"ID parsing too slow: {parse_time:.2f}s"
    
    def test_concurrent_database_access(self, performance_database):
        """Test concurrent database access performance."""
        db_init = performance_database
        connection = db_init.get_database_manager().get_connection()
        system_repo = EntityFactory.get_repository(connection, System)
        
        def create_systems_batch(start_id, count):
            """Create a batch of systems."""
            try:
                for i in range(count):
                    system = System(
                        type_identifier="S",
                        level_identifier=0,
                        sequential_identifier=start_id + i,
                        system_hierarchy=f"S-{start_id + i}",
                        system_name=f"Concurrent Test System {start_id + i}",
                        system_description="System created in concurrent test"
                    )
                    system_repo.create(system)
                return True
            except Exception as e:
                print(f"Error in batch {start_id}: {e}")
                return False
        
        # Test concurrent creation
        num_threads = 5
        systems_per_thread = 100
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = []
            for i in range(num_threads):
                start_id = 3000 + (i * systems_per_thread)
                future = executor.submit(create_systems_batch, start_id, systems_per_thread)
                futures.append(future)
            
            # Wait for all threads to complete
            results = [future.result() for future in futures]
        
        end_time = time.time()
        concurrent_time = end_time - start_time
        
        print(f"Created {num_threads * systems_per_thread} systems concurrently in {concurrent_time:.2f} seconds")
        
        # Verify all operations succeeded
        assert all(results), "Some concurrent operations failed"
        
        # Performance assertion - concurrent creation should be reasonably fast
        assert concurrent_time < 60.0, f"Concurrent creation too slow: {concurrent_time:.2f}s"


class TestMemoryPerformance:
    """Test memory usage and performance."""
    
    @pytest.mark.skipif(not PSUTIL_AVAILABLE, reason="psutil not available")
    def test_memory_usage_large_dataset(self, performance_database):
        """Test memory usage with large dataset."""
        db_init = performance_database
        connection = db_init.get_database_manager().get_connection()
        system_repo = EntityFactory.get_repository(connection, System)
        
        # Get initial memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create large dataset
        num_systems = 2000
        with connection.transaction():
            for i in range(num_systems):
                system = System(
                    type_identifier="S",
                    level_identifier=0,
                    sequential_identifier=i + 4000,
                    system_hierarchy=f"S-{i + 4000}",
                    system_name=f"Memory Test System {i + 4000}",
                    system_description="System created for memory testing" * 10  # Larger description
                )
                system_repo.create(system)
        
        # Load all systems into memory
        all_systems = system_repo.list()
        assert len(all_systems) >= num_systems
        
        # Get peak memory usage
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = peak_memory - initial_memory
        
        print(f"Initial memory: {initial_memory:.1f} MB")
        print(f"Peak memory: {peak_memory:.1f} MB")
        print(f"Memory increase: {memory_increase:.1f} MB")
        print(f"Memory per system: {memory_increase / num_systems * 1024:.1f} KB")
        
        # Memory assertion - should not use excessive memory
        assert memory_increase < 500, f"Memory usage too high: {memory_increase:.1f} MB"
        
        # Cleanup and check memory release
        del all_systems
        gc.collect()
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_released = peak_memory - final_memory
        
        print(f"Final memory: {final_memory:.1f} MB")
        print(f"Memory released: {memory_released:.1f} MB")
    
    @pytest.mark.skipif(not PSUTIL_AVAILABLE, reason="psutil not available")
    def test_memory_leak_detection(self, performance_database):
        """Test for potential memory leaks."""
        db_init = performance_database
        connection = db_init.get_database_manager().get_connection()
        system_repo = EntityFactory.get_repository(connection, System)
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Perform repeated operations that should not leak memory
        for iteration in range(10):
            # Create and delete systems
            systems_to_create = 100
            created_ids = []
            
            for i in range(systems_to_create):
                system = System(
                    type_identifier="S",
                    level_identifier=0,
                    sequential_identifier=5000 + iteration * 1000 + i,
                    system_hierarchy=f"S-{5000 + iteration * 1000 + i}",
                    system_name=f"Leak Test System {i}",
                    system_description="System for memory leak testing"
                )
                system_id = system_repo.create(system)
                created_ids.append(system_id)
            
            # Read all systems
            all_systems = system_repo.list()
            
            # Delete created systems
            for system_id in created_ids:
                system_repo.delete(system_id)
            
            # Force garbage collection
            del all_systems
            gc.collect()
            
            # Check memory every few iterations
            if iteration % 3 == 0:
                current_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_increase = current_memory - initial_memory
                print(f"Iteration {iteration}: Memory increase: {memory_increase:.1f} MB")
                
                # Should not have significant memory growth
                assert memory_increase < 50, f"Potential memory leak detected: {memory_increase:.1f} MB"


class TestExportPerformance:
    """Test export functionality performance."""
    
    def test_json_export_performance(self, performance_database):
        """Test JSON export performance with large dataset."""
        db_init = performance_database
        connection = db_init.get_database_manager().get_connection()
        system_repo = EntityFactory.get_repository(connection, System)
        function_repo = EntityFactory.get_repository(connection, Function)
        
        # Create system with many functions
        test_system = System(
            type_identifier="S",
            level_identifier=0,
            sequential_identifier=6000,
            system_hierarchy="S-6000",
            system_name="Large Export Test System",
            system_description="System with many components for export testing"
        )
        system_id = system_repo.create(test_system)
        
        # Create many functions
        num_functions = 1000
        for i in range(num_functions):
            function = Function(
                type_identifier="F",
                level_identifier=0,
                sequential_identifier=i + 1,
                system_hierarchy=f"F-6000.{i + 1}",
                system_id=system_id,
                function_name=f"Export Function {i + 1}",
                function_description=f"Function {i + 1} for export performance testing"
            )
            function_repo.create(function)
        
        # Test export performance
        exporter = JsonExporter(connection)
        
        start_time = time.time()
        result = exporter.export_system_of_interest(system_id)
        end_time = time.time()
        
        export_time = end_time - start_time
        
        print(f"Exported system with {num_functions} functions in {export_time:.2f} seconds")
        
        # Verify export result
        assert result is not None
        assert 'system' in result
        assert 'functions' in result
        assert len(result['functions']) == num_functions
        
        # Performance assertion - export should complete in reasonable time
        assert export_time < 30.0, f"Export too slow: {export_time:.2f}s"
        
        # Test file export performance
        export_file = db_init.working_directory / "performance_test.json"
        
        start_time = time.time()
        success = exporter.export_to_file(system_id, export_file)
        end_time = time.time()
        
        file_export_time = end_time - start_time
        
        print(f"Exported to file in {file_export_time:.2f} seconds")
        
        assert success is True
        assert export_file.exists()
        
        # Performance assertion
        assert file_export_time < 45.0, f"File export too slow: {file_export_time:.2f}s"
        
        # Check file size
        file_size = export_file.stat().st_size / 1024 / 1024  # MB
        print(f"Export file size: {file_size:.1f} MB")


class TestUIPerformance:
    """Test UI performance (if UI components are available)."""
    
    @pytest.mark.skipif(os.environ.get('QT_QPA_PLATFORM') == 'offscreen', 
                       reason="UI performance tests require display")
    def test_hierarchy_tree_performance(self, performance_database):
        """Test hierarchy tree performance with large dataset."""
        try:
            from PySide6.QtWidgets import QApplication
            from src.ui.hierarchy_tree import HierarchyTreeWidget
        except ImportError:
            pytest.skip("PySide6 not available for UI testing")
        
        app = QApplication.instance()
        if app is None:
            app = QApplication(['test'])
        
        db_init = performance_database
        connection = db_init.get_database_manager().get_connection()
        system_repo = EntityFactory.get_repository(connection, System)
        
        # Create hierarchical system structure
        num_root_systems = 50
        num_child_systems = 5
        
        with connection.transaction():
            for i in range(num_root_systems):
                # Create root system
                root_system = System(
                    type_identifier="S",
                    level_identifier=0,
                    sequential_identifier=i + 7000,
                    system_hierarchy=f"S-{i + 7000}",
                    system_name=f"Root System {i + 7000}",
                    system_description="Root system for UI performance testing"
                )
                root_id = system_repo.create(root_system)
                
                # Create child systems
                for j in range(num_child_systems):
                    child_system = System(
                        type_identifier="S",
                        level_identifier=1,
                        sequential_identifier=j + 1,
                        system_hierarchy=f"S-{i + 7000}.{j + 1}",
                        system_name=f"Child System {i + 7000}.{j + 1}",
                        system_description="Child system for UI performance testing",
                        parent_system_id=root_id
                    )
                    system_repo.create(child_system)
        
        # Test hierarchy tree loading performance
        tree = HierarchyTreeWidget()
        
        start_time = time.time()
        tree.load_systems(connection)
        end_time = time.time()
        
        load_time = end_time - start_time
        total_systems = num_root_systems * (1 + num_child_systems)
        
        print(f"Loaded {total_systems} systems into hierarchy tree in {load_time:.2f} seconds")
        
        # Performance assertion
        assert load_time < 10.0, f"Hierarchy tree loading too slow: {load_time:.2f}s"
        
        # Verify tree structure
        assert tree.topLevelItemCount() >= num_root_systems


class TestStressConditions:
    """Test application behavior under stress conditions."""
    
    def test_rapid_database_operations(self, performance_database):
        """Test rapid database operations."""
        db_init = performance_database
        connection = db_init.get_database_manager().get_connection()
        system_repo = EntityFactory.get_repository(connection, System)
        
        # Perform rapid operations
        num_operations = 500
        operation_times = []
        
        for i in range(num_operations):
            start_time = time.time()
            
            # Create system
            system = System(
                type_identifier="S",
                level_identifier=0,
                sequential_identifier=i + 8000,
                system_hierarchy=f"S-{i + 8000}",
                system_name=f"Stress Test System {i + 8000}",
                system_description="System for stress testing"
            )
            system_id = system_repo.create(system)
            
            # Read system back
            retrieved_system = system_repo.read(system_id)
            assert retrieved_system is not None
            
            # Update system
            retrieved_system.system_description = "Updated description"
            system_repo.update(retrieved_system)
            
            # Delete system
            system_repo.delete(system_id)
            
            end_time = time.time()
            operation_times.append(end_time - start_time)
        
        # Analyze performance
        avg_time = sum(operation_times) / len(operation_times)
        max_time = max(operation_times)
        min_time = min(operation_times)
        
        print(f"Rapid operations - Avg: {avg_time * 1000:.2f}ms, "
              f"Min: {min_time * 1000:.2f}ms, Max: {max_time * 1000:.2f}ms")
        
        # Performance assertions
        assert avg_time < 0.1, f"Average operation time too slow: {avg_time * 1000:.2f}ms"
        assert max_time < 0.5, f"Maximum operation time too slow: {max_time * 1000:.2f}ms"
    
    def test_large_transaction_performance(self, performance_database):
        """Test performance of large transactions."""
        db_init = performance_database
        connection = db_init.get_database_manager().get_connection()
        system_repo = EntityFactory.get_repository(connection, System)
        
        # Large transaction test
        num_systems = 5000
        
        start_time = time.time()
        
        for i in range(num_systems):
            system = System(
                type_identifier="S",
                level_identifier=0,
                sequential_identifier=i + 9000,
                system_hierarchy=f"S-{i + 9000}",
                system_name=f"Large Transaction System {i + 9000}",
                system_description="System created in large transaction"
            )
            system_repo.create(system)
        
        end_time = time.time()
        transaction_time = end_time - start_time
        
        print(f"Large transaction ({num_systems} systems) completed in {transaction_time:.2f} seconds")
        print(f"Rate: {num_systems / transaction_time:.0f} systems per second")
        
        # Performance assertion
        assert transaction_time < 120.0, f"Large transaction too slow: {transaction_time:.2f}s"
        
        # Verify all systems were created
        all_systems = system_repo.list()
        created_systems = [s for s in all_systems if s.sequential_identifier >= 9000]
        assert len(created_systems) >= num_systems


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])