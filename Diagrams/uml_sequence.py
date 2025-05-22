from plantuml import PlantUML

plantuml_code = """
@startuml
actor Client
participant "Web Interface" as Web
participant "CodeExecutionServer" as Server
participant "Database" as DB
participant "CodeExecutor" as Executor
participant "PythonSecurityChecker" as Checker

Client -> Web : Request (POST /process-code)
Web -> Server : HTTP POST /process-code

Server -> DB : is_api_key_valid(api_key)
DB --> Server : API key is valid

Server -> Executor : execute_code(file)
Executor -> Checker : check_file(file)
Checker --> Executor : safe file for execution

Executor --> Server : execution result
Server -> Web : HTTP Response (result)
Web -> Client : Answer (JSON)

@enduml
"""

formats = {
    "svg": "http://www.plantuml.com/plantuml/svg/",
    "png": "http://www.plantuml.com/plantuml/png/"
}

for ext, url in formats.items():
	server = PlantUML(url=url)
	result = server.processes(plantuml_code)

	file_path = f"Diagrams/{ext}/UML_diagram_sequence.{ext}"
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
