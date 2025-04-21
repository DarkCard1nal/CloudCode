#!/usr/bin/env python3
import unittest
import os
import sys

def run_tests():
	"""Runs all unit tests from the tests directory structure"""
	current_dir = os.path.dirname(os.path.abspath(__file__))
	parent_dir = os.path.dirname(current_dir)
	sys.path.append(parent_dir)
	
	test_paths = [
		os.path.join(current_dir, 'server', 'unit'),
		os.path.join(current_dir, 'client', 'unit'),
		os.path.join(current_dir, 'common', 'unit') if os.path.exists(os.path.join(current_dir, 'common', 'unit')) else None
	]
	
	test_suite = unittest.TestSuite()
	for path in test_paths:
		if path and os.path.exists(path):
			discovered_tests = unittest.defaultTestLoader.discover(path, pattern='test_*.py')
			test_suite.addTests(discovered_tests)
	
	test_runner = unittest.TextTestRunner(verbosity=2)
	result = test_runner.run(test_suite)
	
	return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
	sys.exit(run_tests())