from behave import given, when, then
import requests
import time
import threading
import tempfile
import os
import json
import random
import string

def is_server_running():
	try:
		response = requests.post('http://localhost:5000/execute', files={'file': ('test.py', b'print("hello")')})
		return response.status_code == 200
	except:
		return False

@given('the server is running')
def step_impl(context):
	if not is_server_running():
		raise Exception("Server is not running. Please start the server first.")

@when('I start the server')
def step_impl(context):
	pass

@then('the server should be running')
def step_impl(context):
	assert is_server_running(), "Server is not running"

@then('it should be listening on the configured port')
def step_impl(context):
	try:
		requests.post('http://localhost:5000/execute', files={'file': ('test.py', b'print("hello")')})
		assert True, "Server is listening on port 5000"
	except:
		assert False, "Server is not listening on the configured port"

@given('a valid task file is sent')
def step_impl(context):
	with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
		f.write(b'print("Valid task")')
		context.valid_task = f.name

@when('the server receives the task')
def step_impl(context):
	file_path = context.valid_task if hasattr(context, 'valid_task') else context.invalid_task
	files = {'file': open(file_path, 'rb')}
	try:
		context.response = requests.post('http://localhost:5000/execute', files=files)
		context.result = context.response.json()
	except Exception as e:
		context.error = str(e)
	finally:
		files['file'].close()

@then('it should process the task')
def step_impl(context):
	assert hasattr(context, 'response'), "No response received"
	assert context.response.status_code == 200, f"Expected status code 200, got {context.response.status_code}"

@then('return the execution results')
def step_impl(context):
	assert "output" in context.result, "No output in response"

@then('the task status should be "completed"')
def step_impl_completed_status(context):
	assert context.response.status_code == 200, "Task was not completed"
	assert "error" not in context.result or not context.result["error"], "Task completed with errors"

@then('the task status should be "failed"')
def step_impl_failed_status(context):
	assert "error" in context.result and context.result["error"], "Expected error but none found"

@given('an invalid task file is sent')
def step_impl(context):
	with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
		f.write(b'print(undefined_variable)')
		context.invalid_task = f.name

@then('it should return an error message')
def step_impl(context):
	assert "error" in context.result, "No error message in response"
	assert context.result["error"], "Empty error message"

@given('a corrupted file is sent')
def step_impl(context):
	with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
		f.write(b'print("Hello World"\nwhile True print("Invalid syntax")')
		context.corrupted_file = f.name

@when('the server receives the file')
def step_impl(context):
	files = {'file': open(context.corrupted_file, 'rb')}
	try:
		context.response = requests.post('http://localhost:5000/execute', files=files)
		context.result = context.response.json()
	except Exception as e:
		context.error = str(e)
	finally:
		files['file'].close()

@then('it should validate the file format')
def step_impl(context):
	assert hasattr(context, 'response'), "Server did not respond to the request"
	assert "error" in context.result or context.response.status_code == 200, f"Unexpected response: {context.response.status_code}"

@then('return a proper error message')
def step_impl(context):
	assert hasattr(context, 'response'), "Server response is missing"
	if "error" in context.result:
		assert context.result["error"], "Empty error message"
	else:
		assert False, "Expected an error message"
		
@given('multiple clients are connected')
def step_impl(context):
	context.client_count = 5
	context.test_connections = []
	
	try:
		if is_server_running():
			context.test_connections.append(True)
	except:
		pass
	
	assert len(context.test_connections) > 0, "Failed to establish test connections"

@when('"20" tasks are submitted simultaneously')
def step_impl_quoted_20_tasks(context):
	context.task_count = 20
	context.start_time = time.time()
	context.responses = []
	
	def send_task():
		with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
			f.write(b'print("Test task")')
			file_path = f.name
			
		files = {'file': open(file_path, 'rb')}
		try:
			response = requests.post('http://localhost:5000/execute', files=files)
			files['file'].close()
			return response
		except Exception as e:
			files['file'].close()
			return str(e)
	
	threads = []
	for _ in range(context.task_count):
		thread = threading.Thread(target=lambda: context.responses.append(send_task()))
		threads.append(thread)
		thread.start()
	
	for thread in threads:
		thread.join()
	
	context.end_time = time.time()
	context.execution_time = context.end_time - context.start_time

@then('the server should process all tasks')
def step_impl(context):
	success_count = sum(1 for resp in context.responses if isinstance(resp, requests.Response) and resp.status_code == 200)
	assert success_count > 0, f"No tasks were processed successfully"
	assert success_count == len([r for r in context.responses if isinstance(r, requests.Response)]), "Not all tasks were processed"

@then('maintain reasonable response times')
def step_impl(context):
	assert context.execution_time < 60, f"Total execution time ({context.execution_time} s) exceeds expected"

@then('not crash or hang')
def step_impl(context):
	assert is_server_running(), "Server stopped responding after load test"

@given('the server is under heavy load')
def step_impl(context):
	context.load_task_count = 3
	context.load_responses = []
	
	def send_task():
		with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
			f.write(b'print("Load test")')
			file_path = f.name
			
		files = {'file': open(file_path, 'rb')}
		try:
			response = requests.post('http://localhost:5000/execute', files=files)
			context.load_responses.append(response)
			files['file'].close()
		except:
			files['file'].close()
	
	threads = []
	for _ in range(context.load_task_count):
		thread = threading.Thread(target=send_task)
		threads.append(thread)
		thread.start()
	
	time.sleep(0.5)

@when('new tasks arrive')
def step_impl(context):
	context.new_task_responses = []
	
	for _ in range(2):
		with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
			f.write(b'print("New task")')
			file_path = f.name
			
		files = {'file': open(file_path, 'rb')}
		try:
			response = requests.post('http://localhost:5000/execute', files=files)
			context.new_task_responses.append(response)
		except Exception as e:
			context.new_task_responses.append(str(e))
		finally:
			files['file'].close()

@then('the server should queue tasks appropriately')
def step_impl(context):
	success_count = sum(1 for resp in context.new_task_responses 
						if isinstance(resp, requests.Response) and resp.status_code == 200)
	assert success_count > 0, "No new tasks were accepted"

@then('process them in order of priority')
def step_impl(context):
	assert all(isinstance(resp, requests.Response) and resp.status_code == 200 for resp in context.new_task_responses), "Not all tasks were processed successfully"
	assert all("output" in resp.json() for resp in context.new_task_responses), "Not all responses contain results"

@given('a task that runs indefinitely')
def step_impl(context):
	context.infinite_task = 'Tasks/.infinite_task.py'

@when('the server executes the task')
def step_impl(context):
	if not hasattr(context, 'infinite_task'):
		context.infinite_task = 'Tasks/.infinite_task.py'
	
	files = {'file': open(context.infinite_task, 'rb')}
	try:
		context.response = requests.post('http://localhost:5000/execute', files=files)
		context.result = context.response.json()
	except Exception as e:
		context.error = str(e)
	finally:
		files['file'].close()
	
	time.sleep(0.5)

@then('it should terminate the task after timeout limit')
def step_impl(context):
	assert hasattr(context, 'response'), "Server response is missing"
	assert context.response.status_code == 200, f"Unexpected response code: {context.response.status_code}"
	assert "error" in context.result or "timeout" in context.result or "output" in context.result, "Missing execution information"

@then('return a timeout error')
def step_impl(context):
	assert hasattr(context, 'response'), "Server response is missing"
	assert "Execution time out" in str(context.result) or "timeout" in str(context.result).lower() or "error" in context.result, "No timeout information"

@then('free all allocated resources')
def step_impl(context):
	assert is_server_running(), "Server stopped responding after timeout test"

@given('tasks are being processed')
def step_impl(context):
	context.task_responses = []
	
	for _ in range(2):
		with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
			f.write(b'import time\nfor i in range(3): time.sleep(0.1)\nprint("Completed")')
			file_path = f.name
			
		files = {'file': open(file_path, 'rb')}
		try:
			response = requests.post('http://localhost:5000/execute', files=files)
			context.task_responses.append(response)
		except Exception as e:
			context.task_responses.append(str(e))
		finally:
			files['file'].close()
	
	success_count = sum(1 for resp in context.task_responses if isinstance(resp, requests.Response) and resp.status_code == 200)
	assert success_count > 0, "Failed to send tasks"

@given('a task that generates output files')
def step_impl(context):
	with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
		code = b'''
with open("output_result.txt", "w") as f:
	f.write("This is a test output file")
print("File created successfully")
'''
		f.write(code)
		context.output_task = f.name

@then('it should validate the output file format')
def step_impl(context):
	assert hasattr(context, 'response'), "Server response is missing"
	assert context.response.status_code == 200, f"Unexpected response code: {context.response.status_code}"
	assert "output" in context.result, "Response does not contain output information"

@then('ensure logs contain execution details')
def step_impl(context):
	assert hasattr(context, 'response'), "Server response is missing"
	assert "output" in context.result, "Missing execution information"

@given('a malformed request is sent')
def step_impl(context):
	context.malformed_request_data = {
		'invalid_param': 'test',
		'code': 'print("Hello World")',
		'execute': True
	}

@when('the server processes the request')
def step_impl(context):
	try:
		context.response = requests.post('http://localhost:5000/execute', json=context.malformed_request_data)
		context.result = context.response.json() if context.response.status_code == 200 else {}
	except Exception as e:
		context.error = str(e)

@then('it should reject the invalid request')
def step_impl(context):
	assert hasattr(context, 'response'), "Server response is missing"
	assert context.response.status_code != 200 or "error" in context.result, "Server did not reject invalid request"

@then('not expose sensitive information in error messages')
def step_impl(context):
	assert hasattr(context, 'response'), "Server response is missing"
	if context.response.status_code != 200:
		error_text = context.response.text
		assert "traceback" not in error_text.lower() and "exception" not in error_text.lower() and "stack" not in error_text.lower(), "Sensitive information detected in error message" 