import subprocess
import os
import uuid
import shutil
from Server.config import Config


class CodeExecutor:

	@staticmethod
	def execute_code(file):
		"""Processing code execution from the transferred file."""
		if not file or file.filename == "":
			return {
			    "error": "File is not provided or does not have a name"
			}, 400

		# Create a unique directory for each request
		unique_folder = os.path.join(Config.UPLOAD_FOLDER, uuid.uuid4().hex)
		os.makedirs(unique_folder, exist_ok=True)

		# Path to the file to be executed
		filename = "script.py"
		filepath = os.path.join(unique_folder, filename)
		file.save(filepath)

		try:
			# Executing the code in this folder
			result = subprocess.run(["python", filename],
			                        capture_output=True,
			                        text=True,
			                        cwd=unique_folder,
			                        timeout=Config.EXECUTION_TIMEOUT)

			output = result.stdout
			error = result.stderr

			# Collect the created files in this folder
			created_files = []
			for item in os.listdir(unique_folder):
				item_path = os.path.join(unique_folder, item)
				if os.path.isfile(
				    item_path
				) and item != "script.py":  # All files except the source code
					with open(item_path, "r", encoding="utf-8") as f:
						created_files.append({
						    "filename": item,
						    "content": f.read()
						})

		except subprocess.TimeoutExpired:
			return {"error": "Execution time out"}, 500
		finally:
			# Deleting the created folder after processing
			shutil.rmtree(unique_folder, ignore_errors=True)

		return {"output": output, "error": error, "files": created_files}
