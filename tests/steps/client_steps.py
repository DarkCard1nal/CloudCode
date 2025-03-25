from behave import given, when, then
from Client.client import CloudComputeClient
import requests
import time
import sys
import os
import tempfile
import threading

def is_server_running():
    try:
        response = requests.post('http://localhost:5000/execute', files={})
        return response.status_code == 200
    except Exception:
        return False

# Перевірка, що сервер запущений і готовий для клієнтських тестів
@given('the server is running for client tests')
def step_impl(context):
    for _ in range(10):
        if is_server_running():
            return
        time.sleep(0.5)
    assert False, "Server is not running after multiple attempts"

# Ініціалізація клієнта
@given('the client is initialized')
def step_impl(context):
    context.client = CloudComputeClient()
    if hasattr(context, 'stdout_capture') and context.stdout_capture:
        try:
            context.stdout_capture.truncate(0)
            context.stdout_capture.seek(0)
        except Exception:
            pass

# Відправка завдань послідовно
@when('I send tasks sequentially')
def step_impl(context):
    context.client.send_sequential()

# Відправка завдань паралельно
@when('I send tasks in parallel')
def step_impl(context):
    context.client.send_parallel()

# Відправка нескінченного завдання
@when('I send an infinite task')
def step_impl(context):
    # Використовуємо існуюче нескінченне завдання
    try:
        context.client.send_single_task('Tasks/.infinite_task.py')
    except Exception as e:
        context.error = str(e)

# Перевірка успішного відправлення всіх завдань
@then('all tasks should be sent successfully')
def step_impl(context):
    output = context.stdout_capture.getvalue() if hasattr(context, 'stdout_capture') else ""
    assert "Error:" not in output or "Error: None" in output, "Знайдено повідомлення про помилку у виводі"
    assert "Result for" in output or "Result:" in output, "Не знайдено результатів виконання"
    assert "code 4" not in output and "code 5" not in output, "Знайдено коди помилок у виводі"

# Перевірка отримання результатів для кожного завдання
@then('I should receive results for each task')
def step_impl(context):
    output = context.stdout_capture.getvalue() if hasattr(context, 'stdout_capture') else ""
    check_texts = [
        'Result for', 
        'Execution time:', 
    ]
    for text in check_texts:
        assert text in output, f"Expected element '{text}' not found in output"

# Перевірка, що завдання обробляються по порядку
@then('the tasks should be processed in order')
def step_impl(context):
    output = context.stdout_capture.getvalue() if hasattr(context, 'stdout_capture') else ""
    assert "Sending files one by one" in output, "Not using sequential execution"
    assert "Total execution time of sequential requests" in output, "Sequential execution summary not found"

# Перевірка, що завдання обробляються паралельно
@then('the tasks should be processed concurrently')
def step_impl(context):
    output = context.stdout_capture.getvalue() if hasattr(context, 'stdout_capture') else ""
    assert "Sending files in parallel" in output, "Not using parallel execution"
    assert "Total execution time of parallel requests" in output, "Parallel execution summary not found"

# Перевірка успішного відправлення завдання
@then('the task should be sent successfully')
def step_impl(context):
    output = context.stdout_capture.getvalue() if hasattr(context, 'stdout_capture') else ""
    assert "Sending single task:" in output, "Task was not sent"

# Перевірка отримання ідентифікатора завдання
@then('I should receive a task ID')
def step_impl(context):
    output = context.stdout_capture.getvalue() if hasattr(context, 'stdout_capture') else ""
    assert "Result for" in output or "--- Result" in output, "No result information found"

# Перевірка, що завдання виконується на сервері
@then('the task should be running on the server')
def step_impl(context):
    output = context.stdout_capture.getvalue() if hasattr(context, 'stdout_capture') else ""
    assert "Error:" in output or "Execution time out" in output, "No error or timeout information found"

# Тести на негативні сценарії

# Відправка пошкодженого файлу
@when('I send a corrupted file')
def step_impl(context):
    with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
        f.write(b'print("Hello\n"')
        context.corrupted_file = f.name
    
    try:
        context.client.send_single_task(context.corrupted_file)
    except Exception as e:
        context.error = str(e)

# Перевірка, що клієнт коректно обробляє помилки
@then('the client should handle the error gracefully')
def step_impl(context):
    output = context.stdout_capture.getvalue() if hasattr(context, 'stdout_capture') else ""
    assert "Error:" in output or hasattr(context, 'error'), "Помилка не була коректно опрацьована"

# Перевірка, що клієнт отримує повідомлення про помилку
@then('I should receive an error message')
def step_impl(context):
    output = context.stdout_capture.getvalue() if hasattr(context, 'stdout_capture') else ""
    assert "Error:" in output or hasattr(context, 'error'), "Повідомлення про помилку не знайдено"

# Імітація недоступності сервера
@given('the server is not responding')
def step_impl(context):
    context.original_url = context.client.api_url
    context.client.api_url = "http://localhost:9999"

# Спроба відправити завдання при недоступному сервері
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

# Перевірка, що клієнт повідомляє про проблеми з'єднання
@then('the client should report connection issues')
def step_impl(context):
    output = context.stdout_capture.getvalue() if hasattr(context, 'stdout_capture') else ""
    assert "Error:" in output or hasattr(context, 'error'), "Клієнт не повідомив про проблеми з'єднання"

# Перевірка наявності детального зворотного зв'язку про помилку
@then('provide proper error feedback')
def step_impl(context):
    output = context.stdout_capture.getvalue() if hasattr(context, 'stdout_capture') else ""
    assert "Error:" in output or hasattr(context, 'error'), "Відсутній зворотній зв'язок про помилку"

# Відправка 10 завдань одночасно
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

# Перевірка, що час відповіді знаходиться в допустимих межах
@then('the response time should be within acceptable limits')
def step_impl(context):
    avg_time = context.execution_time / context.task_count
    assert avg_time < 10, f"Середній час відповіді перевищує ліміт: {avg_time} секунд"

# Відправка завдання, що перевищує ліміт часу
@when('I send a task that exceeds time limit')
def step_impl(context):
    # Використовуємо існуюче нескінченне завдання
    try:
        context.client.send_single_task('Tasks/.infinite_task.py')
    except Exception as e:
        context.error = str(e)

# Перевірка, що клієнт коректно обробляє таймаут
@then('the client should handle the timeout gracefully')
def step_impl(context):
    output = context.stdout_capture.getvalue() if hasattr(context, 'stdout_capture') else ""
    timeout_indicators = ["Error:", "Execution time out", "timed out", "timeout"]
    assert any(indicator in output for indicator in timeout_indicators) or hasattr(context, 'error'), "Клієнт не опрацював таймаут належним чином"

# Перевірка наявності відповідного повідомлення про таймаут
@then('show appropriate timeout message')
def step_impl(context):
    output = context.stdout_capture.getvalue() if hasattr(context, 'stdout_capture') else ""
    timeout_indicators = ["Error:", "Execution time out", "timed out", "timeout"]
    assert any(indicator in output for indicator in timeout_indicators) or hasattr(context, 'error'), "Повідомлення про таймаут не знайдено"

# Перевірка, що клієнт завершив кілька завдань
@given('the client has completed several tasks')
def step_impl(context):
    for _ in range(3):
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
            f.write(b'print("Test task")')
            file_path = f.name
            context.client.send_single_task(file_path)
    
    output = context.stdout_capture.getvalue() if hasattr(context, 'stdout_capture') else ""
    assert "Result for" in output, "Клієнт не виконав завдання перед реініціалізацією"

# Реініціалізація клієнта
@when('I reinitialize the client')
def step_impl(context):
    context.previous_output = context.stdout_capture.getvalue() if hasattr(context, 'stdout_capture') else ""
    
    if hasattr(context, 'stdout_capture') and context.stdout_capture:
        context.stdout_capture.truncate(0)
        context.stdout_capture.seek(0)
    
    context.client = CloudComputeClient()

# Перевірка, що клієнт готовий до нових завдань
@then('the client should be ready for new tasks')
def step_impl(context):
    with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
        f.write(b'print("New task after reinitialization")')
        file_path = f.name
    
    try:
        context.client.send_single_task(file_path)
        success = True
    except Exception:
        success = False
    
    assert success, "Клієнт не готовий до виконання нових завдань після реініціалізації"

# Перевірка, що результати попередніх завдань очищені
@then('previous task results should be cleared')
def step_impl(context):
    current_output = context.stdout_capture.getvalue() if hasattr(context, 'stdout_capture') else ""
    assert "New task after reinitialization" in current_output, "Новий вивід не містить результати нових завдань"
    assert context.previous_output not in current_output, "Результати попередніх завдань не очищені"
