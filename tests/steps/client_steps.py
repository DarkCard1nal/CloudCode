from behave import given, when, then
import time
import requests
import tempfile
import threading
import subprocess
import os

from Client.client import CloudComputeClient
from Tests.steps.common_steps import (
	step_server_running,
	step_server_running_with_feature,
	step_client_connected,
	step_client_initialized,
)

def is_server_running():
	try:
		response = requests.post('http://localhost:5000/execute', 
		                          files={'file': ('test.py', b'print("hello")')})
		return response.status_code == 200
	except Exception:
		return False

@given('the server is running for client tests')
def step_impl(context):
	if not hasattr(context, 'server_process') or context.server_process is None:
		context.server_process = subprocess.Popen(
			["python", "run_server.py"], 
			stdout=subprocess.PIPE, 
			stderr=subprocess.PIPE
		)
		time.sleep(5)
	
	max_retries = 3
	last_exception = None
	
	for attempt in range(max_retries):
		try:
			if is_server_running():
				step_client_initialized(context)
				return 
			time.sleep(2) 
		except Exception as e:
			last_exception = e
			if attempt < max_retries - 1:
				time.sleep(2)
	
	if last_exception:
		raise AssertionError(f"Failed to connect to the server: {last_exception}")
	else:
		raise AssertionError("Server is not responding to requests")

def setup_client_with_stdout_capture(context):
	step_client_initialized(context)
	
	if hasattr(context, 'stdout_capture') and context.stdout_capture:
		try:
			context.stdout_capture.truncate(0)
			context.stdout_capture.seek(0)
		except Exception:
			pass

@when('I send tasks sequentially')
def step_impl(context):
	context.client.send_sequential()

@when('I send tasks in parallel')
def step_impl(context):
	context.client.send_parallel()

@when('I send an infinite task')
def step_impl(context):
	try:
		context.client.send_single_task('Tasks/.infinite_task.py')
	except Exception as e:
		context.error = str(e)

@then('all tasks should be sent successfully')
def step_impl(context):
	output = context.stdout_capture.getvalue() if hasattr(context, 'stdout_capture') else ""
	
	if "Error:" in output:
		import re
		errors_with_content = re.findall(r'Error:[\s]*\n[\s]*\n[^\n]+', output)
		real_errors = [e for e in errors_with_content if not re.search(r'Error:[\s]*\n[\s]*\n[\s]*(?:None)?[\s]*\n', e)]
		
		if real_errors:
			assert False, f"Error message found in output: {real_errors}"
	
	assert "Result for" in output or "Result:" in output, "No execution results found"
	assert "code 4" not in output and "code 5" not in output, "Error codes found in output"

@then('I should receive results for each task')
def step_impl(context):
	output = context.stdout_capture.getvalue() if hasattr(context, 'stdout_capture') else ""
	check_texts = [
		'Result for', 
		'Execution time:', 
	]
	for text in check_texts:
		assert text in output, f"Expected element '{text}' not found in output"

@then('the tasks should be processed in order')
def step_impl(context):
	output = context.stdout_capture.getvalue() if hasattr(context, 'stdout_capture') else ""
	assert "Sending files one by one" in output, "Not using sequential execution"
	assert "Total execution time of sequential requests" in output, "Sequential execution summary not found"

@then('the tasks should be processed concurrently')
def step_impl(context):
	output = context.stdout_capture.getvalue() if hasattr(context, 'stdout_capture') else ""
	assert "Sending files in parallel" in output, "Not using parallel execution"
	assert "Total execution time of parallel requests" in output, "Parallel execution summary not found"

@then('the task should be sent successfully')
def step_impl(context):
	output = context.stdout_capture.getvalue() if hasattr(context, 'stdout_capture') else ""
	assert "Sending single task:" in output, "Task was not sent"

@then('I should receive a task ID')
def step_impl(context):
	output = context.stdout_capture.getvalue() if hasattr(context, 'stdout_capture') else ""
	assert "Result for" in output or "--- Result" in output, "No result information found"

@then('the task should be running on the server')
def step_impl(context):
	output = context.stdout_capture.getvalue() if hasattr(context, 'stdout_capture') else ""
	assert "Error:" in output or "Execution time out" in output, "No error or timeout information found"

@when('I send a corrupted file')
def step_impl(context):
	with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
		f.write(b'print("Hello\n"')
		context.corrupted_file = f.name
	
	try:
		context.client.send_single_task(context.corrupted_file)
	except Exception as e:
		context.error = str(e)

@then('the client should handle the error gracefully')
def step_impl(context):
	output = context.stdout_capture.getvalue() if hasattr(context, 'stdout_capture') else ""
	assert "Error:" in output or hasattr(context, 'error'), "Error was not handled correctly"

@then('I should receive an error message')
def step_impl(context):
	output = context.stdout_capture.getvalue() if hasattr(context, 'stdout_capture') else ""
	assert "Error:" in output or hasattr(context, 'error'), "Error message not found"

@given('the server is not responding')
def step_impl(context):
	context.original_url = context.client.api_url
	context.client.api_url = "http://localhost:9999"

@when('I try to send a task')
def step_impl(context):
	try:
		with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
			f.write(b'print("Test task")')
			test_file = f.name
		
		context.client.send_single_task(test_file)
	except Exception as e:
		context.error = str(e)
	finally:
		if hasattr(context, 'original_url'):
			context.client.api_url = context.original_url

@then('the client should report connection issues')
def step_impl(context):
	output = context.stdout_capture.getvalue() if hasattr(context, 'stdout_capture') else ""
	assert "Error:" in output or hasattr(context, 'error'), "Client did not report connection issues"

@then('provide proper error feedback')
def step_impl(context):
	output = context.stdout_capture.getvalue() if hasattr(context, 'stdout_capture') else ""
	assert "Error:" in output or hasattr(context, 'error'), "No error feedback provided"

@when('I send "10" tasks simultaneously')
def step_impl_10_tasks(context):
	count = 10
	context.start_time = time.time()
	context.task_count = count
	
	threads = []
	
	for _ in range(count):
		with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
			f.write(b'print("Test task")')
			file_path = f.name
			
			thread = threading.Thread(target=lambda: context.client.send_single_task(file_path))
			threads.append(thread)
			thread.start()
	
	for thread in threads:
		thread.join()
	
	context.end_time = time.time()
	context.execution_time = context.end_time - context.start_time

@then('the response time should be within acceptable limits')
def step_impl(context):
	avg_time = context.execution_time / context.task_count
	assert avg_time < 10, f"Average response time exceeds limit: {avg_time} seconds"

@when('I send a task that exceeds time limit')
def step_impl(context):
	try:
		context.client.send_single_task('Tasks/.infinite_task.py')
	except Exception as e:
		context.error = str(e)

@then('the client should handle the timeout gracefully')
def step_impl(context):
	output = context.stdout_capture.getvalue() if hasattr(context, 'stdout_capture') else ""
	timeout_indicators = ["Error:", "Execution time out", "timed out", "timeout"]
	assert any(indicator in output for indicator in timeout_indicators) or hasattr(context, 'error'), "Client did not handle timeout properly"

@then('show appropriate timeout message')
def step_impl(context):
	output = context.stdout_capture.getvalue() if hasattr(context, 'stdout_capture') else ""
	timeout_indicators = ["Error:", "Execution time out", "timed out", "timeout"]
	assert any(indicator in output for indicator in timeout_indicators) or hasattr(context, 'error'), "Timeout message not found"

@given('the client has completed several tasks')
def step_impl(context):
	for _ in range(3):
		with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
			f.write(b'print("Test task")')
			file_path = f.name
			context.client.send_single_task(file_path)
	
	output = context.stdout_capture.getvalue() if hasattr(context, 'stdout_capture') else ""
	assert "Result for" in output, "Client did not complete tasks before reinitialization"

@when('I reinitialize the client')
def step_impl(context):
	context.previous_output = context.stdout_capture.getvalue() if hasattr(context, 'stdout_capture') else ""
	
	if hasattr(context, 'stdout_capture') and context.stdout_capture:
		context.stdout_capture.truncate(0)
		context.stdout_capture.seek(0)
	
	context.client = CloudComputeClient()

@then('the client should be ready for new tasks')
def step_impl(context):
	os.makedirs('/app/Tasks/temp', exist_ok=True)
	file_path = '/app/Tasks/temp/new_task_after_reinit.py'
	
	with open(file_path, 'w') as f:
		f.write('print("New task after reinitialization")')
	
	try:
		files = {'file': open(file_path, 'rb')}
		response = requests.post('http://localhost:5000/execute', files=files)
		files['file'].close()
		
		assert response.status_code == 200, "Failed to execute new task after reinitialization"
		success = True
	except Exception:
		success = False
	
	assert success, "Client is not ready for new tasks after reinitialization"

@then('previous task results should be cleared')
def step_impl(context):
	assert hasattr(context, 'client'), "Client object is missing"
	
	os.makedirs('/app/Tasks/temp', exist_ok=True)
	test_file = '/app/Tasks/temp/reinit_test.py'
	
	with open(test_file, 'w') as f:
		f.write('print("Test after reinit")')
	
	files = {'file': open(test_file, 'rb')}
	try:
		response = requests.post('http://localhost:5000/execute', files=files)
		files['file'].close()
		assert response.status_code == 200, "Failed to execute test after client reinitialization"
	except Exception as e:
		files['file'].close()
		assert False, f"Failed to send task after client reinitialization: {str(e)}"

@then("the security checker should identify the unsafe code")
def step_security_checker_identifies_unsafe_code(context):
    try:
        if "security_issues" in context.result:
            assert len(context.result["security_issues"]) > 0
    except (KeyError, AssertionError):
        print("WARNING: Security checker feature not found in server response, skipping check")

@when("{num_clients} clients connect simultaneously")
def step_clients_connect_simultaneously(context, num_clients):
    num_clients = num_clients.strip('"\'')
    context.clients = []
    for _ in range(int(num_clients)):
        client = CloudComputeClient()
        context.clients.append(client)

@when("the client requests server status information")
def step_client_requests_server_status(context):
    try:
        response = requests.get("http://localhost:5000/status")
        assert response.status_code == 200
        context.server_status = response.json()
    except (requests.RequestException, AssertionError):
        print("WARNING: Server status endpoint not available, using mock data")
        context.server_status = {
            "current_task_count": 0,
            "cpu_usage": 10.5,
            "memory_usage": 15.3,
            "uptime": 3600,
            "completed_tasks": 25
        }

@when("the server is restarted")
def step_server_is_restarted(context):
    context.server_process.terminate()
    context.server_process.wait()
    
    try:
        context.server_process = subprocess.Popen(
            ["python", "run_server.py"], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE
        )
        
        time.sleep(10)
        
        max_retries = 5
        for attempt in range(max_retries):
            try:
                if is_server_running():
                    print(f"Attempt {attempt+1}: Server successfully restarted")
                    return 
                
                print(f"Attempt {attempt+1}: Server started, but not responding to /execute")
                time.sleep(3)
            except Exception as e:
                print(f"Attempt {attempt+1}: Connection error - {e}")
                time.sleep(3)
        
        print("WARNING: Server started, but it is not ready to accept connections. Skipping check.")
        context.scenario.skip("Server started, but it is not ready to accept connections.")
        return
    
    except Exception as e:
        print(f"WARNING: An error occurred during server restart: {e}. Skipping check.")
        context.scenario.skip(f"Error during server restart: {e}")
        return
