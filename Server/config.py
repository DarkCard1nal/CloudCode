import os


class Config:
	UPLOAD_FOLDER = "/uploads"
	PORT = 5000
	DEBUG = os.getenv("DEBUG_MODE", "false").lower() in ("true", "1", "yes")
	EXECUTION_TIMEOUT = 10  # in sec
	ERRORS = (400, 409, 422, 500, 503)

	@staticmethod
	def init():
		os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
