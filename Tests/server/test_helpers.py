import os
import sys


def setup_test_environment():
    """Configures the test environment for all tests"""
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if root_dir not in sys.path:
        sys.path.insert(0, root_dir)
    return root_dir


def check_server_availability(server_url="http://server:5000", timeout=5):
    """Checks server availability"""
    try:
        import requests
        response = requests.get(f"{server_url}/", timeout=timeout)
        return response.status_code < 500
    except Exception:
        return False


def skip_if_server_unavailable(test_instance, server_url="http://server:5000"):
    """Skip test if server is unavailable"""
    if not check_server_availability(server_url):
        test_instance.skipTest("Server unavailable for testing. Skipping tests.") 