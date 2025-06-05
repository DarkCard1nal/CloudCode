import unittest
import logging
import time
import os
import sys

root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, root_dir)

tests_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, tests_dir)

from server.test_helpers import setup_test_environment

setup_test_environment()

from Server.config import Config
from Server.database import Database


class TestDatabaseReal(unittest.TestCase):
    """
    Tests for working with the database.
    """

    @classmethod
    def setUpClass(cls):
        """Setting up before all class tests"""
        cls.db = None
        cls.db_available = False
        
        max_retries = 10
        for attempt in range(max_retries):
            try:
                cls.db = Database(
                    server=Config.DB_SERVER,
                    database=Config.DB_NAME,
                    user=Config.DB_USER,
                    password=Config.DB_PASSWORD
                )
                cls.db_available = True
                break
            except Exception:
                if attempt < max_retries - 1:
                    time.sleep(2)
        
        if not cls.db_available:
            print("WARNING: Database is not available for testing. Tests will be skipped.")

    @classmethod
    def tearDownClass(cls):
        """Cleaning after all class tests"""
        if cls.db and hasattr(cls.db, 'connection'):
            try:
                cursor = cls.db.connection.cursor()
                cursor.execute("DELETE FROM Users WHERE username LIKE 'test_%'")
                cls.db.connection.commit()
                cursor.close()
            except:
                pass

    def setUp(self):
        """Settings before each test"""
        if not self.db_available:
            self.skipTest("Database unavailable for testing. Skipping tests.")

    def test_database_connection(self):
        """Database connection test"""
        self.assertIsNotNone(self.db)
        self.assertIsNotNone(self.db.connection)
        
        cursor = self.db.connection.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        cursor.close()
        
        self.assertIsNotNone(result)
        self.assertEqual(result[0], 1)

    def test_users_table_exists(self):
        """Test for the existence of the Users table"""
        cursor = self.db.connection.cursor()
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = 'Users'
        """)
        result = cursor.fetchone()
        cursor.close()
        
        self.assertEqual(result[0], 1)

    def test_add_and_validate_user(self):
        """User addition and API key validation test"""
        test_username = "test_user_123"
        test_email = "test@example.com"
        test_api_key = "test_api_key_123456"
        
        try:
            self.db.add_user(test_username, test_email, test_api_key)
            
            is_valid = self.db.is_api_key_valid(test_api_key)
            self.assertTrue(is_valid)
            
            is_invalid = self.db.is_api_key_valid("invalid_key_12345")
            self.assertFalse(is_invalid)
            
        finally:
            try:
                cursor = self.db.connection.cursor()
                cursor.execute("DELETE FROM Users WHERE username = ?", (test_username,))
                self.db.connection.commit()
                cursor.close()
            except:
                pass

    def test_duplicate_user_handling(self):
        """Duplicate user handling test"""
        test_username = "test_duplicate_user"
        test_email = "duplicate@example.com"
        test_api_key = "duplicate_api_key_123"
        
        try:
            self.db.add_user(test_username, test_email, test_api_key)
            
            with self.assertRaises(Exception):
                self.db.add_user(test_username, test_email, test_api_key + "_different")
                
        finally:
            try:
                cursor = self.db.connection.cursor()
                cursor.execute("DELETE FROM Users WHERE username = ?", (test_username,))
                self.db.connection.commit()
                cursor.close()
            except:
                pass

    def test_api_key_validation_with_empty_table(self):
        """API key validation test in case of empty table"""
        cursor = self.db.connection.cursor()
        cursor.execute("SELECT username, email, api_key FROM Users")
        original_users = cursor.fetchall()
        
        try:
            cursor.execute("DELETE FROM Users")
            self.db.connection.commit()
            
            is_valid = self.db.is_api_key_valid("non_existent_key")
            self.assertFalse(is_valid)
            
        finally:
            for user in original_users:
                cursor.execute(
                    "INSERT INTO Users (username, email, api_key) VALUES (?, ?, ?)",
                    user
                )
            self.db.connection.commit()
            cursor.close()


if __name__ == "__main__":
    unittest.main() 