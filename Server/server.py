from flask import Flask, request, jsonify, send_from_directory
from Server.config import Config
from Server.executor import CodeExecutor
from flask_cors import CORS
import os


class CodeExecutionServer:

    def __init__(self):
        self.app = Flask(__name__)
    
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
                
            file = request.files.get("codeFile")
            
            if not file:
                return jsonify({"error": "File not provided"}), 400

            result = CodeExecutor.execute_code(file)
            return jsonify(result)
            
        @self.app.route("/", defaults={"path": "index.html"})
        @self.app.route("/<path:path>")
        def serve_webclient(path):
            """Serve WebClient static files."""
            webclient_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "WebClient")
            return send_from_directory(webclient_dir, path)

    def run(self):
        """Launches the server in multi-threaded mode."""
        self.app.run(host="0.0.0.0", port=Config.PORT, threaded=True)
