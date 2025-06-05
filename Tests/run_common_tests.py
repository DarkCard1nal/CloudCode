#!/usr/bin/env python3
import os
from test_helpers import setup_test_paths, run_behave_tests, run_unittest_discover


def run_common_tests():
    """Runs all common tests (integration and behavioral)"""
    current_dir, parent_dir = setup_test_paths()
    success = True

    print("\n--- Running all general tests ---")
    success = success and run_unittest_discover(
        os.path.join(current_dir, "common"),
        "general tests"
    )

    print("\n--- Running general behavioral tests ---")
    success = success and run_behave_tests(
        os.path.join(current_dir, "common", "features"),
        "general behavioral tests"
    )

    return 0 if success else 1


if __name__ == "__main__":
    import sys
    sys.exit(run_common_tests())
