import os
import tempfile
from behave import given, when, then
from Client.python_security_checker import PythonSecurityChecker


@given('the Python Security Checker is initialized')
def step_impl(context):
	context.security_checker = PythonSecurityChecker()


@given('I have a Python file with safe code')
def step_impl(context):
	with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
		content = """
import math
import random

def calculate_area(radius):
	return math.pi * radius * radius

def generate_random_number(min_value, max_value):
	return random.randint(min_value, max_value)

# Using functions
radius = 5
print(f"Area of circle with radius {radius} is {calculate_area(radius)}")
print(f"Random number between 1 and 10: {generate_random_number(1, 10)}")
		"""
		f.write(content.encode('utf-8'))
		context.test_file_path = f.name


@given('I have a Python file with "{module}" module import')
def step_impl(context, module):
	with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
		content = f"""
import {module}
import math

def calculate_area(radius):
	return math.pi * radius * radius

print(f"Current directory: {{{module}.getcwd()}}")
		"""
		f.write(content.encode('utf-8'))
		context.test_file_path = f.name


@given('the file contains system command execution')
def step_impl(context):
	with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
		content = """
import os
import subprocess

def execute_command(cmd):
	return os.system(cmd)

def get_command_output(cmd):
	return subprocess.check_output(cmd, shell=True)

# Executing commands
execute_command("echo 'Hello from system'")
output = get_command_output("echo 'Hello from subprocess'")
print(f"Command output: {output}")
		"""
		f.write(content.encode('utf-8'))
		context.test_file_path = f.name


@given('I have a Python file with "eval" function calls')
def step_impl(context):
	with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
		content = """
def calculate_expression(expression):
	return eval(expression)

def get_dynamic_function(code):
	# Dangerous function that evaluates code at runtime
	return eval(f"lambda x: {code}")

# Using eval
result = calculate_expression("2 + 2 * 3")
dynamic_func = get_dynamic_function("x * x + 5")
print(f"Result: {result}")
print(f"Function result: {dynamic_func(3)}")
		"""
		f.write(content.encode('utf-8'))
		context.test_file_path = f.name


@given('the file contains "exec" function calls')
def step_impl(context):
	with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
		content = """
def execute_code(code):
	exec(code)

# Using exec
execute_code("print('Hello from exec')")
execute_code("import random; print(random.randint(1, 100))")

# Dangerous dynamic import
code = '''
import os
print(os.listdir('.'))
'''
exec(code)
		"""
		f.write(content.encode('utf-8'))
		context.test_file_path = f.name


@given('I have a Python file with hardcoded passwords')
def step_impl(context):
	with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
		content = """
# Configuration with embedded passwords
config = {
	'username': 'admin',
	'password': 'super_secret_123',
	'database': 'production_db'
}

# Sensitive data in code
password = "qwerty123456"
api_token = "s3cr3t_t0k3n"

def authenticate(user, pwd):
	if user == config['username'] and pwd == config['password']:
		return True
	return False

# Using passwords
if authenticate('admin', 'super_secret_123'):
	print("Authentication successful")
		"""
		f.write(content.encode('utf-8'))
		context.test_file_path = f.name


@given('the file contains API keys')
def step_impl(context):
	with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
		content = """
# API keys
GITHUB_API_KEY = "ghp_12345678901234567890123456789012345678"
STRIPE_SECRET_KEY = "sk_test_1234567890abcdefghijklmnopqrstuvwxyz1234"

def make_api_request(api_key, endpoint):
	# Function for making API requests
	print(f"Making request to {endpoint} with key {api_key[:5]}...")
	return {"status": "success"}

# Using API keys
result = make_api_request(GITHUB_API_KEY, "https://api.github.com/user")
payment = make_api_request(STRIPE_SECRET_KEY, "https://api.stripe.com/v1/charges")
		"""
		f.write(content.encode('utf-8'))
		context.test_file_path = f.name


@given('I have a Python file with both safe and unsafe code')
def step_impl(context):
	with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
		content = """
import math
import os
import subprocess

def calculate_area(radius):
	return math.pi * radius * radius

def get_files():
	return os.listdir('.')

def run_command(cmd):
	return subprocess.check_output(cmd, shell=True)

# Safe operations
radius = 5
area = calculate_area(radius)
print(f"Area of circle with radius {radius} is {area}")

# Unsafe operations
files = get_files()
output = run_command("echo 'test'")
print(f"Files: {files}")
print(f"Command output: {output}")
		"""
		f.write(content.encode('utf-8'))
		context.test_file_path = f.name


@given('I have a non-existent file path')
def step_impl(context):
	context.test_file_path = "/non/existent/file/path.py"


@given('I have a text file that is not a Python file')
def step_impl(context):
	with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
		content = """
This is a plain text file, not a Python file.
It doesn't contain any Python code.
Just some text content.
		"""
		f.write(content.encode('utf-8'))
		context.test_file_path = f.name


@given('I have a Python file with {issue_type} issues')
def step_impl(context, issue_type):
	if issue_type == "subprocess":
		with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
			content = """
import subprocess

def run_process(command):
	return subprocess.check_output(command, shell=True)

def execute_background(command):
	subprocess.Popen(command, shell=True)

# Using subprocess
result = run_process('echo "Hello, subprocess!"')
execute_background('echo "Background process"')
print(f"Result: {result}")
			"""
			f.write(content.encode('utf-8'))
			context.test_file_path = f.name
	
	elif issue_type == "socket":
		with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
			content = """
import socket

def create_server():
	server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server.bind(('localhost', 12345))
	server.listen(5)
	return server

def create_client():
	client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	client.connect(('localhost', 12345))
	return client

# Creating server and client
server = create_server()
print("Server created")
			"""
			f.write(content.encode('utf-8'))
			context.test_file_path = f.name
	
	elif issue_type == "file operations":
		with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
			content = """
def write_to_file(content):
	with open("sensitive_data.txt", "w") as f:
		f.write(content)

def read_from_file():
	with open("config.txt", "r") as f:
		return f.read()

# Working with files
write_to_file("This is sensitive information")
try:
	data = read_from_file()
	print(f"Read data: {data}")
except:
	print("Could not read file")
			"""
			f.write(content.encode('utf-8'))
			context.test_file_path = f.name
	
	elif issue_type == "network access":
		with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
			content = """
import urllib.request
import requests

def download_content(url):
	with urllib.request.urlopen(url) as response:
		return response.read()

def make_request(url):
	return requests.get(url).text

# Network operations
# Uncomment to execute dangerous network operations
# content = download_content("http://example.com")
# response = make_request("http://example.com")
			"""
			f.write(content.encode('utf-8'))
			context.test_file_path = f.name
	
	elif issue_type == "pickle":
		with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
			content = """
import pickle

def save_object(obj, filename):
	with open(filename, 'wb') as f:
		pickle.dump(obj, f)

def load_object(filename):
	with open(filename, 'rb') as f:
		return pickle.load(f)

# Working with pickle
data = {"username": "admin", "role": "superuser"}
save_object(data, "user.pkl")
try:
	loaded_data = load_object("user.pkl")
	print(f"Loaded data: {loaded_data}")
except:
	print("Could not load pickled data")
			"""
			f.write(content.encode('utf-8'))
			context.test_file_path = f.name
	
	elif issue_type == "input validation":
		with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
			content = """
def get_user_input():
	user_input = input("Enter expression: ")
	return eval(user_input)

def validate_age(age_str):
	# Missing input validation
	age = int(age_str)
	return age >= 18

# Get and process user input
# result = get_user_input()
# print(f"Result: {result}")

is_adult = validate_age("25")
print(f"Is adult: {is_adult}")
			"""
			f.write(content.encode('utf-8'))
			context.test_file_path = f.name


@when('I check the file for security issues')
def step_impl(context):
	try:
		context.safe_file_path = context.security_checker.check_file(context.test_file_path)
		context.unsafe_operations = context.security_checker.get_unsafe_operations()
	except Exception as e:
		context.exception = e


@when('I try to check the file for security issues')
def step_impl(context):
	try:
		context.safe_file_path = context.security_checker.check_file(context.test_file_path)
		context.unsafe_operations = context.security_checker.get_unsafe_operations()
	except Exception as e:
		context.exception = e

@then('the file should be considered safe')
def step_impl(context):
	assert not context.unsafe_operations, "File was incorrectly marked as unsafe"
	assert context.safe_file_path, "No safe file path returned"
	assert os.path.exists(context.safe_file_path), "Safe file does not exist"


@then('the file should be marked as unsafe')
def step_impl(context):
	assert context.unsafe_operations, "File was incorrectly marked as safe"
	assert len(context.unsafe_operations) > 0, "No unsafe operations found"


@then('the safe file should contain all the original code')
def step_impl(context):
	with open(context.test_file_path, "r") as original:
		original_content = original.read()
	with open(context.safe_file_path, "r") as safe:
		safe_content = safe.read()
	
	assert len(safe_content) >= len(original_content) * 0.9, "Safe content is significantly shorter than original"
	for line in original_content.splitlines():
		if not line.strip() or line.strip().startswith('#'):
			continue
		assert line in safe_content or line.strip() in safe_content, f"Line not preserved: {line}"


@then('the unsafe imports should be removed')
def step_impl(context):
	with open(context.safe_file_path, "r") as safe:
		safe_content = safe.read()
	
	assert "import os" not in safe_content, "Unsafe import 'os' was not removed"
	assert "import subprocess" not in safe_content, "Unsafe import 'subprocess' was not removed"


@then('the system command execution should be removed')
def step_impl(context):
	with open(context.safe_file_path, "r") as safe:
		safe_content = safe.read()
	
	assert "os.system" not in safe_content, "System command execution 'os.system' was not removed"
	assert "subprocess.check_output" not in safe_content, "System command execution 'subprocess.check_output' was not removed"


@then('the eval function calls should be removed')
def step_impl(context):
	with open(context.safe_file_path, "r") as safe:
		safe_content = safe.read()
	
	assert "eval(" not in safe_content, "Eval function call was not removed"


@then('the exec function calls should be removed')
def step_impl(context):
	with open(context.safe_file_path, "r") as safe:
		safe_content = safe.read()
	
	assert "exec(" not in safe_content, "Exec function call was not removed"


@then('a safe version of the file should be created')
def step_impl(context):
	assert context.safe_file_path is not None, "No safe file path returned"
	assert os.path.exists(context.safe_file_path), "Safe file does not exist"
	
	# Check if name follows the convention
	original_name = os.path.basename(context.test_file_path)
	safe_name = os.path.basename(context.safe_file_path)
	assert "secure" in safe_name or "safe" in safe_name, f"Safe file name does not follow convention: {safe_name}"


@then('the hardcoded passwords should be removed')
def step_impl(context):
	with open(context.safe_file_path, "r") as safe:
		safe_content = safe.read()
	
	assert "super_secret_123" not in safe_content, "Hardcoded password was not removed"
	assert "password = " not in safe_content or "password = \"API_KEY_REMOVED\"" in safe_content, "Password assignment was not removed"


@then('the API keys should be removed')
def step_impl(context):
	with open(context.safe_file_path, "r") as safe:
		safe_content = safe.read()
	
	assert "GITHUB_API_KEY" not in safe_content or "GITHUB_API_KEY = \"API_KEY_REMOVED\"" in safe_content, "GitHub API key was not removed"
	assert "STRIPE_SECRET_KEY" not in safe_content or "STRIPE_SECRET_KEY = \"API_KEY_REMOVED\"" in safe_content, "Stripe API key was not removed"
	assert "ghp_" not in safe_content, "GitHub API key value was not removed"
	assert "sk_test_" not in safe_content, "Stripe API key value was not removed"


@then('the safe code should be preserved')
def step_impl(context):
	with open(context.safe_file_path, "r") as safe:
		safe_content = safe.read()
	
	assert "import math" in safe_content, "Safe import 'math' was removed"
	assert "def calculate_area(radius):" in safe_content, "Safe function 'calculate_area' was removed"
	assert "math.pi" in safe_content, "Safe code using 'math.pi' was removed"


@then('the unsafe code should be removed')
def step_impl(context):
	with open(context.safe_file_path, "r") as safe:
		safe_content = safe.read()
	
	assert "import os" not in safe_content, "Unsafe import 'os' was not removed"
	assert "os.listdir" not in safe_content, "Unsafe code 'os.listdir' was not removed"
	assert "os.system" not in safe_content, "Unsafe code 'os.system' was not removed"


@then('I should get a "{error_type}" error')
def step_impl(context, error_type):
	assert context.exception is not None, "No exception was raised"
	
	error_message = str(context.exception).lower()
	if error_type == "file not found":
		assert "not found" in error_message or "no such file" in error_message, f"Expected 'file not found' error, got: {error_message}"
	elif error_type == "not a Python file":
		assert "python" in error_message and "file" in error_message, f"Expected 'not a Python file' error, got: {error_message}"
	else:
		assert error_type.lower() in error_message, f"Expected '{error_type}' in error message, got: {error_message}"


@then('the {issue_type} issues should be removed')
def step_impl(context, issue_type):
	with open(context.safe_file_path, "r") as safe:
		safe_content = safe.read()
	
	if issue_type == "subprocess":
		assert "import subprocess" not in safe_content, "Subprocess import was not removed"
		assert "subprocess.check_output" not in safe_content, "Subprocess call was not removed"
	elif issue_type == "socket":
		assert "import socket" not in safe_content, "Socket import was not removed"
		assert "socket.socket" not in safe_content, "Socket creation was not removed"
	elif issue_type == "file operations":
		assert 'open("sensitive_data.txt", "w")' not in safe_content, "File write operation was not removed"
	elif issue_type == "network access":
		assert "import urllib" not in safe_content, "Network access import was not removed"
		assert "urllib.request.urlopen" not in safe_content, "Network access call was not removed"
	elif issue_type == "pickle":
		assert "import pickle" not in safe_content, "Pickle import was not removed"
		assert "pickle.loads" not in safe_content, "Pickle deserialization was not removed"
	elif issue_type == "input validation":
		assert "input(" not in safe_content, "Input function was not removed"
		assert "eval(" not in safe_content, "Eval function was not removed"


@given('I have a Python file with hidden imports')
def step_impl(context):
	with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
		content = """
# Hidden imports
__import__('os').system('echo hidden import')
exec("import subprocess; subprocess.check_output(['echo', 'hidden subprocess'])")

def get_sys_info():
	sys = __import__('sys')
	return sys.version
	
def dynamic_import(module_name):
	return __import__(module_name)
	
# Masked import via variable
dangerous_module = 'socket'
network = __import__(dangerous_module)
connection = network.socket(network.AF_INET, network.SOCK_STREAM)
		"""
		f.write(content.encode('utf-8'))
		context.test_file_path = f.name


@given('I have a Python file with GitHub API keys')
def step_impl(context):
	with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
		content = """
import requests

# GitHub API keys of different types
github_api_key = "ghp_************************************"
github_token = "github_pat_************************************"
oauth_token = "gho_******************************"

def fetch_github_data():
	url = "https://api.github.com/user"
	headers = {"Authorization": f"token {github_api_key}"}
	response = requests.get(url, headers=headers)
	return response.json()

# Additional token in line
secret = "ghu_************************************"
key = "****************************************"
		"""
		f.write(content.encode('utf-8'))
		context.test_file_path = f.name


@given('I have a Python file with AWS credentials')
def step_impl(context):
	with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
		content = """
import boto3

# AWS credentials
AWS_ACCESS_KEY_ID = "AKIA****************"
AWS_SECRET_ACCESS_KEY = "wJalr*******************************"
region = "us-west-2"

def connect_to_aws():
	session = boto3.Session(
		aws_access_key_id=AWS_ACCESS_KEY_ID,
		aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
		region_name=region
	)
	return session.client('s3')
		"""
		f.write(content.encode('utf-8'))
		context.test_file_path = f.name


@given('I have a Python file with Stripe API keys')
def step_impl(context):
	# Creating a temporary file with Stripe API keys
	with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
		content = """
import stripe

# Stripe API keys
stripe.api_key = "sk_test_********************************"
publishable_key = "pk_test_********************************"

def charge_customer():
	return stripe.Charge.create(
		amount=2000,
		currency="usd",
		source="tok_amex",
		description="Direct charge test"
	)
		"""
		f.write(content.encode('utf-8'))
		context.test_file_path = f.name


@given('I have a Python file with Slack tokens')
def step_impl(context):
	with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
		content = """
from slack_sdk import WebClient

# Slack token
slack_token = "xoxb-************************************"
bot_token = "xoxa-************************************"

def send_slack_message():
	client = WebClient(token=slack_token)
	response = client.chat_postMessage(
		channel="general",
		text="Hello from Python!"
	)
	return response
		"""
		f.write(content.encode('utf-8'))
		context.test_file_path = f.name


@then('the GitHub API keys should be removed')
def step_impl(context):
	with open(context.safe_file_path, "r") as safe:
		safe_content = safe.read()
	
	assert "ghp_" not in safe_content, "GitHub Personal Access Token was not removed"
	assert "github_pat_" not in safe_content, "GitHub Fine-grained Token was not removed"
	assert "gho_" not in safe_content, "GitHub OAuth Token was not removed"
	assert "ghu_" not in safe_content, "GitHub User-to-Server Token was not removed"
	assert "40-character key" not in safe_content, "40-character key not removed"


@then('the AWS credentials should be removed')
def step_impl(context):
	with open(context.safe_file_path, "r") as safe:
		safe_content = safe.read()
	
	assert "AKIAIOSFODNN7EXAMPLE" not in safe_content, "AWS Access Key was not removed"
	assert "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY" not in safe_content, "AWS Secret Key was not removed"


@then('the Stripe API keys should be removed')
def step_impl(context):
	with open(context.safe_file_path, "r") as safe:
		safe_content = safe.read()
	
	assert "sk_test_" not in safe_content, "Stripe Secret Key was not removed"
	assert "pk_test_" not in safe_content, "Stripe Publishable Key was not removed"


@then('the Slack tokens should be removed')
def step_impl(context):
	with open(context.safe_file_path, "r") as safe:
		safe_content = safe.read()
	
	assert "xoxb-" not in safe_content, "Slack Bot Token was not removed"
	assert "xoxa-" not in safe_content, "Slack App Token was not removed"


@then('the hidden imports should be removed')
def step_impl(context):
	with open(context.safe_file_path, "r") as safe:
		safe_content = safe.read()
	
	assert "__import__('os')" not in safe_content, "Hidden os import was not removed"
	assert "__import__('sys')" not in safe_content, "Hidden sys import was not removed"
	assert "__import__(module_name)" not in safe_content, "Dynamic import was not removed"
	assert "__import__(dangerous_module)" not in safe_content, "Masked import was not removed"
	assert "exec(" not in safe_content, "exec() was not removed" 