import os
import sys
import time
import requests
import subprocess


def setup_test_paths():
    """Configures paths for all tests"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.append(parent_dir)
    return current_dir, parent_dir


def is_server_running(server_url="http://localhost:5000", timeout=2):
    """Quick server availability check"""
    try:
        response = requests.get(f"{server_url}/health", timeout=timeout)
        if response.status_code == 200:
            return True
    except Exception:
        pass
    
    try:
        response = requests.get(f"{server_url}/", timeout=timeout)
        if response.status_code < 500:
            return True
    except Exception:
        pass
    
    try:
        response = requests.post(
            f"{server_url}/execute",
            files={"file": ("test.py", b'print("hello")')},
            timeout=timeout
        )
        return response.status_code == 200
    except Exception:
        return False


def wait_for_server(server_url="http://localhost:5000", max_attempts=30, delay=1):
    """Waiting for server availability"""
    for attempt in range(max_attempts):
        if is_server_running(server_url, timeout=1):
            return True
        if attempt < max_attempts - 1:
            time.sleep(delay)
    return False


def run_behave_tests(features_dir, test_name="tests"):
    """Runs behave tests with presence check"""
    try:
        import behave
        
        if not os.path.exists(features_dir):
            print(f"The directory '{features_dir}' does not exist. Skipping {test_name}.")
            return True
            
        feature_files = [f for f in os.listdir(features_dir) if f.endswith(".feature")]
        if not feature_files:
            print(f"There are no .feature files in '{features_dir}'. Skipping {test_name}.")
            return True
            
        result = subprocess.run(
            ["python", "-m", "behave", features_dir], 
            capture_output=False
        )
        return result.returncode == 0
        
    except ImportError:
        print(f"Package 'behave' not found. Skipping {test_name}.")
        return True
    except Exception as e:
        print(f"Startup error {test_name}: {str(e)}")
        return False


def run_unittest_discover(test_dir, test_name="tests"):
    """Runs unittest discovery for the specified directory"""
    result = subprocess.run(
        [
            "python", "-m", "unittest", "discover",
            "-s", test_dir,
            "-p", "test_*.py",
        ],
        capture_output=False,
    )
    return result.returncode == 0 