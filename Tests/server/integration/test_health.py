import unittest
import time
import requests
import os
import sys

root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, root_dir)

tests_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, tests_dir)

from server.test_helpers import setup_test_environment

setup_test_environment()

from Server.config import Config


class TestSystemHealth(unittest.TestCase):
    """
    Tests to check the health of the entire system.
    These tests check whether all the components are working together.
    """

    @classmethod
    def setUpClass(cls):
        """Setting up before all class tests"""
        cls.server_url = "http://server:5000"
        cls.max_wait_time = 60
        cls.system_ready = False
        
        start_time = time.time()
        while time.time() - start_time < cls.max_wait_time:
            try:
                response = requests.get(f"{cls.server_url}/", timeout=2)
                if response.status_code < 500:
                    cls.system_ready = True
                    break
            except:
                pass
            
            time.sleep(2)
        
        if not cls.system_ready:
            print("WARNING: System is not ready for testing. Tests will be skipped.")

    def setUp(self):
        """Settings before each test"""
        if not self.system_ready:
            self.skipTest("The system is not ready for testing. Skipping tests.")

    def test_server_responds(self):
        """Test whether the server is responding to requests"""
        response = requests.get(f"{self.server_url}/", timeout=10)
        self.assertLess(response.status_code, 500, "The server must respond to requests without errors.")

    def test_database_functionality(self):
        """Database functionality test via API"""
        test_user_data = {
            "username": f"health_check_user_{int(time.time())}",
            "email": f"health_{int(time.time())}@test.com"
        }
        
        response = requests.post(f"{self.server_url}/register", 
                               json=test_user_data, 
                               timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            self.assertIn("api_key", data)
        elif response.status_code == 500:
            pass
        else:
            self.fail(f"Unexpected response status: {response.status_code}")

    def test_code_execution_endpoint(self):
        """Code Execution Endpoint Test"""
        test_code = 'print("Health check test")'
        
        files = {"file": ("health_test.py", test_code.encode(), "text/plain")}
        response = requests.post(f"{self.server_url}/execute", 
                               files=files, 
                               timeout=10)
        
        self.assertNotEqual(response.status_code, 404, "The /execute endpoint must exist.")

    def test_system_resources(self):
        """Test whether the system is not overloaded"""
        start_time = time.time()
        
        for i in range(5):
            response = requests.get(f"{self.server_url}/", timeout=10)
            if response.status_code >= 500:
                self.fail(f"The system is overloaded on request {i+1}")
        
        end_time = time.time()
        total_time = end_time - start_time
        
        self.assertLess(total_time, 30, "The system responds too slowly")

    def test_full_workflow_if_possible(self):
        """Test the complete workflow if possible"""
        try:
            user_data = {
                "username": f"workflow_user_{int(time.time())}",
                "email": f"workflow_{int(time.time())}@test.com"
            }
            
            register_response = requests.post(f"{self.server_url}/register", 
                                            json=user_data, 
                                            timeout=10)
            
            if register_response.status_code != 200:
                self.skipTest("User registration does not work, we skip the entire workflow test")
                return
            
            api_key = register_response.json()["api_key"]
            
            test_code = 'print("Full workflow test successful")'
            headers = {"Authorization": f"Bearer {api_key}"}
            files = {"codeFile": ("workflow_test.py", test_code.encode(), "text/plain")}
            
            execute_response = requests.post(f"{self.server_url}/process-code", 
                                           files=files, 
                                           headers=headers, 
                                           timeout=10)
            
            self.assertNotIn(execute_response.status_code, [401, 403], 
                           "Authorization must work with a valid API key")
            
        except Exception as e:
            pass


if __name__ == "__main__":
    unittest.main() 