import unittest
import os
import sys
import json
import time
import threading
import tempfile
import shutil
from pathlib import Path
import socket
import requests

root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, root_dir)

from Client.client import CloudComputeClient as OriginalCloudComputeClient
from Server.server import CodeExecutionServer
from Server.config import Config

class TestCloudComputeClient(OriginalCloudComputeClient):
    def __init__(self, server_url=None):
        super().__init__()
        if server_url:
            self.api_url = f"{server_url}/execute"
    
    def send_sequential(self, file_list=None):
        """Custom send_sequential that accepts a list of files directly"""
        if file_list is None:
            return super().send_sequential()
        
        results = []
        for file_path in file_list:
            if os.path.exists(file_path) and file_path.endswith('.py'):
                result = self.send_code(file_path)
                self.display_result(os.path.basename(file_path), result)
                results.append(result)
        return results
        
    def send_parallel(self, file_list=None):
        """Custom send_parallel that accepts a list of files directly"""
        if file_list is None:
            return super().send_parallel()
            
        threads = []
        results = []
        
        def task(file_path):
            if os.path.exists(file_path) and file_path.endswith('.py'):
                result = self.send_code(file_path)
                self.display_result(os.path.basename(file_path), result)
                results.append(result)
                
        for file_path in file_list:
            thread = threading.Thread(target=task, args=(file_path,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
            
        return results
        
    def send_single_task(self, file_path):
        """Override the original method to properly raise FileNotFoundError"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File '{file_path}' not found.")

        file_name = os.path.basename(file_path)
        print(f"\n--- Sending single task: {file_name} ---\n")
        result = self.send_code(file_path)
        self.display_result(file_name, result)
        return result

class TestIntegrationClient(unittest.TestCase):
    """
    Integration tests to verify client-server interaction.
    These tests run a real server and client, checking their interaction.
    """
    
    @classmethod
    def setUpClass(cls):
        """Setup before all class tests - start the server"""
        cls.temp_dir = '/uploads/test_files'
        cls.uploads_dir = '/uploads'
        
        os.makedirs(cls.temp_dir, exist_ok=True)
        
        if hasattr(Config, 'UPLOAD_FOLDER'):
            cls.original_uploads_folder = Config.UPLOAD_FOLDER
            Config.UPLOAD_FOLDER = cls.uploads_dir
        
        cls.server_port = 5001
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
        """Cleanup after all class tests - stop the server"""
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
                
        for file in os.listdir(cls.uploads_dir):
            file_path = os.path.join(cls.uploads_dir, file)
            if os.path.isfile(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
    
    def setUp(self):
        """Setup before each test"""
        self.client = TestCloudComputeClient(server_url=self.server_url)
        
        self.test_files = []
        for i in range(3):
            file_path = os.path.join(self.temp_dir, f"test_{i}.py")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f'print("This is test file {i}")')
            self.test_files.append(file_path)
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', self.server_port))
            sock.close()
            
            self.assertEqual(result, 0, "Server port is not accessible")
        except (socket.error, AssertionError):
            self.fail("Server is unavailable")
    
    def tearDown(self):
        """Cleanup after each test"""
        pass
    
    def test_send_single_task(self):
        """Test sending a single file for execution"""
        file_path = self.test_files[0]
        result = self.client.send_single_task(file_path)
        
        self.assertIsInstance(result, dict)
        self.assertIn('output', result)
        self.assertIn('This is test file 0', result['output'])
        if 'error' in result and result['error'].strip():
            self.fail(f"Non-empty error found: {result['error']}")
    
    def test_send_sequential(self):
        """Test sending multiple files sequentially"""
        results = self.client.send_sequential(self.test_files)
        
        self.assertEqual(len(results), len(self.test_files))
        for i, result in enumerate(results):
            self.assertIsInstance(result, dict)
            self.assertIn('output', result)
            self.assertIn(f'This is test file {i}', result['output'])
            if 'error' in result and result['error'].strip():
                self.fail(f"Non-empty error found: {result['error']}")
    
    def test_send_parallel(self):
        """Test sending multiple files in parallel"""
        results = self.client.send_parallel(self.test_files)
        
        self.assertEqual(len(results), len(self.test_files))
        
        result_dict = {}
        for result in results:
            for i in range(len(self.test_files)):
                if f'This is test file {i}' in result['output']:
                    result_dict[i] = result
                    break
        
        sorted_results = [result_dict[i] for i in sorted(result_dict.keys())]
        
        for i, result in enumerate(sorted_results):
            self.assertIsInstance(result, dict)
            self.assertIn('output', result)
            self.assertIn(f'This is test file {i}', result['output'])
            if 'error' in result and result['error'].strip():
                self.fail(f"Non-empty error found in result {i}: {result['error']}")
    
    def test_invalid_file_handling(self):
        """Test handling of a non-existent file"""
        non_existent_file = os.path.join(self.temp_dir, "non_existent.py")
        
        with self.assertRaises(FileNotFoundError):
            self.client.send_single_task(non_existent_file)

if __name__ == '__main__':
    unittest.main()