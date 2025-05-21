import unittest
import os
import tempfile
import shutil
import sys
import logging

logging.disable(logging.CRITICAL)

root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, root_dir)

from Server.python_security_checker import PythonSecurityChecker


class TestSecurityCheckerReal(unittest.TestCase):
    """
    Real tests for PythonSecurityChecker without mocks.
    These tests verify the actual security analysis logic.
    """

    def setUp(self):
        """Preparation before each test"""
        self.temp_dir = tempfile.mkdtemp()
        PythonSecurityChecker.setup()

    def tearDown(self):
        """Cleanup after each test"""
        shutil.rmtree(self.temp_dir)

    def test_is_safe_import(self):
        """Test import safety check"""
        safe_imports = ["import math", "from datetime import datetime"]
        unsafe_imports = ["import pickle", "import socket"]

        for imp in safe_imports:
            self.assertTrue(
                PythonSecurityChecker._is_safe_import(imp),
                f"Import {imp} should be safe",
            )

        for imp in unsafe_imports:
            self.assertFalse(
                PythonSecurityChecker._is_safe_import(imp),
                f"Import {imp} should be identified as unsafe",
            )

    def test_check_file_safe_and_unsafe_code(self):
        """Test for both safe and unsafe code checking"""
        safe_code = '''
import math
from datetime import datetime

def calculate_fibonacci(n):
	"""Calculates the n-th Fibonacci number."""
	if n <= 1:
		return n
	return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

def main():
	now = datetime.now()
	result = calculate_fibonacci(5)
	print(f"Time: {now}")
	print(f"Fibonacci(5) = {result}")
	print(f"Square root of 2 is {math.sqrt(2)}")

if __name__ == "__main__":
	main()
'''

        test_file = os.path.join(self.temp_dir, "safe_code.py")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(safe_code)

        safe_file_path = PythonSecurityChecker.check_file(test_file)

        self.assertIsNotNone(safe_file_path)
        self.assertTrue(os.path.exists(safe_file_path))

        with open(safe_file_path, "r", encoding="utf-8") as f:
            safe_content = f.read()

        self.assertTrue("import math" in safe_content)
        self.assertTrue("from datetime import datetime" in safe_content)
        self.assertNotIn("WARNING", safe_content)

        unsafe_code = '''
import os
import subprocess

def perform_dangerous_operations():
	"""Performs dangerous operations."""
	os.system("rm -rf /tmp/test")
	subprocess.call(["ls", "-la"], shell=True)
	
	user_input = "2 + 2"
	result = eval(user_input)
	
	return result

if __name__ == "__main__":
	perform_dangerous_operations()
'''

        test_file = os.path.join(self.temp_dir, "unsafe_code.py")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(unsafe_code)

        safe_file_path = PythonSecurityChecker.check_file(test_file)

        self.assertIsNotNone(safe_file_path)
        self.assertTrue(os.path.exists(safe_file_path))

        with open(safe_file_path, "r", encoding="utf-8") as f:
            safe_content = f.read()

        self.assertIn("WARNING", safe_content)

        unsafe_operations = PythonSecurityChecker.get_unsafe_operations()
        self.assertGreater(len(unsafe_operations), 0)

    def test_multiple_unsafe_operations_tracking(self):
        """Test for tracking multiple different unsafe operations"""
        unsafe_code = """
import os
import subprocess
import pickle

os.system("rm -rf /tmp/test")
subprocess.call(["ls", "-la"], shell=True)

with open("data.pkl", "rb") as f:
	data = pickle.load(f)

code = "print('Hello, world!')"
exec(code)
"""

        test_file = os.path.join(self.temp_dir, "multiple_unsafe.py")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(unsafe_code)

        result_file = PythonSecurityChecker.check_file(test_file)
        self.assertIsNotNone(result_file)

        self.assertTrue(os.path.exists(result_file))

        with open(result_file, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("WARNING", content)

        print("Unsafe operations test passed successfully")


if __name__ == "__main__":
    unittest.main()
