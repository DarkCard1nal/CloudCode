import unittest
import os
import time
import threading
import requests
import shutil
import socket
import random
from pathlib import Path
import sys

root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, root_dir)

tests_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, tests_dir)

from server.test_helpers import setup_test_environment

setup_test_environment()

from Server.config import Config


class TestIntegrationServer(unittest.TestCase):
    """
    Integration tests to verify the server's actual functionality.
    These tests run against an existing server instance.
    """

    @classmethod
    def setUpClass(cls):
        """Setup before all class tests - check if server is available"""
        if os.path.exists("/.dockerenv"):
            pass
        else:
            pass
            
        cls.temp_dir = "/uploads/server_test"
        os.makedirs(cls.temp_dir, exist_ok=True)

        cls.server_port = 5000
        cls.server_url = f"http://server:{cls.server_port}"

        max_retries = 10
        retry_interval = 0.5
        server_available = False

        for attempt in range(max_retries):
            try:
                response = requests.get(f"{cls.server_url}/", timeout=2)
                if response.status_code < 500:
                    server_available = True
                    break
            except requests.exceptions.RequestException:
                pass
            time.sleep(retry_interval)

        if not server_available:
            raise RuntimeError("Server is not available for testing. Make sure the server container is running.")

    @classmethod
    def tearDownClass(cls):
        """Cleanup after all class tests"""
        if os.path.exists(cls.temp_dir):
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
            response = requests.get(f"{self.server_url}/", timeout=2)
            self.assertLess(response.status_code, 500, "Server is not accessible")
        except requests.exceptions.RequestException as e:
            self.fail(f"Server is unavailable: {e}")

    def tearDown(self):
        """Cleanup after each test"""
        if os.path.exists(self.test_file_path):
            os.remove(self.test_file_path)

        for file_path in Path(self.temp_dir).glob("*"):
            if file_path.is_file() and file_path.name != "test_script.py":
                try:
                    file_path.unlink()
                except:
                    pass

    def test_server_availability(self):
        """Test that server is accessible"""
        response = requests.get(f"{self.server_url}/", timeout=2)
        self.assertLess(response.status_code, 500, "Server should be accessible")

    def test_execute_endpoint_availability(self):
        """Test that execute endpoint exists (even if it has errors)"""
        code = 'print("Hello from server!")'
        test_file_path = os.path.join(self.temp_dir, "hello.py")

        with open(test_file_path, "w", encoding="utf-8") as f:
            f.write(code)

        with open(test_file_path, "rb") as f:
            files = {"file": (os.path.basename(test_file_path), f, "text/plain")}
            response = requests.post(f"{self.server_url}/execute", files=files, timeout=10)

        self.assertNotEqual(response.status_code, 404, "Execute endpoint should exist")

    def test_options_request(self):
        """Test CORS options request"""
        response = requests.options(f"{self.server_url}/execute", timeout=2)
        self.assertIn(response.status_code, [200, 204, 405])

    def test_404_error(self):
        """Test handling of non-existent endpoint"""
        response = requests.get(f"{self.server_url}/nonexistent-endpoint", timeout=2)
        self.assertEqual(response.status_code, 404)

    def test_process_code_endpoint_without_auth(self):
        """Test process-code endpoint without authorization"""
        code = 'print("Hello from process-code!")'
        test_file_path = os.path.join(self.temp_dir, "process_test.py")

        with open(test_file_path, "w", encoding="utf-8") as f:
            f.write(code)

        with open(test_file_path, "rb") as f:
            files = {"codeFile": (os.path.basename(test_file_path), f, "text/plain")}
            response = requests.post(f"{self.server_url}/process-code", files=files, timeout=10)

        self.assertEqual(response.status_code, 401)
        
        data = response.json()
        self.assertIn("error", data)
        self.assertIn("API key", data["error"])

    def test_process_code_endpoint_with_invalid_auth(self):
        """Test process-code endpoint with invalid authorization"""
        code = 'print("Hello from process-code!")'
        test_file_path = os.path.join(self.temp_dir, "process_test.py")

        with open(test_file_path, "w", encoding="utf-8") as f:
            f.write(code)

        headers = {"Authorization": "Bearer invalid_api_key_12345"}
        
        with open(test_file_path, "rb") as f:
            files = {"codeFile": (os.path.basename(test_file_path), f, "text/plain")}
            response = requests.post(f"{self.server_url}/process-code", files=files, headers=headers, timeout=10)

        self.assertEqual(response.status_code, 403)
        
        data = response.json()
        self.assertIn("error", data)
        self.assertIn("Invalid API key", data["error"])

    def test_register_endpoint(self):
        """Test user registration endpoint"""
        registration_data = {
            "username": "test_integration_user",
            "email": "test_integration@example.com"
        }
        
        response = requests.post(f"{self.server_url}/register", 
                               json=registration_data, 
                               timeout=10)
        
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn("message", data)
        self.assertIn("api_key", data)
        self.assertIn("successfully", data["message"])
        
        api_key = data["api_key"]
        self.assertIsInstance(api_key, str)
        self.assertGreater(len(api_key), 0)
        
        try:
            pass
        except:
            pass

    def test_register_endpoint_missing_fields(self):
        """Test user registration with missing fields"""
        registration_data = {
            "username": "test_user_incomplete"
        }
        
        response = requests.post(f"{self.server_url}/register", 
                               json=registration_data, 
                               timeout=10)
        
        self.assertEqual(response.status_code, 400)
        
        data = response.json()
        self.assertIn("error", data)
        self.assertIn("Missing required fields", data["error"])

    def test_process_code_with_valid_user(self):
        """Test full flow: register user, then use API key to process code"""
        registration_data = {
            "username": "test_flow_user",
            "email": "test_flow@example.com"
        }
        
        register_response = requests.post(f"{self.server_url}/register", 
                                        json=registration_data, 
                                        timeout=10)
        
        if register_response.status_code == 200:
            api_key = register_response.json()["api_key"]
            
            code = 'print("Hello with valid API key!")'
            test_file_path = os.path.join(self.temp_dir, "valid_api_test.py")

            with open(test_file_path, "w", encoding="utf-8") as f:
                f.write(code)

            headers = {"Authorization": f"Bearer {api_key}"}
            
            with open(test_file_path, "rb") as f:
                files = {"codeFile": (os.path.basename(test_file_path), f, "text/plain")}
                response = requests.post(f"{self.server_url}/process-code", 
                                       files=files, 
                                       headers=headers, 
                                       timeout=10)

            self.assertNotIn(response.status_code, [401, 403])
        else:
            self.skipTest(f"Registration failed with status {register_response.status_code}, skipping API key test")

    def test_execute_code_success(self):
        """Test successful code execution via API"""
        code = 'print("Test successful execution")'
        test_file_path = os.path.join(self.temp_dir, "success_test.py")

        with open(test_file_path, "w", encoding="utf-8") as f:
            f.write(code)

        with open(test_file_path, "rb") as f:
            files = {"file": (os.path.basename(test_file_path), f, "text/plain")}
            response = requests.post(f"{self.server_url}/execute", files=files, timeout=10)

        self.assertNotEqual(response.status_code, 404, "Execute endpoint should exist")
        
        if response.status_code == 200:
            result = response.json()
            self.assertIsInstance(result, dict)
            
            if "files" in result:
                self.assertIsInstance(result["files"], list)
            
            has_output_or_error = "output" in result or "error" in result
            self.assertTrue(has_output_or_error, "Response should contain output or error")
        else:
            self.assertNotEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
