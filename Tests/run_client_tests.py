#!/usr/bin/env python3
import unittest
import os
import sys
import subprocess
import shutil

def run_client_tests():
	"""Runs all client tests (unit, integration, and behavioral)"""
	current_dir = os.path.dirname(os.path.abspath(__file__))
	parent_dir = os.path.dirname(current_dir)
	sys.path.append(parent_dir)
	
	success = True
	
	print("\n--- Running client unit tests ---")
	unit_result = subprocess.run([
		"python", "-m", "unittest", "discover",
		"-s", os.path.join(current_dir, "client", "unit"), 
		"-p", "test_*.py"
	], capture_output=False)
	success = success and (unit_result.returncode == 0)
	
	print("\n--- Running client integration tests ---")
	integration_result = subprocess.run([
		"python", "-m", "unittest", "discover",
		"-s", os.path.join(current_dir, "client", "integration"), 
		"-p", "test_*.py"
	], capture_output=False)
	success = success and (integration_result.returncode == 0)
	
	try:
		import behave
		print("\n--- Running client behavioral tests ---")
		features_dir = os.path.join(current_dir, "client", "features")
		
		if not os.path.exists(features_dir):
			print(f"Directory '{features_dir}' does not exist. Skipping behavioral tests.")
			return 0 if success else 1
			
		feature_files = [f for f in os.listdir(features_dir) if f.endswith(".feature")]
		if not feature_files:
			print(f"No .feature files in directory '{features_dir}'. Skipping behavioral tests.")
			return 0 if success else 1
		
		behave_result = subprocess.run([
			"python", "-m", "behave", features_dir
		], capture_output=False)
		success = success and (behave_result.returncode == 0)
	except ImportError:
		print("Package 'behave' not found. Skipping behavioral tests.")
	except Exception as e:
		print(f"Error running behavioral tests: {str(e)}")
	
	return 0 if success else 1

if __name__ == '__main__':
	sys.exit(run_client_tests()) 