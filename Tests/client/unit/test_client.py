import unittest
import os
import tempfile
import time
import shutil
from Client.client import CloudComputeClient

class TestCloudComputeClient(unittest.TestCase):
	
	def setUp(self):
		"""Setup before each test"""
		self.client = CloudComputeClient()
		
	def test_client_initialization(self):
		"""Test client initialization"""
		self.assertIsNotNone(self.client)
		self.assertEqual(self.client.api_url, "http://localhost:5000/execute")
		
	def test_send_code(self):
		"""Test real code sending to actual server"""
		with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as temp:
			temp.write(b'print("Real integration test")')
			temp_file_path = temp.name
		
		try:
			result = self.client.send_code(temp_file_path)
			
			self.assertIn('output', result)
			self.assertIn('execution_time_ms', result)
			self.assertIn('files', result)
		except Exception as e:
			self.fail(f"Real server test failed: {str(e)}")
		finally:
			os.unlink(temp_file_path)
	
	def test_send_parallel(self):
		"""Real test of parallel file sending"""
		tasks_dir = os.path.join(os.getcwd(), 'Tasks')
		tasks_existed = os.path.exists(tasks_dir)
		
		if not tasks_existed:
			os.makedirs(tasks_dir)
		
		original_files = os.listdir(tasks_dir) if tasks_existed else []
		
		try:
			test_files = []
			for i in range(3):
				file_path = os.path.join(tasks_dir, f'test_parallel_{i}.py')
				with open(file_path, 'w') as f:
					f.write(f'print("Test parallel file {i}")')
				test_files.append(file_path)
			
			start_time = time.time()
			self.client.send_parallel()
			execution_time = time.time() - start_time
			
			self.assertLess(execution_time, 10.0, "Parallel execution took too long")
			
		finally:
			for file_path in test_files:
				if os.path.exists(file_path):
					os.remove(file_path)
			
			if not tasks_existed:
				for file_name in os.listdir(tasks_dir):
					file_path = os.path.join(tasks_dir, file_name)
					if file_path not in original_files:
						try:
							os.remove(file_path)
						except:
							pass
				os.rmdir(tasks_dir)
			
	def test_file_not_found(self):
		"""Test handling of non-existent file"""
		non_existent_file = "/path/to/non_existent_file.py"
		
		try:
			result = self.client.send_code(non_existent_file)
			self.fail("Expected FileNotFoundError but got a result")
		except FileNotFoundError:
			pass

if __name__ == '__main__':
	unittest.main() 