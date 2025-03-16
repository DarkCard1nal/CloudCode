import os


class Config:
	UPLOAD_FOLDER = "uploads"
	PORT = 5000
	DEBUG = True

	@staticmethod
	def init():
		os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
