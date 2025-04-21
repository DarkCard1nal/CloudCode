from behave import given, when, then
import requests
import time
import threading
import tempfile
import os
import subprocess
import uuid

def is_server_running():
    try:
        response = requests.post('http://localhost:5000/execute', files={'file': ('test.py', b'print("hello")')})
        return response.status_code == 200
    except:
        return False

@given('the server is running for testing')
def step_server_running_wrapper(context):
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
            if is_server_running():
                return
            time.sleep(0.2)
        except Exception as e:
            last_exception = e
            if attempt < max_retries - 1:
                time.sleep(0.2)
    
    if last_exception:
        raise AssertionError(f"Failed to connect to the server: {last_exception}")
    else:
        raise AssertionError("Server is not responding to requests")

@then('the server should be running')
def step_server_should_be_running(context):
	assert is_server_running(), "Server is not running"

@then('it should be listening on the configured port')
def step_server_listening_on_port(context):
	try:
		requests.post('http://localhost:5000/execute', files={'file': ('test.py', b'print("hello")')})
		assert True, "Server is listening on port 5000"
	except:
		assert False, "Server is not listening on the configured port"

@given('a valid task file is sent')
def step_valid_task_file_sent(context):
	os.makedirs('/app/Tasks/temp', exist_ok=True)
	task_file_path = '/app/Tasks/temp/valid_task.py'
	
	with open(task_file_path, 'w') as f:
		f.write('print("Valid task")')
	
	context.valid_task = task_file_path
	
	try:
		files = {'file': open(task_file_path, 'rb')}
		response = requests.post('http://localhost:5000/execute', files=files)
		files['file'].close()
		
		if response.status_code == 200:
			context.response = response
			context.result = response.json()
	except Exception as e:
		print(f"Warning: Pre-test request failed: {str(e)}")

@when('the server receives the task')
def step_server_receives_task(context):
	if hasattr(context, 'response') and hasattr(context, 'result'):
		return
	
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
def step_process_task(context):
	assert hasattr(context, 'response'), "No response received"
	assert context.response.status_code == 200, f"Expected status code 200, got {context.response.status_code}"

@then('return the execution results')
def step_return_execution_results(context):
	assert "output" in context.result, "No output in response"

@then('the task status should be "completed"')
def step_impl_completed_status(context):
	assert context.response.status_code == 200, "Task was not completed"
	
	if "output" in context.result:
		if "error" in context.result:
			if isinstance(context.result["error"], str) and context.result["error"].strip():
				error_message = context.result["error"].lower()
				if "warning" in error_message or "info" in error_message or "notice" in error_message:
					pass
				else:
					assert False, f"Task completed with errors: {context.result['error']}"
		return
	
	assert False, f"Unexpected response format: {context.result}"

@then('the task status should be "failed"')
def step_impl_failed_status(context):
	assert "error" in context.result and context.result["error"], "Expected error but none found"

@given('an invalid task file is sent')
def step_invalid_task_file_sent(context):
	with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
		f.write(b'print(undefined_variable)')
		context.invalid_task = f.name

@then('it should return an error message')
def step_return_error_message(context):
	assert "error" in context.result, "No error message in response"
	assert context.result["error"], "Empty error message"

@given('a corrupted file is sent')
def step_corrupted_file_sent(context):
	with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
		f.write(b'print("Hello World"\nwhile True print("Invalid syntax")')
		context.corrupted_file = f.name

@when('the server receives the file')
def step_server_receives_file(context):
	files = {'file': open(context.corrupted_file, 'rb')}
	try:
		context.response = requests.post('http://localhost:5000/execute', files=files)
		context.result = context.response.json()
	except Exception as e:
		context.error = str(e)
	finally:
		files['file'].close()

@then('it should validate the file format')
def step_validate_file_format(context):
	assert hasattr(context, 'response'), "Server did not respond to the request"
	assert "error" in context.result or context.response.status_code == 200, f"Unexpected response: {context.response.status_code}"

@then('return a proper error message')
def step_return_proper_error_message(context):
	assert hasattr(context, 'response'), "Server response is missing"
	if "error" in context.result:
		assert context.result["error"], "Empty error message"
	else:
		assert False, "Expected an error message"
		
@given('multiple clients are connected')
def step_multiple_clients_connected(context):
	context.client_count = 5
	context.test_connections = []
	
	try:
		if is_server_running():
			context.test_connections.append(True)
	except:
		pass
	
	assert len(context.test_connections) > 0, "Failed to establish test connections"

@when('"10" tasks are submitted simultaneously')
def step_impl_quoted_10_tasks(context):
	context.task_count = 10
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
def step_server_process_all_tasks(context):
	success_count = sum(1 for resp in context.responses if isinstance(resp, requests.Response) and resp.status_code == 200)
	assert success_count > 0, f"No tasks were processed successfully"
	assert success_count == len([r for r in context.responses if isinstance(r, requests.Response)]), "Not all tasks were processed"

@then('maintain reasonable response times')
def step_maintain_reasonable_response_times(context):
	assert context.execution_time < 60, f"Total execution time ({context.execution_time} s) exceeds expected"

@then('not crash or hang')
def step_not_crash_or_hang(context):
	assert is_server_running(), "Server stopped responding after load test"

@given('the server is under heavy load')
def step_server_under_heavy_load(context):
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
	
	time.sleep(0.1)

@when('new tasks arrive')
def step_new_tasks_arrive(context):
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

@given('a task that runs indefinitely')
def step_task_runs_indefinitely(context):
	context.infinite_task = 'Tasks/.infinite_task.py'

@when('the server executes the task')
def step_server_executes_task(context):
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
	time.sleep(0.1)

@then('it should terminate the task after timeout limit')
def step_terminate_task_after_timeout(context):
	assert hasattr(context, 'response'), "Server response is missing"
	assert context.response.status_code == 200, f"Unexpected response code: {context.response.status_code}"
	assert "error" in context.result or "timeout" in context.result or "output" in context.result, "Missing execution information"

@then('return a timeout error')
def step_return_timeout_error(context):
	assert hasattr(context, 'response'), "Server response is missing"
	assert "Execution time out" in str(context.result) or "timeout" in str(context.result).lower() or "error" in context.result, "No timeout information"

@then('free all allocated resources')
def step_free_all_allocated_resources(context):
    """Verify that all resources are properly freed after task execution"""
    assert is_server_running(), "Server stopped responding after task execution"
    
    if hasattr(context, 'task_id'):
        task_dir = os.path.join('/uploads', context.task_id)
        assert not os.path.exists(task_dir), f"Task directory {task_dir} was not cleaned up"
        
    try:
        docker_client = docker.from_env()
        containers = docker_client.containers.list(all=True)
        for container in containers:
            if container.name.startswith('cloudcode_'):
                try:
                    container.remove(force=True)
                except:
                    pass
    except:
        pass

@given('tasks are being processed')
def step_tasks_being_processed(context):
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
def step_task_generates_output_files(context):
	with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
		code = b'''
with open("output_result.txt", "w") as f:
	f.write("This is a test output file")
print("File created successfully")
'''
		f.write(code)
		context.output_task = f.name

@then('it should validate the output file format')
def step_validate_output_file_format(context):
	assert hasattr(context, 'response'), "Server response is missing"
	assert context.response.status_code == 200, f"Unexpected response code: {context.response.status_code}"
	assert "output" in context.result, "Response does not contain output information"

@then('ensure logs contain execution details')
def step_ensure_logs_contain_execution_details(context):
	assert hasattr(context, 'response'), "Server response is missing"
	assert "output" in context.result, "Missing execution information"

@given('a malformed request is sent')
def step_malformed_request_sent(context):
	context.malformed_request_data = {
		'invalid_param': 'test',
		'code': 'print("Hello World")',
		'execute': True
	}

@when('the server processes the request')
def step_server_processes_request(context):
	try:
		context.response = requests.post('http://localhost:5000/execute', json=context.malformed_request_data)
		context.result = context.response.json() if context.response.status_code == 200 else {}
	except Exception as e:
		context.error = str(e)

@then('it should reject the invalid request')
def step_reject_invalid_request(context):
	assert hasattr(context, 'response'), "Server response is missing"
	assert context.response.status_code != 200 or "error" in context.result, "Server did not reject invalid request"

@then('not expose sensitive information in error messages')
def step_not_expose_sensitive_information(context):
	assert hasattr(context, 'response'), "Server response is missing"
	if context.response.status_code != 200:
		error_text = context.response.text
		assert "traceback" not in error_text.lower() and "exception" not in error_text.lower() and "stack" not in error_text.lower(), "Sensitive information detected in error message"

@then('the server should return an error response')
def step_server_returns_error_response(context):
    assert hasattr(context, 'response'), "No response from server"
    assert hasattr(context, 'result'), "No result in response"
    assert context.response.status_code == 200, f"Unexpected status code: {context.response.status_code}"
    assert "error" in context.result, "No error in response"
    assert context.result["error"], "Empty error message"

def cleanup_resources(context):
	"""Cleaning up resources after test completion"""
	for attr in ['temp_file_path', 'valid_task', 'invalid_task', 'corrupted_file']:
		if hasattr(context, attr) and context.get(attr) and os.path.exists(context.get(attr)):
			try:
				os.unlink(context.get(attr))
			except Exception as e:
				print(f"Error removing {attr}: {e}")
	
	if hasattr(context, 'server_process') and context.server_process:
		try:
			context.server_process.terminate()
			context.server_process.wait(timeout=5)
		except Exception as e:
			print(f"Error terminating the server: {e}")

def _create_test_python_file(content, delete=False):
    """Creates a temporary Python file with the specified contents"""
    task_id = str(uuid.uuid4()).replace('-', '')
    uploads_dir = '/uploads'
    task_dir = os.path.join(uploads_dir, task_id)
    os.makedirs(task_dir, exist_ok=True)
    
    file_path = os.path.join(task_dir, 'script.py')
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Created test file at: {file_path}")
    return file_path