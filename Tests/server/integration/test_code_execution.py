import unittest
import os
import requests
import tempfile
import sys

root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, root_dir)

tests_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, tests_dir)

from server.test_helpers import setup_test_environment, skip_if_server_unavailable

setup_test_environment()

class TestCodeExecution(unittest.TestCase):
    """
    Tests to verify code execution via API
    """

    @classmethod
    def setUpClass(cls):
        """Setting up before all class tests"""
        cls.server_url = "http://server:5000"
        cls.temp_dir = "/uploads/test_execution"
        os.makedirs(cls.temp_dir, exist_ok=True)

    def setUp(self):
        """Settings before each test"""
        skip_if_server_unavailable(self, self.server_url)

    def test_execute_simple_code(self):
        """Simple code execution test"""
        code = 'print("Hello, world!")'
        test_file_path = os.path.join(self.temp_dir, "simple_test.py")

        with open(test_file_path, "w", encoding="utf-8") as f:
            f.write(code)

        with open(test_file_path, "rb") as f:
            files = {"file": (os.path.basename(test_file_path), f, "text/plain")}
            response = requests.post(f"{self.server_url}/execute", files=files, timeout=10)

        self.assertNotEqual(response.status_code, 404, "The endpoint must exist.")
        
        if response.status_code == 200:
            result = response.json()
            self.assertIsInstance(result, dict)
            if "files" in result:
                self.assertIsInstance(result["files"], list)

    def test_execute_code_with_output(self):
        """Code execution test with output"""
        code = '''
import datetime
print(f"Current time: {datetime.datetime.now()}")
print("Test output line 2")
'''
        test_file_path = os.path.join(self.temp_dir, "output_test.py")

        with open(test_file_path, "w", encoding="utf-8") as f:
            f.write(code)

        with open(test_file_path, "rb") as f:
            files = {"file": (os.path.basename(test_file_path), f, "text/plain")}
            response = requests.post(f"{self.server_url}/execute", files=files, timeout=10)

        self.assertNotEqual(response.status_code, 404)
        
        if response.status_code == 200:
            result = response.json()
            has_output_or_error = "output" in result or "error" in result
            self.assertTrue(has_output_or_error, "The response must contain output or error.")

    def test_execute_code_with_error(self):
        """Code execution test with error"""
        code = '''
# Code with a syntax error
print("Start")
undefined_variable_that_does_not_exist
print("End")
'''
        test_file_path = os.path.join(self.temp_dir, "error_test.py")

        with open(test_file_path, "w", encoding="utf-8") as f:
            f.write(code)

        with open(test_file_path, "rb") as f:
            files = {"file": (os.path.basename(test_file_path), f, "text/plain")}
            response = requests.post(f"{self.server_url}/execute", files=files, timeout=10)

        self.assertNotEqual(response.status_code, 404)
        
        if response.status_code == 200:
            result = response.json()
            self.assertTrue("error" in result or "output" in result, "The answer must contain the result.")


if __name__ == "__main__":
    unittest.main() 