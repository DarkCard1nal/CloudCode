import os
from Client.client import CloudComputeClient

from Tests.common.steps.common_steps import step_server_running_with_feature, cleanup_resources

def before_all(context):
	"""Function called before all tests"""
	context.config.paths.append('Tests/common/steps')
	context.config.paths.append('Tests/server/features/steps')
	context.config.paths.append('Tests/client/features/steps')
	
	steps_dir = 'Tests/common/steps'
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