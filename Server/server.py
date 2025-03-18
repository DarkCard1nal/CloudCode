from flask import Flask, request, jsonify
from Server.config import Config
from Server.executor import CodeExecutor
from Server.metrics import REQUEST_COUNT, SUCCESS_COUNT, FAILURE_COUNT, REQUEST_LATENCY, get_metrics
import time

class CodeExecutionServer:

	def __init__(self):
		self.app = Flask(__name__)
		self.setup_routes()
		self.setup_metrics()
	
	def setup_metrics(self):
		"""Sets a default value to ensure it always returns data."""
		FAILURE_COUNT.labels(endpoint="404").inc(0)

	def setup_routes(self):
		"""Set up API routes."""

		@self.app.route("/execute", methods=["POST"])
		def execute():
			"""Processes requests for code execution."""
			start_time = time.time()
			REQUEST_COUNT.labels(method="POST", endpoint="/execute").inc()

			result = CodeExecutor.execute_code(request.files.get("file"))

			latency = time.time() - start_time
			REQUEST_LATENCY.labels(endpoint="/execute").observe(latency)

			if not result.get("error"):
				SUCCESS_COUNT.labels(endpoint="/execute").inc()
			else:
				FAILURE_COUNT.labels(endpoint="/execute").inc()

			return jsonify(result)
		
		@self.app.route("/metrics", methods=["GET"])
		def metrics():
			"""Endpoint for Prometheus to scrape metrics."""
			return get_metrics()
		
		@self.app.errorhandler(404)
		def not_found(error):
			"""Handles 404 errors and registers them in failure metrics."""
			FAILURE_COUNT.labels(endpoint="404").inc()
			return jsonify({"error": "Endpoint not found"}), 404

	def run(self):
		"""Launches the server in multi-threaded mode."""
		self.app.run(debug=Config.DEBUG, port=Config.PORT, threaded=True)
