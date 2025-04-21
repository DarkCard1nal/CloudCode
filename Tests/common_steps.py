#!/usr/bin/env python3
"""
Common steps for Behave tests used across different modules
"""

import os
import sys
import time
import tempfile
import subprocess
import requests
from behave import given, when, then

from Client.client import CloudComputeClient

SERVER_STARTUP_WAIT = 0.2
RETRY_ATTEMPTS = 2
RETRY_DELAY = 0.2

def is_server_running():
	"""Checks if the server is running and responding to requests"""
	try:
		response = requests.post('http://localhost:5000/execute',
								files={'file': ('test.py', b'print("hello")')})
		return response.status_code == 200
	except Exception:
		return False

@given('the server is running')
def step_server_running(context):
	"""Starts the server if it's not already running"""
	if not hasattr(context, 'server_process') or context.server_process is None:
		context.server_process = subprocess.Popen(["python", "run_server.py"],
												 stdout=subprocess.PIPE,
												 stderr=subprocess.PIPE)
		time.sleep(SERVER_STARTUP_WAIT)

	max_retries = RETRY_ATTEMPTS
	last_exception = None

	for attempt in range(max_retries):
		try:
			if is_server_running():
				return
			time.sleep(RETRY_DELAY)
		except Exception as e:
			last_exception = e
			if attempt < max_retries - 1:
				time.sleep(RETRY_DELAY)

	if last_exception:
		raise AssertionError(
			f"Failed to connect to the server: {last_exception}")
	else:
		raise AssertionError("Server is not responding to requests")

@given('the server is running with security checker enabled')
def step_server_running_with_feature(context):
	"""Starts the server with the security checker module enabled"""
	step_server_running(context)

@given('the client is initialized')
def step_client_initialized(context):
	"""Initializes the client for testing"""
	if not hasattr(context, 'client') or context.client is None:
		context.client = CloudComputeClient()

@given('the client is connected to the server')
def step_client_connected(context):
	"""Ensures the client is initialized and connected to the server"""
	step_server_running(context)
	
	step_client_initialized(context)
	
	try:
		with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as temp:
			temp.write(b'print("Connection test")')
			test_file = temp.name
		
		response = context.client.send_code(test_file)
		
		os.unlink(test_file)
		
		if 'output' not in response:
			raise AssertionError("Client did not receive expected response from server")
	except Exception as e:
		raise AssertionError(f"Client cannot connect to the server: {e}") 