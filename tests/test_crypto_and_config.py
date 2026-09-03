import unittest
import os
import database
import config
import utils

class TestCryptoAndConfig(unittest.TestCase):
    def test_password_hashing_and_verification(self):
        password = "SecurePassword123!"
        hashed = database.hash_password(password)

        self.assertIsInstance(hashed, str)
        self.assertGreater(len(hashed), 64)
        self.assertNotEqual(password, hashed)

        # Verification with correct password
        self.assertTrue(database.verify_password(hashed, password))

        # Verification with incorrect password
        self.assertFalse(database.verify_password(hashed, "WrongPassword"))

        # Verification with corrupted hash
        self.assertFalse(database.verify_password("corrupted_hash", password))

    def test_odbc_val_escaping(self):
        # Plain text
        self.assertEqual(config._escape_odbc_val("simple"), "simple")
        self.assertEqual(config._escape_odbc_val(""), "")

        # String with semicolon
        self.assertEqual(config._escape_odbc_val("pass;word"), "{pass;word}")

        # String with spaces
        self.assertEqual(config._escape_odbc_val("My Database"), "{My Database}")

        # String with braces
        self.assertEqual(config._escape_odbc_val("p{a}ss"), "{p{a}}ss}")

    def test_build_connection_string(self):
        # Default unencrypted
        settings = {
            "sql_driver": "{ODBC Driver 18 for SQL Server}",
            "sql_server": "10.0.0.1",
            "sql_database": "VisitorDB",
            "sql_user": "sa",
            "sql_password": "pass;word{123}",
            "sql_encrypt": "no",
            "sql_trust_cert": "yes"
        }
        conn_str = config.build_connection_string(settings)
        self.assertIn("DRIVER={ODBC Driver 18 for SQL Server};", conn_str)
        self.assertIn("SERVER=10.0.0.1;", conn_str)
        self.assertIn("DATABASE=VisitorDB;", conn_str)
        self.assertIn("UID=sa;", conn_str)
        self.assertIn("PWD={pass;word{123}}};", conn_str)
        self.assertIn("Encrypt=no;", conn_str)

        # Encrypted with TLS
        settings["sql_encrypt"] = "yes"
        conn_str_enc = config.build_connection_string(settings)
        self.assertIn("Encrypt=yes;", conn_str_enc)
        self.assertIn("TrustServerCertificate=yes;", conn_str_enc)

    def test_shamsi_years_generation(self):
        years = utils.get_shamsi_years()
        self.assertIsInstance(years, list)
        self.assertGreater(len(years), 10)
        # Should include years like 1400, 1403, 1404
        self.assertIn("1400", years)
        self.assertIn("1403", years)
        self.assertIn("1404", years)

    def test_get_icon_path(self):
        icon_path = utils.get_icon_path()
        self.assertTrue(os.path.isabs(icon_path))
        self.assertTrue(os.path.exists(icon_path), f"Icon file does not exist at {icon_path}")

if __name__ == "__main__":
    unittest.main()
