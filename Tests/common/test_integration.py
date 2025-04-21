import unittest
import os
import sys
import time
import threading
import requests
import shutil
import socket
import random

root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, root_dir)

from Client.client import CloudComputeClient
from Server.server import CodeExecutionServer
from Server.config import Config


class TestIntegration(unittest.TestCase):
    """
    Common integration tests to verify client-server interaction.
    These tests run both server and client and verify their interaction.
    """

    @classmethod
    def setUpClass(cls):
        """Setup before all class tests - server startup"""
        cls.uploads_dir = os.path.join(os.getcwd(), "uploads")
        os.makedirs(cls.uploads_dir, exist_ok=True)

        cls.temp_dir = os.path.join(cls.uploads_dir, "integration_test")
        os.makedirs(cls.temp_dir, exist_ok=True)

        if hasattr(Config, "UPLOAD_FOLDER"):
            cls.original_uploads_folder = Config.UPLOAD_FOLDER
            Config.UPLOAD_FOLDER = cls.uploads_dir

        preferred_port = 5001
        for port_offset in range(10):
            test_port = preferred_port + port_offset
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.bind(("", test_port))
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
                result = sock.connect_ex(("localhost", cls.server_port))
                sock.close()

                if result == 0:
                    server_started = True
                    break
            except:
                pass
            time.sleep(retry_interval)

        if not server_started:
            raise RuntimeError("Failed to start the server for testing")

    @classmethod
    def tearDownClass(cls):
        """Cleanup after all class tests"""
        if hasattr(cls, "original_uploads_folder"):
            Config.UPLOAD_FOLDER = cls.original_uploads_folder

        if hasattr(cls, "original_port"):
            Config.PORT = cls.original_port

        for file in os.listdir(cls.temp_dir):
            file_path = os.path.join(cls.temp_dir, file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f"Error while deleting {file_path}: {e}")

        for file in os.listdir(cls.uploads_dir):
            if file not in ["server_test", "client_test", "integration_test"]:
                file_path = os.path.join(cls.uploads_dir, file)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f"Error deleting {file_path}: {e}")

    def setUp(self):
        """Setup before each test"""
        self.client = CloudComputeClient()
        self.client.api_url = f"{self.server_url}/execute"

        self.test_files = []
        for i in range(3):
            file_path = os.path.join(self.temp_dir, f"test_{i}.py")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f'print("This is test file {i}")')
            self.test_files.append(file_path)

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(("localhost", self.server_port))
            sock.close()

            self.assertEqual(result, 0, "Server port is not accessible")
        except (socket.error, AssertionError):
            self.fail("Server is not available")

    def tearDown(self):
        """Cleanup after each test"""
        pass

    def test_send_single_task(self):
        """Test sending one file for execution via client and processing by server"""
        file_path = self.test_files[0]
        result = self.client.send_code(file_path)

        self.assertIsInstance(result, dict)
        self.assertIn("output", result)
        self.assertIsInstance(result["output"], str)
        self.assertIn("error", result)

    def test_send_sequential_tasks(self):
        """Test sending sequential tasks via client and their processing by server"""
        results = []
        for file_path in self.test_files:
            result = self.client.send_code(file_path)
            results.append(result)

        self.assertEqual(len(results), len(self.test_files))
        for i, result in enumerate(results):
            self.assertIsInstance(result, dict)
            self.assertIn("output", result)
            self.assertIsInstance(result["output"], str)
            self.assertIn("error", result)

    def test_send_parallel_tasks(self):
        """Test sending parallel tasks via client and their processing by server"""
        threads = []
        results = []

        def send_task(file_path):
            result = self.client.send_code(file_path)
            results.append(result)

        for file_path in self.test_files:
            thread = threading.Thread(target=send_task, args=(file_path,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        self.assertEqual(len(results), len(self.test_files))
        for result in results:
            self.assertIsInstance(result, dict)
            self.assertIn("output", result)
            self.assertIsInstance(result["output"], str)
            self.assertIn("error", result)

    def test_cors_headers(self):
        """Test presence of CORS headers in server responses to client requests"""
        response = requests.options(f"{self.server_url}/execute")

        self.assertIn(response.status_code, [200, 204])

        if "Access-Control-Allow-Origin" in response.headers:
            self.assertEqual(response.headers["Access-Control-Allow-Origin"], "*")

        self.assertIn("Allow", response.headers)
        self.assertIn("POST", response.headers["Allow"])

    def test_client_error_handling(self):
        """Test error handling by client when server responds with an error"""
        error_file = os.path.join(self.temp_dir, "error_test.py")
        with open(error_file, "w", encoding="utf-8") as f:
            f.write(
                'print("Before error")\n# Syntax error:\nif True print("This will fail")'
            )

        result = self.client.send_code(error_file)

        self.assertIsInstance(result, dict)
        self.assertIn("output", result)
        self.assertIn("error", result)
        self.assertTrue(result["error"], "The 'error' field should not be empty")

    def test_client_file_handling(self):
        """Test processing of created files during client-server interaction"""
        file_gen_path = os.path.join(self.temp_dir, "file_generator.py")
        with open(file_gen_path, "w", encoding="utf-8") as f:
            f.write(
                """
import os
# Trying to create a file and print a message
print("Processing test task")
try:
	with open("generated_output.txt", "w") as out_file:
		out_file.write("This content was generated by the test")
	print("File operation completed")
except Exception as e:
	print(f"Error: {e}")
"""
            )

        result = self.client.send_code(file_gen_path)
        self.assertIn("files", result, "Result should contain 'files' field")
        self.assertIsInstance(result["files"], list, "Files should be a list")


if __name__ == "__main__":
    unittest.main()
