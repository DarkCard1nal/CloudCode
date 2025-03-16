import subprocess
import os
import uuid
from Server.config import Config


class CodeExecutor:

	@staticmethod
	def execute_code(file):
		"""Processing code execution from the transferred file."""
		if not file or file.filename == "":
			return {
			    "error": "File is not provided or does not have a name"
			}, 400

		# Generate a unique name for the file
		filename = f"{uuid.uuid4().hex}.py"
		filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
		file.save(filepath)

		try:
			# Run the code in a separate process
			result = subprocess.run(["python", filepath],
			                        capture_output=True,
			                        text=True,
			                        timeout=10)

			output = result.stdout
			error = result.stderr
		except subprocess.TimeoutExpired:
			return {"error": "Execution time out"}, 500
		finally:
			# Delete the file after execution
			os.remove(filepath)

		return {"output": output, "error": error}
