import unittest
import os
import sys
import json
import tempfile
import shutil
import docker
import time
import threading
from pathlib import Path
import traceback

root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, root_dir)

from Server.executor import CodeExecutor
from Server.config import Config

class TestIntegrationExecutor(unittest.TestCase):
    """
    Integration tests for verifying the code executor.
    These tests check CodeExecutor functionality with real Docker and file system.
    """
    
    @classmethod
    def setUpClass(cls):
        """Setup before all class tests"""
        try:
            print("Attempting to connect to Docker...")
            cls.docker_client = docker.from_env()
            cls.docker_client.ping()
            print("Successfully connected to Docker")
        except Exception as e:
            error_details = traceback.format_exc()
            print(f"Error connecting to Docker: {str(e)}")
            print(f"Error details:\n{error_details}")
            raise unittest.SkipTest(f"Docker is unavailable: {str(e)}")
        
        cls.uploads_dir = tempfile.mkdtemp()
        
        cls.original_upload_folder = Config.UPLOAD_FOLDER
        Config.UPLOAD_FOLDER = cls.uploads_dir
        
        try:
            Config.init()
        except AttributeError:
            os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        
        cls.temp_dir = tempfile.mkdtemp()
        
        cls.executor = CodeExecutor()
    
    @classmethod
    def tearDownClass(cls):
        """Cleanup after all class tests"""
        Config.UPLOAD_FOLDER = cls.original_upload_folder
            
        shutil.rmtree(cls.temp_dir, ignore_errors=True)
        shutil.rmtree(cls.uploads_dir, ignore_errors=True)
        
        try:
            for container in cls.docker_client.containers.list(all=True):
                if container.name.startswith('cloudcode_'):
                    try:
                        container.remove(force=True)
                    except:
                        pass
        except:
            pass
    
    def setUp(self):
        """Setup before each test"""
        self.test_dir = tempfile.mkdtemp(dir=self.temp_dir)
    
    def tearDown(self):
        """Cleanup after each test"""
        pass
    
    def create_test_file(self, filename, content):
        """Helper method to create a test file"""
        file_path = os.path.join(self.test_dir, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        class FileWrapper:
            def __init__(self, filename, filepath):
                self.filename = filename
                self.filepath = filepath
                
            def save(self, destination):
                shutil.copy(self.filepath, destination)
        
        return FileWrapper(filename, file_path)
    
    def test_execute_code_no_file(self):
        """Test execution without a file"""
        result = self.executor.execute_code(None)
        
        self.assertIn('error', result)
        self.assertNotEqual(result['error'], '')

if __name__ == '__main__':
    unittest.main()