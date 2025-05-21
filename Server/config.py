import os


class Config:
	UPLOAD_FOLDER = "/uploads"  # Related to volumes 'uploads' in docker-compose.yaml
	PORT = 5000
	DEBUG = os.getenv("DEBUG_MODE", "false").lower() in ("true", "1", "yes")
	EXECUTION_TIMEOUT = 10  # in sec
	ERRORS = (400, 422, 500, 503)

	DB_SERVER = os.getenv("DB_SERVER", "localhost")
	DB_NAME = os.getenv("DB_NAME", "cloudcode")
	DB_USER = os.getenv("DB_USER", "sa")
	DB_PASSWORD = os.getenv("DB_PASSWORD", "YourStrong!Passw0rd")

	@staticmethod
	def init():
		os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
