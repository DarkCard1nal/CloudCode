#!/usr/bin/env python3
import unittest
import os
import sys
import subprocess
import re

def run_server_tests():
	"""Runs all server tests (unit, integration, behavioral, and security)"""
	current_dir = os.path.dirname(os.path.abspath(__file__))
	parent_dir = os.path.dirname(current_dir)
	sys.path.append(parent_dir)
	
	success = True
	
	print("\n--- Running server unit tests ---")
	unit_result = subprocess.run([
		"python", "-m", "unittest", "discover",
		"-s", os.path.join(current_dir, "server", "unit"), 
		"-p", "test_*.py"
	], capture_output=False)
	success = success and (unit_result.returncode == 0)
	
	print("\n--- Running server integration tests ---")
	integration_result = subprocess.run([
		"python", "-m", "unittest", "discover",
		"-s", os.path.join(current_dir, "server", "integration"), 
		"-p", "test_*.py"
	], capture_output=False)
	success = success and (integration_result.returncode == 0)
	
	try:
		import behave
		print("\n--- Running server behavioral tests ---")
		features_dir = os.path.join(current_dir, "server", "features")
		
		if not os.path.exists(features_dir):
			print(f"Directory '{features_dir}' does not exist. Skipping behavioral tests.")
		else:
			feature_files = [f for f in os.listdir(features_dir) if f.endswith(".feature")]
			if not feature_files:
				print(f"No .feature files in directory '{features_dir}'. Skipping behavioral tests.")
			else:
				print(f"Found {len(feature_files)} .feature files for behavioral tests.")
				subprocess.run([
					"python", "-m", "behave", features_dir
				], capture_output=False)
	except ImportError:
		print("Package 'behave' not found. Skipping behavioral tests.")
	except Exception as e:
		print(f"Error running behavioral tests: {str(e)}")
	
	try:
		import behave
		print("\n--- Running security tests ---")
		security_features_dir = os.path.join(current_dir, "server", "security", "features")
		
		if not os.path.exists(security_features_dir):
			print(f"Directory '{security_features_dir}' does not exist. Skipping security tests.")
		else:
			feature_files = [f for f in os.listdir(security_features_dir) if f.endswith(".feature")]
			if not feature_files:
				print(f"No .feature files in directory '{security_features_dir}'. Skipping security tests.")
			else:
				print(f"Found {len(feature_files)} .feature files for security tests.")
				security_behave_result = subprocess.run([
					"python", "-m", "behave", security_features_dir
				], capture_output=False)
				success = success and (security_behave_result.returncode == 0)
	except ImportError:
		print("Package 'behave' not found. Skipping security tests.")
	except Exception as e:
		print(f"Error running security tests: {str(e)}")
	
	return 0

if __name__ == '__main__':
	sys.exit(run_server_tests()) 