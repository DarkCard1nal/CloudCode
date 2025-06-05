import os
from test_helpers import setup_test_paths, wait_for_server, run_behave_tests, run_unittest_discover


def wait_for_server_availability():
    """Quickly check server availability"""
    print("Checking server availability...")
    
    if wait_for_server("http://server:5000", max_attempts=10, delay=0.5):
        print("Server is ready (Docker)")
        return True
    
    if wait_for_server("http://localhost:5000", max_attempts=5, delay=0.5):
        print("Server is ready (localhost)")
        return True
    
    print("Server unavailable for testing!")
    return False


def run_server_tests():
    """Runs all server tests (unit, integration, behavioral, and security)"""
    if not wait_for_server_availability():
        return 1
    
    current_dir, parent_dir = setup_test_paths()
    success = True

    print("\n--- Running server unit tests ---")
    success = success and run_unittest_discover(
        os.path.join(current_dir, "server", "unit"),
        "server unit tests"
    )

    print("\n--- Running server integration tests ---")
    success = success and run_unittest_discover(
        os.path.join(current_dir, "server", "integration"),
        "server integration tests"
    )

    print("\n--- Running server behavioral tests ---")
    success = success and run_behave_tests(
        os.path.join(current_dir, "server", "features"),
        "server behavioral tests"
    )

    print("\n--- Running security tests ---")
    success = success and run_behave_tests(
        os.path.join(current_dir, "server", "security", "features"),
        "security tests"
    )

    if success:
        print("\n All tests passed successfully!")
    else:
        print("\n Some tests failed.")
    
    return 0 if success else 1


if __name__ == "__main__":
    import sys
    sys.exit(run_server_tests())
