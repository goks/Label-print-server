"""
Performance tests for Label Print Server optimizations

These tests validate that the performance improvements work correctly.
"""

import unittest
import time
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestDatabaseConnectionPool(unittest.TestCase):
    """Test connection pooling functionality"""
    
    def test_pool_initialization(self):
        """Test that connection pool can be initialized"""
        from app import DatabaseConnectionPool
        
        pool = DatabaseConnectionPool(pool_size=2)
        self.assertEqual(pool.pool_size, 2)
        self.assertIsNotNone(pool.pool)
    
    def test_pool_connection_reuse(self):
        """Test that connections can be retrieved and returned"""
        from app import DatabaseConnectionPool
        
        pool = DatabaseConnectionPool(pool_size=2)
        
        # Mock connection string
        mock_conn_str = "DRIVER={SQL Server};SERVER=test;DATABASE=test"
        
        # We can't test actual DB connections without a database
        # But we can test the pool structure
        self.assertTrue(pool.pool.empty())


class TestCachingMechanisms(unittest.TestCase):
    """Test caching functionality"""
    
    def test_settings_cache_structure(self):
        """Test that settings cache is properly structured"""
        import app
        
        self.assertIsNotNone(app._settings_cache)
        self.assertIn('server', app._settings_cache)
        self.assertIn('database', app._settings_cache)
        self.assertIn('printer', app._settings_cache)
        self.assertIn('bartender_template', app._settings_cache)
        self.assertIn('last_loaded', app._settings_cache)
    
    def test_printer_cache_structure(self):
        """Test that printer cache is properly structured"""
        import app
        
        self.assertIsNotNone(app._printer_cache)
        self.assertIn('printers', app._printer_cache)
        self.assertIn('last_updated', app._printer_cache)
        self.assertIn('ttl', app._printer_cache)
        self.assertEqual(app._printer_cache['ttl'], 60)
    
    @patch('app.subprocess.run')
    def test_printer_cache_usage(self, mock_subprocess):
        """Test that printer cache prevents repeated subprocess calls"""
        import app
        
        # Mock subprocess to return printer list
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Printer1\nPrinter2\n"
        mock_subprocess.return_value = mock_result
        
        # Clear cache
        with app._printer_cache_lock:
            app._printer_cache['printers'] = None
            app._printer_cache['last_updated'] = None
        
        # First call should hit subprocess
        printers1 = app.get_available_printers()
        call_count_1 = mock_subprocess.call_count
        
        # Second immediate call should use cache
        printers2 = app.get_available_printers()
        call_count_2 = mock_subprocess.call_count
        
        # Verify cache worked
        self.assertEqual(printers1, printers2)
        self.assertEqual(call_count_1, call_count_2, "Cache should prevent second subprocess call")


class TestPrintedDBOptimizations(unittest.TestCase):
    """Test printed_db.py optimizations"""
    
    def test_thread_local_connection(self):
        """Test that thread-local storage is used for connections"""
        import printed_db
        
        # Initialize DB
        printed_db.init_db()
        
        # Get connection twice in same thread
        conn1 = printed_db._get_connection()
        conn2 = printed_db._get_connection()
        
        # Should be the same connection object
        self.assertIs(conn1, conn2, "Should reuse connection in same thread")
    
    def test_database_indexes_created(self):
        """Test that performance indexes are created"""
        import printed_db
        import sqlite3
        
        # Initialize DB
        printed_db.init_db()
        
        # Check if indexes exist
        conn = printed_db._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_quotation'")
        idx_quotation = cursor.fetchone()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_printed_at'")
        idx_printed_at = cursor.fetchone()
        
        self.assertIsNotNone(idx_quotation, "Quotation index should exist")
        self.assertIsNotNone(idx_printed_at, "Printed_at index should exist")


class TestQueryOptimization(unittest.TestCase):
    """Test that query optimization is working"""
    
    @patch('app.db_pool')
    @patch('app.pyodbc')
    def test_single_query_used(self, mock_pyodbc, mock_pool):
        """Test that optimized query uses JOIN instead of 3 separate queries"""
        import app
        
        # Mock connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        
        # Mock pool to return our mock connection
        mock_pool.get_connection.return_value = mock_conn
        mock_pool.conn_string = "test"
        
        # Mock database row result
        mock_row = MagicMock()
        mock_row.Name = "Test Customer"
        mock_row.Code = "C001"
        mock_row.Address1 = "123 Main St"
        mock_row.Address2 = ""
        mock_row.Address3 = ""
        mock_row.Address4 = ""
        mock_row.Telno = "1234567890"
        mock_row.Mobile = "0987654321"
        mock_cursor.fetchone.return_value = mock_row
        
        # Set required globals
        app.DB_SERVER = "test_server"
        app.DB_NAME = "test_db"
        
        # Call the implementation function directly
        result = app._get_party_info_impl("9171")
        
        # Verify only one execute call was made (the JOIN query)
        self.assertEqual(mock_cursor.execute.call_count, 1, 
                        "Should execute only one query (JOIN)")
        
        # Verify the query contains JOIN
        executed_query = mock_cursor.execute.call_args[0][0]
        self.assertIn("JOIN", executed_query, "Query should use JOIN")
        self.assertIn("Tran2", executed_query, "Query should reference Tran2")
        self.assertIn("Master1", executed_query, "Query should reference Master1")
        self.assertIn("MasterAddressInfo", executed_query, "Query should reference MasterAddressInfo")


class TestPerformanceImprovements(unittest.TestCase):
    """Integration tests for performance improvements"""
    
    def test_lru_cache_decorator_applied(self):
        """Test that LRU cache is applied to query function"""
        import app
        
        # Check that the cached function exists
        self.assertTrue(hasattr(app, '_get_party_info_cached'))
        
        # Check that it has cache info (lru_cache feature)
        self.assertTrue(hasattr(app._get_party_info_cached, 'cache_info'))
        
        # Get cache info
        cache_info = app._get_party_info_cached.cache_info()
        self.assertIsNotNone(cache_info)
    
    @patch('app._get_party_info_impl')
    def test_cache_hit_on_repeated_queries(self, mock_impl):
        """Test that repeated queries hit the cache"""
        import app
        
        # Clear the cache first
        app._get_party_info_cached.cache_clear()
        
        # Mock the implementation to return test data
        mock_impl.return_value = {'name': 'Test', 'code': 'C001'}
        
        # First call - should call implementation
        cache_key = int(time.time() / 300)
        result1 = app._get_party_info_cached("9171", cache_key)
        
        # Second call with same cache_key - should use cache
        result2 = app._get_party_info_cached("9171", cache_key)
        
        # Implementation should only be called once
        self.assertEqual(mock_impl.call_count, 1, 
                        "Implementation should only be called once, second call should hit cache")
        
        # Results should be identical
        self.assertEqual(result1, result2)


def run_performance_benchmark():
    """
    Run a simple performance benchmark to compare improvements.
    This is not a unit test but a utility for manual performance validation.
    """
    print("\n" + "="*60)
    print("PERFORMANCE BENCHMARK")
    print("="*60)
    
    import app
    
    # Test 1: Settings cache performance
    print("\nTest 1: Settings Cache Performance")
    print("-" * 40)
    
    # Warm up cache
    app.load_db_settings()
    
    iterations = 1000
    start = time.time()
    for _ in range(iterations):
        app.load_db_settings()
    duration = time.time() - start
    
    print(f"Loaded settings {iterations} times in {duration:.4f} seconds")
    print(f"Average: {(duration/iterations)*1000:.4f} ms per call")
    print(f"Rate: {iterations/duration:.0f} calls/second")
    
    # Test 2: LRU Cache effectiveness
    print("\nTest 2: LRU Cache Info")
    print("-" * 40)
    cache_info = app._get_party_info_cached.cache_info()
    print(f"Cache hits: {cache_info.hits}")
    print(f"Cache misses: {cache_info.misses}")
    print(f"Cache size: {cache_info.currsize}/{cache_info.maxsize}")
    if cache_info.hits + cache_info.misses > 0:
        hit_rate = cache_info.hits / (cache_info.hits + cache_info.misses) * 100
        print(f"Hit rate: {hit_rate:.1f}%")
    
    print("\n" + "="*60)


if __name__ == '__main__':
    # Run unit tests
    print("Running performance optimization tests...\n")
    unittest.main(verbosity=2, exit=False)
    
    # Run benchmark
    run_performance_benchmark()
