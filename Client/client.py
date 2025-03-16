import requests
import os
import threading
import time
from Client.config import Config


class CloudComputeClient:

	def __init__(self):
		self.api_url = Config.API_URL
		self.api_key = Config.API_KEY
		self.tasks_folder = Config.TASKS_FOLDER

	def send_code(self, file_path):
		"""Sends a single file to the server and returns a response."""
		with open(file_path, "rb") as f:
			files = {"file": f}
			headers = {"Authorization": f"Bearer {self.api_key}"}

			start_time = time.time()
			response = requests.post(self.api_url, files=files, headers=headers)
			end_time = time.time()

			execution_time = (end_time - start_time) * 1000
			result = response.json()
			result["execution_time_ms"] = execution_time

		return result

	def display_result(self, file_name, result):
		"""Formats and prints the execution result in a structured way."""
		print(f"\n--- Result for {file_name} ---\n")

		# Displaying files received in response
		if "files" in result and result["files"]:
			print("Generated Files:")
			for file in result["files"]:
				print(f"\nFile: {file['filename']}\n--- Content ---")
				content_lines = file["content"].splitlines()

				if len(content_lines) > 10:
					display_lines = (
					    content_lines[:5] + ["..."] + content_lines[-5:]
					)  # Limit 5 lines at the beginning and 5 at the end
				else:
					display_lines = content_lines

				for line in display_lines:
					print(line)
			print("\n-------------------\n")
		else:
			print("No additional files generated.\n")

		# Output from the executed code
		if "output" in result:
			print("Output:")
			output_lines = result["output"].splitlines()
			if len(output_lines) > 10:
				display_output = output_lines[:5] + ["..."] + output_lines[-5:]
			else:
				display_output = output_lines

			for line in display_output:
				print(line)
			print("\n-------------------\n")

		# Display of errors
		if "error" in result and result["error"]:
			print(f"Error: {result['error']}\n")

		# Execution time
		print(f"Execution time: {result['execution_time_ms']:.2f} ms")
		print("\n======================\n")

	def send_single_task(self, file_path):
		"""Sends a single specified task file to the server."""
		if not os.path.exists(file_path):
			print(f"Error: File '{file_path}' not found.")
			return

		file_name = os.path.basename(file_path)

		print(f"\n--- Sending single task: {file_name} ---\n")
		result = self.send_code(file_path)
		self.display_result(file_name, result)

	def send_sequential(self):
		"""Sends all files from TASKS_FOLDER one by one."""
		print("\n--- Sending files one by one ---\n")

		start_time = time.time()

		for file_name in os.listdir(self.tasks_folder):
			if file_name.startswith(".") or not file_name.endswith(".py"):
				continue  # Skip files starting with '.'

			file_path = os.path.join(self.tasks_folder, file_name)
			if file_name.endswith(".py"):
				result = self.send_code(file_path)
				self.display_result(file_name, result)

		end_time = time.time()
		total_execution_time = (end_time - start_time) * 1000

		print(
		    f"\nTotal execution time of sequential requests: {total_execution_time:.2f} ms\n"
		)

	def send_parallel(self):
		"""Sends all files at once and waits for a response."""
		print("\n--- Sending files in parallel ---\n")
		threads = []
		results = {}

		def task(file_name):
			file_path = os.path.join(self.tasks_folder, file_name)
			if file_name.endswith(".py"):
				results[file_name] = self.send_code(file_path)

		start_time = time.time()

		# Run each request in a separate thread
		for file_name in os.listdir(self.tasks_folder):
			if file_name.startswith(".") or not file_name.endswith(".py"):
				continue  # Skip files starting with '.'

			thread = threading.Thread(target=task, args=(file_name,))
			threads.append(thread)
			thread.start()

		# We are waiting for the completion of all streams
		for thread in threads:
			thread.join()

		end_time = time.time()
		total_execution_time = (end_time - start_time) * 1000

		# Displaying the results
		for file_name, result in results.items():
			self.display_result(file_name, result)

		print(
		    f"\nTotal execution time of parallel requests: {total_execution_time:.2f} ms\n"
		)
