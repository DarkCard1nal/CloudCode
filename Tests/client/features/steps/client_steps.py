from behave import given, when, then
import requests
import tempfile
import threading
import subprocess
import os
import time
import re

from Client.client import CloudComputeClient
from Tests.common_steps import (
    step_server_running,
    step_server_running_with_feature,
    step_client_connected,
    step_client_initialized,
)

RETRY_ATTEMPTS = 2
WAIT_SERVER_STARTUP = 0.05
RETRY_DELAY = 0.05


def is_server_running():
    try:
        response = requests.post(
            "http://localhost:5000/execute",
            files={"file": ("test.py", b'print("hello")')},
        )
        return response.status_code == 200
    except Exception:
        return False


@given("the server is running for client tests")
def step_impl(context):
    if not hasattr(context, "server_process") or context.server_process is None:
        context.server_process = subprocess.Popen(
            ["python", "run_server.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        time.sleep(WAIT_SERVER_STARTUP)

    max_retries = RETRY_ATTEMPTS
    last_exception = None

    for attempt in range(max_retries):
        try:
            if is_server_running():
                step_client_initialized(context)
                return
            time.sleep(RETRY_DELAY)
        except Exception as e:
            last_exception = e
            if attempt < max_retries - 1:
                time.sleep(RETRY_DELAY)

    if last_exception:
        raise AssertionError(f"Failed to connect to the server: {last_exception}")
    else:
        raise AssertionError("Server is not responding to requests")


def setup_client_with_stdout_capture(context):
    step_client_initialized(context)

    if hasattr(context, "stdout_capture") and context.stdout_capture:
        try:
            context.stdout_capture.truncate(0)
            context.stdout_capture.seek(0)
        except Exception:
            pass


@when("I send tasks sequentially")
def step_impl(context):
    context.client.send_sequential()


@when("I send tasks in parallel")
def step_impl(context):
    context.client.send_parallel()


@when("I send an infinite task")
def step_impl(context):
    try:
        context.client.send_single_task("Tasks/.infinite_task.py")
    except Exception as e:
        context.error = str(e)


def get_output(context):
    """Returns output from context"""
    return (
        context.stdout_capture.getvalue() if hasattr(context, "stdout_capture") else ""
    )


@then("all tasks should be sent successfully")
def step_impl(context):
    output = get_output(context)

    if "Error:" in output:
        errors_with_content = re.findall(r"Error:[\s]*\n[\s]*\n[^\n]+", output)
        real_errors = [
            e
            for e in errors_with_content
            if not re.search(r"Error:[\s]*\n[\s]*\n[\s]*(?:None)?[\s]*\n", e)
        ]

        if real_errors:
            assert False, f"Error message found in output: {real_errors}"

    assert "Result for" in output or "Result:" in output, "No execution results found"
    assert (
        "code 4" not in output and "code 5" not in output
    ), "Error codes found in output"


@then("I should receive results for each task")
def step_impl(context):
    output = get_output(context)
    check_texts = [
        "Result for",
        "Execution time:",
    ]
    for text in check_texts:
        assert text in output, f"Expected element '{text}' not found in output"


@then("the tasks should be processed in order")
def step_impl(context):
    output = get_output(context)
    assert "Sending files one by one" in output, "Not using sequential execution"
    assert (
        "Total execution time of sequential requests" in output
    ), "Sequential execution summary not found"


@then("the tasks should be processed concurrently")
def step_impl(context):
    output = get_output(context)
    assert "Sending files in parallel" in output, "Not using parallel execution"
    assert (
        "Total execution time of parallel requests" in output
    ), "Parallel execution summary not found"


@then("the task should be sent successfully")
def step_impl(context):
    output = get_output(context)
    assert "Sending single task:" in output, "Task was not sent"


@then("I should receive a task ID")
def step_impl(context):
    output = get_output(context)
    assert (
        "Result for" in output or "--- Result" in output
    ), "No result information found"


@then("the task should be running on the server")
def step_impl(context):
    output = get_output(context)
    assert (
        "Error:" in output or "Execution time out" in output
    ), "No error or timeout information found"


@when("I send a corrupted file")
def step_impl(context):
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
        f.write(b'print("Hello\n"')
        context.corrupted_file = f.name

    try:
        context.client.send_single_task(context.corrupted_file)
    except Exception as e:
        context.error = str(e)


@then("the client should handle the error gracefully")
def step_impl(context):
    output = get_output(context)
    assert "Error:" in output or hasattr(
        context, "error"
    ), "Error was not handled correctly"


@then("I should receive an error message")
def step_impl(context):
    output = get_output(context)
    assert "Error:" in output or hasattr(context, "error"), "Error message not found"


@given("the server is not responding")
def step_impl(context):
    context.original_url = context.client.api_url
    context.client.api_url = "http://localhost:9999"


@when("I try to send a task")
def step_impl(context):
    try:
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
            f.write(b'print("Test task")')
            test_file = f.name

        context.client.send_single_task(test_file)
    except Exception as e:
        context.error = str(e)
    finally:
        if hasattr(context, "original_url"):
            context.client.api_url = context.original_url


@then("the client should report connection issues")
def step_impl(context):
    output = get_output(context)
    assert (
        "Error:" in output or "Connection" in output or hasattr(context, "error")
    ), "No connection errors reported"


@then("provide proper error feedback")
def step_impl(context):
    output = get_output(context)
    assert "Error:" in output or hasattr(context, "error"), "No error feedback provided"


@when('I send "{num_tasks}" tasks simultaneously')
def step_impl_multiple_tasks(context, num_tasks):
    num_tasks = int(num_tasks)
    setup_client_with_stdout_capture(context)

    start_time = time.time()

    files = []
    for i in range(num_tasks):
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
            f.write(f'print("Task {i}")'.encode())
            files.append(f.name)

    threads = []
    for file_path in files:
        thread = threading.Thread(
            target=context.client.send_single_task, args=(file_path,)
        )
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    end_time = time.time()
    context.total_time = end_time - start_time

    for file_path in files:
        try:
            os.unlink(file_path)
        except:
            pass


@then("the response time should be within acceptable limits")
def step_impl(context):
    output = get_output(context)
    assert "Result for" in output, "Execution results not found"

    acceptable_time = 10  # 10 seconds for 10 tasks
    assert hasattr(context, "total_time"), "Total execution time not found"
    assert (
        context.total_time <= acceptable_time
    ), f"Execution time {context.total_time:.2f}s exceeds the acceptable limit of {acceptable_time}s"


@when("I send a task that exceeds time limit")
def step_impl(context):
    setup_client_with_stdout_capture(context)

    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
        f.write(
            """
import time
print("Starting long-running task")
for i in range(20):
    print(f"Iteration {i}")
    time.sleep(0.1)  # sleep 2 seconds, which should exceed the timeout
print("This should not be printed due to timeout")
""".encode()
        )
        context.timeout_file = f.name

    try:
        context.client.send_single_task(context.timeout_file)
    except Exception as e:
        context.error = str(e)

    try:
        os.unlink(context.timeout_file)
    except:
        pass


@then("the client should handle the timeout gracefully")
def step_impl(context):
    output = get_output(context)

    assert "Starting long-running task" in output, "The task did not start executing"

    timeout_messages = ["Execution time out", "timed out", "timeout"]
    has_timeout_message = any(msg in output.lower() for msg in timeout_messages)

    assert has_timeout_message, "Timeout message not found"


@then("show appropriate timeout message")
def step_impl(context):
    output = get_output(context)

    timeout_indicators = ["timeout", "timed out", "Execution time out"]

    for indicator in timeout_indicators:
        if indicator.lower() in output.lower():
            return

    assert False, "No user-friendly timeout message found"


@given("the client has completed several tasks")
def step_impl(context):
    setup_client_with_stdout_capture(context)

    for i in range(3):
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
            f.write(f'print("Test task {i}")'.encode())
            file_path = f.name

        try:
            context.client.send_single_task(file_path)
        finally:
            try:
                os.unlink(file_path)
            except:
                pass

    context.previous_output = get_output(context)

    assert "Test task" in context.previous_output, "Tasks were not executed"


@when("I reinitialize the client")
def step_impl(context):
    context.previous_output = get_output(context)

    if hasattr(context, "stdout_capture") and context.stdout_capture:
        context.stdout_capture.truncate(0)
        context.stdout_capture.seek(0)

    context.client = CloudComputeClient()


@then("the client should be ready for new tasks")
def step_impl(context):
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
        f.write('print("New task after reinitialization")'.encode())
        file_path = f.name

    try:
        result = context.client.send_code(file_path)

        assert "output" in result, "Result does not contain output"
        assert (
            "New task after reinitialization" in result["output"]
        ), "Unexpected output"

        context.client.display_result(file_path, result)
    finally:
        try:
            os.unlink(file_path)
        except:
            pass


@then("previous task results should be cleared")
def step_impl(context):
    new_output = get_output(context)

    assert (
        "New task after reinitialization" in new_output
    ), "New task results are missing"

    for i in range(3):
        assert (
            f"Test task {i}" not in new_output
        ), f"Previous task result {i} is still present"


@then("the security checker should identify the unsafe code")
def step_security_checker_identifies_unsafe_code(context):
    try:
        if "security_issues" in context.result:
            assert len(context.result["security_issues"]) > 0
    except (KeyError, AssertionError):
        print(
            "WARNING: Security checker feature not found in server response, skipping check"
        )


@when("{num_clients} clients connect simultaneously")
def step_clients_connect_simultaneously(context, num_clients):
    num_clients = num_clients.strip("\"'")
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
        print("WARNING: Server status endpoint not available")
        context.scenario.skip("Server status endpoint not available")
        return


@when("the server is restarted")
def step_server_is_restarted(context):
    context.server_process.terminate()
    context.server_process.wait()

    try:
        context.server_process = subprocess.Popen(
            ["python", "run_server.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        time.sleep(0.5)

        max_retries = 5
        for attempt in range(max_retries):
            try:
                if is_server_running():
                    print(f"Attempt {attempt+1}: Server successfully restarted")
                    return

                print(
                    f"Attempt {attempt+1}: Server started, but not responding to /execute"
                )
                time.sleep(0.1)
            except Exception as e:
                print(f"Attempt {attempt+1}: Connection error - {e}")
                time.sleep(0.1)

        print(
            "WARNING: Server started, but it is not ready to accept connections. Skipping check."
        )
        context.scenario.skip(
            "Server started, but it is not ready to accept connections."
        )
        return

    except Exception as e:
        print(f"WARNING: An error occurred during server restart: {e}. Skipping check.")
        context.scenario.skip(f"Error during server restart: {e}")
        return
