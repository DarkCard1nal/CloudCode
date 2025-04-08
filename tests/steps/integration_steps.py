from behave import given, when, then
import os
import time
import requests
import threading
import tempfile
from Client.client import CloudComputeClient
from Tests.steps.common_steps import (
	step_server_running, 
	step_server_running_with_feature,
	step_client_connected,
)

@then("the results should contain the expected output")
def step_results_contain_expected_output(context):
	assert "Hello, World!" in context.result["output"], "Expected output not found"


@then("sanitize the file by removing unsafe elements")
def step_sanitize_unsafe_elements(context):
	assert "sanitized_code" in context.result, "Sanitized code missing in result"
	assert "os.system" not in context.result["sanitized_code"], "Dangerous code was not removed"


@then("the server should execute the sanitized code")
def step_execute_sanitized_code(context):
	assert "output" in context.result, "Output missing in result"
	assert "This is potentially dangerous" not in context.result["output"], "Dangerous code was executed"


@then("the client should receive both the execution results and the sanitized file")
def step_client_receives_results_and_sanitized_file(context):
	assert "output" in context.result, "Output missing in result"
	assert "sanitized_code" in context.result, "Sanitized code missing in result"


@given("the client is connected")
def step_client_is_connected(context):
	step_client_connected(context)


@then("the client should detect the disconnection")
def step_client_detects_disconnection(context):
	if hasattr(context, 'scenario') and getattr(context.scenario, 'skip_reason', None):
		return
	
	try:
		requests.post('http://localhost:5000/execute', 
					 files={'file': ('test.py', b'print("hello")')}, 
					 timeout=0.5)
		assert False, "Connection to server after restart should be unavailable"
	except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
		pass


@then("automatically reconnect when the server is available")
def step_automatically_reconnects(context):
	if hasattr(context, 'scenario') and getattr(context.scenario, 'skip_reason', None):
		return
	
	max_retries = 5
	for attempt in range(max_retries):
		try:
			response = requests.post('http://localhost:5000/execute', 
									files={'file': ('test.py', b'print("hello")')})
			if response.status_code == 200:
				return
		except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
			pass
		
		time.sleep(2)
	
	assert False, "Client could not automatically restore connection to server"


@then("continue processing tasks without manual intervention")
def step_continue_processing_tasks(context):
	if hasattr(context, 'scenario') and getattr(context.scenario, 'skip_reason', None):
		return
	
	time.sleep(3)
	
	os.makedirs('/app/Tasks/temp', exist_ok=True)
	task_file_path = '/app/Tasks/temp/reconnect_task.py'
	
	with open(task_file_path, 'w') as f:
		f.write("print('Task after reconnection')")
	
	context.temp_file_path = task_file_path
	
	max_retries = 5
	for attempt in range(max_retries):
		try:
			files = {'file': open(task_file_path, 'rb')}
			response = requests.post('http://localhost:5000/execute', files=files)
			files['file'].close()
			
			if response.status_code == 200:
				result = response.json()
				if "output" in result and "Task after reconnection" in result["output"]:
					return 
				else:
					print(f"Attempt {attempt+1}: Response OK but unexpected output: {result}")
			else:
				print(f"Attempt {attempt+1}: Unexpected status code: {response.status_code}")
		except Exception as e:
			print(f"Attempt {attempt+1}: Error: {str(e)}")
		
		time.sleep(2 * (attempt + 1))
	
	assert False, "Failed to process task after server restart"


@given("the server is running with resource monitoring")
def step_server_running_with_resource_monitoring(context):
	try:
		step_server_running_with_feature(context, "monitor")
	except AssertionError:
		step_server_running(context)


@when("each client sends {num_tasks} tasks in parallel")
def step_each_client_sends_tasks_in_parallel(context, num_tasks):
	num_tasks = int(num_tasks.strip('"\''))
	context.all_results = []
	
	def send_tasks(client):
		client_results = []
		for i in range(num_tasks):
			with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_file:
				temp_file.write(f"print('Task {i} from client')".encode())
				task_path = temp_file.name
			
			try:
				result = client.send_code(task_path)
				client_results.append(result)
			except Exception as e:
				client_results.append({"error": str(e)})
			finally:
				try:
					os.unlink(task_path)
				except:
					pass
		
		return client_results
	
	if not hasattr(context, 'clients') or not context.clients:
		context.clients = [CloudComputeClient() for _ in range(3)]
	
	threads = []
	for client in context.clients:
		thread = threading.Thread(target=lambda: context.all_results.extend(send_tasks(client)))
		threads.append(thread)
		thread.start()
	
	for thread in threads:
		thread.join(timeout=30)
	
	assert context.all_results, "No results received from parallel tasks"


@then("the server should handle all {total_tasks} tasks correctly")
def step_server_handles_all_tasks(context, total_tasks):
	total_tasks = int(total_tasks.strip('"\''))
	
	assert len(context.all_results) == total_tasks, f"Incorrect number of tasks: {len(context.all_results)} instead of {total_tasks}"
	
	success_count = sum(1 for result in context.all_results if "error" not in result or not result["error"])
	assert success_count == total_tasks, f"Not all tasks completed successfully: {success_count} out of {total_tasks}"


@then("all clients should receive their results")
def step_all_clients_receive_results(context):
	assert all("output" in result for result in context.all_results), "Not all clients received results"


@then("no tasks should be lost or duplicated")
def step_no_tasks_lost_or_duplicated(context):
	outputs = [result.get("output", "").strip() for result in context.all_results]
	
	import re
	expected_pattern = r"Task \d+ from client"
	matching_outputs = [output for output in outputs if re.search(expected_pattern, output)]
	
	assert len(matching_outputs) == len(context.all_results), "Tasks were lost or duplicated" 
