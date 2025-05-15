from Server.database import Database
from flask import Flask, request, jsonify, send_from_directory
from Server.config import Config
from Server.executor import CodeExecutor
from flask_cors import CORS
import os
import pyodbc
import secrets


class CodeExecutionServer:

	def __init__(self):
		self.app = Flask(__name__)

		self.db = Database(
			server=Config.DB_SERVER,
			database=Config.DB_NAME,
			user=Config.DB_USER,
			password=Config.DB_PASSWORD
		)

		CORS(self.app)

		self.setup_routes()

	def setup_routes(self):
		"""Set up API routes."""

		@self.app.route("/execute", methods=["POST"])
		def execute():
			"""Processes requests for code execution."""
			result = CodeExecutor.execute_code(request.files.get("file"))
			return jsonify(result)

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
				return jsonify({"message": "User registered successfully", "api_key": api_key}), 200
			except pyodbc.IntegrityError:
				return jsonify({"error": "User with this username or email or API key already exists"}), 409
			except Exception as e:
				return jsonify({"error": f"Internal server error: {str(e)}"}), 500

		@self.app.route("/", defaults={"path": "index.html"})
		@self.app.route("/<path:path>")
		def serve_webclient(path):
			"""Serve WebClient static files."""
			webclient_dir = os.path.join(
				os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "WebClient"
			)
			return send_from_directory(webclient_dir, path)

	def run(self):
		"""Launches the server in multi-threaded mode."""
		self.app.run(host="0.0.0.0", port=Config.PORT, threaded=True)
