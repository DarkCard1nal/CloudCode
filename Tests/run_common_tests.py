#!/usr/bin/env python3
import os
import sys
import subprocess


def run_common_tests():
    """Run all common tests (integration and behavioral)"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.append(parent_dir)

    success = True

    print("\n--- Running all common tests ---")
    all_common_tests_result = subprocess.run(
        [
            "python",
            "-m",
            "unittest",
            "discover",
            "-s",
            os.path.join(current_dir, "common"),
            "-p",
            "test_*.py",
        ],
        capture_output=False,
    )
    success = success and (all_common_tests_result.returncode == 0)

    try:
        import behave

        print("\n--- Running common behavioral tests ---")
        features_dir = os.path.join(current_dir, "common", "features")

        if not os.path.exists(features_dir):
            print(
                f"The directory '{features_dir}' does not exist. Skipping behavioral tests."
            )
            return 0 if success else 1

        feature_files = [f for f in os.listdir(features_dir) if f.endswith(".feature")]
        if not feature_files:
            print(
                f"No .feature files found in '{features_dir}'. Skipping behavioral tests."
            )
            return 0 if success else 1

        behave_result = subprocess.run(
            ["python", "-m", "behave", features_dir], capture_output=False
        )
        success = success and (behave_result.returncode == 0)
    except ImportError:
        print("The 'behave' package is not installed. Skipping behavioral tests.")
    except Exception as e:
        print(f"Error while running behavioral tests: {str(e)}")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(run_common_tests())
