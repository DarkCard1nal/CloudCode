import requests
import os
import threading
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
			response = requests.post(self.api_url, files=files, headers=headers)

		return response.json()

	def send_sequential(self):
		"""Sends all files from TASKS_FOLDER one by one."""
		print("\n--- Sending files one by one ---\n")
		for file_name in os.listdir(self.tasks_folder):
			file_path = os.path.join(self.tasks_folder, file_name)
			if file_name.endswith(".py"):
				result = self.send_code(file_path)
				print(f"File: {file_name}\nResult: {result}\n")

	def send_parallel(self):
		"""Sends all files at once and waits for a response."""
		print("\n--- Sending files in parallel ---\n")
		threads = []
		results = {}

		def task(file_name):
			file_path = os.path.join(self.tasks_folder, file_name)
			if file_name.endswith(".py"):
				results[file_name] = self.send_code(file_path)

		# Run each request in a separate thread
		for file_name in os.listdir(self.tasks_folder):
			thread = threading.Thread(target=task, args=(file_name,))
			threads.append(thread)
			thread.start()

		# We are waiting for the completion of all streams
		for thread in threads:
			thread.join()

		# Displaying the results
		for file_name, result in results.items():
			print(f"File: {file_name}\nResult: {result}\n")
