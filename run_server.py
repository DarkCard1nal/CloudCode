from Server.server import CodeExecutionServer
from Server.config import Config

if __name__ == "__main__":
    Config.init()  # Initializing the configuration
    server = CodeExecutionServer()
    server.run()
