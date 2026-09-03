import unittest
from unittest.mock import MagicMock, patch
import os
import sqlite3
import tempfile
from datetime import datetime
import utils
import database

class TestBackupRestore(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.backup_path = os.path.join(self.temp_dir.name, "test_backup.db")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_backup_creates_complete_schema(self):
        mock_visitors = [
            (1, "رضا احمدی", "0010340890", "دکتر سهرابی", "امور اداری", datetime(2026, 8, 20, 10, 30, 0), "1405/05/30", "12:00", "admin")
        ]
        mock_users = [
            (1, "admin", "hashed_pass", "admin", "مدیر سیستم")
        ]
        mock_audit = [
            (1, "1405/05/30", "10:30:00", "visitor_added", "admin", 1, "رضا احمدی", "0010340890", "دکتر سهرابی", "امور اداری", "details", "2026-08-20T10:30:00",
             "sess-123", "PC-01", "winuser", "00:11:22:33:44:55", None, None)
        ]

        with patch('database.get_all_visitors_for_backup', return_value=mock_visitors), \
             patch('database.get_all_users_for_backup', return_value=mock_users), \
             patch('database.get_all_audit_logs_for_backup', return_value=mock_audit), \
             patch('database.log_audit'), \
             patch('tkinter.filedialog.asksaveasfilename', return_value=self.backup_path), \
             patch('tkinter.messagebox.showinfo'):

            utils.do_backup(None, current_username="testadmin")

        self.assertTrue(os.path.exists(self.backup_path))

        conn = sqlite3.connect(self.backup_path)
        cur = conn.cursor()

        # Check tables exist
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [t[0] for t in cur.fetchall()]
        self.assertIn("visitors", tables)
        self.assertIn("users", tables)
        self.assertIn("audit_log", tables)

        # Check audit_log columns (must have 18 columns including forensic fields)
        cur.execute("PRAGMA table_info(audit_log)")
        cols = [c[1] for c in cur.fetchall()]
        self.assertEqual(len(cols), 18)
        self.assertIn("session_id", cols)
        self.assertIn("workstation_name", cols)
        self.assertIn("windows_user", cols)
        self.assertIn("mac_address", cols)
        self.assertIn("old_state", cols)
        self.assertIn("new_state", cols)

        # Check rows
        cur.execute("SELECT COUNT(*) FROM visitors")
        self.assertEqual(cur.fetchone()[0], 1)

        cur.execute("SELECT entry_time FROM visitors")
        self.assertEqual(cur.fetchone()[0], "2026-08-20 10:30:00")

        conn.close()

    def test_restore_roundtrip_new_and_legacy_backups(self):
        # 1. Create a legacy backup database with 12 audit columns
        legacy_path = os.path.join(self.temp_dir.name, "legacy_backup.db")
        conn = sqlite3.connect(legacy_path)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE visitors (
                visitor_name TEXT, national_id TEXT, employee_to_meet TEXT,
                department TEXT, entry_time TEXT, shamsi_date TEXT,
                exit_time TEXT, created_by TEXT
            )
        """)
        cur.execute("INSERT INTO visitors VALUES ('مهمان تست', '0010340890', 'کارمند', 'واحد', '2026-08-20 10:00:00', '1405/05/30', '', 'admin')")

        cur.execute("CREATE TABLE users (username TEXT, password TEXT, role TEXT, full_name TEXT)")
        cur.execute("INSERT INTO users VALUES ('legacy_user', 'hash', 'guard', 'نگهبان')")

        cur.execute("""
            CREATE TABLE audit_log (
                shamsi_date TEXT, shamsi_time TEXT, event_type TEXT, user_name TEXT,
                visitor_id INTEGER, visitor_name TEXT, national_id TEXT,
                employee_to_meet TEXT, department TEXT, details TEXT, created_at TEXT
            )
        """)
        cur.execute("INSERT INTO audit_log VALUES ('1405/05/30', '10:00:00', 'login_success', 'admin', NULL, NULL, NULL, NULL, NULL, 'ok', '2026-08-20')")
        conn.commit()
        conn.close()

        with patch('database.get_visitor_by_natid_employee_date', return_value=False), \
             patch('database.insert_visitor_from_backup') as mock_ins_vis, \
             patch('database.get_user_by_username', return_value=False), \
             patch('database.insert_user_from_backup') as mock_ins_user, \
             patch('database.get_audit_log_duplicate', return_value=False), \
             patch('database.insert_audit_log_from_backup') as mock_ins_audit, \
             patch('database.log_audit'), \
             patch('tkinter.filedialog.askopenfilename', return_value=legacy_path), \
             patch('tkinter.messagebox.showinfo'):

            utils.do_restore(None, current_username="testadmin")

            mock_ins_vis.assert_called_once()
            mock_ins_user.assert_called_once()
            mock_ins_audit.assert_called_once()

if __name__ == "__main__":
    unittest.main()
