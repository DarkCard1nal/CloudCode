import os
from test_helpers import setup_test_paths, run_behave_tests, run_unittest_discover


def run_client_tests():
    """Runs all client tests (unit, integration, and behavioral)"""
    current_dir, parent_dir = setup_test_paths()
    success = True

    print("\n--- Running client unit tests ---")
    success = success and run_unittest_discover(
        os.path.join(current_dir, "client", "unit"),
        "unit тести клієнта"
    )

    print("\n--- Running client integration tests ---")
    success = success and run_unittest_discover(
        os.path.join(current_dir, "client", "integration"),
        "client integration tests"
    )

    print("\n--- Running client behavioral tests ---")
    success = success and run_behave_tests(
        os.path.join(current_dir, "client", "features"),
        "client behavioral tests"
    )

    return 0 if success else 1


if __name__ == "__main__":
    import sys
    sys.exit(run_client_tests())
