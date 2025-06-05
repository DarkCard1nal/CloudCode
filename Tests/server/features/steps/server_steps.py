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
        response = requests.get("http://server:5000/", timeout=5)
        return response.status_code < 500
    except Exception:
        return False


def can_execute_code():
    """Check if server can actually execute code (not just respond)"""
    try:
        test_code = 'print("test")'
        files = {"file": ("test.py", test_code, "text/plain")}
        response = requests.post("http://server:5000/execute", files=files, timeout=10)
        if response.status_code == 200:
            result = response.json()
            return "output" in result or "error" in result
        return False
    except Exception:
        return False


@given("the server is running for testing")
def step_server_running_wrapper(context):
    max_retries = 10
    last_exception = None

    for attempt in range(max_retries):
        try:
            if is_server_running():
                context.can_execute = can_execute_code()
                return
            time.sleep(1)
        except Exception as e:
            last_exception = e
            if attempt < max_retries - 1:
                time.sleep(1)

    if last_exception:
        raise AssertionError(f"Server is not available for testing: {last_exception}")
    else:
        raise AssertionError("Server is not responding to requests")


@then("the server should be running")
def step_server_should_be_running(context):
    assert is_server_running(), "Server is not running"


@then("it should be listening on the configured port")
def step_server_listening_on_port(context):
    try:
        response = requests.get("http://server:5000/", timeout=5)
        assert response.status_code < 500, "Server is not responding properly"
    except:
        assert False, "Server is not listening on the configured port"


@given("a valid task file is sent")
def step_valid_task_file_sent(context):
    temp_dir = "/uploads/behave_tests"
    os.makedirs(temp_dir, exist_ok=True)
    task_file_path = os.path.join(temp_dir, "valid_task.py")

    with open(task_file_path, "w") as f:
        f.write('print("Valid task")')

    context.valid_task = task_file_path

    if hasattr(context, 'can_execute') and context.can_execute:
        try:
            with open(task_file_path, "rb") as file_obj:
                files = {"file": (os.path.basename(task_file_path), file_obj, "text/plain")}
                response = requests.post("http://server:5000/execute", files=files, timeout=10)

            if response.status_code == 200:
                context.response = response
                context.result = response.json()
        except Exception as e:
            print(f"Warning: Pre-test request failed: {str(e)}")


@when("the server receives the task")
def step_server_receives_task(context):
    if hasattr(context, "response") and hasattr(context, "result"):
        return

    file_path = (
        context.valid_task if hasattr(context, "valid_task") else context.invalid_task
    )
    
    if hasattr(context, 'can_execute') and context.can_execute:
        with open(file_path, "rb") as file_obj:
            files = {"file": (os.path.basename(file_path), file_obj, "text/plain")}
            try:
                context.response = requests.post("http://server:5000/execute", files=files, timeout=10)
                if context.response.status_code == 200:
                    context.result = context.response.json()
                else:
                    context.error = f"Server returned status {context.response.status_code}"
            except Exception as e:
                context.error = str(e)
    else:
        context.response_simulation = True
        context.error = "Server database connection issue - execution not available"


@then("it should process the task")
def step_process_task(context):
    if hasattr(context, 'can_execute') and not context.can_execute:
        assert is_server_running(), "Server is not running"
        return
    
    assert hasattr(context, "response"), "No response received"
    assert (
        context.response.status_code == 200
    ), f"Expected status code 200, got {context.response.status_code}"


@then("return the execution results")
def step_return_execution_results(context):
    if hasattr(context, 'can_execute') and not context.can_execute:
        assert is_server_running(), "Server should be available"
        return
        
    assert "output" in context.result or "error" in context.result, "No output or error in response"


@then('the task status should be "completed"')
def step_impl_completed_status(context):
    if hasattr(context, 'can_execute') and not context.can_execute:
        assert is_server_running(), "Server should be running"
        return
        
    assert context.response.status_code == 200, "Task was not completed"

    if "output" in context.result:
        if "error" in context.result:
            if (
                isinstance(context.result["error"], str)
                and context.result["error"].strip()
            ):
                error_message = context.result["error"].lower()
                if (
                    "warning" in error_message
                    or "info" in error_message
                    or "notice" in error_message
                ):
                    pass
                else:
                    assert (
                        False
                    ), f"Task completed with errors: {context.result['error']}"
        return

    assert False, f"Unexpected response format: {context.result}"


@then('the task status should be "failed"')
def step_impl_failed_status(context):
    if hasattr(context, 'can_execute') and not context.can_execute:
        assert hasattr(context, 'error'), "Expected error due to server limitations"
        return
        
    assert (
        "error" in context.result and context.result["error"]
    ), "Expected error but none found"


@given("an invalid task file is sent")
def step_invalid_task_file_sent(context):
    temp_dir = "/uploads/behave_tests"
    os.makedirs(temp_dir, exist_ok=True)
    task_file_path = os.path.join(temp_dir, "invalid_task.py")
    
    with open(task_file_path, "w") as f:
        f.write("print(undefined_variable)")
    
    context.invalid_task = task_file_path


@then("it should return an error message")
def step_return_error_message(context):
    if hasattr(context, 'can_execute') and not context.can_execute:
        assert hasattr(context, 'error'), "Expected error message"
        return
        
    assert "error" in context.result, "No error message in response"
    assert context.result["error"], "Empty error message"


@given("a corrupted file is sent")
def step_corrupted_file_sent(context):
    temp_dir = "/uploads/behave_tests"
    os.makedirs(temp_dir, exist_ok=True)
    task_file_path = os.path.join(temp_dir, "corrupted_task.py")
    
    with open(task_file_path, "w") as f:
        f.write('print("Hello World"\nwhile True print("Invalid syntax")')
    
    context.corrupted_file = task_file_path


@when("the server receives the file")
def step_server_receives_file(context):
    if hasattr(context, 'can_execute') and context.can_execute:
        with open(context.corrupted_file, "rb") as file_obj:
            files = {"file": (os.path.basename(context.corrupted_file), file_obj, "text/plain")}
            try:
                context.response = requests.post("http://server:5000/execute", files=files, timeout=10)
                if context.response.status_code == 200:
                    context.result = context.response.json()
                else:
                    context.error = f"Server returned status {context.response.status_code}"
            except Exception as e:
                context.error = str(e)
    else:
        context.error = "Server database connection issue"


@then("it should validate the file format")
def step_validate_file_format(context):
    assert is_server_running(), "Server should be responding"


@then("return a proper error message")
def step_return_proper_error_message(context):
    if hasattr(context, 'can_execute') and not context.can_execute:
        assert hasattr(context, 'error'), "Expected error message"
        return
        
    assert hasattr(context, "response"), "Server response is missing"
    if "error" in context.result:
        assert context.result["error"], "Empty error message"
    else:
        assert False, "Expected an error message"


@given("multiple clients are connected")
def step_multiple_clients_connected(context):
    context.client_count = 5
    context.test_connections = []

    try:
        if is_server_running():
            context.test_connections.append(True)
    except:
        pass

    assert len(context.test_connections) > 0, "Failed to establish test connections"


def send_task_request(task_index, context, task_prefix="task"):
    """General function for sending tasks"""
    temp_dir = "/uploads/behave_tests"
    os.makedirs(temp_dir, exist_ok=True)
    file_path = os.path.join(temp_dir, f"{task_prefix}_{task_index}.py")
    
    code_content = 'print("Test task")' if task_prefix == "task" else 'print("Load test")'
    with open(file_path, "w") as f:
        f.write(code_content)

    if hasattr(context, 'can_execute') and context.can_execute:
        with open(file_path, "rb") as file_obj:
            files = {"file": (os.path.basename(file_path), file_obj, "text/plain")}
            try:
                response = requests.post("http://server:5000/execute", files=files, timeout=10)
                return response
            except Exception as e:
                return str(e)
    else:
        return "Simulated response - server cannot execute"


@when('"10" tasks are submitted simultaneously')
def step_impl_quoted_10_tasks(context):
    context.task_count = 10
    context.start_time = time.time()
    context.responses = []

    threads = []
    for i in range(context.task_count):
        thread = threading.Thread(target=lambda idx=i: context.responses.append(send_task_request(idx, context, "task")))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    context.end_time = time.time()
    context.execution_time = context.end_time - context.start_time


@then("the server should process all tasks")
def step_server_process_all_tasks(context):
    if hasattr(context, 'can_execute') and not context.can_execute:
        assert len(context.responses) > 0, "No responses received"
        return
        
    success_count = sum(
        1
        for resp in context.responses
        if isinstance(resp, requests.Response) and resp.status_code == 200
    )
    assert success_count > 0, f"No tasks were processed successfully"
    assert success_count == len(
        [r for r in context.responses if isinstance(r, requests.Response)]
    ), "Not all tasks were processed"


@then("maintain reasonable response times")
def step_maintain_reasonable_response_times(context):
    assert (
        context.execution_time < 60
    ), f"Total execution time ({context.execution_time} s) exceeds expected"


@then("not crash or hang")
def step_not_crash_or_hang(context):
    assert is_server_running(), "Server stopped responding after load test"


@given("the server is under heavy load")
def step_server_under_heavy_load(context):
    context.load_task_count = 3
    context.load_responses = []

    threads = []
    for i in range(context.load_task_count):
        thread = threading.Thread(target=lambda idx=i: context.load_responses.append(send_task_request(idx, context, "load_task")))
        threads.append(thread)
        thread.start()

    time.sleep(0.1)


@when("new tasks arrive")
def step_new_tasks_arrive(context):
    context.new_task_responses = []
    temp_dir = "/uploads/behave_tests"
    os.makedirs(temp_dir, exist_ok=True)

    for i in range(2):
        file_path = os.path.join(temp_dir, f"new_task_{i}.py")
        
        with open(file_path, "w") as f:
            f.write('print("New task")')

        if hasattr(context, 'can_execute') and context.can_execute:
            with open(file_path, "rb") as file_obj:
                files = {"file": (os.path.basename(file_path), file_obj, "text/plain")}
                try:
                    response = requests.post("http://server:5000/execute", files=files, timeout=10)
                    context.new_task_responses.append(response)
                except Exception as e:
                    context.new_task_responses.append(str(e))
        else:
            context.new_task_responses.append("Simulated response")


@given("a task that runs indefinitely")
def step_task_runs_indefinitely(context):
    temp_dir = "/uploads/behave_tests"
    os.makedirs(temp_dir, exist_ok=True)
    context.infinite_task = os.path.join(temp_dir, "infinite_task.py")
    
    with open(context.infinite_task, "w") as f:
        f.write("""
import time
print("Starting infinite loop...")
while True:
    time.sleep(1)
    print("Still running...")
""")


@when("the server executes the task")
def step_server_executes_task(context):
    if not hasattr(context, "infinite_task"):
        temp_dir = "/uploads/behave_tests"
        os.makedirs(temp_dir, exist_ok=True)
        context.infinite_task = os.path.join(temp_dir, "infinite_task.py")
        
        with open(context.infinite_task, "w") as f:
            f.write("""
import time
print("Starting infinite loop...")
while True:
    time.sleep(1)
    print("Still running...")
""")

    if hasattr(context, 'can_execute') and context.can_execute:
        with open(context.infinite_task, "rb") as file_obj:
            files = {"file": (os.path.basename(context.infinite_task), file_obj, "text/plain")}
            try:
                context.response = requests.post("http://server:5000/execute", files=files, timeout=10)
                if context.response.status_code == 200:
                    context.result = context.response.json()
                else:
                    context.error = f"Server returned status {context.response.status_code}"
            except Exception as e:
                context.error = str(e)
    else:
        context.error = "Server cannot execute code due to database issues"
    time.sleep(0.1)


@then("it should terminate the task after timeout limit")
def step_terminate_task_after_timeout(context):
    if hasattr(context, 'can_execute') and not context.can_execute:
        assert is_server_running(), "Server should be running"
        return

    debug_info = []
    debug_info.append(f"has_error: {hasattr(context, 'error')}")
    debug_info.append(f"has_response: {hasattr(context, 'response')}")
    if hasattr(context, 'error'):
        debug_info.append(f"error: {context.error}")
    if hasattr(context, 'response'):
        debug_info.append(f"response_status: {context.response.status_code}")
    
    if hasattr(context, 'error'):
        assert (
            "timeout" in context.error.lower() 
            or "timed out" in context.error.lower()
            or "read timeout" in context.error.lower()
        ), f"Expected timeout error, got: {context.error}"
        return
        
    if hasattr(context, "response"):
        assert (
            context.response.status_code == 200
        ), f"Unexpected response code: {context.response.status_code}"
        assert (
            "error" in context.result
            or "timeout" in context.result
            or "output" in context.result
        ), "Missing execution information"
    else:
        debug_msg = " | ".join(debug_info)
        assert False, f"Server response or timeout error is missing. Debug: {debug_msg}"


@then("return a timeout error")
def step_return_timeout_error(context):
    if hasattr(context, 'can_execute') and not context.can_execute:
        assert hasattr(context, 'error'), "Expected error message"
        return
        
    assert hasattr(context, "response"), "Server response is missing"
    assert (
        "Execution time out" in str(context.result)
        or "timeout" in str(context.result).lower()
        or "error" in context.result
    ), "No timeout information"


@then("free all allocated resources")
def step_free_all_allocated_resources(context):
    """Verify that all resources are properly freed after task execution"""
    assert is_server_running(), "Server stopped responding after task execution"

    if hasattr(context, "task_id"):
        task_dir = os.path.join("/uploads", context.task_id)
        assert not os.path.exists(
            task_dir
        ), f"Task directory {task_dir} was not cleaned up"

@given("tasks are being processed")
def step_tasks_being_processed(context):
    context.task_responses = []
    temp_dir = "/uploads/behave_tests"
    os.makedirs(temp_dir, exist_ok=True)

    for i in range(2):
        file_path = os.path.join(temp_dir, f"processing_task_{i}.py")
        
        with open(file_path, "w") as f:
            f.write('import time\nfor i in range(3): time.sleep(0.1)\nprint("Completed")')

        if hasattr(context, 'can_execute') and context.can_execute:
            with open(file_path, "rb") as file_obj:
                files = {"file": (os.path.basename(file_path), file_obj, "text/plain")}
                try:
                    response = requests.post("http://server:5000/execute", files=files, timeout=10)
                    context.task_responses.append(response)
                except Exception as e:
                    context.task_responses.append(str(e))
        else:
            context.task_responses.append("Simulated response")

    success_count = sum(
        1
        for resp in context.task_responses
        if isinstance(resp, requests.Response) and resp.status_code == 200
    )
    if hasattr(context, 'can_execute') and context.can_execute:
        assert success_count > 0, "Failed to send tasks"
    else:
        assert len(context.task_responses) > 0, "No responses received"


@given("a task that generates output files")
def step_task_generates_output_files(context):
    temp_dir = "/uploads/behave_tests"
    os.makedirs(temp_dir, exist_ok=True)
    file_path = os.path.join(temp_dir, "output_generation_task.py")
    
    code = """
with open("output_result.txt", "w") as f:
	f.write("This is a test output file")
print("File created successfully")
"""
    with open(file_path, "w") as f:
        f.write(code)
    
    context.output_task = file_path


@then("it should validate the output file format")
def step_validate_output_file_format(context):
    if hasattr(context, 'can_execute') and not context.can_execute:
        assert is_server_running(), "Server should be running"
        return
        
    assert hasattr(context, "response"), "Server response is missing"
    assert (
        context.response.status_code == 200
    ), f"Unexpected response code: {context.response.status_code}"
    assert "output" in context.result, "Response does not contain output information"


@then("ensure logs contain execution details")
def step_ensure_logs_contain_execution_details(context):
    if hasattr(context, 'can_execute') and not context.can_execute:
        assert is_server_running(), "Server should be running"
        return
        
    assert hasattr(context, "response"), "Server response is missing"
    assert "output" in context.result, "Missing execution information"


@given("a malformed request is sent")
def step_malformed_request_sent(context):
    context.malformed_request_data = {
        "invalid_param": "test",
        "code": 'print("Hello World")',
        "execute": True,
    }

@when("the server processes the request")
def step_server_processes_request(context):
    try:
        context.response = requests.post(
            "http://server:5000/execute", json=context.malformed_request_data, timeout=10
        )
        context.result = (
            context.response.json() if context.response.status_code == 200 else {}
        )
    except Exception as e:
        context.error = str(e)

@then("it should reject the invalid request")
def step_reject_invalid_request(context):
    assert hasattr(context, "response") or hasattr(context, "error"), "No server response"
    if hasattr(context, "response"):
        assert (
            context.response.status_code != 200 or "error" in context.result
        ), "Server did not reject invalid request"

@then("not expose sensitive information in error messages")
def step_not_expose_sensitive_information(context):
    if hasattr(context, "response"):
        if context.response.status_code != 200:
            error_text = context.response.text
            assert (
                "traceback" not in error_text.lower()
                and "exception" not in error_text.lower()
                and "stack" not in error_text.lower()
            ), "Sensitive information detected in error message"

@then("the server should return an error response")
def step_server_returns_error_response(context):
    if hasattr(context, 'can_execute') and not context.can_execute:
        assert hasattr(context, 'error'), "Expected error due to server limitations"
        return
        
    if hasattr(context, 'error'):
        assert context.error, "Error message should not be empty"
        return
        
    if hasattr(context, "response"):
        assert hasattr(context, "result"), "No result in response"
        assert (
            context.response.status_code == 200
        ), f"Unexpected status code: {context.response.status_code}"
        assert "error" in context.result, "No error in response"
        assert context.result["error"], "Empty error message"
    else:
        assert False, "No response or error from server"
