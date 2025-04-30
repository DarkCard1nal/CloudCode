import pyodbc
import os

class Database:
    def __init__(self, server, database, user, password):
        self.connection = self._connect(server, database, user, password)
        self._ensure_tables()

    def __del__(self):
        if hasattr(self, "connection"):
            self.connection.close()

    def _connect(self, server, database, user, password):
        return pyodbc.connect(
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"UID={user};"
            f"PWD={password};"
            "TrustServerCertificate=yes;"
        )

    def _ensure_tables(self):
        path = os.path.join(os.path.dirname(__file__), "SETUP.sql")
        with open(path, "r") as file:
            sql = file.read()
            cursor = self.connection.cursor()
            cursor.execute(sql)
            self.connection.commit()
            cursor.close()

    def is_api_key_valid(self, api_key: str) -> bool:
        cur = self.connection.cursor()
        cur.execute("SELECT 1 FROM Users WHERE api_key = ?", (api_key,))
        row = cur.fetchone()
        cur.close()
        return row is not None

    def add_user(self, username, email, api_key):
        cursor = self.connection.cursor()
        cursor.execute(
            "INSERT INTO Users (username, email, api_key) VALUES (?, ?, ?)",
            (username, email, api_key)
        )
        self.connection.commit()
        cursor.close()
