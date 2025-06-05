import unittest
import os
from test_helpers import setup_test_paths


def run_tests():
    """Runs all integration tests from the test directory structure"""
    current_dir, parent_dir = setup_test_paths()

    test_paths = [
        os.path.join(current_dir, "server", "integration"),
        os.path.join(current_dir, "client", "integration"),
        os.path.join(current_dir, "common", "integration"),
    ]

    test_suite = unittest.TestSuite()
    for path in test_paths:
        if os.path.exists(path):
            discovered_tests = unittest.defaultTestLoader.discover(
                path, pattern="test_*.py"
            )
            test_suite.addTests(discovered_tests)

    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)

    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    import sys
    sys.exit(run_tests())
