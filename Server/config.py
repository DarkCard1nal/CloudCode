import os


class Config:
	UPLOAD_FOLDER = "uploads"
	PORT = 5000
	DEBUG = True
	EXECUTION_TIMEOUT = 10  # in sec
	GRACE_PERIOD = 2  # Additional time in seconds after timeout in sec
	ERRORS = (400, 409, 422, 500, 503)

	@staticmethod
	def init():
		os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
