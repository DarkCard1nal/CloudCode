from plantuml import PlantUML

plantuml_code = """
@startuml

class CodeExecutionServer {
  -app
  -db

  +__init__()
  +run() : void
  -setup_routes() : void
}

class PythonSecurityChecker {
  DANGEROUS_MODULES : Set[str]
  SAFE_MODULES : Set[str]
  DANGEROUS_OPERATIONS : Set[str]
  SSRF_KEYWORDS : Set[str]
  DANGEROUS_URL_SCHEMES : Set[str]
  DANGEROUS_VARIABLE_NAMES : Set[str]
  REGEX_PATTERNS : List[Tuple[str, str, str]]
  SENSITIVE_DATA_PATTERNS : List[Tuple[str, str]]

  +__init__()
  +setup(max_file_size : int = 1024 * 1024, is_docker_environment : bool = False) : List[Tuple[str, str]]
  +check_file(file_path: str) : str
  +get_unsafe_operations() : List[Dict[str, Any]]

  -_validate_file(file_path: str) : void
  -_detect_unsafe_code(content: str) : Tuple[List[Dict[str, Any]], List[int]]
  -_create_safe_content(content: str, unsafe_lines: List[int]) : str
  -_is_safe_import(line: str) : bool
  -_create_safe_file(original_path: str, safe_content: str) : str
}

class Config {
  +UPLOAD_FOLDER : str = "/uploads"
  +PORT : int = 5000
  +DEBUG : bool
  +EXECUTION_TIMEOUT : int = 10

  +DB_SERVER : str
  +DB_NAME : str
  +DB_USER : str
  +DB_PASSWORD : str

  +init()
}

class Database {
  -connection

  +__init__(server : str, database : str, user : str, password : str)
  +__del__()
  +is_api_key_valid(api_key : str) : bool
  +add_user(username, email, api_key) : void
  -_connect(server : str, database : str, user : str, password : str)
  -_ensure_tables()
}

class CodeExecutor {
  +execute_code(file : str) : dict[str, Any]
}

CodeExecutionServer o-- "1" Config : has
CodeExecutionServer o-- "1" Database : has
CodeExecutionServer o-- "1" PythonSecurityChecker : has

CodeExecutionServer --> CodeExecutor : calls

CodeExecutor --> PythonSecurityChecker : uses

@enduml
"""

formats = {
    "svg": "http://www.plantuml.com/plantuml/svg/",
    "png": "http://www.plantuml.com/plantuml/png/"
}

for ext, url in formats.items():
	server = PlantUML(url=url)
	result = server.processes(plantuml_code)

	file_path = f"Diagrams/{ext}/UML_diagram_class.{ext}"
	if ext == "svg":
		if isinstance(result, bytes):
			result = result.decode('utf-8')
		with open(file_path, "w", encoding="utf-8") as file:
			file.write(result)
	else:  # PNG
		if isinstance(result, bytes):
			with open(file_path, "wb") as file:
				file.write(result)
		else:
			print(f"Failed to generate {ext.upper()}")
