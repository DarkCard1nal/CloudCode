from flask import Flask, request, jsonify
from Server.config import Config
from Server.executor import CodeExecutor
from Server.metrics import Metrics
import time

class CodeExecutionServer:

	def __init__(self):
		self.app = Flask(__name__)
		self.metrics = Metrics()
		self.setup_routes()
		self.setup_metrics()
	
	def setup_metrics(self):
		"""Sets a default value to ensure it always returns data."""
		for code in Config.ERRORS:
			self.metrics.failure_count.labels(endpoint=str(code)).inc(0)

	def setup_routes(self):
		"""Set up API routes."""

		@self.app.route("/execute", methods=["POST"])
		def execute():
			"""Processes requests for code execution."""
			start_time = time.time()
			self.metrics.request_count.labels(method="POST", endpoint="/execute").inc()

			if "file" not in request.files:
				self.metrics.failure_count.labels(endpoint="400").inc()
				return jsonify({"error": "No file"}), 400

			result = CodeExecutor.execute_code(request.files.get("file"))

			latency = time.time() - start_time
			self.metrics.request_latency.labels(endpoint="/execute").observe(latency)

			if result.get("error"):
				status_code = result.get("status")
				if status_code in Config.ERRORS:
					self.metrics.failure_count.labels(endpoint=str(status_code)).inc()
				return jsonify(result), status_code
			else:
				self.metrics.success_count.labels(endpoint="/execute").inc()
				return jsonify(result), 200
		
		@self.app.route("/metrics", methods=["GET"])
		def metrics():
			"""Endpoint for Prometheus to scrape metrics."""
			return self.metrics.get_metrics()
		
		for code in Config.ERRORS:
			self.app.register_error_handler(code, self.handle_errors)

	def handle_errors(self, error):
		status_code = getattr(error, "code", None)
		if status_code in Config.ERRORS:
			self.metrics.failure_count.labels(endpoint=str(status_code)).inc()
		return jsonify({"error": f"HTTP {status_code} error"}), status_code

	def run(self):
		"""Launches the server in multi-threaded mode."""
		self.app.run(debug=Config.DEBUG, port=Config.PORT, threaded=True)
