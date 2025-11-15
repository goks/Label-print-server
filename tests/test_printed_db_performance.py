"""
Performance unit tests for printed_db.py optimizations

These tests can run on any platform.
"""

import unittest
import time
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import printed_db


class TestPrintedDBOptimizations(unittest.TestCase):
    """Test printed_db.py optimizations"""
    
    @classmethod
    def setUpClass(cls):
        """Initialize database once for all tests"""
        printed_db.init_db()
    
    def test_thread_local_connection_reuse(self):
        """Test that connections are reused in the same thread"""
        # Get connection twice in same thread
        conn1 = printed_db._get_connection()
        conn2 = printed_db._get_connection()
        
        # Should be the same connection object
        self.assertIs(conn1, conn2, 
                     "Should reuse connection in same thread")
    
    def test_database_indexes_exist(self):
        """Test that performance indexes are created"""
        conn = printed_db._get_connection()
        cursor = conn.cursor()
        
        # Check for quotation index
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_quotation'"
        )
        idx_quotation = cursor.fetchone()
        self.assertIsNotNone(idx_quotation, "Quotation index should exist")
        
        # Check for printed_at index
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_printed_at'"
        )
        idx_printed_at = cursor.fetchone()
        self.assertIsNotNone(idx_printed_at, "Printed_at index should exist")
    
    def test_record_print_performance(self):
        """Test that record_print is efficient"""
        iterations = 100
        
        start = time.time()
        for i in range(iterations):
            printed_db.record_print(
                quotation=f"TEST-{i}",
                party=f"Customer {i}",
                address="123 Test St",
                phone="1234567890",
                mobile="0987654321"
            )
        duration = time.time() - start
        
        avg_time = (duration / iterations) * 1000  # in milliseconds
        
        print(f"\nRecorded {iterations} prints in {duration:.4f} seconds")
        print(f"Average: {avg_time:.2f} ms per record")
        
        # Should be fast (< 10ms per record on average)
        self.assertLess(avg_time, 10, 
                       "Recording should be fast with connection reuse")
    
    def test_get_recent_performance(self):
        """Test that get_recent query is efficient"""
        # Insert some test data first
        for i in range(50):
            printed_db.record_print(
                quotation=f"PERF-{i}",
                party=f"Customer {i}",
                address="123 Test St"
            )
        
        iterations = 100
        
        start = time.time()
        for _ in range(iterations):
            result = printed_db.get_recent(limit=20)
        duration = time.time() - start
        
        avg_time = (duration / iterations) * 1000  # in milliseconds
        
        print(f"\nQueried {iterations} times in {duration:.4f} seconds")
        print(f"Average: {avg_time:.2f} ms per query")
        
        # Should be fast with indexes (< 5ms per query)
        self.assertLess(avg_time, 5, 
                       "Queries should be fast with proper indexing")
    
    def test_search_performance(self):
        """Test that search queries are efficient with indexes"""
        # Insert test data
        for i in range(50):
            printed_db.record_print(
                quotation=f"SEARCH-{i}",
                party=f"SearchCustomer {i}",
                address="123 Search St"
            )
        
        iterations = 50
        
        start = time.time()
        for _ in range(iterations):
            result = printed_db.get_recent(limit=20, q="SearchCustomer")
        duration = time.time() - start
        
        avg_time = (duration / iterations) * 1000  # in milliseconds
        
        print(f"\nSearched {iterations} times in {duration:.4f} seconds")
        print(f"Average: {avg_time:.2f} ms per search")
        
        # Should be reasonably fast with indexes
        self.assertLess(avg_time, 10, 
                       "Search should be efficient with indexing")


class TestConnectionReuse(unittest.TestCase):
    """Test connection reuse across multiple operations"""
    
    def test_multiple_operations_reuse_connection(self):
        """Test that multiple operations reuse the same connection"""
        conn1 = printed_db._get_connection()
        
        # Perform multiple operations
        printed_db.record_print("CONN-TEST-1", "Test Party 1")
        conn2 = printed_db._get_connection()
        
        printed_db.get_recent(limit=5)
        conn3 = printed_db._get_connection()
        
        printed_db.record_print("CONN-TEST-2", "Test Party 2")
        conn4 = printed_db._get_connection()
        
        # All should be the same connection in the same thread
        self.assertIs(conn1, conn2)
        self.assertIs(conn2, conn3)
        self.assertIs(conn3, conn4)


def run_benchmark():
    """
    Run performance benchmark comparing old vs new approach.
    This is a simulation showing the improvement.
    """
    print("\n" + "="*70)
    print("PERFORMANCE IMPROVEMENT BENCHMARK")
    print("="*70)
    
    print("\nSimulated comparison (actual implementations):")
    print("-" * 70)
    
    # Test current optimized implementation
    iterations = 1000
    
    print(f"\nTest: {iterations} sequential operations with connection reuse")
    start = time.time()
    for i in range(iterations):
        conn = printed_db._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        # Connection is reused, not closed
    optimized_duration = time.time() - start
    
    print(f"✓ Optimized (connection reuse): {optimized_duration:.4f} seconds")
    print(f"  Average: {(optimized_duration/iterations)*1000:.2f} ms per operation")
    
    # Simulate old approach (open/close each time)
    import sqlite3
    print(f"\nTest: {iterations} operations with open/close each time")
    start = time.time()
    for i in range(iterations):
        conn = sqlite3.connect(printed_db.DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        conn.close()
    old_duration = time.time() - start
    
    print(f"✗ Old (open/close): {old_duration:.4f} seconds")
    print(f"  Average: {(old_duration/iterations)*1000:.2f} ms per operation")
    
    improvement = ((old_duration - optimized_duration) / old_duration) * 100
    speedup = old_duration / optimized_duration
    
    print(f"\n{'='*70}")
    print(f"IMPROVEMENT: {improvement:.1f}% faster ({speedup:.1f}x speedup)")
    print(f"Time saved: {(old_duration - optimized_duration):.4f} seconds")
    print(f"{'='*70}\n")


if __name__ == '__main__':
    print("="*70)
    print("Testing printed_db.py Performance Optimizations")
    print("="*70)
    
    # Run unit tests
    unittest.main(verbosity=2, exit=False)
    
    # Run benchmark
    run_benchmark()
