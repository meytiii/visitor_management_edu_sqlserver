import unittest
from unittest.mock import MagicMock, patch
import threading
from queue import Empty
import database
import config

class TestConnectionPool(unittest.TestCase):
    def setUp(self):
        self.pool = database.ConnectionPool()
        # Reset pool state
        self.pool.shutdown()
        self.pool._initialized = True
        self.pool._max_size = 3
        self.pool._timeout = 1

    def tearDown(self):
        self.pool.shutdown()

    def test_pool_connection_lifecycle(self):
        mock_conn = MagicMock()
        mock_conn.execute.return_value = True

        with patch.object(self.pool, '_create_connection', return_value=mock_conn):
            conn1 = self.pool.get_connection()
            self.assertEqual(self.pool.stats()["active_count"], 1)

            # Return connection healthy
            self.pool.return_connection(conn1, is_healthy=True)
            self.assertEqual(self.pool.stats()["pool_size"], 1)

            # Re-acquire from pool without creating new
            conn2 = self.pool.get_connection()
            self.assertEqual(conn2, mock_conn)
            self.assertEqual(self.pool.stats()["pool_size"], 0)

            # Return unhealthy: should close and decrement active count
            self.pool.return_connection(conn2, is_healthy=False)
            mock_conn.close.assert_called()
            self.assertEqual(self.pool.stats()["active_count"], 0)

    def test_pool_capacity_and_exhaustion(self):
        mock_conn = MagicMock()
        mock_conn.execute.return_value = True

        with patch.object(self.pool, '_create_connection', return_value=mock_conn):
            c1 = self.pool.get_connection()
            c2 = self.pool.get_connection()
            c3 = self.pool.get_connection()

            self.assertEqual(self.pool.stats()["active_count"], 3)

            # 4th request exceeds max_size (3) and should timeout without deadlocking
            with self.assertRaises(TimeoutError):
                self.pool.get_connection()

            # Returning one allows a waiting thread to acquire
            self.pool.return_connection(c1, is_healthy=True)
            c4 = self.pool.get_connection()
            self.assertEqual(c4, mock_conn)

    def test_create_connection_failure_unwinds_active_count(self):
        # When _create_connection fails, active_count must NOT stay incremented
        with patch.object(self.pool, '_create_connection', side_effect=Exception("DB Down")):
            with patch('time.sleep', return_value=None):
                with self.assertRaises(Exception):
                    self.pool.get_connection()

            self.assertEqual(self.pool.stats()["active_count"], 0)

    def test_concurrent_access_no_deadlock(self):
        mock_conn = MagicMock()
        mock_conn.execute.return_value = True

        errors = []

        def worker():
            try:
                with patch.object(self.pool, '_create_connection', return_value=mock_conn):
                    c = self.pool.get_connection()
                    self.pool.return_connection(c, is_healthy=True)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=3.0)
            self.assertFalse(t.is_alive(), "Worker thread deadlocked!")

        self.assertEqual(len(errors), 0)

if __name__ == "__main__":
    unittest.main()
