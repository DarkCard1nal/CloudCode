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
			    "error": "File is not provided or does not have a name",
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

		created_files = []
		env = os.environ.copy()
		env["PYTHONUNBUFFERED"] = "1"  # Ensure unbuffered output

		try:
			process = subprocess.Popen(["python", "-u", filename],
			                           stdout=subprocess.PIPE,
			                           stderr=subprocess.PIPE,
			                           text=True,
			                           cwd=unique_folder,
			                           env=env)

			total_timeout = Config.EXECUTION_TIMEOUT + Config.GRACE_PERIOD
			try:
				out, err = process.communicate(timeout=total_timeout)
			except subprocess.TimeoutExpired:
				process.kill()
				out, err = process.communicate()
				out += "\nExecution time out, code 500"

			output = out
			error = err.strip()
		except Exception as e:
			output = ""
			error = f"Unexpected error: {str(e)}"
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

		return {"output": output, "error": error, "files": created_files}
