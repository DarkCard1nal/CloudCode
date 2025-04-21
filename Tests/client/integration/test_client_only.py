import unittest
import os
import sys
import tempfile
from io import StringIO

root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, root_dir)

from Client.client import CloudComputeClient
from Client.config import Config

class TestClientOnly(unittest.TestCase):
	"""
	Client tests to verify individual client functionality.
	These tests verify only the client, without interaction with the server.
	"""
	
	def setUp(self):
		"""Setup before each test"""
		self.client = CloudComputeClient()
		self.temp_dir = tempfile.mkdtemp()
		self.old_stdout = sys.stdout
		self.stdout_capture = StringIO()
		sys.stdout = self.stdout_capture
	
	def tearDown(self):
		"""Cleanup after each test"""
		sys.stdout = self.old_stdout
		
		import shutil
		shutil.rmtree(self.temp_dir, ignore_errors=True)
	
	def test_client_initialization(self):
		"""Test client initialization"""
		self.assertIsInstance(self.client, CloudComputeClient)
		self.assertTrue(hasattr(self.client, 'api_url'))
		self.assertEqual(self.client.api_url, Config.API_URL)

	def test_client_send_single_task_file_check(self):
		"""Test file existence check when sending a single task"""
		nonexistent_file = os.path.join(self.temp_dir, "nonexistent.py")
		
		self.client.send_single_task(nonexistent_file)
		
		output = self.stdout_capture.getvalue()
		self.assertIn(f"Error: File '{nonexistent_file}' not found", output)
	
	def test_client_display_result(self):
		"""Test client result display"""
		test_cases = [
			{
				"name": "test.py",
				"result": {
					"output": "Test output",
					"error": "",
					"files": [],
					"execution_time_ms": 100.5
				},
				"expected": ["--- Result for test.py ---", "Test output", "Execution time: 100.50 ms"]
			},
			{
				"name": "error_test.py",
				"result": {
					"output": "Test output with error",
					"error": "Test error message",
					"files": [],
					"execution_time_ms": 50.25
				},
				"expected": ["--- Result for error_test.py ---", "Test output with error", "Error: Test error message"]
			},
			{
				"name": "files_test.py",
				"result": {
					"output": "Test output with files",
					"error": "",
					"files": [
						{"filename": "output.txt", "content": "File content 1"},
						{"filename": "data.csv", "content": "1,2,3\n4,5,6"}
					],
					"execution_time_ms": 75.75
				},
				"expected": ["--- Result for files_test.py ---", "Generated Files:", "File: data.csv", "File: output.txt"]
			}
		]
		
		for case in test_cases:
			self.stdout_capture.truncate(0)
			self.stdout_capture.seek(0)
			
			self.client.display_result(case["name"], case["result"])
			output = self.stdout_capture.getvalue()
			
			for expected_str in case["expected"]:
				self.assertIn(expected_str, output)

if __name__ == '__main__':
	unittest.main() 