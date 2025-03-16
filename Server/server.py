from flask import Flask, request, jsonify
from Server.config import Config
from Server.executor import CodeExecutor
import threading


class CodeExecutionServer:

	def __init__(self):
		self.app = Flask(__name__)
		self.setup_routes()

	def setup_routes(self):
		"""Set up API routes."""

		@self.app.route("/execute", methods=["POST"])
		def execute():
			"""Processes requests for code execution."""
			result = CodeExecutor.execute_code(request.files.get("file"))
			return jsonify(result)

	def run(self):
		"""Launches the server in multi-threaded mode."""
		self.app.run(debug=Config.DEBUG, port=Config.PORT, threaded=True)
