import os
from Client.client import CloudComputeClient

from Tests.steps.common_steps import step_server_running_with_feature

def cleanup_resources(context):
	"""Cleaning up resources after test completion"""
	for attr in ['temp_file_path', 'valid_task', 'invalid_task', 'corrupted_file', 
				'oversized_file', 'high_priority_task', 'mp_task']:
		if hasattr(context, attr):
			file_path = getattr(context, attr)
			if file_path and os.path.exists(file_path):
				try:
					os.unlink(file_path)
				except Exception as e:
					print(f"Error removing {attr}: {e}")
	
	if hasattr(context, 'background_tasks'):
		for thread, file_path in context.background_tasks:
			if file_path and os.path.exists(file_path):
				try:
					os.unlink(file_path)
				except Exception as e:
					print(f"Error removing background task: {e}")
	
	if hasattr(context, 'server_process') and context.server_process:
		try:
			context.server_process.terminate()
			context.server_process.wait(timeout=5)
		except Exception as e:
			print(f"Error terminating the server: {e}")


def before_all(context):
	"""Function called before all tests"""
	context.config.paths.append('Tests/steps')
	steps_dir = 'Tests/steps'
	if os.path.exists(steps_dir):
		common_steps_path = os.path.join(steps_dir, 'common_steps.py')
		if os.path.exists(common_steps_path):
			context.config.steps_dir = steps_dir
			context.config.steps_file = ['common_steps.py']


def setup_client_with_stdout_capture(context):
	"""Setting up client with stdout capture"""
	if not hasattr(context, 'client'):
		context.client = CloudComputeClient()
	
	if hasattr(context, 'stdout_capture') and context.stdout_capture:
		try:
			context.stdout_capture.truncate(0)
			context.stdout_capture.seek(0)
		except Exception:
			pass


def setup_server_with_security_checker(context):
	"""Starting server with security checks enabled"""
	try:
		step_server_running_with_feature(context, "security checker")
	except Exception as e:
		print(f"WARNING: Failed to set up server with security checker: {e}")


def before_scenario(context, scenario):
	"""Function called before each scenario"""
	context.server_process = None
	context.temp_file_path = None
	context.result = None
	context.clients = []
	context.all_results = []
	
	if 'client' in scenario.tags or 'common_client' in scenario.tags:
		setup_client_with_stdout_capture(context)
	
	if "security_checker" in scenario.tags:
		setup_server_with_security_checker(context)


def after_scenario(context, scenario):
	"""Function called after each scenario"""
	cleanup_resources(context) 