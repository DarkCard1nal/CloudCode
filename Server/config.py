import os


class Config:
    UPLOAD_FOLDER = "/uploads"  # Related to volumes 'uploads' in docker-compose.yaml
    PORT = 5000
    DEBUG = os.getenv("DEBUG_MODE", "false").lower() in ("true", "1", "yes")
    EXECUTION_TIMEOUT = 10  # in sec

    @staticmethod
    def init():
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
