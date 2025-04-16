import docker
import os
import uuid
import shutil
from urllib3.exceptions import ReadTimeoutError
from requests.exceptions import ConnectionError
from Server.config import Config

class CodeExecutor:

	@staticmethod
	def execute_code(file):
		"""Processing code execution from the transferred file."""
		if not file or file.filename == "":
			return {
			    "error": "File is not provided or does not have a name",
				"status": 400,
			    "output": "",
			    "files": []
			}

		# Create a unique directory for each request
		unique_folder = os.path.join(Config.UPLOAD_FOLDER, uuid.uuid4().hex)
		os.makedirs(unique_folder, exist_ok=True)

		# Save the file as script.py in the unique folder
		filename = "script.py"
		filepath = os.path.join(unique_folder, filename)
		file.save(filepath)
		
		if not os.path.exists(filepath):
			return {
                "error": "File is not saved on the server",
                "status": 500,
                "output": "",
                "files": []
            }
		
		created_files = []
		output = ""
		error = ""

		docker_client = docker.from_env()

		try:
			container = docker_client.containers.run(
				image="python:3.10.6-slim",
				working_dir=f"{unique_folder}",
				environment={"PYTHONUNBUFFERED": "1"},
				detach=True,
				volumes={
					'cloudcode_uploads': {
						'bind': f"{Config.UPLOAD_FOLDER}",
						'mode': 'rw'
					}
				},
				command=["python", "-u", filename]
			)

			try:
				container.wait(timeout=Config.EXECUTION_TIMEOUT)
			except (ReadTimeoutError, ConnectionError, docker.errors.DockerException):
				container.kill()
				error += "Execution time exceeded limit\n"
				return {
					"error": error.strip(),
					"status": 206,
					"output": output.strip(),
					"files": []
				}
			
			output += container.logs(stdout=True, stderr=False).decode("utf-8")
			stderr_output = container.logs(stdout=False, stderr=True).decode("utf-8").strip()
			error += stderr_output

			if error:
				return {
					"error": error,
					"status": 422,
					"output": output.strip(),
					"files": []
				}
			
		except Exception as e:
			return {
				"error": f"Unexpected error: {str(e)}",
				"status": 500,
				"output": "",
				"files": []
			}
		finally:
			# Collect all created files except the source code
			for item in os.listdir(unique_folder):
				item_path = os.path.join(unique_folder, item)
				if os.path.isfile(item_path) and item != "script.py":
					with open(item_path, "r", encoding="utf-8") as f:
						created_files.append({
						    "filename": item,
						    "content": f.read()
						})
			# Delete the folder after execution
			shutil.rmtree(unique_folder, ignore_errors=True)

			try:
				container.remove(force=True)
			except Exception:
				pass

		return {"output": output.strip(), "files": created_files}
