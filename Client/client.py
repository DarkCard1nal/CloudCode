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

	def send_sequential(self):
		"""Sends all files from TASKS_FOLDER one by one."""
		print("\n--- Sending files one by one ---\n")

		start_time = time.time()

		for file_name in os.listdir(self.tasks_folder):
			file_path = os.path.join(self.tasks_folder, file_name)
			if file_name.endswith(".py"):
				result = self.send_code(file_path)
				print(
				    f"File: {file_name}\nResult: {result}\nExecution time: {result['execution_time_ms']:.2f} ms\n"
				)

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
			print(
			    f"File: {file_name}\nResult: {result}\nExecution time: {result['execution_time_ms']:.2f} ms\n"
			)

		print(
		    f"\nTotal execution time of parallel requests: {total_execution_time:.2f} ms\n"
		)
