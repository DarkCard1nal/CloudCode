from behave import given, when, then
import os
import time
import tempfile
import requests
import subprocess
from Client.client import CloudComputeClient

@given("the server is running")
def step_server_running(context):
	"""Starting the server if it's not already running"""
	if not hasattr(context, 'server_process') or context.server_process is None:
		context.server_process = subprocess.Popen(
			["python", "run_server.py"], 
			stdout=subprocess.PIPE, 
			stderr=subprocess.PIPE
		)
		time.sleep(0.3)
	
	max_retries = 3
	last_exception = None
	
	for attempt in range(max_retries):
		try:
			response = requests.get("http://localhost:5000/health", timeout=0.5)
			if response.status_code == 200:
				return
		except (requests.RequestException, ConnectionError) as e:
			last_exception = e
			if attempt < max_retries - 1:
				time.sleep(0.2)
	
	if last_exception:
		raise AssertionError(f"Failed to connect to the server: {last_exception}")
	else:
		raise AssertionError(f"Server returned code {response.status_code}")

@given("the server is running with {feature} enabled")
def step_server_running_with_feature(context, feature):
	"""Starting the server with a specific feature"""
	feature_flag = f"--{feature.replace(' ', '-')}=enabled"
	
	if not hasattr(context, 'server_process') or context.server_process is None:
		context.server_process = subprocess.Popen(
			["python", "run_server.py", feature_flag], 
			stdout=subprocess.PIPE, 
			stderr=subprocess.PIPE
		)
		time.sleep(0.3)
	
	max_retries = 3
	last_exception = None
	
	for attempt in range(max_retries):
		try:
			response = requests.post('http://localhost:5000/execute', 
									files={'file': ('test.py', b'print("hello")')})
			
			if response.status_code == 200:
				if "security_checker" in feature.lower() or "monitor" in feature.lower():
					return
					
				api_feature_name = feature.lower().replace(" ", "_")
				result = response.json()
				if "features" in result and api_feature_name in result["features"]:
					assert result["features"][api_feature_name] == "enabled"
				
				return
				
		except (requests.RequestException, ConnectionError, KeyError, AssertionError) as e:
			last_exception = e
			if attempt < max_retries - 1:
				time.sleep(0.2)
	
	if last_exception:
		raise AssertionError(f"Failed to connect to the server: {last_exception}")
	else:
		raise AssertionError(f"Server returned code {response.status_code}")

@given("the client is initialized")
def step_client_initialized(context):
	"""Client initialization"""
	context.client = CloudComputeClient()


@given("the client is connected to the server")
def step_client_connected(context):
	"""Client initialization and connection check with the server"""
	context.client = CloudComputeClient()
	try:
		response = requests.post('http://localhost:5000/execute', 
							   files={'file': ('test.py', b'print("hello")')})
		assert response.status_code == 200, f"Server returned code {response.status_code}"
	except Exception as e:
		raise AssertionError(f"Failed to connect to the server: {e}")

def create_python_file(content, delete=False):
	"""Creating a temporary Python file with the specified content"""
	uploads_dir = '/uploads'
	
	task_id = str(int(time.time() * 1000))
	task_dir = os.path.join(uploads_dir, task_id)
	os.makedirs(task_dir, exist_ok=True)
	
	file_path = os.path.join(task_dir, "test_script.py")
	with open(file_path, 'w', encoding='utf-8') as f:
		if isinstance(content, str):
			f.write(content)
		else:
			f.write(content.decode())
	
	return file_path

@when("I send a file with content to the server:")
def step_send_file_with_content(context):
	"""Sending a file to the server with content from the data table"""
	content = context.text
	file_path = create_python_file(content)
	context.temp_file_path = file_path
	
	context.result = context.client.send_code(file_path)


@when("I send a Python file with {code_type} code from the client")
def step_send_python_file_from_client(context, code_type):
	"""Sending a Python file with a specific type of code"""
	if code_type == "safe":
		content = """
def greet(name):
	return f"Hello, {name}!"

result = greet("World")
print(result)
"""
	elif code_type == "unsafe":
		content = """
import os

def dangerous_operation():
	os.system("echo 'This is potentially dangerous'")
	
dangerous_operation()
"""
	else:
		content = f"print('This is a {code_type} code example')"
	
	file_path = create_python_file(content)
	context.temp_file_path = file_path
	
	context.result = context.client.send_code(file_path)


@then("the task should complete successfully")
def step_task_completes_successfully(context):
	"""Checking successful task completion"""
	assert "output" in context.result
	assert "error" not in context.result or not context.result["error"]


@then("the server should execute the code successfully")
def step_server_executes_code(context):
	"""Checking successful code execution on the server"""
	assert "output" in context.result
	assert "error" not in context.result or not context.result["error"]


@then("the client should receive the execution results")
def step_client_receives_results(context):
	"""Checking that the client received execution results"""
	assert "output" in context.result
	assert "execution_time_ms" in context.result


def cleanup_resources(context):
	"""Cleaning up resources after test completion"""
	uploads_dir = os.path.join(os.getcwd(), 'uploads')
	if os.path.exists(uploads_dir):
		for item in os.listdir(uploads_dir):
			item_path = os.path.join(uploads_dir, item)
			if item in ['server_test', 'client_test', 'integration_test']:
				continue
			try:
				if os.path.isfile(item_path):
					os.unlink(item_path)
				elif os.path.isdir(item_path):
					shutil.rmtree(item_path)
			except Exception as e:
				print(f"Error removing {item_path}: {e}")
	
	for attr in ['temp_file_path', 'valid_task', 'invalid_task', 'corrupted_file']:
		if hasattr(context, attr):
			file_path = getattr(context, attr)
			if file_path and os.path.exists(file_path):
				try:
					if os.path.isfile(file_path):
						os.unlink(file_path)
					elif os.path.isdir(os.path.dirname(file_path)):
						shutil.rmtree(os.path.dirname(file_path))
				except Exception as e:
					print(f"Error removing {attr}: {e}")
	
	if hasattr(context, 'server_process') and context.server_process:
		try:
			context.server_process.terminate()
			context.server_process.wait(timeout=5)
		except Exception as e:
			print(f"Error terminating the server: {e}")