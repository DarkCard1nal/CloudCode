from Server.database import Database
from Server.config import Config

if __name__=="__main__":
    db = Database(
        server=Config.DB_SERVER,
        database=Config.DB_NAME,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD
    )

    username = "LiamTest"
    email = "liamtest@email.com"
    api_key = "my_secret_key"

    db.add_user(username, email, api_key)
    print(f"User has been added!")