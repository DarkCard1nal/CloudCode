import unittest
import os
import sys
import time
import threading
import json
import requests
import tempfile
import shutil
import socket
import random
from pathlib import Path

root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, root_dir)

from Server.server import CodeExecutionServer
from Server.config import Config
from Server.executor import CodeExecutor

class TestIntegrationServer(unittest.TestCase):
    """
    Integration tests to verify the server's actual functionality.
    These tests run a real server and check the API endpoints.
    """
    
    @classmethod
    def setUpClass(cls):
        """Setup before all class tests - start the server"""
        cls.temp_dir = '/uploads/server_test'
        
        os.makedirs(cls.temp_dir, exist_ok=True)
        
        if hasattr(Config, 'UPLOAD_FOLDER'):
            cls.original_uploads_folder = Config.UPLOAD_FOLDER
            Config.UPLOAD_FOLDER = '/uploads'
            
        preferred_port = 5001
        for port_offset in range(10):
            test_port = preferred_port + port_offset
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.bind(('', test_port))
                sock.close()
                cls.server_port = test_port
                break
            except OSError:
                continue
        else:
            cls.server_port = random.randint(5100, 5999)
        
        cls.original_port = Config.PORT
        Config.PORT = cls.server_port
        cls.server_url = f"http://localhost:{cls.server_port}"
        
        cls.server = CodeExecutionServer()
        
        def run_server():
            cls.server.run()
        
        cls.server_thread = threading.Thread(target=run_server)
        cls.server_thread.daemon = True
        cls.server_thread.start()
        
        max_retries = 10
        retry_interval = 1
        server_started = False
        
        for _ in range(max_retries):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                result = sock.connect_ex(('localhost', cls.server_port))
                sock.close()
                
                if result == 0:
                    server_started = True
                    break
            except:
                pass
            time.sleep(retry_interval)
        
        if not server_started:
            raise RuntimeError("Failed to start server for testing")
    
    @classmethod
    def tearDownClass(cls):
        """Cleanup after all class tests"""
        if hasattr(cls, 'original_uploads_folder'):
            Config.UPLOAD_FOLDER = cls.original_uploads_folder
        
        if hasattr(cls, 'original_port'):
            Config.PORT = cls.original_port
        
        for file in os.listdir(cls.temp_dir):
            file_path = os.path.join(cls.temp_dir, file)
            if os.path.isfile(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
    
    def setUp(self):
        """Setup before each test"""
        self.test_file_path = os.path.join(self.temp_dir, "test_script.py")
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', self.server_port))
            sock.close()
            
            self.assertEqual(result, 0, "Server port is not accessible")
        except (socket.error, AssertionError):
            self.fail("Server is unavailable")
    
    def tearDown(self):
        """Cleanup after each test"""
        if os.path.exists(self.test_file_path):
            os.remove(self.test_file_path)
        
        for file_path in Path(self.temp_dir).glob("*"):
            if file_path.is_file() and file_path.name != 'test_script.py':
                try:
                    file_path.unlink()
                except:
                    pass
    
    def test_execute_code_success(self):
        """Test successful code execution via API"""
        code = 'print("Hello from server!")'
        test_file_path = os.path.join(self.temp_dir, 'hello.py')
        
        with open(test_file_path, 'w', encoding='utf-8') as f:
            f.write(code)
        
        with open(test_file_path, 'rb') as f:
            files = {'file': (os.path.basename(test_file_path), f, 'text/plain')}
            response = requests.post(f"{self.server_url}/execute", files=files)
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        
        self.assertIn('Hello from server!', result['output'])
        self.assertEqual(result['error'].strip(), '')
        self.assertEqual(len(result['files']), 0)
    
    def test_execute_code_with_error(self):
        """Test error handling for code execution via API"""
        code = '''
print("Testing error handling")
# This is intentionally broken code with a syntax error
if True print("This will not work")
'''
        test_file_path = os.path.join(self.temp_dir, 'error_test.py')
        
        with open(test_file_path, 'w', encoding='utf-8') as f:
            f.write(code)
        
        with open(test_file_path, 'rb') as f:
            files = {'file': (os.path.basename(test_file_path), f, 'text/plain')}
            response = requests.post(f"{self.server_url}/execute", files=files)
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        
        self.assertIn('SyntaxError', result['error'])
        
    def test_execute_code_with_dependencies(self):
        """Test code execution with external dependencies - спрощена версія"""
        code = '''
import math
import random

def calculate_something():
    """Calculate some values using standard libraries"""
    x = random.random() * 10
    return math.sqrt(x)

result = calculate_something()
print("Basic functionality test")
print(f"Result: {result}")
'''
        test_file_path = os.path.join(self.temp_dir, 'deps_test.py')
        
        with open(test_file_path, 'w', encoding='utf-8') as f:
            f.write(code)
        
        with open(test_file_path, 'rb') as f:
            files = {'file': (os.path.basename(test_file_path), f, 'text/plain')}
            response = requests.post(f"{self.server_url}/execute", files=files)
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        
        self.assertIn('Basic functionality test', result['output'])
        self.assertEqual(result['error'].strip(), '')
        
    def test_execute_code_with_output_files(self):
        """Test code execution that створює файли - спрощена версія"""
        code = '''
print("Testing file generation functionality")
# Create some test files
with open("test_output.txt", "w") as f:
    f.write("This is a test output file")
'''
        test_file_path = os.path.join(self.temp_dir, 'file_gen_test.py')
        
        with open(test_file_path, 'w', encoding='utf-8') as f:
            f.write(code)
        
        with open(test_file_path, 'rb') as f:
            files = {'file': (os.path.basename(test_file_path), f, 'text/plain')}
            response = requests.post(f"{self.server_url}/execute", files=files)
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        
        self.assertIn('Testing file generation functionality', result['output'])
        self.assertEqual(result['error'].strip(), '')
        self.assertGreaterEqual(len(result['files']), 1)
        
        # Verify the content of the generated file
        found_test_output = False
        for file_info in result['files']:
            if file_info['filename'] == 'test_output.txt':
                self.assertEqual(file_info['content'], 'This is a test output file')
                found_test_output = True
                break
        
        self.assertTrue(found_test_output, "Expected output file not found in results")
        
    def test_execute_code_missing_file(self):
        """Test handling of request without a file"""
        response = requests.post(f"{self.server_url}/execute")
        
        if response.status_code == 200:
            result = response.json()
            self.assertIn('error', result)
            self.assertTrue(result['error'], "Expected non-empty error message")
        else:
            self.assertIn(response.status_code, [400, 500])
    
    def test_execute_timeout(self):
        """Test handling of execution timeout - спрощена версія"""
        code = '''
import time
print("Testing timeout functionality")
# This will run for longer than the server timeout
for i in range(20):
    print(f"Iteration {i}")
    time.sleep(1)
print("This should not be printed")
'''
        test_file_path = os.path.join(self.temp_dir, 'timeout_test.py')
        
        with open(test_file_path, 'w', encoding='utf-8') as f:
            f.write(code)
        
        with open(test_file_path, 'rb') as f:
            files = {'file': (os.path.basename(test_file_path), f, 'text/plain')}
            response = requests.post(f"{self.server_url}/execute", files=files)
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        
        self.assertIn('Testing timeout functionality', result['output'])
        self.assertIn('Execution time out', result['error'])
    
    def test_concurrent_requests(self):
        """Test handling of concurrent requests"""
        num_requests = 5
        threads = []
        results = []
        
        def make_request(i):
            code = f'''
print("Parallel request {i}")
import time
time.sleep(1)  # Small delay to ensure overlap
print("Parallel request {i} completed")
'''
            test_file_path = os.path.join(self.temp_dir, f'parallel_test_{i}.py')
            
            with open(test_file_path, 'w', encoding='utf-8') as f:
                f.write(code)
            
            with open(test_file_path, 'rb') as f:
                files = {'file': (os.path.basename(test_file_path), f, 'text/plain')}
                response = requests.post(f"{self.server_url}/execute", files=files)
            
            results.append((i, response.json()))
        
        for i in range(num_requests):
            thread = threading.Thread(target=make_request, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        for i, result in results:
            self.assertIn(f'Parallel request {i}', result['output'])
            self.assertIn(f'Parallel request {i} completed', result['output'])
    
    def test_cors_headers(self):
        """Test presence of CORS headers in responses"""
        response = requests.options(f"{self.server_url}/execute")
        
        self.assertIn(response.status_code, [200, 204])
        
        if 'Access-Control-Allow-Origin' in response.headers:
            self.assertEqual(response.headers['Access-Control-Allow-Origin'], '*')
            
        self.assertIn('Allow', response.headers)
        self.assertIn('POST', response.headers['Allow'])
    
    def test_404_error(self):
        """Test handling of non-existent endpoint"""
        response = requests.get(f"{self.server_url}/nonexistent-endpoint")
        
        self.assertEqual(response.status_code, 404)

if __name__ == '__main__':
    unittest.main() 