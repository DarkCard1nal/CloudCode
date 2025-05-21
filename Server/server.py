from Server.database import Database
from flask import Flask, request, jsonify, send_from_directory
from Server.config import Config
from Server.executor import CodeExecutor
from Server.python_security_checker import PythonSecurityChecker
from flask_cors import CORS
import os
import pyodbc
import secrets
from Server.metrics import Metrics
import time


class CodeExecutionServer:

	def __init__(self):
		self.app = Flask(__name__)
		self.metrics = Metrics()
		self.setup_metrics()

		PythonSecurityChecker.setup(is_docker_environment=True)

		self.db = Database(server=Config.DB_SERVER,
		                   database=Config.DB_NAME,
		                   user=Config.DB_USER,
		                   password=Config.DB_PASSWORD)

		CORS(self.app)

		self.setup_routes()

	def handle_errors(self, error):
		"""Generic error handler for HTTP error codes."""
		code = getattr(error, 'code', 500)
		return jsonify({"error": f"An error occurred (status code: {code})"}), code

	def setup_metrics(self):
		"""Sets a default value to ensure it always returns data."""
		self.metrics.success_count.labels(method="POST", endpoint="/execute").inc(0)
		for code in Config.ERRORS:
			self.metrics.failure_count.labels(endpoint=str(code)).inc(0)

	def setup_routes(self):
		"""Set up API routes."""

		@self.app.route("/execute", methods=["POST"])
		def execute():
			"""Processes requests for code execution."""
			start_time = time.time()
			self.metrics.request_count.labels(method="POST", endpoint="/execute").inc()
	
			result = CodeExecutor.execute_code(request.files.get("file"))
			
			latency = time.time() - start_time
			self.metrics.request_latency.labels(endpoint="/execute").observe(latency)

			status_code = result.get("status", 200)
			if status_code != 200:
				if status_code in Config.ERRORS:
					self.metrics.failure_count.labels(endpoint=str(status_code)).inc()
				return jsonify(result), status_code

			self.metrics.success_count.labels(method="POST", endpoint="/execute").inc()
			return jsonify(result), 200
			
		@self.app.route("/metrics", methods=["GET"])
		def metrics():
			"""Endpoint for Prometheus to scrape metrics."""
			return self.metrics.get_metrics()
		
		for code in Config.ERRORS:
			self.app.register_error_handler(code, self.handle_errors)

		@self.app.route("/process-code", methods=["POST", "OPTIONS"])
		def process_code():
			"""Processes code file from web client."""
			if request.method == "OPTIONS":
				return {"message": "OK"}, 200

			auth_header = request.headers.get("Authorization")

			if not auth_header or not auth_header.startswith("Bearer "):
				return jsonify({"error": "Missing or malformed API key"}), 401

			api_key = auth_header.replace("Bearer ", "").strip()

			if not self.db.is_api_key_valid(api_key):
				return jsonify({"error": "Invalid API key"}), 403

			file = request.files.get("codeFile")

			if not file:
				return jsonify({"error": "File not provided"}), 400

			result = CodeExecutor.execute_code(file)
			return jsonify(result)

		@self.app.route("/register", methods=["POST"])
		def register_user():
			"""Registers new user with username, email and generated API key."""
			data = request.get_json()

			username = data.get("username", "").strip()
			email = data.get("email", "").strip()

			if not username or not email:
				return jsonify({"error": "Missing required fields"}), 400

			api_key = secrets.token_hex(10)

			try:
				self.db.add_user(username, email, api_key)
				return jsonify({
				    "message": "User registered successfully",
				    "api_key": api_key
				}), 200
			except pyodbc.IntegrityError:
				return jsonify({
				    "error":
				        "User with this username or email or API key already exists"
				}), 409
			except Exception as e:
				return jsonify({"error": f"Internal server error: {str(e)}"
				               }), 500

		@self.app.route("/", defaults={"path": "index.html"})
		@self.app.route("/<path:path>")
		def serve_webclient(path):
			"""Serve WebClient static files."""
			webclient_dir = os.path.join(
			    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
			    "WebClient")
			return send_from_directory(webclient_dir, path)

	def run(self):
		"""Launches the server in multi-threaded mode."""
		self.app.run(host="0.0.0.0", port=Config.PORT, threaded=True)
